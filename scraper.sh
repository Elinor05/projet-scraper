#!/bin/bash

# Récupérer la page web
curl -s "https://example.com" > page.html

# Extraire une information avec grep et sed
grep -oP '(?<=<span class="price">).*?(?=</span>)' page.html

# Nettoyer après utilisation
rm page.html
