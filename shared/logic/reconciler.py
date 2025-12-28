import pandas as pd
import numpy as np
from logic.optimizer import SentinelOptimizer

"""
Reconciliation Layer for Sentinel.

This module implements Hierarchical Forecast Reconciliation (Layer 3).
It ensures consistency between forecasts generated at different levels of granularity
(e.g., Global vs. Regional vs. Country). It supports both Bottom-Up aggregation for
project-based "lumpy" demand and Top-Down distribution for macro-trend driven commodities.
"""

class SentinelReconciler:
    """
    Handles Hierarchical Reconciliation for Cable Material Demand.
    
    Ensures that the sum of lower-level forecasts equals the higher-level forecast,
    providing a "Single Source of Truth" across the organization.

    Attributes:
        regions (dict): Configuration mapping countries to regions (from UnifiedSentinel config).
    """
    def __init__(self, regions_config):
        """
        Initialize the SentinelReconciler.

        Args:
            regions_config (dict or None): The hierarchical structure definition.
        """
        # regions_config comes from your UnifiedSentinel structure
        self.regions = regions_config

    def reconcile_bottom_up(self, df_results):
        """
        Aggregates granular country-level forecasts upwards to Region and Global levels.
        
        This strategy is best for 'Lumpy' demand where local infrastructure projects 
        drive the totals, rather than global averages.

        Args:
            df_results (pd.DataFrame): DataFrame containing 'country', 'material', 'date', 
                                     and 'predicted_demand'.

        Returns:
            tuple: (regional_agg DataFrame, global_agg DataFrame)
        """
        # 1. Aggregate to Region
        # Group by region/material/date to get total regional demand
        regional_agg = df_results.groupby(['region', 'material', 'date'])['predicted_demand'].sum().reset_index()
        regional_agg.rename(columns={'predicted_demand': 'regional_forecast'}, inplace=True)
        
        # 2. Aggregate to Global
        # Sum regional totals to get the global demand
        global_agg = regional_agg.groupby(['material', 'date'])['regional_forecast'].sum().reset_index()
        global_agg.rename(columns={'regional_forecast': 'global_forecast'}, inplace=True)
        
        return regional_agg, global_agg

    def reconcile_top_down(self, global_forecast, historical_proportions):
        """
        Distributes a high-level global forecast down to country levels based on historical shares.
        
        This strategy is best for commodities driven by global macro trends (e.g., LME Copper stats)
        rather than specific local projects.

        Args:
            global_forecast (pd.DataFrame): Global level predictions.
            historical_proportions (pd.DataFrame): DataFrame with 'material', 'country', and 'weight'.

        Returns:
            pd.DataFrame: Reconciled country-level forecasts.
        """
        # Logic: Country_Forecast = Global_Forecast * (Country_Historical_Share)
        reconciled_forecasts = []
        
        for _, row in global_forecast.iterrows():
            material = row['material']
            date = row['date']
            total_val = row['global_forecast']
            
            # Get historical weights for this material to distribute total_val
            weights = historical_proportions[historical_proportions['material'] == material]
            
            for _, w in weights.iterrows():
                reconciled_forecasts.append({
                    'date': date,
                    'country': w['country'],
                    'material': material,
                    'reconciled_demand': total_val * w['weight']
                })
                
        return pd.DataFrame(reconciled_forecasts)

    def calculate_historical_weights(self, training_data_path):
        """
        Calculates the average demand share of each country based on historical data.

        Args:
            training_data_path (str): Path to the historical CSV data.

        Returns:
            pd.DataFrame: DataFrame containing mean weights per material-country pair.
        """
        df = pd.read_csv(training_data_path)
        
        # Calculate total demand per material to normalize country demand
        total_demand = df.groupby('material')['demand'].transform('sum')
        
        # Determine weight as fraction of total
        df['weight'] = df['demand'] / total_demand
        
        # Average the weights over time for a stable proportion
        weights = df.groupby(['material', 'country'])['weight'].mean().reset_index()
        return weights

def run_sentinel_logic():
    """
    Main entry point to demonstrate the Sentinel Logic Loop.
    Simulates the flow from Forecast -> Reconciliation -> Optimization.
    """
    # 1. Initialize Layers
    reconciler = SentinelReconciler(regions_config=None) # Uses your Sentinel config
    # Lead time for Mica tape is long, XLPE is medium
    optimizer = SentinelOptimizer(material_name="XLPE", lead_time_days=30)

    print("🛰️ Sentinel Intelligence Loop: Reconciling & Optimizing...")

    # 2. Simulate/Fetch Forecast Data (From Layer 2)
    # This data represents the "Lumpy" demand predicted for the next 4 weeks
    raw_forecasts = pd.DataFrame({
        'region': ['MENA', 'MENA', 'EU'],
        'country': ['Egypt', 'KSA', 'Germany'],
        'material': ['XLPE', 'XLPE', 'XLPE'],
        'predicted_demand': [150.0, 300.0, 100.0], # "Lumpy" spikes from projects
        'date': ['2026-01-01'] * 3
    })

    # 3. Layer 3: Reconciliation (Bottom-Up)
    # We aggregate country spikes to see the total regional load
    _, global_view = reconciler.reconcile_bottom_up(raw_forecasts)
    
    total_needed = global_view[global_view['material'] == 'XLPE']['global_forecast'].values[0]
    print(f"🌍 Reconciled Global Demand for XLPE: {total_needed} units")

    # 4. Layer 4: Optimization
    # We assume a price trend where price is expected to rise
    prices = [85.0, 87.0, 92.0, 95.0] # Rising trend
    demand_plan = [total_needed / 4] * 4 # Distributed weekly
    
    buy_plan = optimizer.optimize_procurement(
        forecast_demand=demand_plan,
        predicted_prices=prices,
        current_stock=50
    )

    print("\n📦 Optimal Procurement Strategy:")
    for week, qty in buy_plan.items():
        if qty > 0:
            print(f"   Week {week+1}: BUY {qty:.2f} units (Predicted Price: ${prices[week]})")
        else:
            print(f"   Week {week+1}: WAIT (Use existing stock)")

if __name__ == "__main__":
    run_sentinel_logic()