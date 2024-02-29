import json

import dash_bootstrap_components as dbc
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

from constants import CHD_GREEN
from migrate_data import APP_DATA_DIR
from utils import calc_plotly_zoom, print_memory_usage

IMPACT_PLOT_VARS = [
    "Total Damage, Adjusted ('000 US$)",
    "Total Deaths",
    "Total Affected",
]
# Haiti
DEFAULT_ASAP0_ID = 68
DEFAULT_START_YEAR = 1980
DEFAULT_IMPACT_PLOT_VAR = "Total Affected"

print_memory_usage()
print("Loading data...")
print("thresholds")
thresholds = pd.read_parquet(APP_DATA_DIR / "all_adm0_thresholds.parquet")
print_memory_usage()
print("tracks")
tracks = pd.read_parquet(APP_DATA_DIR / "ibtracs_with_wmo_wind.parquet")
print_memory_usage()
print("adm0s")
adm0s = gpd.read_file(APP_DATA_DIR / "gaul0_asap_v04" / "gaul0_asap.shp")
print_memory_usage()
adm0s = adm0s.sort_values("name0")
print("emdat")
damage = pd.read_csv(
    APP_DATA_DIR / "emdat-tropicalcyclone-2000-2022-processed-sids.csv"
)

print("Processing data...")
print("cyclones")
cyclones = tracks.groupby("sid").first()
cyclones["year"] = cyclones["time"].dt.year
cyclones["name"] = cyclones["name"].str.title()
cyclones["nameyear"] = cyclones.apply(
    lambda row: f'{row["name"].capitalize()} {row["year"]}', axis=1
)
cyclones = cyclones.reset_index()
MAX_YEAR = cyclones["year"].max()

print("emdat")
damage["sid"] = damage["sid"].fillna("")
damage = damage.merge(cyclones[["sid", "nameyear", "year"]], on="sid", how="left")

print_memory_usage()
print("thresholds")
thresholds = thresholds.merge(cyclones[["sid", "year", "name"]], on="sid")
print("thresholds dtypes:")
print(thresholds.dtypes)

adm0s = adm0s[adm0s["asap0_id"].isin(thresholds["asap0_id"].unique())]

print_memory_usage()
print("Setting up app...")

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
    style={"height": "60px", "margin": "0px"},
    brand="Tropical Cyclones Return Period Analysis",
    fixed="top",
    color="primary",
    dark=True,
)

alerts = [
    dbc.Alert(
        [
            "This is an internal tool under development. "
            "For any enquires please contact the OCHA Centre for Humanitarian "
            "Data via Tristan Downing at ",
            html.A("tristan.downing@un.org", href="mailto:tristan.downing@un.org"),
            ".",
        ],
        color="danger",
    ),
    dbc.Alert(
        [
            "Known issue: for countries near the antimeridian (180° W or E), "
            "certain cyclones may be erroneously excluded, resulting in a "
            "less frequent return period."
        ],
        color="warning",
        dismissable=True,
    ),
]

intro_text = """
When determining the return period of tropical cyclones for a certain country,
an important factor is the maximum sustained wind speed of the cyclone while
it is within a certain distance of the country. This app allows you to pick
combinations of maximum sustained wind speed and distance to determine which
cyclones in the past would have met these conditions, and therefore the return
period.
"""

data_sources = html.Div(
    [
        html.H6("Data sources"),
        html.P(
            [
                "Cyclone track data is from the ",
                html.A(
                    "IBTrACS",
                    href="https://www.ncei.noaa.gov/products/international-best-track-archive",
                    target="_blank",
                ),
                " dataset. Administrative boundaries are from the ",
                html.A(
                    "GAUL",
                    href="https://data.apps.fao.org/map/catalog/static/search?keyword=HiH_boundaries",
                    target="_blank",
                ),
                " dataset. Impact data is from the ",
                html.A(
                    "EM-DAT database",
                    href="https://public.emdat.be/data",
                    target="_blank",
                ),
                ".",
            ],
        ),
    ],
    style={"color": "grey", "font-size": "0.8rem"},
)

methodology = html.Div(
    [
        html.H6("Methodology"),
        html.P(
            [
                "Distances are calculated using the ",
                html.I("EPSG:3857"),
                " projection. Distances are calculated only from the points "
                "reported in IBTrACS, not the interpolated path. This can "
                "result in overestimating the distance, particularly for "
                "small countries, and when the cyclone is relatively close.",
            ],
        ),
        html.P(
            [
                "The maximum sustained wind speed used for triggering "
                "and shown in the plot is from the official WMO agency for "
                "the basin in which the cyclone occurred. Note that "
                "different agencies use different wind speed averaging "
                "periods. For more information, and conversion from wind "
                "speed to Category, see ",
                html.A(
                    "here",
                    href="https://en.wikipedia.org/wiki/Tropical_cyclone_scales",
                    target="_blank",
                ),
                ".",
            ]
        ),
        html.P(
            [
                "Cyclone track data only goes up to 2022, inclusive. More "
                "recent tracks will be added once the WMO endorses the best "
                "track data and it is updated in IBTrACS."
            ]
        ),
    ],
    style={"color": "grey", "font-size": "0.8rem"},
)

code_references = html.Div(
    [
        html.H6("Code"),
        html.P(
            [
                "The code used to calculate the distances is available on GitHub ",
                html.A(
                    "here",
                    href="https://github.com/OCHA-DAP/ds-glb-tropicalcyclones",
                    target="_blank",
                ),
                ". The code used to calculate the return period and run this app is "
                "available on GitHub ",
                html.A(
                    "here",
                    href="https://github.com/OCHA-DAP/ds-glb-tropicalcyclones-app",
                    target="_blank",
                ),
                ".",
            ],
        ),
    ],
    style={"color": "grey", "font-size": "0.8rem"},
)

adm0_input = dbc.InputGroup(
    [
        dbc.InputGroupText("Country"),
        dbc.Select(
            id="adm0-input",
            value=DEFAULT_ASAP0_ID,
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
            min=30,
            max=185,
            step=5,
            value=100,
            marks={i: f"{i}" for i in range(30, 186, 50)},
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
            max=400,
            step=10,
            value=250,
            marks={i: f"{i}" for i in range(0, 401, 100)},
            tooltip={"placement": "bottom", "always_visible": True},
        ),
    ]
)

year_input = dbc.InputGroup(
    [
        dbc.InputGroupText("Since year"),
        dbc.Select(
            id="year-input",
            value=DEFAULT_START_YEAR,
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
        dcc.Loading(html.H1(id="return-period")),
        html.Label(id="return-period-description"),
    ]
)

# trigger_cyclones_display = html.Div(
#     [
#         html.H3("Triggered cyclones:"),
#         dash_table.DataTable(
#             id="triggered-table",
#             columns=[{"name": x.capitalize(), "id": x} for x in ["name", "year"]],
#             style_cell={"textAlign": "left"},
#             style_as_list_view=True,
#         ),
#     ]
# )

cyclone_tracks_display = html.Div(
    [
        dcc.Loading(
            dcc.Graph(
                id="cyclone-tracks-graph",
                style={"height": "700px"},
                config={"displayModeBar": False},
            ),
            parent_className="loading_wrapper",
        )
    ],
)

impact_data_text = html.Div(
    [
        html.H3("Impact data"),
        html.P(
            "The plot to the right indicates the historical impact of "
            "cyclones on the country. This can be used to determine how "
            "effective the chosen threshold is at capturing high-impact "
            "cyclones. Recall that the trigger in this app is based only "
            "on wind speed and distance, so does not consider other "
            "potentially important factors that can contribute to the "
            "cyclone's impact. Cyclones without impact data are not shown."
        ),
    ]
)

impact_data_disclaimer = html.Div(
    [
        html.P(
            [
                "Data is from the ",
                html.A(
                    "EM-DAT database",
                    href="https://public.emdat.be/data",
                    target="_blank",
                ),
                ", which indicates that ",
                html.I('"Pre-2000 data is particularly subject to reporting biases."'),
                ", hence its exclusion from this analysis.",
            ]
        )
    ],
    style={"color": "grey", "font-size": "0.8rem"},
    className="mt-3",
)

impact_data_var_input = dbc.InputGroup(
    [
        dbc.InputGroupText("Impact metric"),
        dbc.Select(
            id="impact-data-var-input",
            value=DEFAULT_IMPACT_PLOT_VAR,
            options=[
                {
                    "label": x,
                    "value": x,
                }
                for x in IMPACT_PLOT_VARS
            ],
        ),
    ]
)

impact_data_plot = dcc.Loading(
    dcc.Graph(
        id="impact-data-plot",
        style={"height": "700px"},
        config={"displayModeBar": False},
    ),
    parent_className="loading_wrapper",
)

app.layout = html.Div(
    children=[
        navbar,
        dbc.Container(
            children=[
                dbc.Row([dbc.Col(alerts)], className="mt-4"),
                dbc.Row([dbc.Col([html.P(intro_text)])]),
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
                                # dbc.Row(
                                #     dbc.Col(trigger_cyclones_display), className="mt-4",
                                # ),
                            ],
                            width=2,
                        ),
                        dbc.Col(
                            [
                                dbc.Row(cyclone_tracks_display),
                            ],
                            width=10,
                        ),
                    ],
                    className="my-4",
                ),
                dbc.Row(
                    children=[
                        dbc.Col(
                            [
                                impact_data_text,
                                impact_data_var_input,
                                impact_data_disclaimer,
                            ],
                            width=4,
                        ),
                        dbc.Col(impact_data_plot, width=8),
                    ],
                    className="mt-4",
                ),
                dbc.Row(
                    [dbc.Col([data_sources, methodology, code_references])],
                    className="mt-4",
                ),
            ],
            style={"marginTop": "80px"},
        ),
        dcc.Store(id="adm0-cyclones"),
        dcc.Store(id="triggered-cyclone-tracks"),
    ]
)

print_memory_usage()


@app.callback(
    Output("adm0-cyclones", "data"),
    Output("triggered-cyclone-tracks", "data"),
    Input("adm0-input", "value"),
    Input("speed-input", "value"),
    Input("distance-input", "value"),
    Input("year-input", "value"),
)
def update_selected_cyclones(adm0, speed, distance, year):
    print("Updating selected cyclones...")
    country_cyclones = thresholds[
        (thresholds["asap0_id"] == int(adm0)) & (thresholds["year"] >= int(year))
    ].copy()
    country_cyclones["triggered"] = (country_cyclones["s_thresh"] == speed) & (
        country_cyclones["d_thresh"] == distance
    )
    country_cyclones = country_cyclones.sort_values("year", ascending=False)
    triggered_tracks = tracks[
        tracks["sid"].isin(country_cyclones[country_cyclones["triggered"]]["sid"])
    ]
    print_memory_usage()
    return country_cyclones.to_dict("records"), triggered_tracks.to_dict("records")


@app.callback(
    Output("return-period", "children"),
    Output("return-period-description", "children"),
    # Output("triggered-table", "data"),
    Input("adm0-cyclones", "data"),
)
def update_return_period(data):
    print("Updating return period...")
    df_country = pd.DataFrame(data)
    if df_country.empty:
        return "No cyclones triggered", "No cyclones in range"  # , []
    df_triggered = df_country[df_country["triggered"]]
    min_year_country = df_country["year"].min()
    n_years = MAX_YEAR - min_year_country + 1

    # df_dict = df_triggered.to_dict("records")
    description = (
        f"based on {n_years} years with cyclone data, since {min_year_country}"
    )
    print_memory_usage()
    if df_triggered.empty:
        return "No cyclones triggered", description  # , df_dict
    else:
        rp = n_years / len(df_triggered)
        return f"{rp:.1f} years", description  # , df_dict


@app.callback(
    Output("cyclone-tracks-graph", "figure"),
    Input("triggered-cyclone-tracks", "data"),
    Input("adm0-input", "value"),
)
def update_cyclone_tracks(data, adm0):
    print("Updating cyclone tracks...")
    triggered_tracks = pd.DataFrame(data)
    codab = adm0s[adm0s["asap0_id"] == int(adm0)]
    lon_min, lat_min, lon_max, lat_max = codab.geometry.total_bounds
    min_zoom = calc_plotly_zoom(lon_min, lat_min, lon_max, lat_max)
    zoom = min(min_zoom, 5)
    fig = go.Figure()
    colorscale = [[0, CHD_GREEN], [1, CHD_GREEN]]
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=json.loads(codab.geometry.to_json()),
            locations=codab.index,
            z=[1],
            hoverinfo="text",
            text=codab["name0"],
            showscale=False,
            colorscale=colorscale,
            marker_opacity=0.5,
        )
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        autosize=True,
        hovermode="closest",
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox_zoom=zoom,
        mapbox_center_lat=(lat_max + lat_min) / 2,
        mapbox_center_lon=(lon_max + lon_min) / 2,
    )
    if triggered_tracks.empty:
        return fig
    triggered_tracks["time"] = pd.to_datetime(triggered_tracks["time"])
    triggered_tracks = triggered_tracks.sort_values("time", ascending=False)
    for sid in triggered_tracks["sid"].unique():
        track = triggered_tracks[triggered_tracks["sid"] == sid]
        year = track["time"].dt.year.iloc[0]
        fig.add_trace(
            go.Scattermapbox(
                lat=track["lat"],
                lon=track["lon"],
                mode="lines+markers",
                name=f"{track['name'].iloc[0].capitalize()} {year}",
                hoverinfo="skip",
                customdata=track[["wmo_wind", "time"]],
                hovertemplate=(
                    "Wind speed: %{customdata[0]} knots<br>"
                    "Date: %{customdata[1]}<br>"
                ),
            )
        )
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(255,255,255,0.5)",
            title="Triggered Cyclones:",
        ),
    )
    print_memory_usage()
    return fig


@app.callback(
    Output("impact-data-plot", "figure"),
    Input("adm0-cyclones", "data"),
    Input("impact-data-var-input", "value"),
    State("adm0-input", "value"),
    State("year-input", "value"),
    State("distance-input", "value"),
    State("speed-input", "value"),
)
def update_impact_plot(data, plot_col, adm0, year, distance, speed):
    print("Updating impact plot...")
    min_year = max(int(year), 2000)
    df_country = pd.DataFrame(data)
    country_name = adm0s[adm0s["asap0_id"] == int(adm0)]["name0"].iloc[0]
    fig = go.Figure()
    fig.update_layout(
        title=(
            f"Cyclone Impact: '{plot_col}'<br>"
            f"<sup>{country_name}, impact data since {min_year}; "
            f"Triggering for <i>wind speed ≥ {speed} knots</i> while "
            f"<i>distance ≤ {distance} km</i></sup>"
        ),
        yaxis_title=plot_col,
        barmode="group",
        height=600,
        template="simple_white",
        legend=dict(
            x=0,
            y=1,
            xanchor="left",
            yanchor="top",
            itemclick=False,
            itemdoubleclick=False,
        ),
        margin=dict(t=60),
        hovermode="x",
    )
    damage_f = damage[(damage["asap0_id"] == int(adm0)) & (damage["year"] >= min_year)]
    if damage_f.empty:
        fig.add_annotation(
            text=f"<i>No impact data available for {country_name} since {min_year}</i>",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color="grey"),
            xref="paper",
            yref="paper",
            xanchor="center",
            yanchor="middle",
        )
        return fig
    triggered = df_country.groupby("sid")["triggered"].any().reset_index()
    damage_f = damage_f.merge(triggered, on="sid", how="left")

    df_plot = damage_f.copy()
    df_plot = df_plot[df_plot[plot_col] > 0].sort_values(plot_col)
    df_plot["color"] = df_plot["triggered"].map(
        {True: "red", False: "blue", np.nan: "grey"}
    )

    fig.add_trace(
        go.Bar(
            x=df_plot["nameyear"],
            y=df_plot[plot_col],
            hovertemplate="%{y:,.0f}",
            marker_color=df_plot["color"],
            showlegend=False,
            name="",
        )
    )

    for legend_name, color in zip(
        ["Triggered", "Not Triggered", "No Track Data"], ["red", "blue", "grey"]
    ):
        fig.add_trace(go.Bar(x=[None], y=[None], marker_color=color, name=legend_name))

    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=df_plot["nameyear"].values,
            title="Cyclone",
        ),
    )
    return fig


if __name__ == "__main__":
    app.run(debug=True)
