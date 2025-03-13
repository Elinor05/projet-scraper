#!/bin/bash

# URL de l'API pour récupérer les données du marché ETH/USDT
url="https://api.huobi.pro/market/detail/merged?symbol=ethusdt"

# Utiliser curl pour envoyer la requête GET et récupérer la réponse
response=$(curl -s "$url")

# Vérifier si la réponse contient des données et afficher le prix de l'ETH
price=$(echo "$response" | jq -r '.tick.close')

# Afficher le prix de l'ETH
if [ "$price" != "null" ]; then
    echo "Prix de l'ETH (USDT) : $price"
else
    echo "Erreur lors de la récupération des données."
fi
