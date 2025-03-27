import sys
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc
import base64

# Charger l'image de fond
image_path = "background.jpg"  # remplace par le nom exact si besoin
encoded_image = base64.b64encode(open(image_path, 'rb').read()).decode()

# Charger les données du CSV
def load_data():
    try:
        df = pd.read_csv("eth_prices.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame(columns=["timestamp", "price"])

# Initialisation de l'application Dash
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap"
])

app.layout = dbc.Container([
    html.Div([
        html.H1("Suivi du prix de l'ETH", style={
            "textAlign": "center",
            "color": "white",
            "marginTop": "20px",
            "fontFamily": "Montserrat"
        }),
        html.Hr(style={"borderColor": "white", "marginBottom": "40px"})
    ]),

    dbc.Row([
        dbc.Col([
            html.Label("Choisir une plage de dates", style={"color": "white"}),
            dcc.DatePickerRange(
                id='date-picker',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                style={"backgroundColor": "white", "borderRadius": "4px"}
            ),
        ], width=6),

        dbc.Col([
            html.Label("Agrégation", style={"color": "white"}),
            dcc.Dropdown(
                id='aggregation',
                options=[
                    {"label": "5 minutes", "value": "5min"},
                    {"label": "1 heure", "value": "1H"},
                    {"label": "1 jour", "value": "1D"},
                ],
                value="5min",
                style={"color": "black", "borderRadius": "4px"}
            )
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="latest-price", style={"fontSize": "24px", "color": "white", "textAlign": "center"}))
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="price-graph"))
    ]),

    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)
], fluid=True, style={
    "backgroundImage": f"url('data:image/png;base64,{encoded_image}')",
    "backgroundSize": "cover",
    "height": "100vh",
    "padding": "30px"
})

@app.callback(
    [Output("latest-price", "children"), Output("price-graph", "figure"),
     Output("date-picker", "start_date"), Output("date-picker", "end_date")],
    [Input("interval-update", "n_intervals"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date"),
     Input("aggregation", "value")]
)
def update_dashboard(n, start_date, end_date, agg):
    df = load_data()
    if df.empty:
        return "Il n'y a pas de données disponibles", {}, None, None

    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

    if agg == "1H":
        df = df.set_index("timestamp").resample("1H").mean().dropna().reset_index()
    elif agg == "1D":
        df = df.set_index("timestamp").resample("1D").mean().dropna().reset_index()

    latest_price = df.iloc[-1]["price"]
    latest_time = df.iloc[-1]["timestamp"]
    moyenne = df['price'].mean()
    variation = df['price'].pct_change().iloc[-1] * 100

    stats = (f"ETH: {latest_price:.2f} USDT (à {latest_time}) | Moyenne: {moyenne:.2f} USDT | Variation: {variation:.2f}%")

    figure = {
        "data": [{"x": df["timestamp"], "y": df["price"], "type": "line", "name": "ETH"}],
        "layout": {
            "title": "Prix ETH dans le temps",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Prix (USDT)", "tickprefix": "$"},
            "plot_bgcolor": "rgba(0,0,0,0)",
            "paper_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "white"}
        }
    }
    return stats, figure, df["timestamp"].min(), df["timestamp"].max()

if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(host="0.0.0.0", port=8050, debug=True)
