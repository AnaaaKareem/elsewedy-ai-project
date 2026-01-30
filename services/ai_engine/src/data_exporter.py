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

This utility module manages the ad-hoc extraction and archival of Sentinel data.
It allows for:
1.  **Historical Data Fetch**: Retrieving long-term history (e.g., 5-10 years) for all tracked materials.
2.  **Dataset Creation**: formatting the data into a standardized CSV structure suitable for offline model training.
3.  **Database Synchronization**: Pushing the fetched historical data to the primary SQL database to ensure the 'Cold Store' is up-to-date.

Usage:
    Run as a standalone script: `python data_exporter.py`
"""

def export_data():
    """
    Executes the data export workflow.

    Workflow:
    1.  **Validation**: Checks for the existence of required API keys in the configuration.
    2.  **Initialization**: Instantiates the `UnifiedSentinel` engine.
    3.  **Acquisition**: Fetches a 10-year historical dataset for all materials defined in Sentinel.
    4.  **Export**: Saves the resulting DataFrame to a local CSV file (`sentinel_training_data.csv`).
    5.  **Persistence**: Attempts to write the dataset to the configured PostgreSQL database.

    Returns:
        None
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
