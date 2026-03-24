"""
discover_endpoint.py
====================
Herramienta de descubrimiento interactivo del endpoint categoría→UUIDs.

Uso:
    python discover_endpoint.py

Abre un Chromium visible, navega a una categoría de Alcampo y muestra
en tiempo real todas las llamadas a la API que contienen UUIDs.
Al final, guarda el endpoint en endpoint_cache.json.
"""

import asyncio
import json
import re
from pathlib import Path

UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)

BASE_URL     = "https://www.compraonline.alcampo.es"
CACHE_FILE   = Path("endpoint_cache.json")
CATEGORY_URL = f"{BASE_URL}/categories/~/OC1102"   # Zumos — fácil de ver


async def main():
    from playwright.async_api import async_playwright

    captured: list[dict] = []

    print("\n" + "="*60)
    print("DESCUBRIMIENTO DE ENDPOINT ALCAMPO")
    print("="*60)
    print(f"Navegando a: {CATEGORY_URL}")
    print("Se capturarán las peticiones que devuelvan UUIDs...\n")

    async with async_playwright() as p:
        # headless=False para ver el navegador (útil para debug)
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
        )
        page = await context.new_page()

        async def handle_response(response):
            url = response.url
            if BASE_URL not in url:
                return
            # Ignorar assets estáticos
            if any(ext in url for ext in [".js", ".css", ".png", ".woff", ".ico"]):
                return
            try:
                body = await response.text()
                uuids = UUID_RE.findall(body)
                if len(uuids) >= 3:
                    method = response.request.method
                    status = response.status
                    print(f"[{method} {status}] {url}")
                    print(f"  → {len(uuids)} UUIDs encontrados")
                    print(f"  → Primeros 3: {uuids[:3]}")
                    print()

                    try:
                        parsed = json.loads(body)
                    except Exception:
                        parsed = None

                    # Intentar detectar la clave donde están los UUIDs
                    uuid_key = "products"
                    if isinstance(parsed, dict):
                        for k, v in parsed.items():
                            if isinstance(v, list) and len(v) > 0:
                                if isinstance(v[0], str) and UUID_RE.match(v[0]):
                                    uuid_key = k
                                    break

                    captured.append({
                        "url":         url,
                        "method":      method,
                        "status":      status,
                        "uuid_count":  len(uuids),
                        "response_key": uuid_key,
                        "sample_uuids": uuids[:5],
                    })
            except Exception:
                pass

        page.on("response", handle_response)

        await page.goto(CATEGORY_URL, wait_until="networkidle", timeout=45_000)

        # Scroll para activar lazy loading
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)

        await asyncio.sleep(2)
        await browser.close()

    print("\n" + "="*60)
    print("RESULTADOS")
    print("="*60)

    if not captured:
        print("❌ No se capturó ningún endpoint con UUIDs.")
        print("\nSugerencias:")
        print("  1. El sitio puede requerir login o un servicio activo en tu zona")
        print("  2. Prueba abriendo DevTools > Network manualmente en Chrome")
        print("  3. Filtra por XHR y busca llamadas con 'products' o 'search'")
        return

    print(f"\n✅ {len(captured)} endpoints capturados:\n")
    for i, c in enumerate(captured, 1):
        print(f"{i}. [{c['method']}] {c['url']}")
        print(f"   UUIDs: {c['uuid_count']}  |  Clave JSON: {c['response_key']}")
        print()

    # Guardar el mejor (más UUIDs)
    best = max(captured, key=lambda x: x["uuid_count"])
    cache_data = {
        "endpoint_url":  best["url"],
        "method":        best["method"],
        "response_key":  best["response_key"],
        "all_captured":  [c["url"] for c in captured],
    }
    CACHE_FILE.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False))
    print(f"💾 Mejor endpoint guardado en {CACHE_FILE}:")
    print(f"   {best['url']}")
    print(f"\nAhora ejecuta el scraper:")
    print(f"   python scraper_alcampo.py --dry-run")


if __name__ == "__main__":
    asyncio.run(main())
