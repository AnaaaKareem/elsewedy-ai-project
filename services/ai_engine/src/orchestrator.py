import sys
import os

# Local import fix
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.abspath(os.path.join(current_dir, '../../../shared'))
if os.path.exists(shared_dir) and shared_dir not in sys.path:
    sys.path.append(shared_dir)

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
# 2. Get Raw Predictions (Layer 2)
# Fetches base forecasts for key materials.
# Note: These forecasts may be 'incoherent' (sum of parts != whole)
# REFACTORED: Logic moved here from UnifiedSentinel to strictly decouple AI.
from ai_models.model_factory import ModelFactory
import pandas as pd

def predict_demand(material_name):
    # Quick helper for prediction
    price, _ = sentinel.fetch_price(material_name)
    if price == 0: return 0.0
    cat = sentinel.materials[material_name]['category']
    model = ModelFactory.get_model(cat)
    if not model: return 0.0
    
    # Simplified Logic matching the old UnifiedSentinel implementation
    # In a real scenario, this would reuse the Worker's get_inference_input
    if cat == 'Polymer': return 300.0
    return 150.0

predictions = []
materials = ['XLPE', 'Copper Tape']

for region_name, region_data in sentinel.regions.items():
    for country_name in region_data['countries']:
        for mat in materials:
            raw_pred = predict_demand(mat)
            predictions.append({
                'region': region_name,
                'country': country_name,
                'material': mat,
                'predicted_demand': raw_pred,
                'date': pd.Timestamp.now().strftime('%Y-%m-%d')
            })

raw_df = pd.DataFrame(predictions)

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