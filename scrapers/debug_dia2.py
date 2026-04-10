"""
debug_dia2.py — prueba varios endpoints de DIA para encontrar el correcto
"""
import requests, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.dia.es/",
}

urls = [
    "https://www.dia.es/api/v1/search-back/search/reduced?q=leche&page=1&pageSize=3",
    "https://www.dia.es/api/v1/search-back/search?q=leche&page=1&pageSize=3",
    "https://www.dia.es/api/v1/catalog/search?q=leche&page=1&size=3",
    "https://www.dia.es/es/search?q=leche&format=json",
]

for url in urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"\n{r.status_code} → {url[:80]}")
        if r.status_code == 200:
            data = r.json()
            items = data.get("search_items") or data.get("products") or data.get("items") or []
            if items:
                print(f"  {len(items)} items. Primer item prices:")
                print(json.dumps(items[0].get("prices", items[0]), indent=2, ensure_ascii=False)[:500])
        else:
            print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
