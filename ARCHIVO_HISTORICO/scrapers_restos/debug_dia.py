"""
debug_dia.py — inspecciona la respuesta raw de la API de DIA
para ver qué campos de precio/unidad están disponibles.

Uso: python scrapers/debug_dia.py
"""
import requests, json

HEADERS_API = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":          "application/json",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         "https://www.dia.es/",
}

url = "https://www.dia.es/api/v1/search-back/search/reduced?categoryId=01&page=1&pageSize=3"
r = requests.get(url, headers=HEADERS_API, timeout=15)
print(f"HTTP {r.status_code}")

data = r.json()
items = data.get("search_items", [])
if items:
    print(f"\nPrimer item completo:")
    print(json.dumps(items[0], indent=2, ensure_ascii=False))
    print(f"\nCampo 'prices' del primer item:")
    print(json.dumps(items[0].get("prices", {}), indent=2, ensure_ascii=False))
