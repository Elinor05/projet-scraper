import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd

# Charger les données du CSV
def load_data():
    try:
        df = pd.read_csv("eth_prices.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])  # Convertir en datetime
        return df
    except Exception as e:
        print(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame(columns=["timestamp", "price"])

# Initialisation de l'application Dash (pas JupyterDash)
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Suivi du prix de l'ETH", style={"textAlign": "center"}),

    html.Div(id="latest-price", style={"fontSize": "24px", "textAlign": "center"}),

    dcc.Graph(id="price-graph"),

    dcc.Interval(id="interval-update", interval=5 * 60 * 1000, n_intervals=0)
])

@app.callback(
    [Output("latest-price", "children"), Output("price-graph", "figure")],
    Input("interval-update", "n_intervals")
)
def update_dashboard(n):
    df = load_data()

    if df.empty:
        return "Il n'y a pas de données disponibles", {}

    latest_price = df.iloc[-1]["price"]
    latest_time = df.iloc[-1]["timestamp"]

    return (f"Dernier prix ETH : {latest_price} USDT (mis à jour à {latest_time})",
            {
                "data": [{"x": df["timestamp"], "y": df["price"], "type": "line", "name": "Prix ETH"}],
                "layout": {"title": "Évolution du prix de l'ETH"}
            })

# Lancer le serveur Dash
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
