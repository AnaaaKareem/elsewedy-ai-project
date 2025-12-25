from data_sources.unified_sentinel import UnifiedSentinel
from logic.reconciler import SentinelReconciler
from logic.optimizer import SentinelOptimizer
import os
from infrastructure.config import config

"""
Orchestrator Service.

This script demonstrates the full "Batch" execution flow of the Sentinel Intelligence logic,
connecting all 4 layers of the Sentinel architecture:
1. Data Ingestion (UnifiedSentinel)
2. Predictive Modeling (Fetches Forecasts)
3. Hierarchical Reconciliation (SentinelReconciler)
4. Prescriptive Optimization (SentinelOptimizer)
"""

# 1. Initialize the Engine (Layer 1)
# Connects to data sources using keys from Config (Vault-backed)
sentinel = UnifiedSentinel(api_keys=config.KEYS, db_config=None)

# 2. Get Raw Predictions (Layer 2)
# Fetches base forecasts for key materials.
# Note: These forecasts may be 'incoherent' (sum of parts != whole)
raw_df = sentinel.fetch_base_forecasts(['XLPE', 'Copper Tape'])

# 3. Reconcile the Hierarchy (Layer 3)
# This solves the 'Input Problem' by aligning local spikes with global trends.
# Uses Bottom-Up reconciliation to let local project needs drive the global total.
reconciler = SentinelReconciler(sentinel.regions)
regional_view, global_view = reconciler.reconcile_bottom_up(raw_df)

# 4. Optimize the Inventory (Layer 4)
# Use the 'Reconciled' global forecast (Single Source of Truth) to make the final 'Buy' decision.
# We optimize for 'Copper Tape' with a 45-day lead time.
optimizer = SentinelOptimizer(material_name="Copper Tape", lead_time_days=45)

# Example predicted price trend (can come from AI models in production)
current_prices = [8500, 8600, 8400, 8700] 

# Solve for the optimal procurement plan
final_buy_plan = optimizer.optimize_procurement(
    forecast_demand=global_view['global_forecast'].tolist(),
    predicted_prices=current_prices,
    current_stock=100
)

print(f"✅ Final AI-Driven Ordering Plan: {final_buy_plan}")