import vizro
import vizro.models as vm
import vizro.plotly.express as px
from vizro import Vizro
import pandas as pd
import plotly.graph_objects as go

# --- MOCK DATA PREP ---
# Vizro loves DataFrames. We flatten our data into a clean DF.
df = pd.DataFrame({
    "Country": ["EGYPT", "SAUDI ARABIA", "UAE", "GERMANY", "CHINA", "USA", "BRAZIL"],
    "Region": ["MENA", "MENA", "MENA", "EU", "APAC", "AMERICAS", "AMERICAS"],
    "Copper Price": [8500, 8450, 8520, 8600, 8400, 8550, 8480],
    "Demand (T)": [50000, 45000, 30000, 60000, 120000, 90000, 40000],
    "Risk Score": [12, 15, 10, 5, 20, 8, 18],
    "lat": [26.8, 23.8, 23.4, 51.1, 35.8, 37.09, -14.2],
    "lon": [30.8, 45.0, 53.8, 10.4, 104.1, -95.7, -51.9]
})

# --- CUSTOM CHART FUNCTION (The Map) ---
def create_map(data_frame=None):
    fig = go.Figure()
    
    # Simple Scatter Mapbox
    fig.add_trace(go.Scattermapbox(
        lat=data_frame['lat'], lon=data_frame['lon'],
        mode='markers+text', text=data_frame['Country'], textposition="top center",
        marker=go.scattermapbox.Marker(size=15, color='#C9302C', opacity=0.9),
        textfont=dict(color='white', size=12),
        customdata=data_frame[['Country', 'Demand (T)', 'Risk Score']]
    ))

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(style="carto-darkmatter", center=dict(lat=20, lon=10), zoom=1.1),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    return fig

# --- VIZRO PAGE DEFINITION ---
page = vm.Page(
    title="Sentinel Command",
    layout=vm.Layout(grid=[[0, 1]]), # Split: Map (Left), Analytics (Right)
    components=[
        # COMPONENT 1: The Map
        vm.Graph(
            id="map_view",
            figure=create_map(df)
        ),
        
        # COMPONENT 2: The "Right Panel" (Vizro makes this a Dashboard Card)
        vm.Table(
            id="metrics_table",
            title="Global Inventory Status",
            figure=vm.Table(
                data_frame=df[['Country', 'Region', 'Demand (T)', 'Copper Price']],
            )
        ),
    ],
    controls=[
        # Vizro handles filtering automatically!
        vm.Filter(column="Region", selector=vm.Dropdown(multi=True))
    ]
)

dashboard = vm.Dashboard(pages=[page], theme="vizro_dark")

if __name__ == "__main__":
    Vizro().build(dashboard).run(port=8050)