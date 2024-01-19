import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
from dash import Dash, dcc, html

from migrate_data import APP_DATA_DIR

thresholds = pd.read_parquet(APP_DATA_DIR / "all_adm0_thresholds.parquet")
tracks = pd.read_parquet(APP_DATA_DIR / "ibtracs_with_wmo_wind.parquet")
adm0s = gpd.read_file(APP_DATA_DIR / "gaul0_asap_v04" / "gaul0_asap.shp")
adm0s = adm0s.sort_values("name0")

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Tropical Cyclones Return Period"
app._favicon = "assets/favicon.ico"
server = app.server

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            html.A(
                html.Img(src="assets/centre_banner_greenbg.png", height=40),
                href="https://centre.humdata.org/anticipatory-action/",
            ),
            className="ml-2",
        ),
    ],
    style={"height": "60px"},
    brand="Tropical Cyclones Return Period Analysis",
    fixed="top",
    color="primary",
    dark=True,
)

intro_text = """
When determining the return period of tropical cyclones for a certain country,
an important factor is the maximum sustained wind speed of the cyclone while
it is within a certain distance of the country. This app allows you to pick
combinations of maximum sustained wind speed and distance to determine which
cyclones in the past would have met these conditions, and therefore the return
period.
"""

adm0_input = dbc.InputGroup(
    [
        dbc.InputGroupText("Country"),
        dbc.Select(
            id="country-input",
            value=116,
            options=[
                {
                    "label": row["name0"],
                    "value": row["asap0_id"],
                }
                for _, row in adm0s.iterrows()
            ],
        ),
    ]
)

speed_input = html.Div(
    [
        html.Label("Maximum sustained wind speed (knots)"),
        dcc.Slider(
            id="speed-input",
            min=0,
            max=185,
            step=5,
            value=100,
            marks={i: f"{i}" for i in range(0, 186, 50)},
            tooltip={"placement": "bottom", "always_visible": True},
        ),
    ]
)

distance_input = html.Div(
    [
        html.Label("Distance from country (km)"),
        dcc.Slider(
            id="distance-input",
            min=0,
            max=500,
            step=10,
            value=250,
            marks={i: f"{i}" for i in range(0, 501, 100)},
            tooltip={"placement": "bottom", "always_visible": True},
        ),
    ]
)


app.layout = html.Div(
    children=[
        navbar,
        dbc.Container(
            children=[
                dbc.Row([dbc.Col([html.P(intro_text)])]),
                dbc.Row(
                    children=[
                        dbc.Col(adm0_input),
                        dbc.Col(speed_input),
                        dbc.Col(distance_input),
                    ]
                ),
            ],
            style={"marginTop": "70px"},
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
