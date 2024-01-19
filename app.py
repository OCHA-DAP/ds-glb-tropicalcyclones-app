from dash import Dash, html

app = Dash(__name__)
app.title = "Fiji Tropical Cyclones - Historical Tracks and Forecasts"
app._favicon = "assets/favicon.ico"
server = app.server

app.layout = html.Div("hi")

if __name__ == "__main__":
    app.run(debug=True)
