import dash
from dash import dcc, html, Input, Output, State, no_update, callback_context
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
import random
import requests

# --- CONFIGURATION ---
MOCK_MODE = True
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"

# --- THEME CONSTANTS ---
COLOR_PRIMARY = "#C9302C"  # Elsewedy Red
COLOR_ACCENT = "#28a745"   # Success Green
COLOR_DARK_BG = "#141517"
COLOR_CARD_BG = "#1F2125"
COLOR_TEXT = "#C1C2C5"
BORDER_STYLE = "1px solid #333"

app = dash.Dash(__name__)
app.title = "Sentinel | Final"

# --- GLOBAL GEOMETRY ---
print("🌍 Initializing Geometry Engine...")
try:
    response = requests.get(GEOJSON_URL)
    WORLD_GEOJSON = response.json()
except Exception:
    WORLD_GEOJSON = None

# --- MAPPING & CONFIG ---
COUNTRY_MAP = {
    "EGYPT": "EGY", "SAUDI ARABIA": "SAU", "UAE": "ARE",
    "GERMANY": "DEU", "FRANCE": "FRA", "ITALY": "ITA", "SPAIN": "ESP",
    "NIGERIA": "NGA", "SOUTH AFRICA": "ZAF", "KENYA": "KEN",
    "CHINA": "CHN", "JAPAN": "JPN", "INDIA": "IND",
    "USA": "USA", "CANADA": "CAN", "BRAZIL": "BRA", "ARGENTINA": "ARG"
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

# --- MOCK DATA ---
MATERIALS_LIST = [
    "Copper (LME)", "Aluminum", "XLPE Polymer", "PVC Compound", 
    "Mica Tape", "Steel Tape", "Lead Ingots", "Masterbatch"
]

rng = np.random.default_rng(42)  # Seeded generator

def get_sparkline_data(base_val, volatility=0.05, steps=30):
    vals = [base_val]
    for _ in range(steps):
        change = rng.normal(0, base_val * volatility)
        vals.append(vals[-1] + change)
    return vals

def get_metrics(context="GLOBAL"):
    if context == "GLOBAL":
        multiplier = 1.0
    else:
        multiplier = 0.6
    data = []
    for mat in MATERIALS_LIST:
        if "Copper" in mat:
            base_price = 8500
        elif "Alum" in mat:
            base_price = 2200
        else:
            base_price = 1200
        base_demand = 50000 if context == "GLOBAL" else 8000
        
        data.append({
            "name": mat,
            "price": int(base_price + rng.integers(-100, 100)),
            "price_trend": get_sparkline_data(base_price, 0.02),
            "demand": int(base_demand * multiplier + rng.integers(-500, 500)),
            "demand_trend": get_sparkline_data(base_demand, 0.05),
        })
    return data

def get_decision_matrix(context):
    status = "BUY" if rng.random() > 0.4 else "HOLD"
    return {
        "signal": status,
        "confidence": rng.integers(87, 99),
        "volatility": "HIGH" if rng.random() > 0.7 else "STABLE",
        "strategy": "Front-load inventory due to projected LME surge." if status == "BUY" else "Maintain safety stock. Price correction expected."
    }

def get_scanner_status():
    return {
        "demand": rng.integers(10000, 150000),
        "confidence": rng.integers(85, 99)
    }

# --- VISUAL COMPONENTS ---

def create_mini_graph(data, color):
    df = pd.DataFrame({"t": range(len(data)), "y": data})
    fig = px.line(df, x="t", y="y")
    fig.update_traces(line={"color": color, "width": 2})
    fig.update_layout(
        margin={"l":0, "r":0, "t":0, "b":0},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=35,
        xaxis={"visible": False}, yaxis={"visible": False}
    )
    return fig

def create_left_panel_card(item):
    return dmc.Paper(
        p="xs", mb="xs", radius="sm",
        style={"backgroundColor": "#25262B", "borderLeft": f"3px solid {COLOR_PRIMARY}"},
        children=[
            dmc.Group(position="apart", children=[
                dmc.Text(item["name"], size="xs", weight=700, color="dimmed"),
                dmc.Badge(f"${item['price']:,}", color="gray", variant="outline", size="xs")
            ]),
            dmc.Group(position="apart", mt=4, children=[
                dmc.Text("Allocated", size="xs", color="dimmed"),
                dmc.Text(f"{item['demand']:,} T", size="xs", color="white", weight=700)
            ])
        ]
    )

def create_bottom_card(material_data, is_price=True):
    val = f"${material_data['price']:,}" if is_price else f"{material_data['demand']:,} T"
    trend_data = material_data['price_trend'] if is_price else material_data['demand_trend']
    color = "#339af0" if is_price else "#51cf66"

    return dmc.Paper(
        p="sm", radius="md",
        style={"backgroundColor": COLOR_CARD_BG, "border": "1px solid #2C2E33"},
        children=[
            dmc.Text(material_data["name"], size="xs", color="dimmed", weight=700, mb=2),
            dmc.Group(position="apart", mb=5, children=[
                dmc.Text(val, size="lg", weight=700, color="white"),
                dmc.Badge("30D", size="xs", variant="dot", color="gray")
            ]),
            dcc.Graph(
                figure=create_mini_graph(trend_data, color),
                config={"displayModeBar": False}, style={"height": "40px"}
            )
        ]
    )

def build_map(highlight_iso_codes=None, center_lat=20, center_lon=10, zoom=1.1):
    fig = go.Figure()

    locations = [
        {'name': 'EGYPT', 'lat': 26.8, 'lon': 30.8}, 
        {'name': 'SAUDI ARABIA', 'lat': 23.8, 'lon': 45.0},
        {'name': 'UAE', 'lat': 23.4, 'lon': 53.8},
        {'name': 'GERMANY', 'lat': 51.1, 'lon': 10.4},
        {'name': 'FRANCE', 'lat': 46.2, 'lon': 2.2},
        {'name': 'NIGERIA', 'lat': 9.08, 'lon': 8.67},
        {'name': 'CHINA', 'lat': 35.8, 'lon': 104.1},
        {'name': 'USA', 'lat': 37.09, 'lon': -95.7},
        {'name': 'BRAZIL', 'lat': -14.2, 'lon': -51.9},
    ]

    # Choropleth Layer (Borders)
    if highlight_iso_codes and WORLD_GEOJSON:
        df_geo = pd.DataFrame({'iso': highlight_iso_codes, 'val': [1]*len(highlight_iso_codes)})
        fig.add_trace(go.Choroplethmapbox(
            geojson=WORLD_GEOJSON, locations=df_geo['iso'], z=df_geo['val'],
            featureidkey="id", colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(201, 48, 44, 0.4)']],
            marker_line_color=COLOR_PRIMARY, marker_line_width=2, showscale=False, hoverinfo='skip'
        ))

    # Scatter Layer (Points)
    fig.add_trace(go.Scattermapbox(
        lat=[loc['lat'] for loc in locations],
        lon=[loc['lon'] for loc in locations],
        mode='markers+text',
        text=[loc['name'] for loc in locations],
        textposition="top center",
        marker=go.scattermapbox.Marker(size=12, color=COLOR_PRIMARY, opacity=0.9),
        textfont={"color": 'white', "size": 10},
        hoverinfo='none',
        customdata=[loc['name'] for loc in locations]
    ))

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox={"style": "carto-darkmatter", "center": {"lat": center_lat, "lon": center_lon}, "zoom": zoom},
        paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG, showlegend=False,
        clickmode='event+select', uirevision='sentinel_map',
        # ANIMATION SETTINGS
        transition={'duration': 2000, 'easing': 'cubic-in-out'}, 
        autosize=True
    )
    return fig

# --- APP LAYOUT (FLEXBOX FOR RESIZING) ---
app.layout = dmc.MantineProvider(
    theme={"colorScheme": "dark", "primaryColor": "red"},
    children=[
        # ROOT FLEX CONTAINER
        html.Div(
            style={
                "backgroundColor": COLOR_DARK_BG, 
                "height": "100vh", 
                "width": "100vw", 
                "display": "flex", 
                "flexDirection": "column",
                "overflow": "hidden"
            },
            children=[
                
                # 1. HEADER (Fixed 60px)
                dmc.Header(
                    height=60, p="xs", style={"backgroundColor": "#1A1B1E", "borderBottom": BORDER_STYLE, "flexShrink": 0},
                    children=[
                        dmc.Group(position="apart", children=[
                            dmc.Group([
                                DashIconify(icon="mdi:shield-check", width=30, color=COLOR_PRIMARY),
                                dmc.Text("SENTINEL | COMMAND", size="lg", weight=800, color="white")
                            ]),
                            dmc.Badge("SYSTEM OPTIMAL", color="green", variant="filled")
                        ])
                    ]
                ),

                # 2. CONTENT BODY (Flex 1)
                html.Div(
                    style={"display": "flex", "flex": 1, "overflow": "hidden"},
                    children=[
                        
                        # A. LEFT PANEL
                        html.Div(
                            style={"width": "20%", "height": "100%", "borderRight": BORDER_STYLE, "backgroundColor": COLOR_CARD_BG, "display": "flex", "flexDirection": "column"},
                            children=[
                                dmc.Stack(style={"flex": 1, "padding": "10px", "overflow": "hidden"}, children=[
                                    dmc.Group(position="apart", children=[
                                        dmc.Text("GLOBAL", id="left-panel-title", weight=800, color="white", size="sm"),
                                        DashIconify(icon="mdi:database", color=COLOR_PRIMARY)
                                    ]),
                                    dmc.Divider(mb="sm"),
                                    dmc.ScrollArea(style={"flex": 1}, children=[html.Div(id="left-panel-content")])
                                ])
                            ]
                        ),

                        # B. CENTER PANEL (Map + Graphs)
                        html.Div(
                            style={"flex": 1, "height": "100%", "display": "flex", "flexDirection": "column", "position": "relative"},
                            children=[
                                # Map Area (70%)
                                html.Div(
                                    style={"flex": "7", "position": "relative", "width": "100%"},
                                    children=[
                                        dcc.Graph(
                                            id="map-view", 
                                            figure=build_map(), 
                                            style={"height": "100%", "width": "100%"}, 
                                            config={'displayModeBar': False, 'responsive': True} # Fixes resize
                                        ),
                                        dmc.ActionIcon(
                                            DashIconify(icon="mdi:close", width=25),
                                            id="btn-reset-view", variant="filled", color="red", size="xl", radius="xl",
                                            style={"display": "none", "position": "absolute", "top": "20px", "right": "20px", "zIndex": 1000}
                                        )
                                    ]
                                ),
                                # Bottom Graphs (30%)
                                html.Div(
                                    style={"flex": "3", "backgroundColor": "#141517", "padding": "10px", "borderTop": BORDER_STYLE, "overflow": "hidden"},
                                    children=[
                                         dmc.SimpleGrid(cols=2, style={"height": "100%"}, spacing="md", children=[
                                            html.Div(style={"height": "100%", "display": "flex", "flexDirection": "column"}, children=[
                                                dmc.Text("PRICE FORECASTS", size="xs", weight=700, color="dimmed", mb="xs"),
                                                dmc.ScrollArea(style={"flex": 1}, children=[html.Div(id="price-cards-container")])
                                            ]),
                                            html.Div(style={"height": "100%", "display": "flex", "flexDirection": "column"}, children=[
                                                dmc.Text("DEMAND FORECASTS", size="xs", weight=700, color="dimmed", mb="xs"),
                                                dmc.ScrollArea(style={"flex": 1}, children=[html.Div(id="demand-cards-container")])
                                            ])
                                         ])
                                    ]
                                )
                            ]
                        ),

                        # C. RIGHT PANEL (Contextual)
                        html.Div(
                            style={"width": "25%", "height": "100%", "borderLeft": BORDER_STYLE, "backgroundColor": COLOR_CARD_BG, "padding": "20px"},
                            children=[html.Div(id="right-panel-content", style={"height": "100%"})]
                        )
                    ]
                )
            ]
        ),
        dcc.Store(id="view-state", data={"view": "GLOBAL", "country": None}),
        dcc.Interval(id='region-cycler', interval=4000, n_intervals=0),
    ]
)

# --- CALLBACKS ---

# 1. RENDER RIGHT PANEL
@app.callback(
    Output("right-panel-content", "children"),
    [Input("view-state", "data"),
     Input("region-cycler", "n_intervals")]
)
def render_right_panel(state, n):
    # Mode A: Country Selected -> Decision Engine
    if state["country"]:
        country = state["country"]
        data = get_decision_matrix(country)
        signal = data["signal"]
        color = "red" if signal == "BUY" else "gray"
        
        return dmc.Stack(style={"height": "100%"}, spacing="xl", children=[
            dmc.Text("DECISION ENGINE", size="sm", weight=700, color="dimmed"),
            html.Div([
                dmc.Text("TARGETING:", size="xs", color="dimmed"),
                dmc.Text(country, size="xl", weight=900, color="white"),
            ]),
            dmc.Paper(p="lg", radius="md", style={"backgroundColor": "#141517", "border": f"1px solid {COLOR_PRIMARY}"}, children=[
                dmc.Center(children=[
                    dmc.Stack(align="center", spacing=0, children=[
                        dmc.Text("AI RECOMMENDATION", size="xs", weight=700, color="dimmed"),
                        dmc.Text(signal, size="2.5rem", weight=900, color=color),
                    ])
                ])
            ]),
            dmc.SimpleGrid(cols=2, children=[
                dmc.Stack(spacing=0, children=[
                    dmc.Text("CONFIDENCE", size="xs", color="dimmed"),
                    dmc.Text(f"{data['confidence']}%", weight=700, color="white", size="lg")
                ]),
                dmc.Stack(spacing=0, children=[
                    dmc.Text("VOLATILITY", size="xs", color="dimmed"),
                    dmc.Text(data["volatility"], weight=700, color="white", size="lg")
                ]),
            ]),
            dmc.Alert(data["strategy"], title="Strategic Rationale", color="gray", variant="light"),
            dmc.Button(
                "EXECUTE ORDER", fullWidth=True, size="lg", color=color, 
                disabled=(signal != "BUY"), leftIcon=DashIconify(icon="mdi:lightning-bolt")
            )
        ])

    # MODE B: GLOBAL VIEW -> AUTONOMOUS SCANNER
    else:
        idx = n % len(REGIONS)
        region = REGIONS[idx] # Get Dynamic Region Name
        data = get_scanner_status()
        sub_list = ", ".join(REGIONS_CONFIG[region])
        
        return dmc.Stack(style={"height": "100%"}, spacing="xl", children=[
            dmc.Group(position="apart", children=[
                dmc.Text("AUTONOMOUS SCANNER", size="sm", weight=700, color="dimmed"),
                dmc.Badge("SCANNING", color="blue", variant="dot", className="blink")
            ]),
            # FIXED: Actually display the region name
            dmc.Text(f"SCANNING: {region}", size="1.5rem", weight=800, color="white"),
            dmc.Divider(variant="dotted", color="gray"),
            dmc.SimpleGrid(cols=2, children=[
                dmc.Stack(spacing=0, children=[
                    dmc.Text("DEMAND", size="xs", color="dimmed"),
                    dmc.Text(f"{data['demand']:,} T", weight=700, color="white", size="lg")
                ]),
                dmc.Stack(spacing=0, children=[
                    dmc.Text("CONFIDENCE", size="xs", color="dimmed"),
                    dmc.Text(f"{data['confidence']}%", weight=700, color="green", size="lg")
                ]),
            ]),
            dmc.Space(h="md"),
            dmc.Text("AI INFERENCE LOG", size="xs", weight=700, color="dimmed"),
            dmc.Code(
                f"> SECTOR: {region}\n> SUB-UNITS: {sub_list}\n> CHECKING LATENCY... OK.\n> SYNCING LME FEED...",
                block=True, style={"height": "150px", "backgroundColor": "#111", "color": "#0f0", "fontSize": "10px"}
            )
        ])

# 2. MAP LOGIC (ZOOM + HIGHLIGHT)
@app.callback(
    [Output("map-view", "figure"),
     Output("btn-reset-view", "style"),
     Output("view-state", "data"),
     Output("left-panel-title", "children")],
    [Input("map-view", "clickData"),
     Input("btn-reset-view", "n_clicks"),
     Input("region-cycler", "n_intervals")],
    [State("map-view", "figure"),
     State("view-state", "data")]
)
def update_map(click_data, reset_click, cycler_n, current_fig, view_state):
    ctx = callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "none"

    if trigger == "map-view" and click_data:
        pt = click_data["points"][0]
        country = pt["customdata"]
        iso_code = COUNTRY_MAP.get(country)
        # ZOOM IN (3.8)
        new_fig = build_map([iso_code] if iso_code else None, pt["lat"], pt["lon"], 3.8)
        return new_fig, {"display": "block", "position": "absolute", "top": "20px", "right": "20px", "zIndex": 1000}, {"view": country, "country": country}, country.upper()

    elif trigger == "btn-reset-view":
        # RESET VIEW (1.1)
        new_fig = build_map(None, 20, 10, 1.1)
        return new_fig, {"display": "none"}, {"view": "GLOBAL", "country": None}, "GLOBAL"

    elif trigger == "region-cycler" and not view_state["country"]:
        idx = cycler_n % len(REGIONS)
        region = REGIONS[idx]
        isos = [COUNTRY_MAP[c] for c in REGIONS_CONFIG[region] if c in COUNTRY_MAP]
        # PASSIVE HIGHLIGHT (NO ZOOM)
        new_fig = build_map(isos, 20, 10, 1.1)
        return new_fig, no_update, no_update, no_update

    return no_update, no_update, no_update, no_update

# 3. UPDATE LISTS
@app.callback(
    [Output("left-panel-content", "children"),
     Output("price-cards-container", "children"),
     Output("demand-cards-container", "children")],
    [Input("view-state", "data")]
)
def update_lists(state):
    context = state["view"]
    data = get_metrics(context) 
    left = [create_left_panel_card(m) for m in data]
    price = [create_bottom_card(m, True) for m in data]
    demand = [create_bottom_card(m, False) for m in data]
    return left, price, demand

if __name__ == '__main__':
    app.run(debug=True, port=8050)