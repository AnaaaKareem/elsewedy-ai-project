# inference_worker.py
import pika
import json
import redis
import numpy as np
import os
import sys

# Add parent directory to path to allow importing sibling modules like ai_models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.config import config

# Import Custom Modules
from ai_models.model_factory import ModelFactory
from data_sources.unified_sentinel import UnifiedSentinel
from logic.optimizer import SentinelOptimizer

"""
Inference Worker Service.

This service executes the "Heavy Lifting" AI tasks. It listens to the 'market_updates'
queue for price events. Upon receiving an event:
1. Determines the material category.
2. Selects and runs the appropriate AI model (Layer 2).
3. Runs the Optimization logic (Layer 4).
4. Persists the results to Redis (Hot) and DB (Cold).
"""

# Initialize Sentinel (for Metadata & History) and Redis Client
sentinel = UnifiedSentinel(config.KEYS, db_config=config.DB_CONFIG)
r = redis.Redis(host=config.REDIS_HOST, port=6379, db=0)

def get_inference_input(category, current_price, material_name=None):
    """
    Prepares the specific input vector required by each model type using REAL data sources.
    
    Args:
        category (str): Material category (Polymer, Shielding, etc.).
        current_price (float): The current market price.
        material_name (str): The specific material name (needed for history fetch).
        
    Returns:
        list or np.array: The formatted input for the model.
    """
    if category == 'Polymer':
        # XGBoost needs: [Current_Price, Oil_Price, Construction_Index]
        # 1. Fetch Real Driver Data (Oil Price)
        driver_str = sentinel.fetch_driver_data('Polymer')
        # Parse "$85.00" from "Oil $85.00"
        try:
            oil_price = float(driver_str.split('$')[1]) if '$' in driver_str else 80.0
        except:
            oil_price = 80.0 # Robust fallback

        # 2. Fetch Secondary Driver (Construction Index)
        const_str = sentinel.fetch_driver_data('Screening')
        try:
            const_idx = float(const_str.split(':')[1]) if ':' in const_str else 100.0
        except:
            const_idx = 100.0

        return [[current_price, oil_price, const_idx]] 
        
    elif category == 'Shielding':
        # LSTM needs a sequence (e.g., last 5 prices)
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
                return np.array([[recent_seq]]) # Shape: (1, 5) or (1, 5, 1) depending on model
        
        # Fallback if history fetch fails: Pad with current price
        return np.array([[[current_price] * 5]]) 
        
    return current_price

def run_ai_inference(material_name, price):
    """
    Selects the correct model via Factory and runs prediction.
    
    Args:
        material_name (str): The material being analyzed.
        price (float): Current price.
        
    Returns:
        float: Predicted demand (clamped to >= 0).
    """
    # 1. Dynamic Category Lookup
    if material_name not in sentinel.materials:
        print(f"⚠️ Unknown material: {material_name}")
        return 0.0
        
    category = sentinel.materials[material_name]['category']
    
    # 2. Get the Brain (Model Instance)
    model = ModelFactory.get_model(category)
    if not model:
        return 0.0

    # 3. Prepare Data & Predict
    try:
        input_data = get_inference_input(category, price, material_name)
        
        if category == 'Polymer':
            # XGBoost Predict
            prediction = model.model.predict(input_data)[0]
        elif category == 'Shielding':
            # LSTM Predict (requires Tensor conversion if using PyTorch)
            import torch
            tensor_in = torch.tensor(input_data, dtype=torch.float32)
            # Ensure input shape matches model expectation (Batch, Seq, Feat)
            if tensor_in.ndim == 2: 
                tensor_in = tensor_in.unsqueeze(-1)
            prediction = model(tensor_in).item()
        elif category == 'Screening':
            # Croston's Predict (Statistical/Custom)
            prediction = model.predict()
        else:
            prediction = 0.0
            
        return max(0.0, prediction) # No negative demand
    except Exception as e:
        print(f"❌ Inference Failed for {material_name}: {e}")
        return 0.0

def callback(ch, method, properties, body):
    """
    RabbitMQ message handler. Triggered on every market update.
    """
    try:
        msg = json.loads(body)
        mat = msg['material']
        price = float(msg['price'])
        
        print(f"📨 Received: {mat} @ ${price}")

        # --- STEP 1: AI Prediction ---
        prediction = run_ai_inference(mat, price)
        
        # --- STEP 2: Optimization ---
        # Fetch specific lead time from metadata (default to 30 if missing)
        lead_time = sentinel.materials.get(mat, {}).get('lead_time', 30)
        
        optimizer = SentinelOptimizer(material_name=mat, lead_time_days=lead_time)
        # We project the single prediction out for 4 weeks for this demo
        plan = optimizer.optimize_procurement([prediction]*4, [price]*4, current_stock=100)
        
        # Decision Logic: If week 0 advice is positive, we buy
        buy_qty = plan.get(0, 0)
        decision = "BUY" if buy_qty > 0 else "WAIT"

        # --- STEP 3: System Updates ---
        # A. Update Redis (Hot Storage for Live Dashboard)
        r.set(f"live:{mat}:price", price)
        r.set(f"live:{mat}:signal", decision)
        r.set(f"live:{mat}:forecast", prediction)

        # B. Update TimescaleDB (Audit Trail / Long term storage)
        sentinel.save_signal_to_db(mat, price, prediction, decision)

        print(f"🤖 {mat}: Forecast {prediction:.2f} | Signal {decision} (Qty: {buy_qty:.2f})")

    except Exception as e:
        print(f"🔥 Worker Error: {e}")

# Start Consuming
print("👷 Inference Worker Started. Waiting for Market Data...")
connection = pika.BlockingConnection(pika.ConnectionParameters(config.RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue='market_updates')

# Consume loop
channel.basic_consume(queue='market_updates', on_message_callback=callback, auto_ack=True)
channel.start_consuming()