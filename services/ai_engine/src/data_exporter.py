# -*- coding: utf-8 -*-
import os
import sys

# Add parent directory to path to allow importing sibling modules like data_sources
current_dir = os.path.dirname(os.path.abspath(__file__))
shared_dir = os.path.abspath(os.path.join(current_dir, '../../../shared'))
if os.path.exists(shared_dir) and shared_dir not in sys.path:
    sys.path.append(shared_dir)


from infrastructure.config import config
from data_sources.unified_sentinel import UnifiedSentinel

"""
Data Exporter Service.

This module provides a utility to manually trigger the data collection pipeline
outside of the automated schedule. It fetches historical data, saves it to a CSV
file for training/backup, and syncs it to the production database.
"""

def export_data():
    """
    Main execution function for data export.

    Steps:
    1. Checks for API keys.
    2. Initializes Sentinel to fetch 5 years of historical data.
    3. Saves data to 'sentinel_training_data.csv'.
    4. Syncs data to the database (optional).
    """
    # Check for keys availability to avoid runtime errors
    if not any(config.KEYS.values()):
        print("⚠️ Warning: API keys not found in .env. Data fetching might fail.")

    print("🚀 Initializing Sentinel Engine...")
    # Initialize Sentinel. 
    # Note: DB Connection might fail if local Postgres is not running, but we continue for CSV export.
    sentinel = UnifiedSentinel(config.KEYS, db_config=config.DB_CONFIG)

    # Fetch 10 years of history for all configured materials
    df = sentinel.generate_historical_dataset(time_range='10y')

    if df.empty:
        print("❌ No data collected. Check API keys or connectivity.")
        return

    # Define filename for local storage
    filename = "sentinel_training_data.csv"
    
    print(f"💾 Saving {len(df)} rows to {filename}...")
    # Save to CSV (Overwrite mode for a fresh export)
    # If appending is desired, logic can be adjusted, but usually 'export' implies full dump.
    df.to_csv(filename, index=False)
    print(f"✅ CSV Export Complete: {filename}")

    # Sync to Production DB (Optional / Best Effort)
    try:
        print("🔄 Syncing to Database...")
        sentinel.save_to_db(df)
    except Exception as e:
        print(f"⚠️ DB Sync skipped or failed: {e}")

if __name__ == "__main__":
    export_data()
