"""
Unified Sentinel Engine.

This module acts as the central data gateway for the entire Sentinel platform.
It abstracts the complexity of connecting to multiple disparate data sources
(Financial APIs, Trade Databases, Economic Indices) and provides a normalized
interface for upstream services.
"""
import requests
import ssl

# Fix for macOS SSL Certificate Verify Failed (Common in local dev environments)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from fredapi import Fred
except ImportError:
    Fred = None

try:
    import numpy as np
except ImportError:
    np = None

import math
import time
from datetime import datetime

# SQLAlchemy imports
from shared.infrastructure.database import SessionLocal
from shared.infrastructure.models import Material, Country, AISignal
from sqlalchemy.exc import SQLAlchemyError

USER_AGENT = 'Mozilla/5.0'


class UnifiedSentinel:
    """
    The Core Data Engine of the Sentinel System.

    This class serves as the central hub for:
    1. Data Ingestion: Fetching market data (Yahoo Finance), economic indicators (FRED), 
       and trade statistics (UN Comtrade).
    2. Data Normalization: standardizing inputs across different regions and units.
    3. Signal Processing: Generating market signals (Layer 2 of Architecture).
    4. Persistence: Handling both hot (Redis/Memory) and cold (PostgreSQL/SQLite) storage.

    Attributes:
        keys (dict): API keys configuration.
        db_config (dict): Database connection parameters (Legacy, now handled by database.py).
        fred (Fred): Client for Federal Reserve Economic Data.
        materials (dict): Master registry of tracked materials and their metadata.
        regions (dict): Master registry of tracked regions and associated countries.
    """

    def __init__(self, api_keys, db_config):
        """
        Initialize the Sentinel Engine.

        Args:
            api_keys (dict): Dictionary containing API keys ('fred', 'comtrade', etc.).
            db_config (dict): Dictionary containing DB host, user, password, etc. (Legacy)
        """
        self.keys = api_keys
        self.db_config = db_config 
        
        # Initialize Fred if key exists and library is available
        self.fred = Fred(api_key=api_keys.get('fred')) if (api_keys.get('fred') and Fred) else None
        
        # Initialize Random Number Generator with a fixed seed for reproducibility
        self.rng = np.random.default_rng(42) if np else None

        # --- Data from SentinelAutomation ---
        
        # MATERIALS MASTER LIST WITH CATEGORIES
        self.materials = {
            # POLYMERS (Oil Derivative)
            'PVC':           {'hs': '390422', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},
            'XLPE':          {'hs': '390110', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},
            'PE':            {'hs': '390110', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},
            'LSF':           {'hs': '390490', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},

            # SHIELDING (Metals - LME Linked)
            'Copper':        {'hs': '740811', 'symbol': 'HG=F',  'category': 'Shielding', 'driver': 'LME'},
            'Aluminum':      {'hs': '760511', 'symbol': 'ALI=F', 'category': 'Shielding', 'driver': 'LME'},
            'GSW':           {'hs': '721720', 'symbol': 'HRC=F', 'category': 'Shielding', 'driver': 'LME'},
            'GST':           {'hs': '721230', 'symbol': 'HRC=F', 'category': 'Shielding', 'driver': 'LME'},
            'Copper Tape':   {'hs': '741011', 'symbol': 'HG=F',  'category': 'Shielding', 'driver': 'LME'},
            'Aluminum Tape': {'hs': '760720', 'symbol': 'ALI=F', 'category': 'Shielding', 'driver': 'LME'},

            # SCREENING (Specialty - Lead Time Risk)
            'Mica Tape':     {'hs': '681490', 'symbol': 'PICK', 'category': 'Screening', 'driver': 'LeadTime'},
            'Water-blocking':{'hs': '560313', 'symbol': 'CL=F',  'category': 'Screening', 'driver': 'LeadTime'}
        }

        # REGIONS (SentinelAutomation version - detailed)
        self.regions = {
            'MENA':  {'countries': {'Egypt': '818', 'UAE': '784', 'Saudi Arabia': '682'}, 'econ_proxy': 'DCOILBRENTEU'},
            'APAC':  {'countries': {'China': '156', 'India': '356', 'Japan': '392', 'S.Korea': '410', 'Australia': '36'}, 'econ_proxy': 'CHNPRINTO01IXPYM'},
            'EU':    {'countries': {'Germany': '276', 'Italy': '380', 'France': '251', 'Spain': '724', 'UK': '826'}, 'econ_proxy': 'DEUPROINDMISMEI'},
            'NA':    {'countries': {'USA': '842', 'Canada': '124'}, 'econ_proxy': 'INDPRO'},
            'LATAM': {'countries': {'Brazil': '76', 'Chile': '152', 'Mexico': '484', 'Argentina': '32'}, 'econ_proxy': 'PRINTO01BRA659S'},
            'SSA':   {'countries': {'South Africa': '710', 'Nigeria': '566', 'Kenya': '404'}, 'econ_proxy': 'PRMNTO01ZAQ657S'}
        }

        # --- Data from CountrySentinel ---
        self.country_registry = {
            # MENA
            'Egypt':        {'trade_code': '818', 'econ_id': 'IR0000EGQ156N'},
            'UAE':          {'trade_code': '784', 'econ_id': 'MKTGDPAEA646NWDB'},
            'Saudi Arabia': {'trade_code': '682', 'econ_id': 'SAUCPALTT01GPM'},
            # APAC
            'China':        {'trade_code': '156', 'econ_id': 'CHNPRINTO01IXPYM'},
            'India':        {'trade_code': '356', 'econ_id': 'INDPROINDMISMEI'},
            'Japan':        {'trade_code': '392', 'econ_id': 'PRINTO01JPQ659S'},
            'S.Korea':      {'trade_code': '410', 'econ_id': 'PRMNTO01KRQ657S'},
            'Australia':    {'trade_code': '36',  'econ_id': 'PRMNTO01AUA657S'},
            # EU
            'Germany':      {'trade_code': '276', 'econ_id': 'A018ADDEA338NNBR'},
            'Italy':        {'trade_code': '380', 'econ_id': 'ITAPROINDMISMEI'},
            'France':       {'trade_code': '251', 'econ_id': 'A018BAFRA324NNBR'},
            'Spain':        {'trade_code': '724', 'econ_id': 'PRMNTO01ESQ661N'},
            'UK':           {'trade_code': '826', 'econ_id': 'IPIUKM'},
            # NA
            'USA':          {'trade_code': '842', 'econ_id': 'IPMAN'},
            'Canada':       {'trade_code': '124', 'econ_id': 'CANPROINDMISMEI'},
            # LATAM
            'Brazil':       {'trade_code': '76',  'econ_id': 'PRINTO01BRA659S'},
            'Chile':        {'trade_code': '152', 'econ_id': 'CHLPROINDMISMEI'},
            'Mexico':       {'trade_code': '484', 'econ_id': 'PRINTO02MXQ661S'},
            'Argentina':    {'trade_code': '32',  'econ_id': 'MKTGDPARA646NWDB'},
            # SSA
            'South Africa': {'trade_code': '710', 'econ_id': 'PRMNTO01ZAQ657S'},
            'Nigeria':      {'trade_code': '566', 'econ_id': 'MKTGDPNGA646NWDB'},
            'Kenya':        {'trade_code': '404', 'econ_id': 'MKTGDPKEA646NWDB'}
        }

        # --- Data mapping from RegionalSentinel ---
        # Proxies for regional price trends
        self.regional_proxies = {
            'MENA': 'DCOILBRENTEU',
            'NA': 'DCOILWTICO',
            'EU': 'DCOILBRENTEU',
            'APAC': 'DCOILBRENTEU',
            'LATAM': 'DCOILWTICO',
            'SSA': 'DCOILBRENTEU'
        }

        # ID Cache (populated on startup)
        self.material_ids = {}
        self.country_ids = {}
        
        # Populate cache using SQLAlchemy
        self._populate_id_cache()

    def _populate_id_cache(self):
        """Fetches ID mappings from Master Tables."""
        db = SessionLocal()
        try:
            # Cache Materials
            materials_list = db.query(Material.name, Material.id).all()
            self.material_ids = {name: id for name, id in materials_list}
            
            # Cache Countries
            countries_list = db.query(Country.name, Country.id).all()
            self.country_ids = {name: id for name, id in countries_list}
            
            print(f"✅ Loaded {len(self.material_ids)} materials and {len(self.country_ids)} countries into cache.")
        except Exception as e:
            print(f"⚠️ Failed to cache IDs: {e}")
            # If DB is not ready, this will fail. That is expected.
        finally:
            db.close()

    def _rate_limit(self, service_name):
        """
        Enforce rate limits for different services to avoid API bans.
        """
        if service_name == 'yahoo':
            time.sleep(1.0) # Yahoo is lenient but good to be safe
        elif service_name == 'comtrade':
            time.sleep(3.0) # Comtrade is strict (1 req/sec officially, but often slower for free tier)
        elif service_name == 'fred':
            time.sleep(0.5) # FRED is fast but has limits

    def get_material_id(self, name):
        return self.material_ids.get(name)

    def get_country_id(self, name):
        return self.country_ids.get(name)

    # --- Methods from SentinelAutomation ---

    def fetch_price(self, material_name):
        """
        Fetches real-time price and trend data from Yahoo Finance.

        Args:
            material_name (str): The common name of the material (e.g., 'Copper').

        Returns:
            tuple: (price (float), trend_percentage (float))
                   Returns (0.0, 0.0) on failure or if material is unknown.
        """
        if material_name not in self.materials:
            return 0.0, 0.0
            
        symbol = self.materials[material_name]['symbol']
        # Fixed price materials (e.g., contracts)
        if symbol == 'FIXED': return 50.0, 0.0
        
        self._rate_limit('yahoo')
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': USER_AGENT}
        try:
            res = requests.get(url, headers=headers).json()
            # Parse response to extract latest Price and Previous Close
            chart = res['chart']['result'][0]['meta']
            price = chart['regularMarketPrice']
            prev_close = chart['chartPreviousClose']
            
            # Calculate simple trend percentage
            trend_pct = (price - prev_close) / prev_close
            return price, trend_pct
        except Exception:
            return 0.0, 0.0

    def fetch_demand(self, reporter_code, hs_code):
        return "Demand Tracking Removed"

    def fetch_driver_data(self, category):
        """Deprecated."""
        return "Market Driven"

    def run_comprehensive_audit(self):
        """
        Executes a full system scan across all regions and materials.
        Fetches current Macro, Price, and Demand data.
        
        Returns:
            pd.DataFrame: A consolidated report of the audit.
        """
        all_results = []
        for region_name, region_data in self.regions.items():
            print(f"--- Fetching Macro for {region_name} ---")

            for country_name, country_code in region_data['countries'].items():
                print(f"   Country: {country_name} ({country_code})")
                for mat_name, mat_data in self.materials.items():
                    # 1. Price Check
                    price, trend = self.fetch_price(mat_name)
                    cat = mat_data['category']
                    driver_info = self.fetch_driver_data(cat)

                    # 2. Demand Check (Removed)
                    demand = "N/A"

                    # 3. Visualization/Logging
                    trend_symbol = "➡️"
                    if trend > 0:
                        trend_symbol = "↗️"
                    elif trend < 0:
                        trend_symbol = "↘️"
                    print(f"      [{mat_name}] Price: ${price:.2f} ({trend_symbol} {trend*100:.2f}%) | Driver: {driver_info}")

                    # 4. Aggregate Result
                    all_results.append({
                        'Region': region_name, 'Country': country_name,
                        'Material': mat_name, 'Category': cat,
                        'Price': price, 'Trend': f"{trend*100:.2f}%",
                        'Driver': driver_info
                    })
                    # Throttle loop to avoid API bans
                    time.sleep(2.0) 
        return pd.DataFrame(all_results)
    
    # --- Methods from CountrySentinel ---

    def fetch_demand_data(self, country_name):
        """Stub for detailed local demand indicator."""
        if country_name not in self.country_registry:
            return {"status": "error", "info": "Country not in registry"}
            
        # code = self.country_registry[country_name]['trade_code']
        # Comtrade Free Access logic
        return {"status": "success", "info": "Local Demand Indicator"}

    def fetch_price_data(self, symbol):
        """Returns the raw JSON response from Yahoo for a symbol."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': USER_AGENT}
        self._rate_limit('yahoo')
        try:
            return requests.get(url, headers=headers).json()
        except Exception:
            return {}

    # --- Methods from RegionalSentinel ---

    def get_regional_demand(self, region_name, hs_code):
        """Aggregates import volumes with mandatory headers for Comtrade."""
        if region_name not in self.regions:
            return {"error": "Invalid region", "data": []}
            
        # Create comma-separated list of country codes for the region
        country_codes = list(self.regions[region_name]['countries'].values())
        country_list_str = ",".join(country_codes)
        
        url = f"https://comtradeplus.un.org/api/get?reporterCode={country_list_str}&cmdCode={hs_code}&flowCode=M"

        # MANDATORY: Comtrade requires the key in the header for the Plus API
        headers = {
            'Ocp-Apim-Subscription-Key': self.keys.get('comtrade'),
            'User-Agent': USER_AGENT
        }
        
        self._rate_limit('comtrade')

        try:
            response = requests.get(url, headers=headers)
            # Check if response is actually JSON before decoding
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "data": []}
        except Exception as e:
            return {"error": str(e), "data": []}

    def get_regional_price_trend(self, region_name):
        """Uses 100% free FRED data to track energy costs (Oil)."""
        if not self.fred:
            return {}
            
        series_id = self.regional_proxies.get(region_name, 'DCOILBRENTEU')
        try:
            self._rate_limit('fred')
            data = self.fred.get_series(series_id).tail(5)
            # Convert timestamp keys to string for cleaner dict output if needed, or keep as is
            return data.to_dict()
        except Exception:
            return {}

    # --- Historical Data Fetching (For AI Training) ---

    def fetch_historical_price_series(self, symbol, time_range='10y'):
        """
        Fetches historical price data (Close price) from Yahoo Finance.
        
        Args:
            symbol (str): Ticker symbol.
            time_range (str): Range to fetch (e.g. '1y', '5y').
            
        Returns:
            pd.Series: Time-indexed series of closing prices.
        """
        if symbol == 'FIXED': return pd.Series()
        
        # Yahoo Chart API supports ranges like 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={time_range}"
        headers = {'User-Agent': USER_AGENT}
        
        self._rate_limit('yahoo')
        
        try:
            res = requests.get(url, headers=headers).json()
            chart = res['chart']['result'][0]
            timestamps = chart['timestamp']
            quotes = chart['indicators']['quote'][0]['close']
            
            # Create Pandas Series
            dates = [datetime.fromtimestamp(ts) for ts in timestamps]
            series = pd.Series(quotes, index=dates)
            series = series.dropna()
            return series
        except Exception as e:
            print(f"⚠️ Error fetching history for {symbol}: {e}")
            return pd.Series()

    def fetch_historical_driver_series(self, category):
        """Deprecated."""
        return pd.Series()

    def fetch_historical_demand_series(self, material_name, time_range='5y', country_code='818'):
        return pd.Series()

    def generate_historical_dataset(self, time_range='5y'):
        """
        Generates a consolidated training dataset from historical sources (Prices).
        This dataset is used to train the Sentinel AI models.
        
        Args:
            time_range (str): How far back to fetch data.
            
        Returns:
            pd.DataFrame: A DataFrame with columns: 
                          [Date, Material, Category, Country, Price]
        """
        print(f"⏳ Fetching historical data ({time_range})... this may take a moment.")
        all_dfs = []

        for mat_name, mat_data in self.materials.items():
            print(f"   Processing History: {mat_name}...")
            
            # 2. Fetch Price History for the material
            price_series = self.fetch_historical_price_series(mat_data['symbol'], time_range)
            if price_series.empty: continue

            # Create individual DF
            df = price_series.to_frame(name='Price')
            df['Material'] = mat_name
            df['Category'] = mat_data['category']
            
            # 5. Loop through ALL Countries (Updated for Full Scope)
            target_countries = self.country_registry
            
            for country_name, c_data in target_countries.items():
                # Copy the base DF (Price is shared globally for now)
                country_df = df.copy()
                country_df['Country'] = country_name
                
                all_dfs.append(country_df)

        if not all_dfs:
            return pd.DataFrame()

        # Combine all material histories
        final_df = pd.concat(all_dfs)
        final_df.index.name = 'Date'
        # Reset index to make Date a column
        final_df = final_df.reset_index()
        
        # Reorder for clarity
        cols = ['Date', 'Material', 'Category', 'Country', 'Price']
        # Intersect with existing in case some are missing
        final_cols = [c for c in cols if c in final_df.columns]
        return final_df[final_cols]
    
    def save_signal_to_db(self, material_name, price, prediction, recommendation, country_name='Egypt', confidence=0.0, risk=0.0):
        """
        Saves AI-generated signals to the 'signals' table using SQLAlchemy.
        """
        # Resolve Foreign Keys
        mat_id = self.get_material_id(material_name)
        country_id = self.get_country_id(country_name)
        
        if not mat_id or not country_id:
            print(f"⚠️ Lookup Failed for Signal: Mat={material_name}, Country={country_name}")
            return

        db = SessionLocal()
        try:
            signal = AISignal(
                material_id=mat_id,
                country_id=country_id,
                input_price=price,
                decision=recommendation,
                confidence_score=confidence,
                stockout_risk=risk
            )
            db.add(signal)
            db.commit()
            print(f"✅ Saved signal for {material_name} in {country_name}")
        except Exception as e:
            print(f"❌ Signal DB Error: {e}")
            db.rollback()
        finally:
            db.close()
