#!/bin/bash

# Définition des variables
URL="https://www.htx.com/fr-fr/price/eth/"
OUTPUT_FILE="eth_prices.csv"

# Récupération du contenu de la page
HTML=$(curl -s "$URL")

# Extraction du prix avec une regex (à ajuster selon le HTML du site)
PRIX=$(echo "$HTML" | grep -oP '(?<=<div class="price">)[0-9]+\.[0-9]+')

# Vérification si on a récupéré une valeur correcte
if [[ -n "$PRIX" ]]; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$TIMESTAMP,$PRIX" >> "$OUTPUT_FILE"
    echo "[$TIMESTAMP] Prix ETH : $PRIX USD ajouté à $OUTPUT_FILE"
else
    echo "Erreur : Impossible d'extraire le prix de l'ETH."
fi

