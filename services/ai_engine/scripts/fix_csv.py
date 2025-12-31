
import os
import sys
import pandas as pd
from datetime import datetime

# Add parent to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../shared')))

from infrastructure.config import config
from data_sources.unified_sentinel import UnifiedSentinel

def fix_csv():
    csv_path = "sentinel_training_data.csv"
    if not os.path.exists(csv_path):
        print("❌ CSV not found.")
        return

    print("🚀 Starting Selective Update (Missing Columns Only)...")
    
    # Load CSV
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Initialize Sentinel
    sentinel = UnifiedSentinel(config.KEYS, config.DB_CONFIG)
    
    # 1. Fetch Drivers (Fast)
    print("⏳ Fetching Drivers (FRED)...")
    oil_series = sentinel.fetch_historical_driver_series('Polymer') # DCOILBRENTEU
    const_series = sentinel.fetch_historical_driver_series('Screening') # TTLCONS
    
    if not oil_series.empty:
        print(f"   ✅ Driver: Oil data fetched ({len(oil_series)} pts)")
    else:
        print("   ⚠️ Driver: Oil data empty/failed.")

    if not const_series.empty:
        print(f"   ✅ Driver: Construction data fetched ({len(const_series)} pts)")
    else:
        print("   ⚠️ Driver: Construction data empty/failed.")

    # 2. Update DataFrame with Drivers
    print("🔄 updating Driver Columns...")
    # Construction Index (Global)
    if not const_series.empty:
        # Reindex to DataFrame Dates
        # We need to map by Date. 
        # Create a mapping series
        mapped_const = const_series.reindex(df['Date'], method='ffill').values
        df['Construction_Index'] = mapped_const
        # Fill NaN with 0
        df['Construction_Index'] = df['Construction_Index'].fillna(0.0)

    # Driver Value (Category Specific)
    # Polymer -> Oil
    if not oil_series.empty:
        mask_poly = df['Category'] == 'Polymer'
        mapped_oil = oil_series.reindex(df.loc[mask_poly, 'Date'], method='ffill').values
        df.loc[mask_poly, 'Driver_Value'] = mapped_oil
    
    # Screening -> Construction (already in Const Index, but logic maps it to Driver_Value too for Screening)
    if not const_series.empty:
        mask_screen = df['Category'] == 'Screening'
        mapped_screen = const_series.reindex(df.loc[mask_screen, 'Date'], method='ffill').values
        df.loc[mask_screen, 'Driver_Value'] = mapped_screen
        
    df['Driver_Value'] = df['Driver_Value'].fillna(0.0)

    # 3. Update Demand (Iterative)
    # Get unique combinations
    pairs = df[['Material', 'Country', 'Category']].drop_duplicates()
    
    print(f"⏳ Processing Demand for {len(pairs)} Material/Country pairs...")
    
    for idx, row in pairs.iterrows():
        mat = row['Material']
        country = row['Country']
        
        # Check if we need to fetch
        # optimization: check if we already have non-zero data for this pair in the CSV
        mask = (df['Material'] == mat) & (df['Country'] == country)
        current_sum = df.loc[mask, 'Demand_Qty'].sum()
        
        if current_sum > 0:
            print(f"   ⏩ Skipping {mat} in {country} (Data exists)")
            continue
            
        # Need to find the Country Code
        # Reverse lookup or direct access if simple
        # accessing sentinel registry
        c_code = '818' # Default
        if country in sentinel.country_registry:
            c_code = sentinel.country_registry[country]['trade_code']
        
        demand_series = sentinel.fetch_historical_demand_series(mat, time_range='10y', country_code=c_code)
        
        if not demand_series.empty:
            print(f"   ✅ Fetched {mat} Demand for {country} ({len(demand_series)} pts)")
            # Map back
            mapped_demand = demand_series.reindex(df.loc[mask, 'Date'], method='ffill').fillna(0).values
            df.loc[mask, 'Demand_Qty'] = mapped_demand
        else:
             print(f"   ⚠️ No Demand data found for {mat} in {country}")
             
    # Save
    print(f"💾 Saving Updates to {csv_path}...")
    df.to_csv(csv_path, index=False)
    print("✅ Done.")

if __name__ == "__main__":
    fix_csv()
