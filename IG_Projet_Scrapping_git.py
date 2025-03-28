import sys
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc

# Charger les données du CSV
def load_data():
    try:
        df = pd.read_csv("eth_prices.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame(columns=["timestamp", "price"])

# Initialisation
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap"
])

# Layout
app.layout = dbc.Container([

    # Titre
    html.Div([
        html.H1("Suivi du prix de l'ETH", style={
            "textAlign": "center",
            "color": "white",
            "fontFamily": "Montserrat",
            "padding": "20px 0",
            "marginBottom": "40px",
        })
    ], style={
        "backgroundColor": "#0a1a2f",
        "borderRadius": "10px"
    }),

    # Filtres (date picker + dropdown)
    dbc.Row([
        dbc.Col([
            html.Label("Choisir une plage de dates", style={"color": "white"}),
            html.Br(),
            dcc.DatePickerRange(
                id='date-picker',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                style={"backgroundColor": "white", "borderRadius": "5px"}
            ),
            html.Br(), html.Br(),
            html.Label("Agrégation", style={"color": "white"}),
            dcc.Dropdown(
                id='aggregation',
                options=[
                    {"label": "5 minutes", "value": "5min"},
                    {"label": "1 heure", "value": "1H"},
                    {"label": "1 jour", "value": "1D"},
                ],
                value="5min",
                style={"width": "60%", "borderRadius": "5px"}
            )
        ], width=6),

        # Encadré de statistiques
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Statistiques", style={"backgroundColor": "#0d1b2a", "color": "white"}),
                dbc.CardBody([
                    html.Div(id="latest-price", style={"color": "white", "fontSize": "16px"})
                ])
            ], style={"backgroundColor": "#1b263b", "border": "1px solid #2b3e5e"})
        ], width=6, style={"textAlign": "right"})
    ], className="mb-4"),

    # Courbe
    dbc.Row([
        dbc.Col(dcc.Graph(id="price-graph"))
    ]),

    # Mise à jour auto
    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)

], fluid=True, style={
    "background": "linear-gradient(to bottom right, #0a1a2f, #123456, #0a1a2f)",
    "minHeight": "100vh",
    "padding": "30px"
})

# Callback
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
    if df.empty or len(df) < 2:
        return "Il n'y a pas de données disponibles", {}, None, None

    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

    if agg == "1H":
        df = df.set_index("timestamp").resample("1H").mean().dropna().reset_index()
    elif agg == "1D":
        df = df.set_index("timestamp").resample("1D").mean().dropna().reset_index()

    if len(df) < 2:
        return "Pas assez de données pour calculer la variation", {}, None, None

    latest_price = df.iloc[-1]["price"]
    prev_price = df.iloc[-2]["price"]
    latest_time = df.iloc[-1]["timestamp"]

    delta = latest_price - prev_price
    delta_pct = (delta / prev_price) * 100 if prev_price != 0 else 0
    color = "green" if delta >= 0 else "red"
    sign = "+" if delta >= 0 else ""

    stats_content = html.Div([
        html.Div([
            html.Span("Prix actuel : ", style={"fontWeight": "bold"}),
            html.Span(f"{latest_price:.4f} USDT")
        ]),
        html.Div([
            html.Span("Variation : ", style={"fontWeight": "bold"}),
            html.Span(f"{sign}{delta:.4f} USDT", style={"color": color})
        ]),
        html.Div([
            html.Span("Variation % : ", style={"fontWeight": "bold"}),
            html.Span(f"{sign}{delta_pct:,.2f}%", style={"color": color})
        ]),
        html.Div([
            html.Span("Dernière mise à jour : ", style={"fontWeight": "bold"}),
            html.Span(latest_time.strftime('%d %b %Y à %H:%M:%S'))
        ])
    ])

    figure = {
        "data": [{
            "x": df["timestamp"],
            "y": df["price"],
            "type": "line",
            "name": "ETH"
        }],
        "layout": {
            "title": "Prix ETH dans le temps",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Prix (USDT)", "tickprefix": "$"},
            "plot_bgcolor": "#1b263b",
            "paper_bgcolor": "#1b263b",
            "font": {"color": "white"}
        }
    }

    return stats_content, figure, df["timestamp"].min(), df["timestamp"].max()

# Lancer le serveur
if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(host="0.0.0.0", port=8050, debug=True)
