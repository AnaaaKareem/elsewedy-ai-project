import os

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️ Numpy not found. Using MockLumpyModel.")

"""
Blocking Materials Model (Pillar 3).

This module implements statistical models for "Lumpy" or Intermittent demand,
common in specialty materials like Mica Tape or Water-blocking Tape where
demand is not continuous but spikes based on specific cable orders.
"""

class SentinelLumpyModel:
    """
    Implements Croston's Method for Intermittent Demand Forecasting.
    
    Croston's method separates the forecast into two components:
    1. Demand Size (how much is ordered when an order occurs).
    2. Inter-Arrival Interval (time between orders).
    
    Attributes:
        alpha (float): Smoothing parameter (0 < alpha < 1).
        demand_level (float): Current estimated demand size.
        period_interval (float): Current estimated time between orders.
    """
    def __init__(self, alpha=0.1):
        """
        Initialize the model.

        Args:
            alpha (float): Smoothing factor for exponential smoothing. Defaults to 0.1.
        """
        self.alpha = alpha
        self.demand_level = 0
        self.period_interval = 1

    def train(self, history):
        """
        Train the model on historical demand data.

        Args:
            history (list/array): Sequence of historical demand values (0s and positive values).
        """
        if not HAS_NUMPY:
            return # Mock Train for environments without numpy
            
        history = np.array(history)
        n = len(history)
        if n == 0: return

        # Initialization logic
        # q = average demand size (excluding zeros)
        q = history[history > 0].mean() if np.sum(history > 0) > 0 else 0
        # p = average interval (total periods / count of non-zero demands)
        p = n / np.sum(history > 0) if np.sum(history > 0) > 0 else 1
        
        last_nonzero_idx = -1
        
        # Iterate history to simulate smoothing process
        for i, val in enumerate(history):
            if val > 0:
                # Update Interval estimate (p)
                if last_nonzero_idx != -1:
                    interval = i - last_nonzero_idx
                    p = self.alpha * interval + (1 - self.alpha) * p
                
                # Update Demand Size estimate (q)
                q = self.alpha * val + (1 - self.alpha) * q
                
                last_nonzero_idx = i

        self.demand_level = q
        self.period_interval = p

    def predict(self):
        """
        Generate a forecast rate (Demand / Interval).
        
        Returns:
            float: The estimated demand rate per period.
        """
        if self.period_interval == 0: return 0
        forecast_rate = self.demand_level / self.period_interval
        return float(forecast_rate)

    def save_weights(self, filename):
        """
        Persist model parameters to disk.
        """
    def save_weights(self, filename):
        """
        Persist model parameters to disk.
        """
        d = os.path.join(os.path.dirname(__file__), "weights")
        os.makedirs(d, exist_ok=True)
        if HAS_NUMPY:
            np.save(os.path.join(d, f"{filename}.npy"), [self.alpha, self.demand_level, self.period_interval])
        else:
            with open(os.path.join(d, f"{filename}.npy"), "w") as f:
                f.write(f"mock_croston:{self.demand_level}:{self.period_interval}")
        print(f"💾 Saved Croston params: {d}/{filename}.npy")

    def load_weights(self, filename):
        """
        Load model parameters from disk.
        """
    def load_weights(self, filename):
        """
        Load model parameters from disk.
        """
        d = os.path.join(os.path.dirname(__file__), "weights")
        path = os.path.join(d, f"{filename}.npy")
        if os.path.exists(path):
            if HAS_NUMPY:
                self.alpha, self.demand_level, self.period_interval = np.load(path)
            else:
                # Mock Load
                try:
                    with open(path, "r") as f:
                        data = f.read().split(":")
                        self.demand_level = float(data[1])
                        self.period_interval = float(data[2])
                except:
                    pass
            print(f"✅ Loaded Croston params: {path}")

    def update(self, new_demand, save_interval=10, step_count=0):
        """
        Online update with new single data point.
        """
        if new_demand > 0:
            interval = 1 # Simplified for demo: assumes called every period? 
            # In real system, interval would be time since last update
            self.period_interval = self.alpha * interval + (1 - self.alpha) * self.period_interval
            self.demand_level = self.alpha * new_demand + (1 - self.alpha) * self.demand_level
        
        # Checkpointing
        if step_count > 0 and step_count % save_interval == 0:
            self.save_weights("screening_croston_checkpoint")
            print(f"🔄 Checkpoint saved at step {step_count}")