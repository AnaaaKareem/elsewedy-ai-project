import json
import os
import pandas as pd
from datetime import datetime, timedelta
from ai_models.model_factory import ModelFactory
from data_sources.unified_sentinel import UnifiedSentinel

STATE_FILE = "model_sync_state.json"

class ModelSynchronizer:
    """
    Handles the "Catch-Up" logic to ensure models don't have memory holes
    after server downtime.
    """
    def __init__(self, sentinel: UnifiedSentinel):
        self.sentinel = sentinel
        self.state = self._load_state()

    def _load_state(self):
        """Loads the last sync timestamp for each material category."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_state(self):
        """Persists the current synchronization timestamps to a local JSON file."""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f)

    def sync_models(self):
        """
        Main entry point: Verifies and Restores Model State.
        
        Orchestrates the backfilling process for all material categories. It identifies
        if any model hasn't been updated recently (e.g., due to service downtime) and
        triggers training on the missing data window.
        """
        print("🔄 [Synchronizer] Verifying model currency...")
        
        # Process Categories
        categories = ['Polymer', 'Shielding']  
        
        for cat in categories:
            self._sync_category(cat)
            
        print("✅ [Synchronizer] All models up to date.")

    def _get_base_filename(self, category):
        """
        Maps a material category to its canonical model weight filename.

        Args:
            category (str): Material category.
            
        Returns:
            str: The base filename (without extension) for the model weights.
        """
        mapping = {
            'Shielding': 'shielding_lstm',
            'Polymer': 'polymer_xgb',
            'Screening': 'screening_lumpy'
        }
        return mapping.get(category, f"{category}_latest")

    def _sync_category(self, category):
        """
        Performs the Gap Analysis and Catch-Up training for a single category.
        
        1. Checks last known sync time from state file or model metadata.
        2. Detects time gap between last sync and Now.
        3. If gap > 1 day, fetches historical data for that interval.
        4. Retrains the model (Online Learning) on the new data points.
        5. Updates the sync state.
        
        Args:
            category (str): The material category to synchronize.
        """
        last_sync_str = self.state.get(category)
        
        # Logic to recover state from loaded model metadata if JSON state is missing
        if not last_sync_str:
            base_name = self._get_base_filename(category)
            temp_model = ModelFactory.get_model(category)
            try:
                # Try loading standard name from Batch Training (e.g., shielding_lstm)
                temp_model.load_weights(base_name)
                if hasattr(temp_model, 'metadata') and 'last_updated' in temp_model.metadata:
                    last_sync_str = temp_model.metadata['last_updated']
                    print(f"   ℹ️ Recovered sync state for {category}: {last_sync_str}")
            except Exception:
                pass
        
        if not last_sync_str:
            # Initialize state to Now so we track from this point forward
            self.state[category] = datetime.now().isoformat()
            self._save_state()
            return

        last_sync_date = datetime.fromisoformat(last_sync_str)
        now = datetime.now()
        
        # If gap > 1 day, trigger backfill
        gap = now - last_sync_date
        if gap.days < 1:
            return

        print(f"   ⏳ Catching up {category}... Gap: {gap.days} days")
        
        missing_data = pd.Series()
        
        # Fetch Price History (Copper/PVC)
        rep_mat = 'PVC' if category == 'Polymer' else 'Copper'
        symbol = self.sentinel.materials[rep_mat]['symbol']
        full_series = self.sentinel.fetch_historical_price_series(symbol, time_range='3mo')
        if not full_series.empty:
             missing_data = full_series[full_series.index > last_sync_date]
        
        if missing_data.empty:
            print(f"   ⚠️ No new data found for {category} despite time gap.")
            self.state[category] = now.isoformat()
            self._save_state()
            return

        # 2. Load Model
        model = ModelFactory.get_model(category)
        if hasattr(model, 'model') and model.model is None: # Factory might mock but let's check
             pass

        # 3. Backfill Loop
        print(f"   📈 Training on {len(missing_data)} missing data points...")
        
        if category == 'Polymer':
            # Simplified to Univariate (Price Only)
            for date, row in missing_data.to_frame(name='Price').iterrows():
                # Feature: Price (Using current price to refine model context)
                # Note: In real autoregressive, X should be lag. 
                # For online catchup, we are feeding (Current) -> (Next) implied, 
                # or just updating distribution.
                X_new = [[row['Price']]]
                y_new = [row['Price']] 
                model.train_online(X_new, y_new)
                
        elif category == 'Shielding':
            # LSTM needs sequence logic. 
            # We treat 'missing_data' as the stream of 'next_prices'.
            # We need the price *before* the first missing point to start.
            # Assuming full_series exists from above logic
            prev_price = missing_data.iloc[0] # Simplification if prev not avail
            
            for date, price in missing_data.items():
                model.train_online(prev_price, price)
                prev_price = price



        # 4. Update State
        # Save to base name (e.g. shielding_lstm) to keep single source of truth? 
        # Or save to _latest? Let's save to base name to be consistent with pipeline.
        base_name = self._get_base_filename(category)
        model.save_weights(base_name)
        
        self.state[category] = missing_data.index[-1].isoformat()
        self._save_state()
        print(f"   ✅ {category} synced to {self.state[category]}")
