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

# Initialisation de l'application Dash
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap"
])

# Mise en page
app.layout = dbc.Container([
    html.H1("Suivi du prix de l'ETH", style={
        "textAlign": "center",
        "color": "white",
        "marginTop": "20px",
        "marginBottom": "40px",
        "fontFamily": "Montserrat"
    }),

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
                style={"color": "black", "borderRadius": "5px"}
            )
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="latest-price", style={
            "fontSize": "24px",
            "color": "white",
            "textAlign": "center"
        }))
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="price-graph"))
    ]),

    dbc.Row([
        dbc.Col(html.Div(id="stats-summary", style={
            "color": "white",
            "fontSize": "18px",
            "marginTop": "30px",
            "padding": "10px",
            "backgroundColor": "#1a2a40",
            "borderRadius": "10px"
        }))
    ]),

    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)
], fluid=True, style={
    "background": "linear-gradient(to bottom right, #0a1a2f, #123456, #0a1a2f)",
    "height": "100vh",
    "padding": "30px"
})

# Callback
@app.callback(
    [Output("latest-price", "children"),
     Output("price-graph", "figure"),
     Output("date-picker", "start_date"),
     Output("date-picker", "end_date"),
     Output("stats-summary", "children")],
    [Input("interval-update", "n_intervals"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date"),
     Input("aggregation", "value")]
)
def update_dashboard(n, start_date, end_date, agg):
    df = load_data()
    if df.empty or len(df) < 2:
        return "Il n'y a pas de données disponibles", {}, None, None, ""

    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

    if agg == "1H":
        df = df.set_index("timestamp").resample("1H").mean().dropna().reset_index()
    elif agg == "1D":
        df = df.set_index("timestamp").resample("1D").mean().dropna().reset_index()

    if len(df) < 2:
        return "Pas assez de données pour calculer la variation", {}, None, None, ""

    latest_price = df.iloc[-1]["price"]
    prev_price = df.iloc[-2]["price"]
    latest_time = df.iloc[-1]["timestamp"]

    delta = latest_price - prev_price
    delta_pct = (delta / prev_price) * 100 if prev_price != 0 else 0
    color = "green" if delta >= 0 else "red"
    sign = "+" if delta >= 0 else ""

    stats = html.Span([
        html.Span(f"{latest_price:.4f} ", style={"fontWeight": "bold", "fontSize": "28px"}),
        html.Span(f"{sign}{delta:.4f} ", style={"color": color, "fontWeight": "bold", "fontSize": "22px"}),
        html.Span(f"({sign}{delta_pct:,.2f}%)", style={"color": color, "fontSize": "20px"}),
        html.Br(),
        html.Span(f"À la clôture : {latest_time.strftime('%d %b %Y à %H:%M:%S')}", style={"fontSize": "14px", "color": "white"})
    ])

    figure = {
        "data": [{
            "x": df["timestamp"],
            "y": df["price"],
            "type": "line",
            "name": "ETH",
            "fill": "tozeroy",
            "fillcolor": "rgba(51, 153, 255, 0.2)"
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

    # Calcul des stats supplémentaires
    max_price = df["price"].max()
    min_price = df["price"].min()
    avg_price = df["price"].mean()
    std_price = df["price"].std()

    stats_box = html.Div([
        html.P(f"📈 Prix max : {max_price:.4f} USDT"),
        html.P(f"📉 Prix min : {min_price:.4f} USDT"),
        html.P(f"📊 Moyenne : {avg_price:.4f} USDT"),
        html.P(f"σ Écart-type : {std_price:.4f}")
    ])

    return stats, figure, df["timestamp"].min(), df["timestamp"].max(), stats_box

# Lancer le serveur
if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(host="0.0.0.0", port=8050, debug=True)
