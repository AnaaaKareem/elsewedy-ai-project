import pickle
import os
import json
import numpy as np
from datetime import datetime

try:
    import xgboost as xgb
    import lightgbm as lgb
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("⚠️ XGBoost/LightGBM not found. Using MockGBMModel.")

"""
Polymer Layers Model (Pillar 1).

This module implements Gradient Boosting Machine (GBM) wrappers for materials driven
by external market factors (e.g., Oil Price, Construction Index). It supports
both XGBoost and LightGBM backends (defaulting to XGBoost).
"""

class SentinelGBMModel:
    """
    Wrapper for Gradient Boosting Regressors (XGBoost/LightGBM).

    Designed for "Polymer" category materials where price is strongly correlated
    with external macroeconomic indicators.

    Attributes:
        engine (str): The underlying library used ('XGBoost' or 'LightGBM').
        model (object): The actual regressor object.
        metadata (dict): storage for feature importance and update timestamps.
        
    Args:
        engine (str): backend to use. Defaults to "XGBoost".
    """
    def __init__(self, engine="XGBoost"):
        self.engine = engine
        if HAS_ML:
            if engine == "XGBoost":
                self.model = xgb.XGBRegressor(n_estimators=1000, max_depth=6, eta=0.05, n_jobs=-1)
            else:
                self.model = lgb.LGBMRegressor()
        else:
            self.model = "MOCK_GBM_OBJECT"
        self.metadata = {}

    def train(self, X, y):
        """
        Train the model on a full dataset.
        """
        if not HAS_ML:
            return

        # Sanity check
        if len(X) == 0 or len(y) == 0:
            print("⚠️ XGBoost Training skipped: No data provided.")
            return

        print(f"⚡ [Polymer] Training XGBoost on {len(X)} samples...")
        try:
            self.model.fit(X, y)
            print("   ✅ Training Complete.")
            
            # Optional: Store feature importance in metadata if possible
            if hasattr(self.model, 'feature_importances_'):
                self.metadata['feature_importance_top'] = float(np.max(self.model.feature_importances_))
                
        except Exception as e:
            print(f"❌ XGBoost Training Failed: {e}")

    def save_weights(self, filename):
        d = os.path.join(os.path.dirname(__file__), "weights")
        os.makedirs(d, exist_ok=True)
        
        # Save Pickle
        with open(os.path.join(d, f"{filename}.pkl"), "wb") as f:
            pickle.dump(self.model, f)
        print(f"💾 Saved: {d}/{filename}.pkl")
        
        # Save Metadata Sidecar
        meta_path = os.path.join(d, f"{filename}_meta.json")
        self.metadata['last_updated'] = datetime.now().isoformat()
        with open(meta_path, "w") as f:
            json.dump(self.metadata, f)

    def load_weights(self, filename):
        """Load model pickle."""
        d = os.path.join(os.path.dirname(__file__), "weights")
        path = os.path.join(d, f"{filename}.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                self.model = pickle.load(f)
            print(f"✅ Loaded: {path}")
            
            # Load Metadata Sidecar
            meta_path = os.path.join(d, f"{filename}_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                print(f"   + Metadata: Last Updated {self.metadata.get('last_updated')}")
            else:
                self.metadata = {}

    def train_online(self, X_new, y_new, save_interval=10, step_count=0):
        """
        Refines the model with new data. 
        """
        # For sklearn API, we can use 'fit' with xgb_model to continue training
        if HAS_ML:
            # Using 'xgb_model' parameter allows continuation of training in XGBoost API
            self.model.fit(X_new, y_new, xgb_model=self.model.get_booster())
        else:
            pass # Mock Online Update
        
        if step_count > 0 and step_count % save_interval == 0:
            self.metadata['last_updated'] = datetime.now().isoformat()
            self.save_weights("polymer_xgb_checkpoint")
            print(f"🔄 Checkpoint saved at step {step_count}")
    
    def predict(self, X):
        """
        Inference method for GBM models.
        
        Args:
            X: Feature matrix (list of lists or numpy array)
            
        Returns:
            float or array: Predicted value(s)
        """
        if not HAS_ML or self.model == "MOCK_GBM_OBJECT":
            # Mock prediction
            return float(np.random.randn() * 10 + 100)
        
        predictions = self.model.predict(X)
        # Return single value if input is single sample
        if len(predictions) == 1:
            return float(predictions[0])
        return predictions