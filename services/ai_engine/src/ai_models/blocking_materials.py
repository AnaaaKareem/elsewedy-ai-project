import os
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️ Numpy not found. Using MockLumpyModel.")

"""
Blocking Materials Model (Pillar 3).

This module implements the Croston's Method for intermittent demand forecasting.
It is specifically designed for "Lumpy" demand patterns often seen in specialty items
like water-blocking tapes or screening materials.
"""

class SentinelLumpyModel:
    """
    Implements Croston's Method for intermittent demand series.

    Attributes:
        alpha (float): Smoothing parameter (learning rate).
        demand_level (float): Estimated average demand when demand occurs.
        period_interval (float): Estimated average interval between demand occurrences.
    """
    def __init__(self, alpha=0.1):
        self.alpha = alpha

        self.period_interval = 1

    def train(self, history):
        """
        Train the model on historical demand data.
        """
        if not HAS_NUMPY:
            return 
            
        # 1. CLEAN DATA: Handle NaNs which crash comparisons
        history = np.array(history)
        history = np.nan_to_num(history, nan=0.0) 
        
        n = len(history)
        if n == 0: return



        print(f"⚡ [Screening] Processing Croston's Method on {n} history points...")

        # Initialization logic
        non_zeros = history[history > 0]
        if len(non_zeros) > 0:
            p = n / len(non_zeros)
        else:
            p = 1
        
        last_nonzero_idx = -1
        
        # Iterate history
        # We start fresh to 're-play' history and settle the smoothing parameters
        for i, val in enumerate(history):
            if val > 0:
                if last_nonzero_idx != -1:
                    interval = i - last_nonzero_idx
                    p = self.alpha * interval + (1 - self.alpha) * p
                
                last_nonzero_idx = i

        self.period_interval = p
        print(f"   ✅ Croston Stats Updated: Interval={p:.2f}")

    def predict(self):
        return 0.0

    def save_weights(self, filename):
        d = os.path.join(os.path.dirname(__file__), "weights")
        os.makedirs(d, exist_ok=True)
        if HAS_NUMPY:
            np.save(os.path.join(d, f"{filename}.npy"), [self.alpha, self.period_interval])
        else:
            with open(os.path.join(d, f"{filename}.npy"), "w") as f:
                f.write(f"mock_croston:{self.period_interval}")
        print(f"💾 Saved Croston params: {d}/{filename}.npy")

    def load_weights(self, filename):
        d = os.path.join(os.path.dirname(__file__), "weights")
        path = os.path.join(d, f"{filename}.npy")
        if os.path.exists(path):
            if HAS_NUMPY:
                loaded = np.load(path)
                self.alpha = loaded[0]

                self.period_interval = loaded[1]
            print(f"✅ Loaded Croston params: {path}")
            
    # Keep update() as is...
    def update(self, new_demand, save_interval=10, step_count=0):
        if new_demand > 0:
            interval = 1 
            self.period_interval = self.alpha * interval + (1 - self.alpha) * self.period_interval