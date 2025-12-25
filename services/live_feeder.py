# live_prediction_feeder.py
from data_sources.unified_sentinel import UnifiedSentinel
from logic.optimizer import SentinelOptimizer
import time
from infrastructure.config import config

"""
Live Feed Service.

This module acts as the "Real-Time Pulse" of the Sentinel system.
It runs a continuous loop that periodically fetches the latest market prices,
generates fresh demand predictions, and updates the immediate-term procurement plan.
"""

class SentinelLiveEngine:
    """
    Orchestrates the real-time inference and optimization loop.

    Attributes:
        sentinel (UnifiedSentinel): Interface to data sources and prediction logic.
        optimizer (SentinelOptimizer): Optimization engine configured for global immediate decisions.
    """
    def __init__(self, keys, db_config):
        """
        Initialize the Live Engine.

        Args:
            keys (dict): API keys for external services.
            db_config (dict): Database arguments.
        """
        self.sentinel = UnifiedSentinel(keys, db_config=db_config)
        # Lead times are critical for the 'Specialty' material pillar
        # Initializing for 'GLOBAL' scope with a default 30-day lead time
        self.optimizer = SentinelOptimizer(material_name="GLOBAL", lead_time_days=30)


    def run_inference_cycle(self):
        """
        Executes a single pass of the intelligence loop:
        1. Fetch Price -> 2. Predict Demand -> 3. Optimize Order -> 4. Persist Result.
        """
        # 1. Fetch current global market state
        for mat_name, mat_data in self.sentinel.materials.items():
            # Get real-time price snapshot
            price, _ = self.sentinel.fetch_price(mat_name)
            
            # 2. Layer 2: Prediction (Heuristic or ML)
            # Predict demand for the GLOBAL scope
            prediction = self.sentinel.predict_demand("GLOBAL", mat_name)
            
            # 3. Layer 4: Optimization (Decision)
            # We assume a 4-week horizon for the live feeder to keep it tactical
            # Current stock is hardcoded to 100 for this demo context
            plan = self.optimizer.optimize_procurement([prediction]*4, [price]*4, current_stock=100)
            
            # Simple binary recommendation based on immediate week's need
            recommendation = "BUY" if plan[0] > 0 else "WAIT"
            
            # 4. Persistence: Store raw data and AI signal
            # This enables the 'Hover' and 'Click' dashboard functionality to show live status
            self.sentinel.save_signal_to_db(mat_name, price, prediction, recommendation)
            
            print(f"📡 [LIVE] {mat_name}: Price ${price:.2f} | Prediction: {prediction} | Decision: {recommendation}")

    def start(self):
        """
        Starts the infinite loop for live monitoring.
        """
        print("🚀 Sentinel Live Feed & Inference Started...")
        while True:
            self.run_inference_cycle()
            # Scan every minute for LME volatility or new data
            time.sleep(60) 

if __name__ == "__main__":
    # Initialize implementation using Vault-backed config
    try:
        engine = SentinelLiveEngine(config.KEYS, config.DB_CONFIG)
        engine.start()

    except Exception as e:
        print(f"❌ Critical Startup Error: {e}")