import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dash_table, dcc, html

from migrate_data import APP_DATA_DIR

thresholds = pd.read_parquet(APP_DATA_DIR / "all_adm0_thresholds.parquet")
tracks = pd.read_parquet(APP_DATA_DIR / "ibtracs_with_wmo_wind.parquet")
adm0s = gpd.read_file(APP_DATA_DIR / "gaul0_asap_v04" / "gaul0_asap.shp")
adm0s = adm0s.sort_values("name0")

cyclones = tracks.groupby("sid").first()
cyclones["year"] = cyclones["time"].dt.year
cyclones["name"] = cyclones["name"].str.title()
cyclones = cyclones.reset_index()

thresholds = thresholds.merge(cyclones[["sid", "year", "name"]], on="sid")

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
            id="adm0-input",
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

year_input = dbc.InputGroup(
    [
        dbc.InputGroupText("Since year"),
        dbc.Select(
            id="year-input",
            value=1970,
            options=[
                {
                    "label": x,
                    "value": x,
                }
                for x in range(1851, 2023)
            ],
        ),
    ]
)

return_period_display = html.Div(
    [
        html.H3("Return period:"),
        html.H1(id="return-period"),
        html.Label(id="return-period-description"),
    ]
)

trigger_cyclones_display = html.Div(
    [
        html.H3("Triggered cyclones:"),
        dash_table.DataTable(
            id="triggered-table",
            columns=[{"name": x.capitalize(), "id": x} for x in ["name", "year"]],
            style_cell={"textAlign": "left"},
            style_as_list_view=True,
        ),
    ]
)

cyclone_tracks_display = html.Div(
    [
        dcc.Graph(id="cyclone-tracks-graph", style={"height": "600px"}),
    ]
)

app.layout = html.Div(
    children=[
        navbar,
        dbc.Container(
            children=[
                dbc.Row([dbc.Col([html.P(intro_text)])], className="mt-4"),
                dbc.Row(
                    children=[
                        dbc.Col(adm0_input, width=2),
                        dbc.Col(speed_input, width=4),
                        dbc.Col(distance_input, width=4),
                        dbc.Col(year_input, width=2),
                    ],
                    className="mt-4",
                ),
                dbc.Row(
                    children=[
                        dbc.Col(
                            [
                                dbc.Row(dbc.Col(return_period_display)),
                                dbc.Row(
                                    dbc.Col(trigger_cyclones_display), className="mt-4"
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Row(cyclone_tracks_display),
                            ],
                            width=8,
                        ),
                    ],
                    className="mt-4",
                ),
            ],
            style={"marginTop": "70px"},
        ),
        dcc.Store(id="adm0-cyclones"),
    ]
)


@app.callback(
    Output("adm0-cyclones", "data"),
    Input("adm0-input", "value"),
    Input("speed-input", "value"),
    Input("distance-input", "value"),
    Input("year-input", "value"),
)
def update_selected_cyclones(adm0, speed, distance, year):
    df_country = thresholds[
        (thresholds["asap0_id"] == int(adm0)) & (thresholds["year"] >= int(year))
    ].copy()
    df_country["triggered"] = (df_country["s_thresh"] == speed) & (
        df_country["d_thresh"] == distance
    )
    return df_country.to_dict("records")


@app.callback(
    Output("return-period", "children"),
    Output("return-period-description", "children"),
    Output("triggered-table", "data"),
    Input("adm0-cyclones", "data"),
)
def update_return_period(data):
    df_country = pd.DataFrame(data)
    if df_country.empty:
        return "No cyclones triggered", "No cyclones in range", []
    df_triggered = df_country[df_country["triggered"]]
    n_years = df_country["year"].nunique()
    min_year = df_country["year"].min()
    df_dict = df_triggered.to_dict("records")
    description = f"out of {n_years} years, since {min_year}"
    if df_triggered.empty:
        return "No cyclones triggered", description, df_dict
    else:
        rp = n_years / len(df_triggered)
        return f"{rp:.1f} years", description, df_dict


@app.callback(
    Output("cyclone-tracks-graph", "figure"),
    # Input("adm0-cyclones", "data"),
    Input("adm0-input", "value"),
)
def update_cyclone_tracks(adm0):
    # df_country = pd.DataFrame(data)
    codab = adm0s[adm0s["asap0_id"] == int(adm0)]
    fig = px.choropleth_mapbox(
        codab,
        geojson=codab.geometry,
        locations=codab.index,
        mapbox_style="open-street-map",
        zoom=3,
        center={"lat": 0, "lon": 0},
        opacity=0.5,
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        autosize=True,
        hovermode="closest",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)
