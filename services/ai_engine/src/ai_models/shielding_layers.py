import os
import random
import json
import numpy as np
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ Torch not found. Using MockDLModel.")

"""
Shielding Layers Model (Pillar 2).

This module implements Deep Learning models (LSTM/GRU) for time-series forecasting.
It is designated for "Shielding" materials (Metals) where historical price patterns
and temporal dependencies are the primary drivers of future price.
"""

class SentinelDLModel:
    """
    Deep Learning Model wrapper for Time-Series Forecasting.
    
    Supports LSTM and GRU architectures via PyTorch. Includes built-in
    handling for data normalization and windowing sequences.

    Attributes:
        model (nn.Module): The PyTorch neural network.
        device (torch.device): Computation device (CPU or CUDA).
        window_size (int): Length of the input sequence window (default: 60).
        data_min (float): Min value for normalization.
        data_max (float): Max value for normalization.
    """
    def __init__(self, model_type="LSTM", input_size=1, hidden_size=64, num_layers=2):
        if HAS_TORCH:
            self.model = self._build_real_model(model_type, input_size, hidden_size, num_layers)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
        else:
            self.model = "MOCK_WEIGHTS_DICT"
        
        self.metadata = {}
        self.window_size = 60
        self.window_buffer = []
        
        # Metadata for normalization (Crucial for LSTMs)
        self.data_min = 0.0
        self.data_max = 1.0

    def _build_real_model(self, model_type, input_size, hidden_size, num_layers):
        class RealModel(nn.Module):
            def __init__(self):
                super().__init__()
                if model_type == "LSTM":
                    self.rnn = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                else:
                    self.rnn = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
                self.fc = nn.Linear(hidden_size, 1)
            
            def forward(self, x):
                out, _ = self.rnn(x)
                return self.fc(out[:, -1, :])
        return RealModel()

    def train_from_history(self, price_series, epochs=20, batch_size=32, learning_rate=0.001):
        """
        Train the model efficiently on a full historical dataset (Batch Training).
        """
        if not HAS_TORCH or len(price_series) < self.window_size + 1:
            print("⚠️ Not enough data or Torch missing.")
            return

        # 1. Normalize Data (LSTMs fail on raw prices like 9000.0)
        prices = np.array(price_series, dtype=np.float32)
        self.data_min = float(np.min(prices))
        self.data_max = float(np.max(prices))
        
        # Avoid division by zero
        scale = (self.data_max - self.data_min) if (self.data_max - self.data_min) > 0 else 1.0
        normalized_prices = (prices - self.data_min) / scale
        
        self.metadata['normalization'] = {'min': self.data_min, 'max': self.data_max}

        # 2. Create Sliding Window Sequences
        X, y = [], []
        for i in range(len(normalized_prices) - self.window_size):
            # Sequence: 0 to 60
            X.append(normalized_prices[i : i + self.window_size])
            # Target: 61
            y.append(normalized_prices[i + self.window_size])
            
        X_tensor = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1) # Add feature dim
        y_tensor = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1)

        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # 3. Training Loop
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.model.train()

        print(f"🚀 Starting Batch Training on {len(X)} sequences for {epochs} epochs...")
        
        for epoch in range(epochs):
            epoch_loss = 0
            for batch_X, batch_y in loader:
                batch_X, batch_y = batch_X.to(self.device), batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            if (epoch+1) % 5 == 0:
                print(f"   Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(loader):.6f}")

        print("✅ Batch Training Complete.")

    def save_weights(self, filename):
        d = os.path.join(os.path.dirname(__file__), "weights")
        os.makedirs(d, exist_ok=True)
        if HAS_TORCH:
            torch.save(self.model.state_dict(), os.path.join(d, f"{filename}.pth"))
        else:
            with open(os.path.join(d, f"{filename}.pth"), "w") as f:
                f.write("mock_torch_weights")
        
        # Save Metadata (Now includes Normalization params AND Window Buffer)
        meta_path = os.path.join(d, f"{filename}_meta.json")
        self.metadata['last_updated'] = datetime.now().isoformat()
        self.metadata['window_buffer'] = self.window_buffer # Persist Buffer
        
        with open(meta_path, "w") as f:
             json.dump(self.metadata, f)
        print(f"💾 Saved: {d}/{filename}.pth with buffer len={len(self.window_buffer)}")

    def load_weights(self, filename):
        d = os.path.join(os.path.dirname(__file__), "weights")
        path = os.path.join(d, f"{filename}.pth")
        if HAS_TORCH and os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            self.model.eval()
            print(f"✅ Loaded: {path}")
            
            meta_path = os.path.join(d, f"{filename}_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                    
                    # Load normalization params
                    norm = self.metadata.get('normalization', {})
                    self.data_min = norm.get('min', 0.0)
                    self.data_max = norm.get('max', 1.0)
                    
                    # Rstore Window Buffer
                    if 'window_buffer' in self.metadata:
                        self.window_buffer = self.metadata['window_buffer']
                        print(f"   + Restored Window Buffer (Size: {len(self.window_buffer)})")
    
    def train_online(self, start_price, next_price, learning_rate=0.001, save_interval=10, step_count=0):
        """
        Perform a single gradient descent step for online learning.
        Maintains a rolling window buffer to match training sequence length.
        """
        loss_val = 0.0
        
        # Update buffer
        self.window_buffer.append(float(start_price))
        if len(self.window_buffer) > self.window_size:
            self.window_buffer.pop(0) # Keep sliding window
        
        # Only train if we have a full sequence
        if len(self.window_buffer) < self.window_size:
            # During startup/warmup, we just accumulate state.
            return 0.0

        if HAS_TORCH:
            # Real Training Logic
            self.model.train()
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
            
            # Prepare tensors (Batch=1, Seq=60, Feat=1)
            # Create sequence from buffer
            seq_data = [[x] for x in self.window_buffer]
            x = torch.tensor([seq_data], dtype=torch.float32)
            y = torch.tensor([[float(next_price)]], dtype=torch.float32)
            
            # Backprop
            optimizer.zero_grad()
            output = self.model(x)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            loss_val = loss.item()
        else:
            # Mock Training Logic
            loss_val = random.random() * 0.1
        
        # Checkpointing
        if step_count > 0 and step_count % save_interval == 0:
            self.metadata['last_updated'] = datetime.now().isoformat()
            self.save_weights("shielding_lstm_checkpoint")
            print(f"🔄 Checkpoint saved at step {step_count}")

        return loss_val
    
    def predict(self, input_tensor):
        """
        Inference method for LSTM/GRU models.
        
        Args:
            input_tensor: PyTorch tensor or numpy array with shape (batch, sequence, features)
            
        Returns:
            float: Predicted value (denormalized if metadata available)
        """
        if not HAS_TORCH:
            # Mock prediction
            return float(np.random.randn() * 10 + 100)
        
        self.model.eval()
        with torch.no_grad():
            if isinstance(input_tensor, np.ndarray):
                input_tensor = torch.tensor(input_tensor, dtype=torch.float32)
            
            input_tensor = input_tensor.to(self.device)
            output = self.model(input_tensor)
            
            # Denormalize if we have the metadata
            prediction = output.item()
            if 'normalization' in self.metadata:
                norm = self.metadata['normalization']
                scale = (norm['max'] - norm['min']) if (norm['max'] - norm['min']) > 0 else 1.0
                prediction = prediction * scale + norm['min']
            
            return float(prediction)