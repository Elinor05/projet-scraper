#!/bin/bash

# Définition des variables
URL="https://api.huobi.pro/market/detail/merged?symbol=ethusdt"
OUTPUT_FILE="eth_prices.csv"

# Vérifier si le fichier CSV existe, sinon ajouter l'en-tête
if [[ ! -f "$OUTPUT_FILE" ]]; then
    echo "timestamp,price" > "$OUTPUT_FILE"
fi

# Récupération des données JSON
JSON=$(curl -s "$URL")

# Extraction du prix avec grep et regex
PRIX=$(echo "$JSON" | grep -oP '"close":\K[\d.]+')

# Vérification si on a récupéré une valeur correcte
if [[ -n "$PRIX" ]]; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$TIMESTAMP,$PRIX" >> "$OUTPUT_FILE"
    echo "[$TIMESTAMP] Prix ETH : $PRIX USD ajouté à $OUTPUT_FILE"
else
    echo "Erreur : Impossible d'extraire le prix de l'ETH."
fi
