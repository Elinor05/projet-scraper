import sys
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

def load_data():
    try:
        df = pd.read_csv("eth_prices.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"]) + pd.Timedelta(hours=2)  # UTC+2 pour Paris
        return df
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame(columns=["timestamp", "price"])

app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap"
])

app.layout = dbc.Container([
    html.Div([
        html.H1("Suivi du prix de l'ETH", style={
            "textAlign": "center", "color": "white",
            "fontFamily": "Montserrat", "padding": "20px 0", "marginBottom": "40px",
        })
    ], style={"backgroundColor": "#0a1a2f", "borderRadius": "10px"}),

    dbc.Row([
        dbc.Col([
            html.Label("Choisir une plage de dates", style={"color": "white"}),
            html.Br(),
            dcc.DatePickerRange(id='date-picker', style={"backgroundColor": "white", "borderRadius": "5px"}),
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

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Statistiques", style={"backgroundColor": "#0d1b2a", "color": "white"}),
                dbc.CardBody([
                    html.Div(id="advanced-stats", style={"color": "white", "fontSize": "15px"})
                ])
            ], style={"backgroundColor": "#1b263b", "border": "1px solid #2b3e5e", "width": "80%", "float": "right"})
        ], width=6)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="latest-price", style={
            "fontSize": "24px", "color": "white", "textAlign": "center"
        }))
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="price-graph"))
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="variation-graph"))
    ]),

    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)

], fluid=True, style={
    "background": "linear-gradient(to bottom right, #0a1a2f, #123456, #0a1a2f)",
    "minHeight": "100vh", "padding": "30px"
})

@app.callback(
    [Output("latest-price", "children"),
     Output("price-graph", "figure"),
     Output("variation-graph", "figure"),
     Output("date-picker", "start_date"),
     Output("date-picker", "end_date"),
     Output("advanced-stats", "children")],
    [Input("interval-update", "n_intervals"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date"),
     Input("aggregation", "value")]
)
def update_dashboard(n, start_date, end_date, agg):
    df = load_data()
    if df.empty or len(df) < 2:
        return "Pas de données", {}, {}, None, None, ""

    if start_date and end_date:
        df = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)]

    if agg == "1H":
        df = df.set_index("timestamp").resample("1H").mean().dropna().reset_index()
    elif agg == "1D":
        df = df.set_index("timestamp").resample("1D").mean().dropna().reset_index()

    if len(df) < 2:
        return "Pas assez de données", {}, {}, None, None, ""

    latest_price = df.iloc[-1]["price"]
    prev_price = df.iloc[-2]["price"]
    latest_time = df.iloc[-1]["timestamp"]
    delta = latest_price - prev_price
    delta_pct = (delta / prev_price) * 100 if prev_price != 0 else 0
    color = "green" if delta >= 0 else "red"
    sign = "+" if delta >= 0 else ""

    stats_main = html.Span([
        html.Span(f"{latest_price:.4f} ", style={"fontWeight": "bold", "fontSize": "28px"}),
        html.Span(f"{sign}{delta:.4f} ", style={"color": color, "fontWeight": "bold", "fontSize": "22px"}),
        html.Span(f"({sign}{delta_pct:.2f}%)", style={"color": color, "fontSize": "20px"}),
        html.Br(),
        html.Span(f"À la clôture : {latest_time.strftime('%d %b %Y à %H:%M:%S')}", style={"fontSize": "14px", "color": "white"})
    ])

    # Stats avancées
    volatility = df["price"].std()
    prix_max = df["price"].max()
    prix_min = df["price"].min()
    moyenne = df["price"].mean()

    df_daily = df.copy()
    df_daily["date"] = df_daily["timestamp"].dt.date
    daily_open = df_daily.groupby("date")["price"].first()
    daily_close = df_daily.groupby("date")["price"].last()
    daily_change_pct = ((daily_close - daily_open) / daily_open) * 100
    daily_volatility = df_daily.groupby("date")["price"].std()

    best_day = daily_change_pct.idxmax()
    best_day_value = daily_change_pct.max()
    most_volatile_day = daily_volatility.idxmax()
    most_volatile_value = daily_volatility.max()
    lowest_price_day = df.loc[df["price"].idxmin()]["timestamp"].date()
    lowest_price = df["price"].min()

    stats_adv = html.Div([
        html.Div([
            html.Div([
                html.Div(f"Volatilité (écart-type) : {volatility:.4f}"),
                html.Div(f"Prix max : {prix_max:.4f}"),
                html.Div(f"Prix min : {prix_min:.4f}"),
                html.Div(f"Moyenne : {moyenne:.4f}")
            ], style={"width": "50%", "display": "inline-block"}),

            html.Div([
                html.Div(f"Plus forte hausse : {best_day_value:.2f}% le {best_day.strftime('%d %b %Y')}"),
                html.Div(f"Journée la plus volatile : {most_volatile_value:.2f} le {most_volatile_day.strftime('%d %b %Y')}"),
                html.Div(f"Prix le plus bas : {lowest_price:.2f} le {lowest_price_day.strftime('%d %b %Y')}")
            ], style={"width": "48%", "display": "inline-block", "paddingLeft": "20px"})
        ])
    ])

    # Courbe classique
    figure_main = {
        "data": [go.Scatter(x=df["timestamp"], y=df["price"], mode="lines", name="ETH")],
        "layout": {
            "title": "Prix ETH dans le temps",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Prix (USDT)", "tickprefix": "$"},
            "plot_bgcolor": "#1b263b",
            "paper_bgcolor": "#1b263b",
            "font": {"color": "white"}
        }
    }

    # Graph variation quotidienne
    variation = (daily_close - daily_open).fillna(0)
    colors = ["green" if val > 0 else "red" for val in variation]

    figure_var = {
        "data": [
            go.Bar(x=variation.index.astype(str), y=variation.values, marker_color=colors)
        ],
        "layout": {
            "title": "Variation quotidienne ETH (barres vertes = hausse, rouges = baisse)",
            "xaxis": {"title": "Date"},
            "yaxis": {"title": "Variation (USDT)"},
            "plot_bgcolor": "#1b263b",
            "paper_bgcolor": "#1b263b",
            "font": {"color": "white"}
        }
    }

    return stats_main, figure_main, figure_var, df["timestamp"].min(), df["timestamp"].max(), stats_adv

if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(host="0.0.0.0", port=8050, debug=True)
