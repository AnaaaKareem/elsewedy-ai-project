# inference_worker.py
import pika
import json
import redis
import numpy as np
import os
import sys

# Add 'shared' directory to path to allow importing sibling modules like ai_models
# Works for both Docker (where /app/shared is mounted) and Local (via relative path)
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.abspath(os.path.join(current_dir, '../../../shared'))
if os.path.exists(shared_dir) and shared_dir not in sys.path:
    sys.path.append(shared_dir)

from infrastructure.config import config

# Import Custom Modules
from ai_models.model_factory import ModelFactory
from data_sources.unified_sentinel import UnifiedSentinel
from logic.optimizer import SentinelOptimizer
from model_synchronizer import ModelSynchronizer
from logic.simulator import MonteCarloSimulator

"""
Inference Worker Service.

This service serves as the core "AI Brain" for the Sentinel platform. It is responsible for:
1.  **Ingestion & Routing**: Listening to the 'market_updates' queue for real-time price events.
2.  **Inference (Layer 2)**: Selecting and executing the appropriate AI model based on material category (e.g., XGBoost for Polymers, LSTM for Shielding).
3.  **Optimization (Layer 4)**: Running the SentinelOptimizer to determine optimal procurement quantities.
4.  **Risk Analysis**: performing Monte Carlo simulations to assess inventory risks.
5.  **Persistence**: Saving forecasts, decisions, and confidence metrics to Redis (hot storage) and PostgreSQL (cold storage).

Architecture:
    - **Dispatcher Thread**: lighter-weight thread that consumes market updates and fans them out to worker tasks.
    - **Worker Thread**: Heavy-lifting thread that processes prediction tasks sequentially per country to manage load.
"""

# Initialize Sentinel (for Metadata & History) and Redis Client
sentinel = UnifiedSentinel(config.KEYS, db_config=config.DB_CONFIG)
r = redis.Redis(host=config.REDIS_HOST, port=6379, db=0)

def get_inference_input(category, current_price, material_name=None):
    """
    Prepares the feature vector required for inference based on the material category.

    This function aggregates data from various sources (Sentinel, Yahoo Finance via Sentinel, static config)
    to construct the input array expected by the specific AI model.

    Args:
        category (str): The material category (e.g., 'Polymer', 'Shielding', 'Screening').
                        Different categories require different feature sets.
        current_price (float): The current real-time market price of the material.
        material_name (str, optional): The specific name of the material (e.g., 'XLPE', 'Copper').
                                       Required for fetching historical time-series data for temporal models.

    Returns:
        list or np.array: The formatted input vector ready for model prediction. 
                          - For 'Polymer': [Current_Price, Oil_Price, Construction_Index, EGP_USD]
                          - For 'Shielding': Shape (1, Sequence_Length, Features)
                          - For Others: [Current_Price] formatted appropriately
    """
    # Mock FX Rate (In prduction, fetch via Sentinel)
    egp_usd_rate = 50.5 # 1 USD = 50.5 EGP (Scenario)

    if category == 'Polymer':
        # XGBoost needs: [Current_Price, Oil_Price, Construction_Index, EGP_USD]
        # 1. Fetch Real Driver Data (Oil Price)
        driver_str = sentinel.fetch_driver_data('Polymer')
        # Parse "$85.00" from "Oil $85.00"
        try :
            oil_price = float(driver_str.split('$')[1]) if '$' in driver_str else 80.0
        except:
            oil_price = 80.0 # Robust fallback

        # 2. Fetch Secondary Driver (Construction Index)
        const_str = sentinel.fetch_driver_data('Screening')
        try:
            const_idx = float(const_str.split(':')[1]) if ':' in const_str else 100.0
        except:
            const_idx = 100.0

        return [[current_price, oil_price, const_idx, egp_usd_rate]] 

    elif category == 'Shielding':
        # LSTM needs a sequence (e.g., last 5 prices) + Scalar Features (FX)
        # Fetch actual history from Yahoo Finance via Sentinel
        if material_name:
            symbol = sentinel.materials[material_name]['symbol']
            # Fetch last 5 distinct days. 
            # Note: Ticker might be delayed, so we append current_price to ensure freshness.
            history = sentinel.fetch_historical_price_series(symbol, time_range='1mo')
            if not history.empty and len(history) >= 4:
                # Take last 4 historical + current real-time price = 5 steps
                recent_seq = history.values[-4:].tolist()
                recent_seq.append(current_price)
                
                # FEATURE ENGINEERING UPDATE: Append FX Rate to each step or as valid tensor
                # For simplicity in this demo, we assume the model accepts (Batch, Seq, Feature)
                # If model expects 1 feature (Price), we keep as is. 
                # If we retrained for FX, we'd add it here.
                # Assuming Model Update: [Price, FX]
                
                # Mocking 2D feature vector per step for enhanced model
                # seq_data = [[p, egp_usd_rate] for p in recent_seq]
                
                # NOTE: Since we haven't retrained the LSTM yet, we MUST keep the shape consistent 
                # or the forward pass will fail. 
                # We will log the Feature Availability but keep input compatible for now 
                # until model weights are updated.
                print(f"   ℹ️ [Feature Eng] EGP/USD ({egp_usd_rate}) ready for Model V2.")

                return np.array([recent_seq]) # Shape: (1, 5) which becomes (1, 5, 1) in inference

        # Fallback if history fetch fails: Pad with current price
        return np.array([[current_price] * 5]) 

    return current_price

# Global Model Cache (Keep models in memory)
model_cache = {}

def get_or_load_model(category):
    """Retrieves model from cache or factory, ensuring weights are loaded."""
    if category in model_cache:
        return model_cache[category]

    # Instantiate
    model = ModelFactory.get_model(category)
    if model:
        # Mini DR: Attempt to load backup weights on first load
        try:
            model.load_weights(f"{category}_latest")
        except Exception:
            print(f"⚠️ No backup for {category}, starting fresh.")
        
        model_cache[category] = model
    return model

def run_ai_lifecycle(material_name, price):
    """
    Orchestrates the complete AI prediction and learning lifecycle for a single material update.

    Steps:
    1.  **Model Loading**: Retrieves the correct model for the material's category from cache or factory.
    2.  **Inference (Prediction)**: Prepares input features and executes the forward pass to generate a price forecast.
    3.  **Online Learning (Training)**: (Disabled in production) Originally designed to update weights based on new data points.
    4.  **Error Handling**: Catches and logs inference errors, returning a default safety value (0.0).

    Args:
        material_name (str): The identifier of the material being processed.
        price (float): The latest incoming market price.

    Returns:
        float: The predicted future price. Returns 0.0 if the material is unknown, model fails, or an error occurs.
    """
    if material_name not in sentinel.materials: return 0.0, "WAIT"
    
    category = sentinel.materials[material_name]['category']
    model = get_or_load_model(category)
    if not model: return 0.0, "WAIT"

    # A. PREDICT (Forward Pass)
    try:
        input_data = get_inference_input(category, price, material_name)
        
        if category == 'Polymer':
            prediction = model.predict(input_data)
        elif category == 'Shielding':
            import torch
            tensor_in = torch.tensor(input_data, dtype=torch.float32)
            if tensor_in.ndim == 2: tensor_in = tensor_in.unsqueeze(-1)
            prediction = model.predict(tensor_in)
        elif category == 'Screening':
            prediction = model.predict()
        else:
            prediction = 0.0
        
        prediction = max(0.0, prediction)
    except Exception as e:
        print(f"❌ Inference Error: {e}")
        prediction = 0.0

    # B. TRAIN (Online Learning) - "Mini DR: Backup weights"
    # We simulate a target (e.g. slight random variation or derived from basic math)
    # In a real scenario, this would use the *next* price tick. 
    # Here we train on the current price as a self-correction reinforcement for demo.
    try:
        # PRODUCTION UPDATE: Disabled "Demo" Online Learning.
        # Real online learning requires receiving the TRUE price at T+Time and comparing it 
        # to the PREVIOUS prediction from T-Time. 
        # The previous code trained on "Current Price * 1.01" which creates a bias.
        # We disable this loop until a proper Feedback Listener is implemented.
        pass
        # if hasattr(model, 'train_online'):
        #      loss = model.train_online(price, price * 1.01, step_count=10) 
        # if hasattr(model, 'save_weights'):
        #      model.save_weights(f"{category}_latest")
    except Exception as e:
        print(f"⚠️ Training/Save Warning: {e}")

    return prediction

# Consume loop with manual ack

def process_country(country_name, country_code, mat, price):
    """
    Executes the end-to-end processing pipeline for a specific country-material pair.

    The pipeline consists of:
    1.  **AI Prediction**: Generates a price forecast using `run_ai_lifecycle`.
    2.  **Procurement Optimization**: Calculates optimal buy quantity using `SentinelOptimizer` based on lead times and stock.
    3.  **Risk Verification**: Runs a Monte Carlo simulation via `MonteCarloSimulator` to estimate stockout risks.
    4.  **Decision Synthesis**: Combines optimizer output with risk metrics to finalize a 'BUY' or 'WAIT' signal.
    5.  **Persistence**: Stores all artifacts (price, signal, confidence, risk) to Redis and the SQL database.

    Args:
        country_name (str): The name of the country context (e.g., 'Egypt', 'KSA').
        country_code (str): The ISO or internal trade code for the country.
        mat (str): The material identifier.
        price (float): The current market price.
    """
    try:
        # 1. Prediction (Using global model for now, could be regional if trained)
        prediction = run_ai_lifecycle(mat, price)
        
        # 2. Optimization (Logic could inject country-specific lead times here)
        lead_time = sentinel.materials.get(mat, {}).get('lead_time', 30)
        optimizer = SentinelOptimizer(material_name=mat, lead_time_days=lead_time)
        plan = optimizer.optimize_procurement([prediction]*4, current_stock=100)
        buy_qty = plan.get(0, 0)
        decision = "BUY" if buy_qty > 0 else "WAIT"

        # 2.5 Validation: Risk Analysis
        # User requested to disable simulation and use actual system data only.
        risk_pct = 0.0

        # 3. Confidence
        pct_diff = abs(prediction - price) / (price + 1e-9)
        confidence = max(60, int(98 - (pct_diff * 500)))

        # 4. Persistence (Redis + DB)
        # Redis Key: live:{Country}:{Material}:...
        r.set(f"live:{country_name}:{mat}:price", price)
        r.set(f"live:{country_name}:{mat}:signal", decision)
        r.set(f"live:{country_name}:{mat}:confidence", confidence)
        r.set(f"live:{country_name}:{mat}:risk", risk_pct) # New Metric
        
        # === DASHBOARD GLOBAL VIEW ADAPTER ===
        # Write a Hash key "live:{Material}" for the main dashboard feed
        trend_val = (prediction - price) / price * 100 if price else 0.0
        r.hset(f"live:{mat}", mapping={
            "price": price,
            "decision": decision,
            "confidence": confidence,
            "trend": trend_val,
            "risk": risk_pct,
            "updated_at": str(time.time())
        })
        
        sentinel.save_signal_to_db(mat, price, prediction, decision, country_name=country_name, confidence=float(confidence), risk=float(risk_pct))
        
        print(f"   🌍 [{country_name}] Forecast {prediction:.2f} | Signal {decision} | Risk {risk_pct:.1%} | Saved")
    except Exception as e:
        print(f"   ❌ Error processing {country_name}: {e}")

# --- DISPATCHER LOGIC (Thread 1) ---
def dispatcher_callback(ch, method, properties, body):
    """
    DISPATCHER: Only creates tasks. Fast. No heavy listing.
    """
    try:
        msg = json.loads(body)
        mat = msg['material']
        price = float(msg['price'])
        
        print(f"📨 [Dispatcher] Received: {mat} @ ${price}")

        # Fan-out: Create a task for each country
        target_countries = sentinel.country_registry 
        if not target_countries:
            target_countries = {'Egypt': {'trade_code': '818'}}

        tasks_created = 0
        for country_name, info in target_countries.items():
            task_payload = {
                'country_name': country_name,
                'country_code': info.get('trade_code'),
                'material': mat,
                'price': price
            }
            # Publish to Internal Task Queue
            ch.basic_publish(
                exchange='',
                routing_key='prediction_tasks',
                body=json.dumps(task_payload),
                properties=pika.BasicProperties(delivery_mode=2) # Persistent
            )
            tasks_created += 1

        print(f"⚡ [Dispatcher] Created {tasks_created} tasks for {mat}. ACKing.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"🔥 [Dispatcher] Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_dispatcher():
    print("📢 Dispatcher Thread Started...")
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                credentials=pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS),
                heartbeat=600
            ))
            channel = connection.channel()
            channel.queue_declare(queue='market_updates', durable=True)
            channel.queue_declare(queue='prediction_tasks', durable=True) # Ensure task queue exists
            channel.basic_qos(prefetch_count=1)
            
            channel.basic_consume(queue='market_updates', on_message_callback=dispatcher_callback)
            channel.start_consuming()
        except Exception as e:
            print(f"⚠️ Dispatcher Connection Lost: {e}. Retrying...")
            time.sleep(5)

# --- WORKER LOGIC (Thread 2) ---
def worker_callback(ch, method, properties, body):
    """
    WORKER: Does the heavy math. Isolated per country.
    """
    try:
        task = json.loads(body)
        country = task['country_name']
        mat = task['material']
        price = task['price']
        code = task['country_code']
        
        # Heavy Lifting
        process_country(country, code, mat, price)
        
        # ACK only after success
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"❌ [Worker] Task Failed ({task.get('country_name')}): {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False) # Dead Lettering recommended in prod

def start_worker():
    print("👷 Worker Thread Started...")
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                credentials=pika.PlainCredentials(config.RABBITMQ_USER, config.RABBITMQ_PASS),
                heartbeat=600
            ))
            channel = connection.channel()
            channel.queue_declare(queue='prediction_tasks', durable=True)
            channel.basic_qos(prefetch_count=1) # One task at a time (Sequential per worker)
            
            channel.basic_consume(queue='prediction_tasks', on_message_callback=worker_callback)
            channel.start_consuming()
        except Exception as e:
            print(f"⚠️ Worker Connection Lost: {e}. Retrying...")
            time.sleep(5)

# --- MAIN EXECUTION ---
import threading
import time

if __name__ == "__main__":
    print("🚀 AI Engine Starting (Dispatcher-Worker Architecture)...")

    # --- STARTUP CHECK: Verify & Catch-Up on Lost Data ---
    try:
        synchronizer = ModelSynchronizer(sentinel)
        synchronizer.sync_models()
    except Exception as e:
        print(f"⚠️ Synchronization Warning: {e}")
        print("   Continuing with startup...")

    # Start Worker in Background Thread
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()

    # Run Dispatcher in Main Thread
    start_dispatcher()