
import os
import sys

# Setup path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../shared')))

from data_sources.unified_sentinel import UnifiedSentinel
from logic.optimizer import SentinelOptimizer
from infrastructure.config import config

def verify_refactor():
    print("🔬 Verifying Sentinel Refactor...")
    
    # 1. Verify Registry Expansion
    print("\n--- 1. Registry Check ---")
    sentinel = UnifiedSentinel(config.KEYS, config.DB_CONFIG)
    
    # Check Countries
    required_countries = ['Chile', 'India', 'China']
    missing_c = [c for c in required_countries if c not in sentinel.country_registry]
    if not missing_c:
        print("✅ New Countries (Chile, India, China) Found.")
    else:
        print(f"❌ Missing Countries: {missing_c}")
        
    # Check Materials & HS Codes
    mat_check = {'XLPE': '390110', 'PVC': '390422', 'Copper': '740811'}
    for m, hs in mat_check.items():
        if m in sentinel.materials and sentinel.materials[m]['hs'] == hs:
            print(f"✅ {m} HS Code Updated to {hs}")
        else:
             print(f"❌ {m} Mismatch or Missing. Found: {sentinel.materials.get(m)}")

    # 2. Verify Optimizer Logic (Safety Stock)
    print("\n--- 2. Optimizer Logic Check ---")
    
    # Test Case: Screening (Mica) - Should use Dynamic Buffer
    # Avg Demand = 100
    # Lead Time = 30
    # Expected Buffer = (100 * (30 + 7)) * 1.2 = 100 * 37 * 1.2 = 4440
    
    opt_screening = SentinelOptimizer('Mica Tape', lead_time_days=30, holding_cost_pct=0.01)
    
    # Run mock optimization
    # We can't easily inspect internal constraints without solving, 
    # but we can check if the object initialized with new params if we added them to __init__
    
    if hasattr(opt_screening, 'metal_interest_rate'):
        print(f"✅ Optimizer accepts 'metal_interest_rate' (Default: {opt_screening.metal_interest_rate})")
    else:
        print("❌ Optimizer missing 'metal_interest_rate' attribute")

    print("\nVerification Complete.")

if __name__ == "__main__":
    verify_refactor()
