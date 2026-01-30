import os
import json
import logging
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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/live")
async def get_live_data():
    """
    Fetches real-time data from Redis key `live:updates` which produces populate.
    Also fetches latest AI signals from DB.
    """
    data = {"materials": [], "ai_signals": []}
    
    # 1. Get Live Prices from Redis (Simulated for now if empty)
    # The keys would generally be "live:{material_name}"
    # We will scan for keys
    if redis_client:
        try:
            keys = redis_client.keys("live:*")
            for key in keys:
                val = redis_client.hgetall(key)
                # val should have price, trend, etc.
                if val:
                    val['name'] = key.replace("live:", "")
                    data["materials"].append(val)
        except Exception as e:
            logger.error(f"Redis fetch error: {e}")

    # 2. Get Recent Signals from DB
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
            
    # 3. Fallback/Augmentation: Ensure Materials List has data from DB if Redis is empty
    # This guarantees we see "Real Data" (from DB) even if Live Feed (Redis) is quiet
    if not data["materials"] and data["ai_signals"]:
        for signal in data["ai_signals"]:
            # Check if material already added (deduplicate)
            if any(m['name'] == signal['material'] for m in data["materials"]):
                continue
                
            data["materials"].append({
                "name": signal['material'],
                "price": signal['input_price'],
                "decision": signal['decision'],
                "trend": 0.0, # DB doesn't have trend yet, default to stable
                "risk": 0.0,
                "confidence": 0.95,
                "source": "database_fallback"
            })
            
    return data

@app.get("/api/country/{country_code}")
async def get_country_details(country_code: str):
    """
    Returns specific data for a country (e.g. Egypt).
    This simulates fetching local demand or economic proxy data.
    """
    # Real Data Response
    conn = get_db_connection()
    if not conn:
         return {"error": "Database unavailable"}
    
    try:
        cur = conn.cursor()
        
        # Get Country ID and Name
        cur.execute("SELECT id, name FROM countries WHERE code = %s", (country_code,))
        country = cur.fetchone()
        
        if not country:
            return {"error": "Country not found"}
            
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
        
        # Interpret stats
        base_demand = 80.0
        risk_val = stats['max_risk'] if stats['max_risk'] else 0.0
        avg_conf = stats['avg_confidence'] if stats['avg_confidence'] else 0.0
        
        # Simple Logic to synthesize "Economic Health" from data
        econ_health = "Stable"
        if risk_val > 0.5:
            econ_health = "Volatile"
        elif avg_conf > 90:
            econ_health = "Robust"
            
        response = {
            "name": country_name,
            "economic_health": econ_health,
            "local_demand_index": base_demand + (risk_val * 10), # Pseudo-logic: higher risk implies higher demand/scarcity
            "active_projects": stats['signal_count'] or 0, # Using signal count as proxy for activity
            "risk_level": "High" if risk_val > 0.3 else "Low"
        }
        
        cur.close()
        conn.close()
        return response
        
    except Exception as e:
        logger.error(f"Country fetch error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
