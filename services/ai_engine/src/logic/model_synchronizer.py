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
        """Persists the sync state."""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f)

    def sync_models(self):
        """
        Main entry point: Checks for gaps and backfills training.
        """
        print("🔄 [Synchronizer] Verifying model currency...")
        
        # We process by Category to avoid redundant driver fetches
        categories = ['Polymer', 'Shielding'] # Screening (Croston) is usually batch-only, skipping for now
        
        for cat in categories:
            self._sync_category(cat)
            
        print("✅ [Synchronizer] All models up to date.")

    def _sync_category(self, category):
        last_sync_str = self.state.get(category)
        
        # Default: If no history, assume we are up to date OR start from 30 days ago?
        # For safety, if it's the first run, we usually rely on the pre-trained weights.
        # We only catch up if we HAVE a record and it's old.
        if not last_sync_str:
            # 1. Attempt to recover from Model Metadata (Sidecar)
            # This handles the "Offline Training -> Production" Handover case
            temp_model = ModelFactory.get_model(category)
            try:
                # Try loading standard name
                temp_model.load_weights(f"{category}_latest")
                if hasattr(temp_model, 'metadata') and 'last_updated' in temp_model.metadata:
                    last_sync_str = temp_model.metadata['last_updated']
                    print(f"   ℹ️ Recovered sync state from Model Metadata: {last_sync_str}")
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
        
        # 1. Fetch Missing Data (Daily resolution)
        # We need a representative material for the category to get price history
        # Polymer -> PVC, Shielding -> Copper
        rep_mat = 'PVC' if category == 'Polymer' else 'Copper'
        symbol = self.sentinel.materials[rep_mat]['symbol']
        
        # Fetch prices since last sync
        # Yahoo range calculation is approximate, let's grab enough coverage
        prices = self.sentinel.fetch_historical_price_series(symbol, time_range='1mo') 
        
        # Filter for dates > last_sync_date
        missing_data = prices[prices.index > last_sync_date]
        
        if missing_data.empty:
            print(f"   ⚠️ No new data found for {category} despite time gap.")
            self.state[category] = now.isoformat()
            self._save_state()
            return

        # 2. Load Model
        model = ModelFactory.get_model(category)
        try:
            model.load_weights(f"{category}_latest")
        except:
             print(f"   ⚠️ No weights found for {category}, skipping backfill.")
             return

        # 3. Backfill Loop
        print(f"   📈 Training on {len(missing_data)} missing data points...")
        
        if category == 'Polymer':
            # Fetch Drivers once (Optimization)
            oil_series = self.sentinel.fetch_historical_driver_series('Polymer')
            const_series = self.sentinel.fetch_historical_driver_series('Screening')
            
            # Align
            df = missing_data.to_frame(name='Price')
            df['Oil'] = oil_series.reindex(df.index, method='ffill').fillna(80.0)
            df['Const'] = const_series.reindex(df.index, method='ffill').fillna(100.0)
            
            for date, row in df.iterrows():
                # Construct X: [Price, Oil, Const]
                X_new = [[row['Price'], row['Oil'], row['Const']]]
                # Construct y: Future Price (Approximate: Use next day as proxy for trend flow or self-reinforce)
                # Ideally we need T+30, but online updates usually reinforce 'current structure'.
                # For this feature, we simulate the target as the Price itself (Auto-Encoder style) or Next Price
                y_new = [row['Price']] 
                
                model.train_online(X_new, y_new)
                
        elif category == 'Shielding':
            # LSTM needs sequence logic. 
            # We treat 'missing_data' as the stream of 'next_prices'.
            # We need the price *before* the first missing point to start.
            prev_price = prices[prices.index <= last_sync_date].iloc[-1] if not prices.empty else missing_data.iloc[0]
            
            for date, price in missing_data.items():
                # train_online(start_price, next_price)
                model.train_online(prev_price, price)
                prev_price = price

        # 4. Update State
        model.save_weights(f"{category}_latest")
        self.state[category] = missing_data.index[-1].isoformat()
        self._save_state()
        print(f"   ✅ {category} synced to {self.state[category]}")
