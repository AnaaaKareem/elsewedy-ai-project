import pickle
import os

try:
    import xgboost as xgb
    import lightgbm as lgb
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("⚠️ XGBoost/LightGBM not found. Using MockGBMModel.")

"""
Polymer Layers Model (Pillar 1).

This module implements Gradient Boosting Machine (GBM) wrappers for materials
whose prices/demand are driven by external macro-factors (e.g., Oil Prices, 
Construction Index). Best for XLPE, PVC.
"""

class SentinelGBMModel:
    """
    Wrapper for XGBoost/LightGBM regressors.
    
    Attributes:
        engine (str): Underlying library ('XGBoost' or 'LightGBM').
        model (object): The actual regressor instance.
    """
    def __init__(self, engine="XGBoost"):
        """
        Initialize the GBM model.
        Args:
            engine (str): Type of GBM to use. Directions: 'XGBoost', 'LightGBM'.
        """
        self.engine = engine
        if HAS_ML:
            if engine == "XGBoost":
                self.model = xgb.XGBRegressor(n_estimators=100, max_depth=5, eta=0.1)
            else:
                # Fallback or alternative
                self.model = lgb.LGBMRegressor()
        else:
            self.model = "MOCK_GBM_OBJECT"

    def train(self, X, y):
        """
        Train the model.
        
        Args:
            X (array-like): Feature matrix (e.g. [Price, Oil_Index, Construction_Index]).
            y (array-like): Target vector (Demand).
        """
        if HAS_ML:
            self.model.fit(X, y)
        else:
            pass # Mock Train

    def save_weights(self, filename):
        """Save model pickle."""
        os.makedirs("weights", exist_ok=True)
        with open(f"weights/{filename}.pkl", "wb") as f:
            pickle.dump(self.model, f)
        print(f"💾 Saved: weights/{filename}.pkl")

    def load_weights(self, filename):
        """Load model pickle."""
        path = f"weights/{filename}.pkl"
        if os.path.exists(path):
            with open(path, "rb") as f:
                self.model = pickle.load(f)
            print(f"✅ Loaded: {path}")

    def train_online(self, X_new, y_new, save_interval=10, step_count=0):
        """
        Refines the model with new data. 
        
        Note: True online learning with Trees is hard. efficient implementations 
        often reload the tree structure and update leaf weights, or just refit 
        on a sliding window. Here we wrap the update API if available.

        Args:
            X_new, y_new: New data point(s).
        """
        # For sklearn API, we can use 'fit' with xgb_model to continue training
        # But for simplicity/stability in this demo, we assume we are just verifying the API 
        if HAS_ML:
            # Using 'xgb_model' parameter allows continuation of training in XGBoost API
            self.model.fit(X_new, y_new, xgb_model=self.model.get_booster())
        else:
            pass # Mock Online Update
        
        if step_count > 0 and step_count % save_interval == 0:
            self.save_weights("polymer_xgb_checkpoint")
            print(f"🔄 Checkpoint saved at step {step_count}")