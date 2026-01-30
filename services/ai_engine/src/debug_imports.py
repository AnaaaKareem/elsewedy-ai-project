import sys
import os

print("Starting debug_imports.py")
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.abspath(os.path.join(current_dir, '../../../shared'))
print(f"Shared dir: {shared_dir}")

if os.path.exists(shared_dir) and shared_dir not in sys.path:
    sys.path.append(shared_dir)
    print("Added shared_dir to path")

try:
    print("Importing infrastructure.config...")
    from infrastructure.config import config
    print("Success: infrastructure.config")
except Exception as e:
    print(f"Failed: infrastructure.config: {e}")

try:
    print("Importing logic.optimizer...")
    from logic.optimizer import SentinelOptimizer
    print("Success: logic.optimizer")
except Exception as e:
    print(f"Failed: logic.optimizer: {e}")

try:
    print("Importing logic.reconciler...")
    from logic.reconciler import SentinelReconciler
    print("Success: logic.reconciler")
except Exception as e:
    print(f"Failed: logic.reconciler: {e}")

try:
    print("Importing data_sources.unified_sentinel...")
    from data_sources.unified_sentinel import UnifiedSentinel
    print("Success: data_sources.unified_sentinel")
except Exception as e:
    print(f"Failed: data_sources.unified_sentinel: {e}")
