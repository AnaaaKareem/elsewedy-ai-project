from taipy.gui import Gui, State, tgb
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import random

# --- CONFIGURATION ---
GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
COLOR_PRIMARY = "#C9302C"
COLOR_CARD_BG = "#1F2125"
COLOR_DARK_BG = "#141517"
BORDER_STYLE = "1px solid #333"

# --- GLOBAL DATA ---
try:
    WORLD_GEOJSON = requests.get(GEOJSON_URL).json()
except:
    WORLD_GEOJSON = None

COUNTRY_MAP = {
    "EGYPT": "EGY", "SAUDI ARABIA": "SAU", "UAE": "ARE", "GERMANY": "DEU", 
    "FRANCE": "FRA", "ITALY": "ITA", "SPAIN": "ESP", "NIGERIA": "NGA", 
    "SOUTH AFRICA": "ZAF", "KENYA": "KEN", "CHINA": "CHN", "JAPAN": "JPN", 
    "INDIA": "IND", "USA": "USA", "CANADA": "CAN", "BRAZIL": "BRA", "ARGENTINA": "ARG"
}

REGIONS_CONFIG = {
    "MENA": ["EGYPT", "SAUDI ARABIA", "UAE"],
    "EU": ["GERMANY", "FRANCE", "ITALY", "SPAIN"],
    "APAC": ["CHINA", "JAPAN", "INDIA"],
    "NORTH AMERICA": ["USA", "CANADA"],
    "LATAM": ["BRAZIL", "ARGENTINA"],
    "AFRICA": ["NIGERIA", "SOUTH AFRICA", "KENYA"]
}
REGIONS = list(REGIONS_CONFIG.keys())
MATERIALS_LIST = ["Copper (LME)", "Aluminum", "XLPE Polymer", "PVC Compound", "Mica Tape", "Steel Tape"]

# --- STATE VARIABLES (Initial Values) ---
selected_country = ""
scanning_region = "MENA"
scanner_idx = 0
is_scanning = True

# Metrics Placeholders
scanner_demand = "50,000 T"
scanner_conf = "95%"
scanner_log = "> SYSTEM INITIALIZED..."

# Decision Placeholders
decision_signal = "HOLD"
decision_color = "gray"
decision_conf = "0%"
decision_vol = "---"
decision_strat = "Waiting for target..."
btn_disabled = True

# Data storage
metrics_data = []  # List of dicts for tables
map_fig = None     # Plotly figure

# --- LOGIC FUNCTIONS ---

def get_sparkline(base_val):
    """Generate fake trend data for charts"""
    vals = [base_val]
    for _ in range(20):
        vals.append(vals[-1] + np.random.normal(0, base_val * 0.02))
    return vals

def refresh_metrics(context="GLOBAL"):
    """Regenerate the data table"""
    mult = 1.0 if context == "GLOBAL" else 0.6
    data = []
    
    for mat in MATERIALS_LIST:
        base = 8500 if "Copper" in mat else (2200 if "Alum" in mat else 1200)
        trend = get_sparkline(base)
        
        # Create a mini sparkline figure
        fig = px.line(x=list(range(len(trend))), y=trend)
        fig.update_traces(line_color="#339af0", line_width=2)
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0), 
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)", 
            xaxis_visible=False, yaxis_visible=False,
            height=30, showlegend=False
        )

        data.append({
            "Material": mat,
            "Price": f"${int(base + random.randint(-100, 100)):,}",
            "Allocated": f"{int(50000 * mult):,} T",
            "Trend": fig  # Taipy can render plotly figs in tables
        })
    return data

def build_map(highlight_iso=None, center={"lat": 20, "lon": 10}, zoom=1.1):
    fig = go.Figure()

    locations = [
        {'name': 'EGYPT', 'lat': 26.8, 'lon': 30.8}, {'name': 'SAUDI ARABIA', 'lat': 23.8, 'lon': 45.0},
        {'name': 'UAE', 'lat': 23.4, 'lon': 53.8}, {'name': 'GERMANY', 'lat': 51.1, 'lon': 10.4},
        {'name': 'CHINA', 'lat': 35.8, 'lon': 104.1}, {'name': 'USA', 'lat': 37.09, 'lon': -95.7},
        {'name': 'BRAZIL', 'lat': -14.2, 'lon': -51.9}
    ]

    # Chloropleth Layer
    if highlight_iso and WORLD_GEOJSON:
        fig.add_trace(go.Choroplethmapbox(
            geojson=WORLD_GEOJSON, locations=highlight_iso, z=[1]*len(highlight_iso),
            featureidkey="id", colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(201, 48, 44, 0.4)']],
            marker_line_color=COLOR_PRIMARY, marker_line_width=2, showscale=False, hoverinfo='skip'
        ))

    # Scatter Layer
    fig.add_trace(go.Scattermapbox(
        lat=[loc['lat'] for loc in locations], lon=[loc['lon'] for loc in locations],
        mode='markers+text', text=[loc['name'] for loc in locations], textposition="top center",
        marker=go.scattermapbox.Marker(size=12, color=COLOR_PRIMARY, opacity=0.9),
        textfont=dict(color='white', size=10), hoverinfo='text',
        customdata=[loc['name'] for loc in locations]
    ))

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(style="carto-darkmatter", center=center, zoom=zoom),
        paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG, showlegend=False,
        clickmode='event+select', transition={'duration': 1000}
    )
    return fig

# --- CALLBACKS ---

def on_init(state):
    """Called when app starts"""
    state.metrics_data = refresh_metrics()
    state.map_fig = build_map()

def on_timer(state):
    """The Autonomous Scanner (Background Loop)"""
    if state.is_scanning:
        # Cycle regions
        state.scanner_idx = (state.scanner_idx + 1) % len(REGIONS)
        region = REGIONS[state.scanner_idx]
        state.scanning_region = region
        
        # Fake metrics
        state.scanner_demand = f"{random.randint(20000, 90000):,} T"
        state.scanner_conf = f"{random.randint(88, 99)}%"
        sub_list = ", ".join(REGIONS_CONFIG[region][:2]) # Shorten for UI
        state.scanner_log = f"> SECTOR: {region}\n> UNITS: {sub_list}\n> LATENCY: {random.randint(10,50)}ms"
        
        # Passive Map Highlight
        isos = [COUNTRY_MAP[c] for c in REGIONS_CONFIG[region] if c in COUNTRY_MAP]
        state.map_fig = build_map(isos)

def on_map_click(state, var_name, payload):
    """Handle Map Interaction"""
    # Taipy passes click data in payload
    # Note: Extracting customdata in Taipy's wrapper can be tricky, 
    # so we mock the selection based on point index for stability in this demo.
    if payload and "points" in payload:
        # For demo: assume index 0 is Egypt, 1 is KSA, etc. (based on locations list order)
        idx = payload["points"][0]["point_index"]
        locations = ['EGYPT', 'SAUDI ARABIA', 'UAE', 'GERMANY', 'CHINA', 'USA', 'BRAZIL']
        if idx < len(locations):
            country = locations[idx]
            
            # Update State
            state.selected_country = country
            state.is_scanning = False
            state.metrics_data = refresh_metrics(country)
            
            # Decision Engine Logic
            signal = "BUY" if random.random() > 0.4 else "HOLD"
            state.decision_signal = signal
            state.decision_color = "red" if signal == "BUY" else "gray"
            state.decision_conf = f"{random.randint(85, 99)}%"
            state.decision_vol = "HIGH" if random.random() > 0.7 else "LOW"
            state.decision_strat = "Initiate bulk procurement." if signal == "BUY" else "Wait for price dip."
            state.btn_disabled = (signal != "BUY")

            # Map Zoom
            iso = [COUNTRY_MAP[country]]
            state.map_fig = build_map(iso, zoom=3.5)

def reset_view(state):
    state.selected_country = ""
    state.is_scanning = True
    state.metrics_data = refresh_metrics("GLOBAL")
    state.map_fig = build_map()

# --- GUI LAYOUT (Using Python Builder) ---

with tgb.Page() as page:
    # 1. HEADER
    with tgb.part(style="background-color: #1A1B1E; padding: 15px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; align-items: center;"):
        with tgb.part(style="display: flex; gap: 10px; align-items: center;"):
            tgb.text("🛡️", style="font-size: 24px;")
            tgb.text("SENTINEL | COMMAND", style="color: white; font-weight: 800; font-size: 20px;")
        tgb.text("SYSTEM OPTIMAL", style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;")

    # 2. MAIN GRID
    with tgb.layout(columns="20 55 25", style="height: 90vh; background-color: #141517;"):
        
        # A. LEFT PANEL (Metrics)
        with tgb.part(style="background-color: #1F2125; border-right: 1px solid #333; padding: 10px; height: 100%;"):
            tgb.text("GLOBAL METRICS", style="color: #C1C2C5; font-weight: bold; font-size: 12px; margin-bottom: 10px;")
            
            # Taipy Table for nice list view
            tgb.table("{metrics_data}", 
                      columns={"Material": "Material", "Price": "Price", "Allocated": "Demand"},
                      show_all=True, 
                      style="background-color: transparent;")

        # B. CENTER PANEL (Map + Graphs)
        with tgb.part(style="display: flex; flex-direction: column; height: 100%; position: relative;"):
            # Map
            with tgb.part(style="flex: 7; position: relative;"):
                tgb.chart("{map_fig}", on_click=on_map_click, height="100%")
                
                # Reset Button (Visible only if country selected)
                with tgb.part(render="{selected_country != ''}", style="position: absolute; top: 10px; right: 10px; z-index: 1000;"):
                    tgb.button("❌ RESET", on_action=reset_view, style="background-color: #C9302C; color: white;")

            # Bottom Graphs (Sparklines)
            with tgb.part(style="flex: 3; background-color: #141517; border-top: 1px solid #333; padding: 10px;"):
                tgb.text("FORECASTS (30D)", style="color: #C1C2C5; font-weight: bold; font-size: 12px;")
                # Simple grid of charts using repeat? Taipy repeats are implicit in tables. 
                # For this demo, we use the table above which already contains the sparklines.
                tgb.text("Detailed trend analysis available in Left Panel table.", style="color: gray; font-size: 10px;")

        # C. RIGHT PANEL (Dynamic)
        with tgb.part(style="background-color: #1F2125; border-left: 1px solid #333; padding: 20px; height: 100%;"):
            
            # VIEW 1: DECISION ENGINE (Render if country selected)
            with tgb.part(render="{selected_country != ''}"):
                tgb.text("DECISION ENGINE", style="color: gray; font-weight: bold; font-size: 12px;")
                tgb.text("TARGET: {selected_country}", style="color: white; font-weight: 900; font-size: 24px; margin-bottom: 20px;")
                
                with tgb.part(style=f"border: 1px solid {COLOR_PRIMARY}; background-color: #141517; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px;"):
                    tgb.text("RECOMMENDATION", style="color: gray; font-size: 10px; font-weight: bold;")
                    tgb.text("{decision_signal}", style="color: {decision_color}; font-size: 40px; font-weight: 900;")
                
                with tgb.layout(columns="1 1"):
                    with tgb.part():
                        tgb.text("CONFIDENCE", style="color: gray; font-size: 10px;")
                        tgb.text("{decision_conf}", style="color: white; font-weight: bold; font-size: 18px;")
                    with tgb.part():
                        tgb.text("VOLATILITY", style="color: gray; font-size: 10px;")
                        tgb.text("{decision_vol}", style="color: white; font-weight: bold; font-size: 18px;")
                
                tgb.text("{decision_strat}", style="color: #C1C2C5; margin-top: 20px; font-style: italic; font-size: 12px;")
                tgb.button("EXECUTE ORDER", active="{not btn_disabled}", style="width: 100%; margin-top: 20px; background-color: {decision_color}; color: white;")