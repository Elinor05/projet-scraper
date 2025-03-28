import sys
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc

# Charger les données
def load_data():
    try:
        df = pd.read_csv("eth_prices.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame(columns=["timestamp", "price"])

# Initialisation de Dash
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap"
])

# Mise en page
app.layout = dbc.Container([
    html.H1("Suivi du prix de l'ETH", style={
        "textAlign": "center",
        "color": "white",
        "marginTop": "30px",
        "marginBottom": "40px",
        "fontFamily": "Montserrat"
    }),

    dbc.Row([
        dbc.Col([
            html.Label("Choisir une plage de dates", style={"color": "white", "fontWeight": "bold"}),
            dcc.DatePickerRange(
                id='date-picker',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                style={"backgroundColor": "white", "borderRadius": "4px"}
            )
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="latest-price", style={
            "fontSize": "22px", "color": "white", "textAlign": "left", "paddingBottom": "20px"
        }), width=6)
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="price-graph"), width=12)
    ]),

    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)
], fluid=True, style={
    "background": "radial-gradient(circle, #1b335f, #0d1b2a)",
    "minHeight": "100vh",
    "padding": "30px"
})

# Callback pour mettre à jour les données
@app.callback(
    [Output("latest-price", "children"), Output("price-graph", "figure"),
     Output("date-picker", "start_date"), Output("date-picker", "end_date")],
    [Input("interval-update", "n_intervals"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date"),
     Input("aggregation", "value")]
)
def update_dashboard(n, start_date, end_date, agg="5min"):
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
    previous_price = df.iloc[-2]["price"] if len(df) > 1 else latest_price
    variation = latest_price - previous_price
    pct_change = (variation / previous_price) * 100 if previous_price != 0 else 0
    latest_time = df.iloc[-1]["timestamp"]

    color = "green" if pct_change >= 0 else "red"

    stats = html.Div([
        html.Span(f"{latest_price:.4f} ", style={"fontWeight": "bold", "fontSize": "26px"}),
        html.Span(f"{variation:+.4f} ", style={"color": color, "fontWeight": "bold", "marginLeft": "10px"}),
        html.Span(f"({pct_change:+.2f}%)", style={"color": color, "fontWeight": "bold"}),
        html.Br(),
        html.Span(f"À la clôture : {latest_time.strftime('%d %b %Y à %H:%M:%S')}", style={"fontSize": "16px"})
    ])

    figure = {
        "data": [{"x": df["timestamp"], "y": df["price"], "type": "line", "name": "ETH"}],
        "layout": {
            "title": "Prix ETH dans le temps",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Prix (USDT)", "tickprefix": "$"},
            "plot_bgcolor": "#1b263b",
            "paper_bgcolor": "#1b263b",
            "font": {"color": "white"}
        }
    }

    return stats, figure, df["timestamp"].min(), df["timestamp"].max()

# Lancement conditionnel
if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(host="0.0.0.0", port=8050, debug=True)
