import solara
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import random
import time
import threading

# --- CONFIGURATION ---
GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
COLOR_PRIMARY = "#C9302C"
COLOR_CARD_BG = "#1F2125"
COLOR_DARK_BG = "#141517"
BORDER = "1px solid #333"

# --- GLOBAL DATA ---
try:
    WORLD_GEOJSON = requests.get(GEOJSON_URL).json()
except:
    WORLD_GEOJSON = None

COUNTRY_MAP = {
    "EGYPT": "EGY", "SAUDI ARABIA": "SAU", "UAE": "ARE", "GERMANY": "DEU",
    "CHINA": "CHN", "USA": "USA", "BRAZIL": "BRA"
}
REGIONS_CONFIG = {
    "MENA": ["EGYPT", "SAUDI ARABIA", "UAE"],
    "EU": ["GERMANY"],
    "APAC": ["CHINA"],
    "AMERICAS": ["USA", "BRAZIL"]
}
REGIONS = list(REGIONS_CONFIG.keys())
MATERIALS = ["Copper (LME)", "Aluminum", "XLPE Polymer", "PVC Compound"]

# --- REACTIVE STATE ---
# In Solara, these act like global state stores
selected_country = solara.reactive("")
scanning_region = solara.reactive("MENA")
scanner_log = solara.reactive("Initializing...")
metrics = solara.reactive([])

# --- LOGIC & HELPERS ---

def generate_sparkline(base):
    vals = [base]
    for _ in range(15):
        vals.append(vals[-1] + np.random.normal(0, base * 0.02))
    df = pd.DataFrame({"x": range(len(vals)), "y": vals})
    fig = px.line(df, x="x", y="y")
    fig.update_traces(line_color="#339af0", line_width=2)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                      xaxis_visible=False, yaxis_visible=False, showlegend=False, height=35)
    return fig

def refresh_metrics(context="GLOBAL"):
    mult = 1.0 if context == "GLOBAL" else 0.6
    data = []
    for mat in MATERIALS:
        base = 8500 if "Copper" in mat else 1200
        data.append({
            "name": mat,
            "price": f"${int(base + random.randint(-100, 100)):,}",
            "demand": f"{int(50000 * mult):,} T",
            "trend": generate_sparkline(base)
        })
    metrics.value = data

def build_map(iso_highlight=None, zoom=1.1, center={"lat": 20, "lon": 10}):
    fig = go.Figure()
    locations = [
        {'name': 'EGYPT', 'lat': 26.8, 'lon': 30.8}, {'name': 'SAUDI ARABIA', 'lat': 23.8, 'lon': 45.0},
        {'name': 'UAE', 'lat': 23.4, 'lon': 53.8}, {'name': 'GERMANY', 'lat': 51.1, 'lon': 10.4},
        {'name': 'CHINA', 'lat': 35.8, 'lon': 104.1}, {'name': 'USA', 'lat': 37.09, 'lon': -95.7},
        {'name': 'BRAZIL', 'lat': -14.2, 'lon': -51.9}
    ]
    
    if iso_highlight and WORLD_GEOJSON:
        fig.add_trace(go.Choroplethmapbox(
            geojson=WORLD_GEOJSON, locations=iso_highlight, z=[1]*len(iso_highlight),
            featureidkey="id", colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(201, 48, 44, 0.4)']],
            marker_line_color=COLOR_PRIMARY, marker_line_width=2, showscale=False, hoverinfo='skip'
        ))

    fig.add_trace(go.Scattermapbox(
        lat=[loc['lat'] for loc in locations], lon=[loc['lon'] for loc in locations],
        mode='markers+text', text=[loc['name'] for loc in locations], textposition="top center",
        marker=go.scattermapbox.Marker(size=12, color=COLOR_PRIMARY, opacity=0.9),
        textfont=dict(color='white', size=10), hoverinfo='none',
        customdata=[loc['name'] for loc in locations]
    ))

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(style="carto-darkmatter", center=center, zoom=zoom),
        paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG, showlegend=False,
        clickmode='event+select', transition={'duration': 1000}, autosize=True
    )
    return fig

# --- BACKGROUND WORKER ---
def scanner_loop():
    """Background thread to update scanner state"""
    idx = 0
    while True:
        if not selected_country.value: # Only scan if global
            idx = (idx + 1) % len(REGIONS)
            reg = REGIONS[idx]
            scanning_region.value = reg
            scanner_log.value = f"> SECTOR: {reg}\n> LATENCY: {random.randint(20,50)}ms\n> SYNCING..."
        time.sleep(4)

# Start background thread on module load
thread = threading.Thread(target=scanner_loop, daemon=True)
thread.start()
refresh_metrics() # Init metrics

# --- COMPONENTS ---

@solara.component
def MetricItem(item):
    """Left Panel Card"""
    with solara.Card(margin=0, classes=["dark-card"]):
        with solara.Column(gap="4px"):
            with solara.Row(justify="space-between"):
                solara.Text(item["name"], style={"font-weight": "bold", "font-size": "11px", "color": "#888"})
                solara.Text(item["price"], style={"border": "1px solid #555", "padding": "0 4px", "border-radius": "4px", "font-size": "10px"})
            with solara.Row(justify="space-between"):
                solara.Text("Allocated", style={"font-size": "10px", "color": "#666"})
                solara.Text(item["demand"], style={"font-weight": "bold", "color": "white", "font-size": "12px"})
    
    # Custom CSS injection for cards to look "Solara-dark"
    solara.Style("""
        .dark-card { background-color: #25262B !important; border-left: 3px solid #C9302C !important; margin-bottom: 8px !important; }
    """)

@solara.component
def RightPanelScanner():
    region = scanning_region.value
    demand = f"{random.randint(50, 150)},000 T"
    conf = f"{random.randint(90, 99)}%"
    
    with solara.Column(gap="20px", style={"height": "100%", "padding": "20px"}):
        with solara.Row(justify="space-between"):
            solara.Text("AUTONOMOUS SCANNER", style={"font-weight": "bold", "color": "#888"})
            solara.Text("SCANNING", style={"color": "#339af0", "font-weight": "bold"})
        
        solara.Text(f"REGION: {region}", style={"font-size": "24px", "font-weight": "900"})
        
        with solara.GridFixed(columns=2):
            with solara.Column():
                solara.Text("DEMAND", style={"color": "#888", "font-size": "10px"})
                solara.Text(demand, style={"font-size": "20px", "font-weight": "bold"})
            with solara.Column():
                solara.Text("CONFIDENCE", style={"color": "#888", "font-size": "10px"})
                solara.Text(conf, style={"font-size": "20px", "font-weight": "bold", "color": "#28a745"})
        
        solara.Text("INFERENCE LOG", style={"font-weight": "bold", "color": "#888", "margin-top": "20px"})
        solara.Preformatted(scanner_log.value, style={"background-color": "#111", "color": "#0f0", "padding": "10px", "font-size": "10px"})

@solara.component
def RightPanelDecision():
    country = selected_country.value
    signal = "BUY"
    color = "red"
    
    with solara.Column(gap="20px", style={"height": "100%", "padding": "20px"}):
        solara.Text("DECISION ENGINE", style={"font-weight": "bold", "color": "#888"})
        solara.Text(f"TARGET: {country}", style={"font-size": "24px", "font-weight": "900"})
        
        with solara.Column(style={"border": f"1px solid {COLOR_PRIMARY}", "padding": "20px", "border-radius": "8px", "background-color": "#141517", "align-items": "center"}):
             solara.Text("RECOMMENDATION", style={"color": "#888", "font-size": "10px", "font-weight": "bold"})
             solara.Text(signal, style={"color": color, "font-size": "40px", "font-weight": "900"})
        
        solara.Button("EXECUTE ORDER", color="error" if signal == "BUY" else "grey", block=True, style={"height": "50px"})

@solara.component
def MainMap():
    # Map State Logic
    iso = None
    zoom = 1.1
    center = {"lat": 20, "lon": 10}

    # If Country Selected -> Zoom
    if selected_country.value:
        iso = [COUNTRY_MAP.get(selected_country.value)]
        zoom = 3.5
        # Simplified centering logic (usually we'd lookup coords)
    # If Global Scanner -> Passive Highlight
    else:
        reg = scanning_region.value
        iso = [COUNTRY_MAP.get(c) for c in REGIONS_CONFIG.get(reg, []) if c in COUNTRY_MAP]
    
    fig = build_map(iso, zoom, center)
    
    def on_click(data):
        if data and "points" in data:
            pt = data["points"][0]
            if "customdata" in pt:
                selected_country.value = pt["customdata"]
                refresh_metrics(pt["customdata"])

    with solara.Column(style={"flex": "7", "position": "relative", "height": "100%"}):
        solara.FigurePlotly(fig, on_click=on_click)
        
        # Reset Button Overlay
        if selected_country.value:
            with solara.Div(style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1000"}):
                solara.Button("❌ RESET", color="primary", on_click=lambda: (selected_country.set(""), refresh_metrics("GLOBAL")))

@solara.component
def Page():
    # Force Dark Theme via CSS injection
    solara.Style("""
        body, .v-application { background-color: #141517 !important; color: #C1C2C5 !important; }
        .v-card { background-color: #1F2125 !important; color: white !important; }
    """)

    with solara.Column(style={"height": "100vh", "max-height": "100vh", "overflow": "hidden", "gap": "0"}):
        
        # 1. HEADER
        with solara.Row(style={"height": "60px", "background-color": "#1A1B1E", "border-bottom": BORDER, "padding": "0 20px", "align-items": "center", "justify-content": "space-between"}):
            with solara.Row(gap="10px", align="center"):
                solara.Text("🛡️", style={"font-size": "24px"})
                solara.Text("SENTINEL | COMMAND", style={"font-weight": "800", "font-size": "20px", "color": "white"})
            solara.Text("SYSTEM OPTIMAL", style={"background-color": "#28a745", "color": "white", "padding": "5px 12px", "border-radius": "15px", "font-size": "12px", "font-weight": "bold"})

        # 2. MAIN CONTENT
        with solara.Row(style={"flex": "1", "overflow": "hidden", "gap": "0"}):
            
            # A. LEFT PANEL
            with solara.Column(style={"width": "20%", "background-color": COLOR_CARD_BG, "border-right": BORDER, "height": "100%", "padding": "10px", "overflow-y": "auto"}):
                solara.Text("GLOBAL INVENTORY", style={"font-weight": "bold", "margin-bottom": "10px"})
                for item in metrics.value:
                    MetricItem(item)

            # B. CENTER PANEL
            with solara.Column(style={"flex": "1", "height": "100%", "gap": "0"}):
                # Map Area
                MainMap()
                
                # Bottom Graphs
                with solara.Row(style={"flex": "3", "background-color": "#141517", "border-top": BORDER, "padding": "10px"}):
                    with solara.Column(style={"width": "50%"}):
                        solara.Text("PRICE FORECASTS", style={"font-weight": "bold", "font-size": "12px", "color": "#666"})
                        # Reuse charts from metrics
                        for m in metrics.value[:2]:
                            solara.FigurePlotly(m["trend"])
                    with solara.Column(style={"width": "50%"}):
                        solara.Text("DEMAND FORECASTS", style={"font-weight": "bold", "font-size": "12px", "color": "#666"})
                        for m in metrics.value[2:4]:
                             solara.FigurePlotly(m["trend"])

            # C. RIGHT PANEL
            with solara.Column(style={"width": "25%", "background-color": COLOR_CARD_BG, "border-left": BORDER, "height": "100%"}):
                if selected_country.value:
                    RightPanelDecision()
                else:
                    RightPanelScanner()