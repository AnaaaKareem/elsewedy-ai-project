import os
import json
import logging
import random
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sentinel Dashboard")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Redis Connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    logger.info(f"Connected to Redis at {REDIS_URL}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    redis_client = None

# Materials Master List (from shared/data_sources/unified_sentinel.py)
MATERIALS_CONFIG = {
    'Copper':        {'category': 'Shielding', 'base_price': 8500.0, 'volatility': 0.03},
    'Aluminum':      {'category': 'Shielding', 'base_price': 2200.0, 'volatility': 0.025},
    'PVC':           {'category': 'Polymer', 'base_price': 950.0, 'volatility': 0.02},
    'XLPE':          {'category': 'Polymer', 'base_price': 1100.0, 'volatility': 0.025},
    'PE':            {'category': 'Polymer', 'base_price': 890.0, 'volatility': 0.02},
    'LSF':           {'category': 'Polymer', 'base_price': 1250.0, 'volatility': 0.03},
    'GSW':           {'category': 'Shielding', 'base_price': 650.0, 'volatility': 0.02},
    'GST':           {'category': 'Shielding', 'base_price': 720.0, 'volatility': 0.02},
    'Copper Tape':   {'category': 'Shielding', 'base_price': 9200.0, 'volatility': 0.03},
    'Aluminum Tape': {'category': 'Shielding', 'base_price': 2400.0, 'volatility': 0.025},
    'Mica Tape':     {'category': 'Screening', 'base_price': 45.0, 'volatility': 0.015},
    'Water-blocking':{'category': 'Screening', 'base_price': 32.0, 'volatility': 0.01}
}

# Countries config (from shared/infrastructure/init_db.py)
COUNTRIES_CONFIG = {
    '818': {'name': 'Egypt', 'region': 'MENA', 'base_demand': 85},
    '784': {'name': 'UAE', 'region': 'MENA', 'base_demand': 92},
    '682': {'name': 'Saudi Arabia', 'region': 'MENA', 'base_demand': 88},
    '156': {'name': 'China', 'region': 'APAC', 'base_demand': 95},
    '356': {'name': 'India', 'region': 'APAC', 'base_demand': 82},
    '392': {'name': 'Japan', 'region': 'APAC', 'base_demand': 78},
    '410': {'name': 'S.Korea', 'region': 'APAC', 'base_demand': 80},
    '36':  {'name': 'Australia', 'region': 'APAC', 'base_demand': 72},
    '276': {'name': 'Germany', 'region': 'EU', 'base_demand': 88},
    '380': {'name': 'Italy', 'region': 'EU', 'base_demand': 75},
    '251': {'name': 'France', 'region': 'EU', 'base_demand': 82},
    '724': {'name': 'Spain', 'region': 'EU', 'base_demand': 70},
    '826': {'name': 'UK', 'region': 'EU', 'base_demand': 77},
    '842': {'name': 'USA', 'region': 'NA', 'base_demand': 90},
    '124': {'name': 'Canada', 'region': 'NA', 'base_demand': 68},
    '76':  {'name': 'Brazil', 'region': 'LATAM', 'base_demand': 72},
    '484': {'name': 'Mexico', 'region': 'LATAM', 'base_demand': 65},
    '32':  {'name': 'Argentina', 'region': 'LATAM', 'base_demand': 58},
    '710': {'name': 'South Africa', 'region': 'SSA', 'base_demand': 62},
    '566': {'name': 'Nigeria', 'region': 'SSA', 'base_demand': 55},
    '404': {'name': 'Kenya', 'region': 'SSA', 'base_demand': 48}
}

# Database Connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "passme123"),
            dbname=os.getenv("DB_NAME", "sentinel_db"),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"DB Connection Error: {e}")
        return None

def generate_live_material_data():
    """Generate live material data with realistic price variations."""
    materials = []
    random.seed(int(datetime.now().timestamp() / 2))  # Change every 2 seconds
    
    for name, config in MATERIALS_CONFIG.items():
        # Generate price variation based on volatility
        price_change = random.uniform(-config['volatility'], config['volatility'])
        current_price = config['base_price'] * (1 + price_change)
        trend = price_change * 100  # Convert to percentage
        
        # Generate decision based on trend
        if trend > 1.5:
            decision = 'BUY'
        elif trend < -1.5:
            decision = 'HOLD'
        else:
            decision = 'WAIT'
        
        materials.append({
            'name': name,
            'category': config['category'],
            'price': round(current_price, 2),
            'trend': round(trend, 2),
            'decision': decision,
            'confidence': round(random.uniform(0.75, 0.98), 2),
            'source': 'live_feed'
        })
    
    return materials

def generate_country_metrics(country_code):
    """Generate country metrics based on config."""
    if country_code not in COUNTRIES_CONFIG:
        return None
    
    config = COUNTRIES_CONFIG[country_code]
    random.seed(int(datetime.now().timestamp() / 30) + hash(country_code))  # Stable for 30 seconds per country
    
    # Generate realistic metrics
    demand_variation = random.uniform(-10, 15)
    demand_index = config['base_demand'] + demand_variation
    
    risk_score = random.uniform(0, 1)
    if risk_score > 0.7:
        risk_level = 'High'
        econ_health = 'Volatile'
    elif risk_score > 0.4:
        risk_level = 'Medium'
        econ_health = 'Stable'
    else:
        risk_level = 'Low'
        econ_health = 'Robust'
    
    active_projects = random.randint(2, 25)
    
    return {
        'name': config['name'],
        'region': config['region'],
        'economic_health': econ_health,
        'local_demand_index': round(demand_index, 1),
        'active_projects': active_projects,
        'risk_level': risk_level
    }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/live")
async def get_live_data():
    """
    Fetches real-time data from Redis or generates live demo data.
    Also fetches latest AI signals from DB.
    Guarantees all 12 tracked materials are present.
    """
    data = {"materials": [], "ai_signals": []}
    
    # 1. Try to get Live Prices from Redis
    if redis_client:
        try:
            keys = redis_client.keys("live:*")
            for key in keys:
                val = redis_client.hgetall(key)
                if val:
                    val['name'] = key.replace("live:", "")
                    data["materials"].append(val)
        except Exception as e:
            logger.error(f"Redis fetch error: {e}")

    # 2. Try to get Recent Signals from DB
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT s.id, m.name as material, s.input_price, s.decision, s.created_at
                FROM ai_signals s
                JOIN materials m ON s.material_id = m.id
                ORDER BY s.created_at DESC
                LIMIT 10
            """)
            data["ai_signals"] = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"DB fetch error: {e}")
            
    # 3. Merge DB signals if they introduce new materials
    for signal in data["ai_signals"]:
        if any(m['name'] == signal['material'] for m in data["materials"]):
            continue
        data["materials"].append({
            "name": signal['material'],
            "price": signal['input_price'],
            "decision": signal['decision'],
            "trend": 0.0,
            "source": "database",
            "category": MATERIALS_CONFIG.get(signal['material'], {}).get('category', 'Unknown')
        })
    
    # 4. GUARANTEE FULL LIST: Backfill any missing materials from simulated data
    # This ensures exactly 12 materials are always returned
    simulated_data = generate_live_material_data()
    for sim_mat in simulated_data:
        # If this material is NOT yet in our list, add it
        if not any(m['name'] == sim_mat['name'] for m in data["materials"]):
            sim_mat["source"] = "live_simulation_backfill"
            data["materials"].append(sim_mat)
            
    # Sort by name for consistent UI
    data["materials"].sort(key=lambda x: x['name'])
            
    return data

@app.get("/api/country/{country_code}")
async def get_country_details(country_code: str):
    """
    Returns specific data for a country.
    Tries database first, falls back to generated metrics.
    """
    # Try Real Data from Database first
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            
            # Get Country ID and Name
            cur.execute("SELECT id, name FROM countries WHERE code = %s", (country_code,))
            country = cur.fetchone()
            
            if country:
                country_id = country['id']
                country_name = country['name']
                
                # Aggregate stats from recent signals
                cur.execute("""
                    SELECT 
                        COUNT(*) as signal_count,
                        AVG(confidence_score) as avg_confidence,
                        MAX(stockout_risk) as max_risk
                    FROM ai_signals 
                    WHERE country_id = %s
                    AND created_at > NOW() - INTERVAL '24 hours'
                """, (country_id,))
                stats = cur.fetchone()
                
                # If we have actual data, use it
                if stats and stats['signal_count'] > 0:
                    risk_val = stats['max_risk'] if stats['max_risk'] else 0.0
                    avg_conf = stats['avg_confidence'] if stats['avg_confidence'] else 0.0
                    
                    econ_health = "Stable"
                    if risk_val > 0.5:
                        econ_health = "Volatile"
                    elif avg_conf > 0.9:
                        econ_health = "Robust"
                        
                    cur.close()
                    conn.close()
                    
                    return {
                        "name": country_name,
                        "economic_health": econ_health,
                        "local_demand_index": round(80.0 + (risk_val * 10), 1),
                        "active_projects": stats['signal_count'] or 0,
                        "risk_level": "High" if risk_val > 0.3 else "Low",
                        "source": "database"
                    }
            
            cur.close()
            conn.close()
                
        except Exception as e:
            logger.error(f"Country fetch error: {e}")
    
    # Fall back to generated metrics
    metrics = generate_country_metrics(country_code)
    if metrics:
        metrics["source"] = "generated"
        return metrics
    
    return {"error": "Country not found", "code": country_code}

@app.get("/api/materials")
async def get_materials_list():
    """Returns the list of all tracked materials."""
    return {"materials": list(MATERIALS_CONFIG.keys())}

@app.get("/api/countries")
async def get_countries_list():
    """Returns the list of all tracked countries."""
    return {"countries": COUNTRIES_CONFIG}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
