import panel as pn
import param
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import random

# --- CONFIGURATION ---
pn.extension('plotly', template='fast', theme='dark') # Dark Mode Native

GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
COLOR_PRIMARY = "#C9302C"
COLOR_CARD_BG = "#1F2125"

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

# --- THE APP CLASS (Reactive State) ---
class SentinelApp(param.Parameterized):
    # State Variables
    selected_country = param.String(default="")
    scanning_idx = param.Integer(default=0)
    
    def __init__(self, **params):
        super().__init__(**params)
        # Background Loop for Scanner
        pn.state.add_periodic_callback(self.tick_scanner, period=4000)

    def tick_scanner(self):
        """Advances the scanner index if no country is selected"""
        if not self.selected_country:
            self.scanning_idx = (self.scanning_idx + 1) % len(REGIONS)

    # --- HELPERS ---
    def get_sparkline(self, base):
        vals = [base]
        for _ in range(20):
            vals.append(vals[-1] + np.random.normal(0, base * 0.02))
        df = pd.DataFrame({"x": range(len(vals)), "y": vals})
        fig = px.line(df, x="x", y="y")
        fig.update_traces(line_color="#339af0", line_width=2)
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                          xaxis_visible=False, yaxis_visible=False, showlegend=False, height=40)
        return fig

    # --- VIEW COMPONENTS ---

    @param.depends('selected_country', 'scanning_idx')
    def map_view(self):
        """Constructs the Map Plotly Pane"""
        fig = go.Figure()
        locations = [
            {'name': 'EGYPT', 'lat': 26.8, 'lon': 30.8}, {'name': 'SAUDI ARABIA', 'lat': 23.8, 'lon': 45.0},
            {'name': 'UAE', 'lat': 23.4, 'lon': 53.8}, {'name': 'GERMANY', 'lat': 51.1, 'lon': 10.4},
            {'name': 'CHINA', 'lat': 35.8, 'lon': 104.1}, {'name': 'USA', 'lat': 37.09, 'lon': -95.7},
            {'name': 'BRAZIL', 'lat': -14.2, 'lon': -51.9}
        ]

        # Determine Highlight
        iso = None
        zoom = 1.1
        center = {"lat": 20, "lon": 10}

        if self.selected_country:
            iso = [COUNTRY_MAP.get(self.selected_country)]
            zoom = 3.5
            # Simple centering logic
            loc = next((x for x in locations if x['name'] == self.selected_country), None)
            if loc: center = {"lat": loc['lat'], "lon": loc['lon']}
        else:
            # Passive Scanner Highlight
            region = REGIONS[self.scanning_idx]
            iso = [COUNTRY_MAP.get(c) for c in REGIONS_CONFIG.get(region, []) if c in COUNTRY_MAP]

        if iso and WORLD_GEOJSON:
            fig.add_trace(go.Choroplethmapbox(
                geojson=WORLD_GEOJSON, locations=iso, z=[1]*len(iso),
                featureidkey="id", colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(201, 48, 44, 0.4)']],
                marker_line_color=COLOR_PRIMARY, marker_line_width=2, showscale=False, hoverinfo='skip'
            ))

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
            clickmode='event+select', transition={'duration': 1000}, autosize=True
        )
        
        # Click Handler
        pane = pn.pane.Plotly(fig, config={'responsive': True}, sizing_mode='stretch_both')
        
        def handle_click(data):
            if data and 'points' in data:
                self.selected_country = data['points'][0]['customdata']

        pane.on_click(handle_click)
        return pane

    @param.depends('selected_country')
    def left_panel(self):
        """Global Metrics List"""
        cards = []
        mult = 0.6 if self.selected_country else 1.0
        
        for mat in MATERIALS:
            base = 8500 if "Copper" in mat else 1200
            price = f"${int(base + random.randint(-100, 100)):,}"
            demand = f"{int(50000 * mult):,} T"
            
            card = pn.Column(
                pn.Row(pn.pane.Markdown(f"**{mat}**", style={'color': '#888', 'font-size': '11px'}), 
                       pn.pane.Markdown(f"`{price}`", style={'color': 'white'})),
                pn.Row(pn.pane.Markdown("Allocated", style={'color': '#666', 'font-size': '10px'}), 
                       pn.pane.Markdown(f"**{demand}**", style={'color': 'white', 'font-size': '12px'})),
                styles={'background': '#25262B', 'border-left': f'3px solid {COLOR_PRIMARY}', 'padding': '10px', 'margin-bottom': '5px'}
            )
            cards.append(card)
        
        return pn.Column(
            pn.pane.Markdown("### GLOBAL INVENTORY"),
            *cards, sizing_mode='stretch_width'
        )

    @param.depends('selected_country', 'scanning_idx')
    def right_panel(self):
        """Switch between Scanner and Decision Engine"""
        if self.selected_country:
            # DECISION VIEW
            signal = "BUY"
            color = "red"
            return pn.Column(
                pn.pane.Markdown("**DECISION ENGINE**", style={'color': '#888'}),
                pn.pane.Markdown(f"# TARGET: {self.selected_country}", style={'color': 'white'}),
                pn.Column(
                    pn.pane.Markdown("RECOMMENDATION", style={'color': '#888', 'text-align': 'center'}),
                    pn.pane.Markdown(f"# {signal}", style={'color': color, 'text-align': 'center', 'font-weight': 'bold'}),
                    styles={'border': f'1px solid {COLOR_PRIMARY}', 'background': '#141517', 'padding': '20px'}
                ),
                pn.widgets.Button(name="EXECUTE ORDER", button_type='danger', height=50, sizing_mode='stretch_width'),
                pn.widgets.Button(name="❌ RESET VIEW", button_type='primary', height=40, sizing_mode='stretch_width', 
                                  on_click=lambda e: setattr(self, 'selected_country', ""))
            )
        else:
            # SCANNER VIEW
            region = REGIONS[self.scanning_idx]
            demand = f"{random.randint(50, 150)},000 T"
            log = f"> SECTOR: {region}\n> LATENCY: {random.randint(20,50)}ms"
            
            return pn.Column(
                pn.Row(pn.pane.Markdown("**AUTONOMOUS SCANNER**", style={'color': '#888'}),
                       pn.indicators.LoadingSpinner(value=True, width=20, height=20, color='primary')),
                pn.pane.Markdown(f"# REGION: {region}", style={'color': 'white'}),
                pn.Row(
                    pn.Column(pn.pane.Markdown("DEMAND"), pn.pane.Markdown(f"## {demand}")),
                    pn.Column(pn.pane.Markdown("CONFIDENCE"), pn.pane.Markdown(f"## {random.randint(90,99)}%", style={'color': '#28a745'}))
                ),
                pn.pane.Markdown("**INFERENCE LOG**"),
                pn.pane.Markdown(f"```bash\n{log}\n```", styles={'background': '#111', 'color': '#0f0'})
            )

# --- LAYOUT ---
sentinel = SentinelApp()

# Panel's FastListTemplate mimics a modern dashboard automatically
template = pn.template.FastListTemplate(
    title="SENTINEL | COMMAND",
    theme="dark",
    accent_base_color=COLOR_PRIMARY,
    header_background="#1A1B1E",
    sidebar=[sentinel.left_panel],
    main=[
        pn.Row(
            sentinel.map_view,
            sentinel.right_panel,
            sizing_mode='stretch_both' # Fills the screen
        ),
        # Bottom graphs would go here
    ]
).servable()