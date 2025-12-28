import sys
import os
import shutil

# Add project root to path
# __file__ = ai_models/test_lifecycle.py
# dirname = ai_models
# dirname(dirname) = Project Root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_models.shielding_layers import SentinelDLModel
from ai_models.polymer_layers import SentinelGBMModel
from ai_models.blocking_materials import SentinelLumpyModel

def test_lifecycle():
    print("🧪 Starting AI Model Lifecycle Test (Save, Load, Live Update)...")
    
    # Anchor to the script location, just like the models do
    base_dir = os.path.dirname(os.path.abspath(__file__))
    weights_dir = os.path.join(base_dir, "weights")

    # Clean weights dir for fresh test
    if os.path.exists(weights_dir):
        shutil.rmtree(weights_dir)
    os.makedirs(weights_dir, exist_ok=True)

    # --- TEST 1: LSTM (Shielding) ---
    print("\n[1] Testing LSTM (Shielding)...")
    lstm = SentinelDLModel()
    # Simulate streaming 20 updates, saving every 5
    for i in range(1, 21):
        loss = lstm.train_online(start_price=8000+i, next_price=8000+i+10, save_interval=5, step_count=i)
        if i % 5 == 0:
            assert os.path.exists(os.path.join(weights_dir, "shielding_lstm_checkpoint.pth"))
    print("✅ LSTM Online Training & Checkpointing Passed.")

    # --- TEST 2: XGBoost (Polymer) ---
    print("\n[2] Testing XGBoost (Polymer)...")
    xgb = SentinelGBMModel()
    # Dummy init training to establish booster
    xgb.train([[100], [200]], [110, 210]) 
    
    for i in range(1, 11):
        xgb.train_online([[300+i]], [310+i], save_interval=5, step_count=i)
        if i % 5 == 0:
            assert os.path.exists(os.path.join(weights_dir, "polymer_xgb_checkpoint.pkl"))
    print("✅ XGBoost Incremental Update & Checkpointing Passed.")

    # --- TEST 3: Croston (Screening) ---
    print("\n[3] Testing Croston (Screening)...")
    croston = SentinelLumpyModel()
    for i in range(1, 11):
        croston.update(new_demand=500 if i%2==0 else 0, save_interval=5, step_count=i)
        if i % 5 == 0:
            assert os.path.exists(os.path.join(weights_dir, "screening_croston_checkpoint.npy"))
    
    # Reload verification
    croston_new = SentinelLumpyModel()
    croston_new.load_weights("screening_croston_checkpoint")
    assert croston_new.demand_level > 0
    print("✅ Croston State Update, Save & Reload Passed.")

    print("\n🎉 ALL LIFECYCLE TESTS PASSED.")

if __name__ == "__main__":
    test_lifecycle()
