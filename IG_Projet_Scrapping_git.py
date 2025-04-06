import sys
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

# Charger les données du CSV et convertir en heure de Paris (UTC+2)
def load_data():
    try:
        df = pd.read_csv("eth_prices.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"]) + pd.Timedelta(hours=2)
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
        html.Div([
            html.Img(src="/assets/logo_eth.png", style={"height": "80px", "marginRight": "30px"}),
            html.H1("Suivi du prix de l'ETH", style={
                "color": "white",
                "fontFamily": "Montserrat",
                "margin": "0px",
                "textAlign": "center"
            }),
            html.Img(src="/assets/logo_eth.png", style={"height": "80px", "marginLeft": "30px"})
        ], style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "padding": "20px 0",
        })
    ], style={"backgroundColor": "#0a1a2f", "borderRadius": "10px", "marginBottom": "40px"}),

    dbc.Row([
        dbc.Col(html.Div(id="latest-price", style={"fontSize": "24px", "color": "white", "textAlign": "center"}))
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="price-graph"))
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id="daily-bars"))
    ]),

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
                ], value="5min",
                style={"width": "60%", "borderRadius": "5px"}
            )
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Statistiques", style={"backgroundColor": "#0d1b2a", "color": "white"}),
                dbc.CardBody([
                    html.Div(id="advanced-stats", style={"color": "white", "fontSize": "15px"})
                ])
            ], style={"backgroundColor": "#1b263b", "border": "1px solid #2b3e5e", "width": "90%", "float": "right"})
        ], width=6)
    ], className="mt-4 mb-4"),

    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)

], fluid=True, style={
    "background": "linear-gradient(to bottom right, #0a1a2f, #123456, #0a1a2f)",
    "minHeight": "100vh", "padding": "30px"
})

@app.callback(
    [Output("latest-price", "children"),
     Output("price-graph", "figure"),
     Output("daily-bars", "figure"),
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
        return "Il n'y a pas de données disponibles", {}, {}, None, None, ""

    if start_date and end_date:
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

    if agg == "1H":
        df = df.set_index("timestamp").resample("1H").mean().dropna().reset_index()
    elif agg == "1D":
        df = df.set_index("timestamp").resample("1D").mean().dropna().reset_index()

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
        html.Span(f"({sign}{delta_pct:,.2f}%)", style={"color": color, "fontSize": "20px"}),
        html.Br(),
        html.Span(f"À la clôture : {latest_time.strftime('%d %b %Y à %H:%M:%S')}", style={"fontSize": "14px", "color": "white"})
    ])

    df_daily = df.set_index("timestamp").resample("1D").agg(["first", "last", "max", "min", "std"])
    df_daily.columns = ['_'.join(col) for col in df_daily.columns]
    df_daily = df_daily.dropna()
    df_daily["variation"] = (df_daily["price_last"] - df_daily["price_first"]) / df_daily["price_first"] * 100

    max_rise = df_daily["variation"].max()
    max_rise_day = df_daily[df_daily["variation"] == max_rise].index[0].strftime('%d %b %Y')
    most_volatile = df_daily["price_std"].max()
    most_volatile_day = df_daily[df_daily["price_std"] == most_volatile].index[0].strftime('%d %b %Y')
    lowest_price = df_daily["price_min"].min()
    lowest_price_day = df_daily[df_daily["price_min"] == lowest_price].index[0].strftime('%d %b %Y')

    volatility = df["price"].std()
    prix_max = df["price"].max()
    prix_min = df["price"].min()
    moyenne = df["price"].mean()

    stats_adv = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Table([
                    html.Thead(html.Tr([html.Th("Statistiques Générales", colSpan=2)])),
                    html.Tbody([
                        html.Tr([html.Td("Volatilité (écart-type)", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{volatility:.4f}", style={"color": "black"})]),
                        html.Tr([html.Td("Prix max", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{prix_max:.4f}", style={"color": "black"})]),
                        html.Tr([html.Td("Prix min", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{prix_min:.4f}", style={"color": "black"})]),
                        html.Tr([html.Td("Moyenne", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{moyenne:.4f}", style={"color": "black"})])
                    ])
                ], bordered=True, style={"fontSize": "12px", "backgroundColor": "#1f3b5c"})
            ], width=6),

            dbc.Col([
                dbc.Table([
                    html.Thead(html.Tr([html.Th("Insights", colSpan=2)])),
                    html.Tbody([
                        html.Tr([html.Td("Plus forte hausse", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{max_rise:.2f}% le {max_rise_day}", style={"color": "black"})]),
                        html.Tr([html.Td("Journée la plus volatile", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{most_volatile:.2f} le {most_volatile_day}", style={"color": "black"})]),
                        html.Tr([html.Td("Prix le plus bas", style={"color": "black", "fontWeight": "bold"}), html.Td(f"{lowest_price:.2f} le {lowest_price_day}", style={"color": "black"})])
                    ])
                ], bordered=True, style={"fontSize": "12px", "backgroundColor": "#1f3b5c"})
            ], width=6)
        ])
    ])

    price_fig = {
        "data": [go.Scatter(x=df["timestamp"], y=df["price"], mode="lines", name="ETH")],
        "layout": go.Layout(
            title="Prix ETH dans le temps",
            plot_bgcolor="#1b263b",
            paper_bgcolor="#1b263b",
            font={"color": "white"},
            xaxis={"title": "Date"},
            yaxis={"title": "Prix (USDT)", "tickprefix": "$"}
        )
    }

    bars = go.Figure()
    for date, row in df_daily.iterrows():
        bar_color = "green" if row["price_last"] > row["price_first"] else "red"
        bars.add_trace(go.Bar(
            x=[date],
            y=[row["price_last"] - row["price_first"]],
            marker_color=bar_color,
            name=date.strftime('%d-%m')
        ))
    bars.update_layout(
        title="Variation journalière :",
        plot_bgcolor="#1b263b",
        paper_bgcolor="#1b263b",
        font={"color": "white"}
    )

    return stats_main, price_fig, bars, df["timestamp"].min(), df["timestamp"].max(), stats_adv

if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(host="0.0.0.0", port=8050, debug=True)
