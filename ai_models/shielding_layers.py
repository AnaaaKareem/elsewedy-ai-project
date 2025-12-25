import os
import random

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

    def save_weights(self, filename):
        """Save state dictionary."""
        os.makedirs("weights", exist_ok=True)
        if HAS_TORCH:
            torch.save(self.model.state_dict(), f"weights/{filename}.pth")
        else:
            # Mock Save
            with open(f"weights/{filename}.pth", "w") as f:
                f.write("mock_torch_weights")
        print(f"💾 Saved: weights/{filename}.pth")

    def load_weights(self, filename):
        """Load state dictionary."""
        path = f"weights/{filename}.pth"
        if os.path.exists(path):
            if HAS_TORCH:
                self.model.load_state_dict(torch.load(path))
                self.model.eval()
            else:
                # Mock Load
                pass
            print(f"✅ Loaded: {path}")

    def train_online(self, start_price, next_price, learning_rate=0.001, save_interval=10, step_count=0):
        """
        Perform a single gradient descent step for online learning.
        
        Args:
            start_price (float): Input t.
            next_price (float): Target t+1.
            learning_rate (float): Step size for optimizer.
            
        Returns:
            float: Loss value (MSE).
        """
        if HAS_TORCH:
            # Real Training Logic
            self.model.train()
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
            
            # Prepare tensors (Batch=1, Seq=1, Feat=1)
            x = torch.tensor([[[float(start_price)]]], dtype=torch.float32)
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
            self.save_weights("shielding_lstm_checkpoint")
            print(f"🔄 Checkpoint saved at step {step_count}")

        return loss_val