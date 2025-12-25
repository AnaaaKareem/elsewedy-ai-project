# ai_models/model_factory.py
import os
from .shielding_layers import SentinelDLModel
from .polymer_layers import SentinelGBMModel
from .blocking_materials import SentinelLumpyModel

"""
Model Factory Module.

This module implements the Factory Method design pattern to instantiate the correct
AI model class based on the material category. It abstracts away the complexity of
model selection and weight loading from the consumer (e.g., worker service).
"""

class ModelFactory:
    """
    Factory class for creating Sentinel AI models.
    """
    @staticmethod
    def get_model(category):
        """
        Returns the specific AI model instance for the given material category.
        
        Logic:
        - Shielding (e.g., Copper) -> LSTM (Deep Learning) for price volatility.
        - Polymer (e.g., XLPE) -> XGBoost (GBM) for multi-variate regression (Oil, etc.).
        - Screening (e.g., Mica) -> Croston's Method for intermittent/lumpy demand.

        Args:
            category (str): The material category.
            
        Returns:
            object: An instance of the appropriate model class, with weights loaded if available.
        """
        weights_dir = "weights"
        
        # --- Pillar 2: Price Volatility (Deep Learning) ---
        if category == 'Shielding':
            # Copper, Aluminum, etc. - Highly volatile, sequential data
            model = SentinelDLModel(model_type="LSTM")
            weight_path = "shielding_lstm"
            # Check for saved weights
            if os.path.exists(f"{weights_dir}/{weight_path}.pth"):
                model.load_weights(weight_path)
            return model

        # --- Pillar 1: External Drivers (XGBoost) ---
        elif category == 'Polymer':
            # XLPE, PVC (Oil-linked) - Driven by external factors
            model = SentinelGBMModel(engine="XGBoost")
            weight_path = "polymer_xgb"
            if os.path.exists(f"{weights_dir}/{weight_path}.pkl"):
                model.load_weights(weight_path)
            return model

        # --- Pillar 3: Intermittent Demand (Croston's) ---
        elif category == 'Screening':
            # Mica Tape (Lumpy demand) - Intermittent project-based usage
            model = SentinelLumpyModel(alpha=0.15)
            weight_path = "screening_lumpy"
            if os.path.exists(f"{weights_dir}/{weight_path}.npy"):
                model.load_weights(weight_path)
            return model
            
        else:
            # Fallback or Error for unknown categories
            print(f"⚠️ Warning: Unknown category '{category}'. Defaulting to simple average request (None returned).")
            return None