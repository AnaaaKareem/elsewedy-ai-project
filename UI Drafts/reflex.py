import reflex as rx
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import asyncio
import random

# --- CONFIGURATION & CONSTANTS ---
GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
COLOR_PRIMARY = "#C9302C"
COLOR_CARD_BG = "#1F2125"
COLOR_DARK_BG = "#141517"
BORDER_STYLE = "1px solid #333"

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

MATERIALS_LIST = [
    "Copper (LME)", "Aluminum", "XLPE Polymer", "PVC Compound", 
    "Mica Tape", "Steel Tape", "Lead Ingots", "Masterbatch"
]

# --- GLOBAL DATA ---
try:
    WORLD_GEOJSON = requests.get(GEOJSON_URL).json()
except:
    WORLD_GEOJSON = None

# --- STATE ---
class SentinelState(rx.State):
    """The App State."""
    selected_country: str = ""
    scanner_idx: int = 0
    scanning_region: str = "MENA"
    is_scanning: bool = True
    
    # Metrics
    metrics: list[dict] = []
    
    # Scanner Data
    scanner_demand: int = 0
    scanner_confidence: int = 0
    
    # Decision Data
    decision_signal: str = ""
    decision_conf: int = 0
    decision_vol: str = ""
    decision_strat: str = ""

    def on_load(self):
        """Initial data load and start background scanner."""
        self.refresh_metrics()
        return SentinelState.tick_scanner

    @rx.background
    async def tick_scanner(self):
        """Background task to cycle regions."""
        while True:
            async with self:
                if self.is_scanning:
                    self.scanner_idx = (self.scanner_idx + 1) % len(REGIONS)
                    self.scanning_region = REGIONS[self.scanner_idx]
                    self.scanner_demand = random.randint(10000, 150000)
                    self.scanner_confidence = random.randint(85, 99)
            await asyncio.sleep(4)

    def select_country(self, data: dict):
        """Handle map click."""
        if "points" in data and len(data["points"]) > 0:
            point = data["points"][0]
            # Plotly click data structure can vary, safeguarding extract
            if "customdata" in point:
                country = point["customdata"]
                self.selected_country = country
                self.is_scanning = False
                self.refresh_metrics(context=country)
                self.generate_decision(country)

    def reset_view(self):
        """Reset to Global Scanner."""
        self.selected_country = ""
        self.is_scanning = True
        self.refresh_metrics(context="GLOBAL")

    def refresh_metrics(self, context="GLOBAL"):
        """Regenerate mock metrics."""
        mult = 1.0 if context == "GLOBAL" else 0.6
        new_data = []
        for mat in MATERIALS_LIST:
            base = 8500 if "Copper" in mat else (2200 if "Alum" in mat else 1200)
            
            # Generate sparkline (simple list for Reflex)
            trend = [base]
            for _ in range(30):
                trend.append(trend[-1] + np.random.normal(0, base * 0.02))
                
            new_data.append({
                "name": mat,
                "price": int(base + random.randint(-100, 100)),
                "price_str": f"${int(base + random.randint(-100, 100)):,}",
                "demand": f"{int(50000 * mult):,} T",
                "trend": trend,
                "color": "#339af0"
            })
        self.metrics = new_data

    def generate_decision(self, country):
        """Generate fake AI decision."""
        self.decision_signal = "BUY" if random.random() > 0.4 else "HOLD"
        self.decision_conf = random.randint(87, 99)
        self.decision_vol = "HIGH" if random.random() > 0.7 else "STABLE"
        self.decision_strat = "Front-load inventory." if self.decision_signal == "BUY" else "Maintain safety stock."

    @rx.var
    def map_figure(self) -> go.Figure:
        """Computed var: Builds the Plotly Map based on state."""
        fig = go.Figure()
        
        locations = [
            {'name': 'EGYPT', 'lat': 26.8, 'lon': 30.8}, {'name': 'SAUDI ARABIA', 'lat': 23.8, 'lon': 45.0},
            {'name': 'UAE', 'lat': 23.4, 'lon': 53.8}, {'name': 'GERMANY', 'lat': 51.1, 'lon': 10.4},
            {'name': 'FRANCE', 'lat': 46.2, 'lon': 2.2}, {'name': 'NIGERIA', 'lat': 9.08, 'lon': 8.67},
            {'name': 'CHINA', 'lat': 35.8, 'lon': 104.1}, {'name': 'USA', 'lat': 37.09, 'lon': -95.7},
            {'name': 'BRAZIL', 'lat': -14.2, 'lon': -51.9}
        ]

        # 1. Highlight Layer
        iso_list = []
        if self.selected_country:
            iso_list = [COUNTRY_MAP.get(self.selected_country)]
            center = next((loc for loc in locations if loc["name"] == self.selected_country), None)
            zoom, clat, clon = (3.5, center['lat'], center['lon']) if center else (1.1, 20, 10)
        else:
            # Passive Region Highlight
            current_region_countries = REGIONS_CONFIG.get(self.scanning_region, [])
            iso_list = [COUNTRY_MAP[c] for c in current_region_countries if c in COUNTRY_MAP]
            zoom, clat, clon = (1.1, 20, 10)

        if WORLD_GEOJSON and iso_list:
             # Using a dummy df to create the chloropleth data
            fig.add_trace(go.Choroplethmapbox(
                geojson=WORLD_GEOJSON, locations=iso_list, z=[1]*len(iso_list),
                featureidkey="id", colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(201, 48, 44, 0.4)']],
                marker_line_color=COLOR_PRIMARY, marker_line_width=2, showscale=False, hoverinfo='skip'
            ))

        # 2. Markers
        fig.add_trace(go.Scattermapbox(
            lat=[loc['lat'] for loc in locations], lon=[loc['lon'] for loc in locations],
            mode='markers+text', text=[loc['name'] for loc in locations], textposition="top center",
            marker=go.scattermapbox.Marker(size=12, color=COLOR_PRIMARY, opacity=0.9),
            textfont=dict(color='white', size=10), hoverinfo='none',
            customdata=[loc['name'] for loc in locations] # Crucial for click event
        ))

        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            mapbox=dict(style="carto-darkmatter", center=dict(lat=clat, lon=clon), zoom=zoom),
            paper_bgcolor=COLOR_CARD_BG, plot_bgcolor=COLOR_CARD_BG, showlegend=False,
            transition={'duration': 1000, 'easing': 'cubic-in-out'},
            clickmode='event+select'
        )
        return fig


# --- COMPONENTS ---

def sparkline(data):
    """A small simple sparkline graph."""
    df = pd.DataFrame({"x": range(len(data)), "y": data})
    fig = px.line(df, x="x", y="y")
    fig.update_traces(line_color="#339af0", line_width=2)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=30)
    return rx.plotly(data=fig, height="40px", width="100%")

def metric_card(item: dict):
    return rx.box(
        rx.flex(
            rx.text(item["name"], font_size="10px", font_weight="bold", color="gray"),
            rx.badge(item["price_str"], variant="outline", color_scheme="gray"),
            justify="between"
        ),
        rx.flex(
            rx.text("Allocated", font_size="10px", color="gray"),
            rx.text(item["demand"], font_size="12px", font_weight="bold", color="white"),
            justify="between",
            margin_top="4px"
        ),
        padding="8px",
        border_left=f"3px solid {COLOR_PRIMARY}",
        bg="#25262B",
        margin_bottom="8px",
        border_radius="4px"
    )

def bottom_card(item: dict):
    return rx.box(
        rx.text(item["name"], font_size="10px", font_weight="bold", color="gray"),
        rx.flex(
            rx.text(item["price_str"], font_size="18px", font_weight="bold", color="white"),
            rx.badge("30D", variant="solid", color_scheme="gray", size="1"),
            justify="between",
            align="center",
            margin_bottom="4px"
        ),
        sparkline(item["trend"]),
        bg=COLOR_CARD_BG,
        padding="10px",
        border=BORDER_STYLE,
        border_radius="8px"
    )

def right_panel():
    return rx.box(
        rx.cond(
            SentinelState.selected_country != "",
            # DECISION VIEW
            rx.vstack(
                rx.text("DECISION ENGINE", font_size="12px", font_weight="bold", color="gray"),
                rx.box(
                    rx.text("TARGETING:", font_size="10px", color="gray"),
                    rx.heading(SentinelState.selected_country, size="8", color="white"),
                ),
                rx.center(
                    rx.vstack(
                        rx.text("AI RECOMMENDATION", font_size="10px", font_weight="bold", color="gray"),
                        rx.heading(SentinelState.decision_signal, size="9", color_scheme="red"),
                        align="center",
                        padding="20px",
                        border=f"1px solid {COLOR_PRIMARY}",
                        border_radius="10px",
                        bg=COLOR_DARK_BG,
                        width="100%"
                    )
                ),
                rx.grid(
                    rx.vstack(rx.text("CONFIDENCE", font_size="10px", color="gray"), rx.text(f"{SentinelState.decision_conf}%", font_size="20px", weight="bold")),
                    rx.vstack(rx.text("VOLATILITY", font_size="10px", color="gray"), rx.text(SentinelState.decision_vol, font_size="20px", weight="bold")),
                    columns="2",
                    width="100%"
                ),
                rx.callout(SentinelState.decision_strat, icon="info_circled", color_scheme="gray", variant="surface"),
                rx.button("EXECUTE ORDER", width="100%", color_scheme="red" if SentinelState.decision_signal == "BUY" else "gray", disabled=SentinelState.decision_signal != "BUY"),
                spacing="5",
                height="100%"
            ),
            # SCANNER VIEW
            rx.vstack(
                rx.flex(
                    rx.text("AUTONOMOUS SCANNER", font_size="12px", font_weight="bold", color="gray"),
                    rx.badge("SCANNING", variant="soft", color_scheme="blue"),
                    justify="between", width="100%"
                ),
                rx.heading(f"SCANNING: {SentinelState.scanning_region}", size="6", color="white"),
                rx.divider(),
                rx.grid(
                    rx.vstack(rx.text("DEMAND", font_size="10px", color="gray"), rx.text(f"{SentinelState.scanner_demand:,} T", font_size="20px", weight="bold")),
                    rx.vstack(rx.text("CONFIDENCE", font_size="10px", color="gray"), rx.text(f"{SentinelState.scanner_confidence}%", font_size="20px", weight="bold", color="green")),
                    columns="2", width="100%"
                ),
                rx.box(
                    rx.text("AI INFERENCE LOG", font_size="10px", font_weight="bold", color="gray"),
                    rx.code_block(f"> SECTOR: {SentinelState.scanning_region}\n> LATENCY: OK", language="bash", theme="a11y-dark"),
                    width="100%"
                ),
                spacing="5",
                height="100%"
            )
        ),
        padding="20px",
        height="100%",
        border_left=BORDER_STYLE,
        bg=COLOR_CARD_BG
    )

def index():
    return rx.flex(
        # HEADER
        rx.flex(
            rx.hstack(
                rx.icon("shield-check", color=COLOR_PRIMARY, size=30),
                rx.heading("SENTINEL | COMMAND", size="4", color="white"),
                align="center"
            ),
            rx.badge("SYSTEM OPTIMAL", color_scheme="green", variant="solid"),
            justify="between",
            padding="15px",
            border_bottom=BORDER_STYLE,
            bg="#1A1B1E",
            width="100%",
            height="60px"
        ),
        
        # MAIN BODY
        rx.flex(
            # LEFT PANEL
            rx.box(
                rx.vstack(
                    rx.flex(
                        rx.text("GLOBAL", font_weight="bold", color="white"),
                        rx.icon("database", color=COLOR_PRIMARY),
                        justify="between", width="100%"
                    ),
                    rx.divider(),
                    rx.scroll_area(
                        rx.vstack(
                            rx.foreach(SentinelState.metrics, metric_card),
                            width="100%"
                        ),
                        type="always", scrollbars="vertical", style={"height": "100%"}
                    ),
                    height="100%",
                    padding="10px"
                ),
                width="20%", height="100%", bg=COLOR_CARD_BG, border_right=BORDER_STYLE
            ),
            
            # CENTER PANEL
            rx.flex(
                # MAP
                rx.box(
                    rx.plotly(
                        data=SentinelState.map_figure,
                        on_click=SentinelState.select_country,
                        style={"height": "100%", "width": "100%"}
                    ),
                    rx.cond(
                        SentinelState.selected_country != "",
                        rx.icon_button("x", on_click=SentinelState.reset_view, variant="solid", color_scheme="red", position="absolute", top="20px", right="20px", z_index="999")
                    ),
                    flex="7", position="relative", width="100%"
                ),
                # BOTTOM GRAPHS
                rx.box(
                    rx.grid(
                        rx.vstack(
                            rx.text("PRICE FORECASTS", font_size="10px", font_weight="bold", color="gray"),
                            rx.scroll_area(
                                rx.grid(
                                    rx.foreach(SentinelState.metrics, bottom_card),
                                    columns="2", spacing="2", width="100%"
                                ),
                                style={"height": "100%"}
                            ),
                            height="100%"
                        ),
                        rx.vstack(
                            rx.text("DEMAND FORECASTS", font_size="10px", font_weight="bold", color="gray"),
                            rx.scroll_area(
                                rx.grid(
                                    rx.foreach(SentinelState.metrics, bottom_card),
                                    columns="2", spacing="2", width="100%"
                                ),
                                style={"height": "100%"}
                            ),
                            height="100%"
                        ),
                        columns="2", spacing="4", height="100%"
                    ),
                    flex="3", bg=COLOR_DARK_BG, border_top=BORDER_STYLE, padding="10px"
                ),
                flex="1", direction="column", height="100%"
            ),
            
            # RIGHT PANEL
            rx.box(
                right_panel(),
                width="25%", height="100%"
            ),
            
            width="100%", flex="1", overflow="hidden"
        ),
        
        direction="column",
        height="100vh",
        bg=COLOR_DARK_BG,
        width="100%"
    )

app = rx.App(theme=rx.theme(appearance="dark"))
app.add_page(index, on_load=SentinelState.on_load)