import os
from .shielding_layers import SentinelDLModel
from .polymer_layers import SentinelGBMModel
from .blocking_materials import SentinelLumpyModel

class ModelFactory:
    """
    Factory class for creating Sentinel AI models.
    
    This class acts as the single entry point for model instantiation, abstracting away
    the complexity of selecting the correct class (LSTM, XGBoost, Croston's) validation
    logic based on the material category.
    """
    @staticmethod
    def get_model(category):
        """
        Returns the initialized and weight-loaded AI model instance for the given category.
        
        Args:
            category (str): Material category (e.g., 'Shielding', 'Polymer'). Case-insensitive.
            
        Returns:
            object: An instance of `SentinelDLModel`, `SentinelGBMModel`, or `SentinelLumpyModel`.
                    Returns None if the category is unrecognized.
        """
        weights_dir = os.path.join(os.path.dirname(__file__), "weights")
        
        # Normalize category string (Trim spaces and lowercase)
        cat_key = str(category).strip().lower()
        
        # --- Pillar 2: Price Volatility (Deep Learning) ---
        if cat_key == 'shielding':
            model = SentinelDLModel(model_type="LSTM")
            weight_path = "shielding_lstm"
            if os.path.exists(f"{weights_dir}/{weight_path}.pth"):
                model.load_weights(weight_path)
            return model

        # --- Pillar 1: External Drivers (XGBoost) ---
        elif cat_key == 'polymer':
            model = SentinelGBMModel(engine="XGBoost")
            weight_path = "polymer_xgb"
            if os.path.exists(f"{weights_dir}/{weight_path}.pkl"):
                model.load_weights(weight_path)
            return model

        # --- Pillar 3: Intermittent Demand (Croston's) ---
        elif cat_key == 'screening':
            model = SentinelLumpyModel(alpha=0.15)
            weight_path = "screening_lumpy"
            if os.path.exists(f"{weights_dir}/{weight_path}.npy"):
                model.load_weights(weight_path)
            return model
            
        else:
            print(f"⚠️ Warning: Unknown category '{category}' (Normalized: {cat_key}). Defaulting to None.")
            return None