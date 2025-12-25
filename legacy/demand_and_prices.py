import requests
import pandas as pd
from fredapi import Fred
import time
import threading
from infrastructure.config import config

KEYS = config.KEYS

"""
LEGACY MODULE - DEPRECATED

This module contains the original monolithic implementation of the Sentinel system.
It includes `SentinelAutomation`, `CountrySentinel`, and `RegionalSentinel` classes.
These functionalities have been refactored and migrated to:
- `data_sources/unified_sentinel.py` (Core Logic)
- `services/` (Orchestration & Workers)

Do not use this module for new development. It is kept for reference and archival purposes.
"""

class SentinelAutomation:
    """
    [DEPRECATED] Original base class for Sentinel Automation.
    Superseded by `UnifiedSentinel` in `data_sources`.
    """
    def __init__(self, api_keys):
        self.keys = api_keys
        self.fred = Fred(api_key=api_keys.get('fred'))

        # MATERIALS MASTER LIST WITH CATEGORIES
        self.materials = {
            # POLYMERS (Oil Derivative)
            'PVC':           {'hs': '3904',   'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},
            'XLPE':          {'hs': '390110', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},
            'PE':            {'hs': '390110', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},
            'LSF':           {'hs': '390490', 'symbol': 'CL=F', 'category': 'Polymer', 'driver': 'Oil'},

            # SHIELDING (Metals - LME Linked)
            'Copper':        {'hs': '7408',   'symbol': 'HG=F',  'category': 'Shielding', 'driver': 'LME'},
            'Aluminum':      {'hs': '7605',   'symbol': 'ALI=F', 'category': 'Shielding', 'driver': 'LME'},
            'GSW':           {'hs': '721720', 'symbol': 'HRC=F', 'category': 'Shielding', 'driver': 'LME'},
            'Copper Tape':   {'hs': '741011', 'symbol': 'HG=F',  'category': 'Shielding', 'driver': 'LME'},
            'Aluminum Tape': {'hs': '760720', 'symbol': 'ALI=F', 'category': 'Shielding', 'driver': 'LME'},

            # SCREENING (Specialty - Lead Time Risk)
            'Mica Tape':     {'hs': '681490', 'symbol': 'FIXED', 'category': 'Screening', 'driver': 'LeadTime'},
            'Water-blocking':{'hs': '560313', 'symbol': 'FIXED', 'category': 'Screening', 'driver': 'LeadTime'}
        }

        # REGIONS
        self.regions = {
            'MENA':  {'countries': {'Egypt': '818', 'UAE': '784', 'Saudi Arabia': '682'}, 'econ_proxy': 'DCOILBRENTEU'},
            'APAC':  {'countries': {'China': '156', 'India': '356', 'Japan': '392', 'S.Korea': '410', 'Australia': '36'}, 'econ_proxy': 'CHNPRINTO01IXPYM'},
            'EU':    {'countries': {'Germany': '276', 'Italy': '380', 'France': '251', 'Spain': '724', 'UK': '826'}, 'econ_proxy': 'DEUPROINDMISMEI'},
            'NA':    {'countries': {'USA': '842', 'Canada': '124'}, 'econ_proxy': 'INDPRO'},
            'LATAM': {'countries': {'Brazil': '76', 'Mexico': '484', 'Argentina': '32'}, 'econ_proxy': 'PRINTO01BRA659S'},
            'SSA':   {'countries': {'South Africa': '710', 'Nigeria': '566', 'Kenya': '404'}, 'econ_proxy': 'PRMNTO01ZAQ657S'}
        }

    def fetch_price(self, material_name):
        symbol = self.materials[material_name]['symbol']
        if symbol == 'FIXED': return 50.0, 0.0
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': USER_AGENT}
        try:
            res = requests.get(url, headers=headers).json()
            # Capture the previous close to calculate trend
            chart = res['chart']['result'][0]['meta']
            price = chart['regularMarketPrice']
            prev_close = chart['chartPreviousClose']
            trend_pct = (price - prev_close) / prev_close
            return price, trend_pct
        except Exception:
            return 0.0, 0.0

    def fetch_demand(self, reporter_code, hs_code):
        """Fetches Real API data from UN Comtrade (Public v1) with Retry."""
        # Public Preview API (Free, Rate Limited)
        url = f"https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode={reporter_code}&period=2023&partnerCode=0&cmdCode={hs_code}&flowCode=M"

        headers = { 'Ocp-Apim-Subscription-Key': self.keys.get('comtrade', ''), 'User-Agent': USER_AGENT }

        for attempt in range(3):
            try:
                res = requests.get(url, headers=headers)

                if res.status_code == 429:
                    wait_time = (attempt + 1) * 5 # Aggressive backoff: 5s, 10s, 15s
                    print(f"   ⏳ Hit Rate Limit (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if res.status_code != 200:
                     return f"API Error {res.status_code}: {res.text[:30]}"

                try:
                    data = res.json()
                except Exception:
                    return f"JSON Error: {res.text[:50]}"

                if 'data' in data and len(data['data']) > 0:
                    rec = data['data'][0]
                    qty = rec.get('netWgt', 0)
                    val = rec.get('primaryValue', 0)
                    return f"{qty} kg (${val})"
                return "No Data (2023)"

            except Exception as e:
                return f"Error: {e}"
        return "API Error 429 (Rate Limit Persisted)"

    def fetch_driver_data(self, category):
        """Fetches the driver for the category (Oil, Construction, etc.)"""
        if category == 'Polymer':
            # Oil Price (Brent)
            try:
                oil = self.fred.get_series('DCOILBRENTEU').iloc[-1]
                return f"Oil ${oil:.2f}"
            except Exception: return "Oil N/A"
        elif category == 'Screening':
            # Construction Seasonality Proxy
            try:
                cons = self.fred.get_series('TTLCONS').iloc[-1]
                return f"Global Const. Index: {cons:.0f}"
            except Exception: return "Const. Index N/A"
        return "Market Driven"

    def run_comprehensive_audit(self):
        all_results = []
        for region_name, region_data in self.regions.items():
            print(f"--- Fetching Macro for {region_name} ---")

            for country_name, country_code in region_data['countries'].items():
                for mat_name, mat_data in self.materials.items():
                    price, trend = self.fetch_price(mat_name)
                    cat = mat_data['category']
                    driver_info = self.fetch_driver_data(cat)

                    # Real Demand Fetch
                    demand = self.fetch_demand(country_code, mat_data['hs'])

                    all_results.append({
                        'Region': region_name, 'Country': country_name,
                        'Material': mat_name, 'Category': cat,
                        'Price': price, 'Trend': f"{trend*100:.2f}%",
                        'Demand': demand, 'Driver': driver_info
                    })
                    time.sleep(2.0) # Slower loop for API
        return pd.DataFrame(all_results)

if __name__ == "__main__":
    # Initialize the Global Engine
    global_sentinel = SentinelAutomation(KEYS)

    print("🚀 Starting Global Smart Audit (Categories + Drivers)...")

    # Run the master loop
    master_df = global_sentinel.run_comprehensive_audit()

    # Save
    master_df.to_csv("global_sentinel_audit.csv", index=False)

    print("\\n✅ Audit Complete. Risk Analysis Preview:")
    print(master_df[['Country', 'Material', 'Category', 'Driver']].head())

"""# Country-Specific Demand & Price Extractor"""

class CountrySentinel(SentinelAutomation):
    def __init__(self, api_keys, country_name):
        super().__init__(api_keys)
        self.country = country_name
        self.registry = {
            # MENA
            'Egypt':        {'trade_code': '818', 'econ_id': 'IR0000EGQ156N'}, # CPI/Inflation proxy
            'UAE':          {'trade_code': '784', 'econ_id': 'MKTGDPAEA646NWDB'}, # GDP (Proxy)
            'Saudi Arabia': {'trade_code': '682', 'econ_id': 'SAUCPALTT01GPM'}, # CPI

            # APAC
            'China':        {'trade_code': '156', 'econ_id': 'CHNPRINTO01IXPYM'}, # IP
            'India':        {'trade_code': '356', 'econ_id': 'INDPROINDMISMEI'}, # IP
            'Japan':        {'trade_code': '392', 'econ_id': 'PRINTO01JPQ659S'}, # IP
            'S.Korea':      {'trade_code': '410', 'econ_id': 'PRMNTO01KRQ657S'}, # Mfg IP
            'Australia':    {'trade_code': '36',  'econ_id': 'PRMNTO01AUA657S'}, # Mfg IP

            # EU
            'Germany':      {'trade_code': '276', 'econ_id': 'A018ADDEA338NNBR'}, # IP
            'Italy':        {'trade_code': '380', 'econ_id': 'ITAPROINDMISMEI'}, # IP
            'France':       {'trade_code': '251', 'econ_id': 'A018BAFRA324NNBR'}, # IP
            'Spain':        {'trade_code': '724', 'econ_id': 'PRMNTO01ESQ661N'}, # Mfg IP
            'UK':           {'trade_code': '826', 'econ_id': 'IPIUKM'}, # IP

            # NA
            'USA':          {'trade_code': '842', 'econ_id': 'IPMAN'}, # Mfg IP
            'Canada':       {'trade_code': '124', 'econ_id': 'CANPROINDMISMEI'}, # IP

            # LATAM
            'Brazil':       {'trade_code': '76',  'econ_id': 'PRINTO01BRA659S'}, # IP
            'Mexico':       {'trade_code': '484', 'econ_id': 'PRINTO02MXQ661S'}, # IP
            'Argentina':    {'trade_code': '32',  'econ_id': 'MKTGDPARA646NWDB'}, # GDP

            # SSA
            'South Africa': {'trade_code': '710', 'econ_id': 'PRMNTO01ZAQ657S'}, # Mfg IP
            'Nigeria':      {'trade_code': '566', 'econ_id': 'MKTGDPNGA646NWDB'}, # GDP
            'Kenya':        {'trade_code': '404', 'econ_id': 'MKTGDPKEA646NWDB'}  # GDP
        }

    def fetch_demand_data(self):
        # Comtrade Free Access logic
        return {"status": "success", "info": "Local Demand Indicator"}

    def fetch_price_data(self, symbol):
        """Replaced paid metals-api with free Yahoo Finance logic."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {'User-Agent': USER_AGENT}
        return requests.get(url, headers=headers).json()

import requests
import time
from fredapi import Fred

# --- Updated Driver Code ---

if __name__ == "__main__":
    # Initialize keys (ensure these are set in your environment/Colab)
    try:
        KEYS = {
            'fred': userdata.get('FRED_API_KEY'),
            'comtrade': userdata.get('COMTRADE_API_KEY')
        }
    except Exception:
        KEYS = {'fred': None, 'comtrade': None}
        print("⚠️ Keys not found. API calls may fail.")

    # Instantiate the sentinel
    # Note: Using 'Egypt' to initialize, but we'll iterate through regions below
    sentinel = SentinelAutomation(KEYS)

    # Define the specific materials you want to scan from the internal master list
    target_materials = ['Copper', 'XLPE', 'Mica Tape']

    print("🌍 Starting Global Demand & Price Analysis...\n")

    # Iterate through the regions and countries defined in the class
    for region, region_data in sentinel.regions.items():
        print(f"=== REGION: {region} ===")

        for country, code in region_data['countries'].items():
            print(f"\n--- {country} (Code: {code}) ---")

            for mat_name in target_materials:
                # 1. Fetch Price & Trend using the class function
                # Logic: Returns (price, trend_pct)
                price, trend = sentinel.fetch_price(mat_name)

                # 2. Fetch Demand using the class function
                # Logic: Uses the registry country code and the material HS code
                hs_code = sentinel.materials[mat_name]['hs']
                demand_info = sentinel.fetch_demand(code, hs_code)

                # Format output
                trend_arrow = "➡️"
                if trend > 0:
                    trend_arrow = "↗️"
                elif trend < 0:
                    trend_arrow = "↘️"

                print(f"📦 {mat_name:10} | Price: ${price:<8.2f} ({trend_arrow} {trend*100:+.2f}%)")
                print(f"   📊 Demand: {demand_info}")

            # Rate limit handling between countries to avoid 429 errors
            time.sleep(1.5)
        print("\n" + "="*30 + "\n")

"""# Region-Specific Demand & Price Extractor"""

class RegionalSentinel:
    def __init__(self, api_keys):
        self.keys = api_keys
        self.fred = Fred(api_key=api_keys.get('fred'))
        self.regions = {
            'MENA':  ['818', '784', '682'],         # Egypt, UAE, Saudi
            'APAC':  ['156', '356', '392', '410'],  # China, India, Japan, Korea
            'EU':    ['276', '380', '251', '826'],  # Germany, Italy, France, UK
            'NA':    ['842', '124'],                # USA, Canada
            'LATAM': ['76', '484', '32'],           # Brazil, Mexico, Argentina
            'SSA':   ['710', '566', '404']          # South Africa, Nigeria, Kenya
        }

    def get_regional_demand(self, region_name, hs_code):
        """Aggregates import volumes with mandatory headers for Comtrade."""
        country_list = ",".join(self.regions[region_name])
        url = f"https://comtradeplus.un.org/api/get?reporterCode={country_list}&cmdCode={hs_code}&flowCode=M"

        # MANDATORY: Comtrade requires the key in the header for the Plus API
        headers = {
            'Ocp-Apim-Subscription-Key': self.keys.get('comtrade'),
            'User-Agent': USER_AGENT
        }

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
        proxies = {
            'MENA': 'DCOILBRENTEU',
            'NA': 'DCOILWTICO',
            'EU': 'DCOILBRENTEU',
            'APAC': 'DCOILBRENTEU',
            'LATAM': 'DCOILWTICO',
            'SSA': 'DCOILBRENTEU'
        }
        series_id = proxies.get(region_name, 'DCOILBRENTEU')
        try:
            data = self.fred.get_series(series_id).tail(5)
            return data.to_dict()
        except Exception:
            return {}

if __name__ == "__main__":
    regional_analyst = RegionalSentinel(KEYS)

    # Iterate through all available regions dynamically
    all_regions = list(regional_analyst.regions.keys())
    print(f"🌍 Starting Regional Analysis for {len(all_regions)} Regions...\\n")

    for region in all_regions:
        try:
            print(f"--- Processing {region} ---")

            # 1. Get Regional Demand (REAL DATA ONLY)
            # Using '2525' (Mica) as example
            print(f"📊 Fetching {region} Mica Demand...")
            demand_data = regional_analyst.get_regional_demand(region, '2525')

            if "error" in demand_data:
                 print(f"⚠️ Comtrade Notice: {demand_data['error']} (No data available)")
            else:
                 print(f"✅ Demand Data Received: {len(demand_data.get('data', []))} records")

            # 2. Check Energy Proxy
            print(f"🔥 checking {region} Energy Trends...")
            energy_trend = regional_analyst.get_regional_price_trend(region)

            if energy_trend:
                # Get the last date/price
                last_date = sorted(energy_trend.keys())[-1]
                last_price = energy_trend[last_date]
                print(f"Energy Proxy (Oil): ${last_price:.2f} (as of {last_date.strftime('%Y-%m-%d')})")
            else:
                print("⚠️ Could not fetch FRED energy trend.")

            print("") # Newline separator

        except Exception as e:
            print(f"⚠️ Error processing {region}: {e}")

        time.sleep(0.5)