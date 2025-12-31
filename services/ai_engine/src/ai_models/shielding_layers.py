import os
import random
import json
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("⚠️ Torch not found. Using MockDLModel.")

"""
Shielding Layers Model (Pillar 2).

This module implements Deep Learning models (LSTM/GRU) for analyzing price volatility.
This is used for high-risk commodities like Copper and Aluminum where understanding
the trend (uptrend/downtrend) is critical for strategic buying (Optimizing Cost).
"""

class SentinelDLModel:
    """
    Wrapper for PyTorch Recurrent Neural Networks (LSTM/GRU).
    
    Attributes:
        model (nn.Module): The underlying PyTorch model.
    """
    def __init__(self, model_type="LSTM", input_size=1, hidden_size=64, num_layers=2):
        """
        Initialize the DL model architecture.
        
        Args:
            model_type (str): 'LSTM' or 'GRU'.
            input_size (int): Number of input features (typically 1 for univariate price series).
            hidden_size (int): Number of hidden units.
            num_layers (int): Number of stacked RNN layers.
        """
        if HAS_TORCH:
            self.model = self._build_real_model(model_type, input_size, hidden_size, num_layers)
        else:
            self.model = "MOCK_WEIGHTS_DICT"
            self.weights = {"fc.weight": [0.5], "fc.bias": [0.1]}
        self.metadata = {}
        # Buffer for online sequence generation (sliding window)
        self.window_size = 60
        self.window_buffer = []

    def _build_real_model(self, model_type, input_size, hidden_size, num_layers):
        """Internal helper to define the torch architecture."""
        class RealModel(nn.Module):
            def __init__(self):
                super().__init__()
                if model_type == "LSTM":
                    self.rnn = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                else:
                    self.rnn = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
                # Output layer predicting the next value (Regression)
                self.fc = nn.Linear(hidden_size, 1)
            
            def forward(self, x):
                # Pass through RNN layers
                out, _ = self.rnn(x)
                # Take the output of the last time step for prediction
                return self.fc(out[:, -1, :])
        return RealModel()

    def __call__(self, x):
        """Forward pass wrapper."""
        if HAS_TORCH:
            return self.model(x)
        else:
            # Mock return for CPU/No-Torch envs (returns a Tensor-like object with .item())
            class MockTensor:
                def item(self): return 50.0 + random.random()
            return MockTensor()

    def save_weights(self, filename):
        """Save state dictionary."""
        d = os.path.join(os.path.dirname(__file__), "weights")
        os.makedirs(d, exist_ok=True)
        if HAS_TORCH:
            torch.save(self.model.state_dict(), os.path.join(d, f"{filename}.pth"))
        else:
            with open(os.path.join(d, f"{filename}.pth"), "w") as f:
                f.write("mock_torch_weights")
        print(f"💾 Saved: {d}/{filename}.pth")
        
        # Save Metadata Sidecar
        meta_path = os.path.join(d, f"{filename}_meta.json")
        if not self.metadata.get('last_updated'):
             self.metadata['last_updated'] = datetime.now().isoformat()
        with open(meta_path, "w") as f:
             json.dump(self.metadata, f)
        print(f"   + Metadata: {meta_path}")

    def load_weights(self, filename):
        """Load state dictionary."""
        d = os.path.join(os.path.dirname(__file__), "weights")
        path = os.path.join(d, f"{filename}.pth")
        if os.path.exists(path):
            if HAS_TORCH:
                self.model.load_state_dict(torch.load(path))
                self.model.eval()
            else:
                # Mock Load
                pass
            print(f"✅ Loaded: {path}")
            
            # Load Metadata Sidecar
            meta_path = os.path.join(d, f"{filename}_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
                print(f"   + Metadata: Last Updated {self.metadata.get('last_updated')}")
            else:
                self.metadata = {}

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