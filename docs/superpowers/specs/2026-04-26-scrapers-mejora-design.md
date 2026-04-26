# Mejora de scrapers DIA, Alcampo y Ahorramas

**Fecha**: 2026-04-26  
**Proyecto**: Mi Mejor Cesta  
**Tablas afectadas**: `precios_dia`, `precios_alcampo`, `precios_ahorramas`  
**Tablas intocables**: `productos_catalogo`, `categorias_maestras`, `productos_match`, `precios_carrefour`, `precios_mercadona`

---

## Contexto

El proyecto compara precios de supermercados españoles. El estado actual de la base de datos es:

| Supermercado | Productos actuales | Estado |
|---|---|---|
| Mercadona | 8.371 | ✅ Referencia |
| Carrefour | 7.241 | ✅ Referencia |
| DIA | ~4.786 | Mejorable |
| Alcampo | 727 | Pocos productos |
| Ahorramas | <500 | Incompleto |

El scraper de referencia es `scrapers/scraper_carrefour.py` (estrategia híbrida: API + Scrapling fallback).

---

## Diagnóstico por scraper

### DIA — Por qué captura ~4.786 productos

1. **IDs de categoría inventados**: Los IDs `"01"`, `"02"`... `"18"` no coinciden con los IDs reales de la API de DIA. Cuando `buscar_por_categoria` falla (HTTP != 200), cae al fallback de términos.
2. **Fallback de términos demasiado limitado**: Solo 3 páginas por término × ~25 términos = techo de ~7.500 pero con muchos duplicados.
3. **Sin argparse / sin `--dry-run`**: No se puede ejecutar sin confirmación interactiva (`input()`).
4. **Campos faltantes**: Sin `ean`, sin `formato`.

### Alcampo — Por qué captura 727 productos

1. **Visita individual por producto (O(n) requests)**: El scraper obtiene URLs de categoría y luego hace una petición HTTP por cada producto. Esto produce rate limiting y timeouts que cortan la ejecución.
2. **SPA sin JS rendering**: El JSON-LD en páginas de categoría no se carga con `requests` estándar — la web de Alcampo es React. Sin renderizado JS, `get_product_urls_from_category` devuelve lista vacía.
3. **Solo 15 categorías top-level**: Sin explorar subcategorías correctamente.
4. **Campos faltantes**: Sin `precio_unidad`, sin `ean`.

### Ahorramas — Por qué captura pocos productos

1. **cgids top-level demasiado amplios**: Demandware limita resultados por categoría. Con solo 9 cgids top-level se pierden subcategorías con productos específicos.
2. **Detección de total poco robusta**: Si el patrón regex no encuentra `"total"` en el JSON, se asume `total=999` pero la paginación para cuando `nuevos == 0`, lo cual ocurre antes de agotar los productos si el parser HTML no coincide.
3. **Selectores HTML posiblemente desactualizados**: `.pdp-link a`, `.price .value` pueden no coincidir con la estructura actual del site.
4. **Confirmación interactiva**: `input("¿Subir X productos? s/n")` bloquea la automatización.
5. **Campos faltantes**: Sin `ean`, sin `formato`.

---

## Schema unificado

Todos los scrapers producirán exactamente estos campos:

| Campo | Tipo | Notas |
|---|---|---|
| `id` | TEXT PK | Prefijo + número: `DI-0001`, `AL-0001`, `AH-0001` |
| `id_api` | TEXT | SKU/ID original del supermercado (clave de upsert) |
| `nombre_comercial` | TEXT | Nombre del producto |
| `precio` | FLOAT | Precio en euros |
| `precio_unidad` | TEXT | Ej: `"1.29€/L"`, `"2.50€/kg"` |
| `marca` | TEXT | Marca del producto |
| `ean` | TEXT | Código EAN (cadena vacía si no disponible) |
| `url` | TEXT | URL completa del producto |
| `imagen` | TEXT | URL de la imagen |
| `disponible` | BOOL | Disponibilidad en tienda online |
| `formato` | TEXT | Ej: `"1 L"`, `"400 g"`, `"6 x 200 ml"` |
| `actualizado` | TEXT | ISO timestamp añadido en cada upsert |

El campo `categoria` de Alcampo y `categoria_ahorramas` de Ahorramas se eliminan del schema de salida (no están en Carrefour ni en el schema objetivo).

---

## Arquitectura: patrón Carrefour aplicado a los tres scrapers

Cada scraper sigue exactamente esta estructura:

```
main(dry_run, only_cat, force_stealth, debug)
  │
  ├─ FASE 1: try_api(cat_id, page) — curl_cffi impersonate chrome124
  │    └─ Si devuelve productos → parse_api_product() → upsert
  │
  └─ FASE 2 (fallback): scrape_first_page() — Scrapling StealthyFetcher
       ├─ solve_cloudflare=True, network_idle=True
       ├─ extract_products_from_html(html)
       │    ├─ Intento 1: JSON embebido (window.__data__, __INITIAL_STATE__, etc.)
       │    ├─ Intento 2: JSON-LD <script type="application/ld+json">
       │    └─ Intento 3: tarjetas HTML con selectores CSS
       └─ fetch_pagination_pages() — curl_cffi para páginas 2..N
```

### Funciones compartidas en cada fichero

```python
# HTTP
_http_session = curl_requests.Session(impersonate="chrome124")
get_stealthy_session() / close_stealthy_session()

# Parsing
try_api(cat_id, page) → list[dict] | None
parse_api_product(item) → dict | None
extract_products_from_html(html) → list[dict]
scrape_first_page(slug, cat_id) → (html, total)
fetch_pagination_pages(slug, cat_id, total) → list[dict]

# Supabase
get_supabase() → client
upsert(client, products) → int

# CLI
argparse: --dry-run, --cat, --stealth, --debug
```

---

## Diseño específico por scraper

### scraper_dia.py

**Endpoint API**: `https://www.dia.es/api/v1/search-back/search/reduced`  
**Bootstrap de categorías**: `GET https://www.dia.es/api/v1/search-back/categories` → IDs reales del árbol. Fallback a lista hardcoded si el endpoint falla.  
**Parámetros de búsqueda**: `?categoryId={id}&page={n}&pageSize=100`  
**Extracción de precio_unidad**: `item["prices"]["price_per_unit"]` + `item["prices"]["measure_unit"]`  
**Extracción de ean**: `item.get("ean") or item.get("gtin") or ""`  
**Extracción de formato**: regex sobre `nombre_comercial` — patrón `\d+\s*(ml|l|g|kg|cl|ud)`  
**ID**: Mantener patrón secuencial `DI-{contador:04d}` (los IDs existentes en `productos_match` son de este formato — cambiarlos rompería los matches). `id_api = item["sku_id"]` es la clave de upsert.  
**Prefijo tabla**: `precios_dia`

**Categorías a usar** (se amplían desde 18 top-level hasta incluir subcategorías):
- Fruta y verdura, Carnes y charcutería, Pescado, Lácteos y huevos, Panadería, Congelados, Bebidas, Bodega, Despensa (aceite, arroz, pasta, conservas, salsas, cereales, snacks), Higiene, Limpieza, Bebés, Mascotas

### scraper_alcampo.py

**Reescritura completa** — no se mantiene ninguna de las dos fases actuales.

**Endpoint API a probar**: 
- `https://www.compraonline.alcampo.es/api/v2/page/category?categoryId={catId}&currentPage={n}&pageSize=50`
- Headers con `curl_cffi impersonate chrome124`

**Extracción desde HTML renderizado** (fallback Scrapling):
- Buscar `window.__INITIAL_STATE__` o `window.__data__` en el HTML
- Fallback: `application/ld+json` tipo `ItemList`
- Fallback: tarjetas CSS `.product-card`, `[data-testid="product"]`

**precio_unidad**: extraer de `pricePerUnit` o `referencePrice` del JSON / del elemento HTML `[class*="unit-price"]`  
**Categorías expandidas**: ~30 categorías cubriendo todo el catálogo de Alcampo  
**ID**: `AL-{pid}` directamente (el scraper actual ya usa este formato — compatible con Carrefour). `id_api = pid`.  
**Prefijo tabla**: `precios_alcampo`

### scraper_ahorramas.py

**Endpoint**: `https://www.ahorramas.com/on/demandware.store/Sites-Ahorramas-Site/es/Search-ShowAjax`  
**Parámetros**: `?cgid={cgid}&pmin=0.01&start={n}&sz=48`

**Mejoras de parsing HTML**:
- Detectar `[data-pid]` como selector raíz de producto (más fiable que `.product-tile`)
- Precio: `[itemprop="price"]`, `[class*="price"]`, `data-price` attribute
- precio_unidad: `[class*="unit"]`, `[class*="per-unit"]`, texto con patrón `€/(kg|L|ud)`
- Paginación: detectar total con múltiples patrones: `"total"`, `"count"`, atributo `data-count`

**Categorías expandidas** (~20):
- alimentacion, bebidas, frescos, congelados, lacteos, drogueria, cuidadopersonal, mascotas, bebe
- Añadir: panaderia, carniceria, pescaderia, conservas, cereales-galletas, aceites-condimentos, limpieza, higiene, vinos-licores, aperitivos

**ID**: Mantener patrón secuencial `AH-{contador:04d}` (misma razón que DIA — backward compatibility con `productos_match`). `id_api` = `data-pid` o regex `-(\d+)\.html`.  
**Prefijo tabla**: `precios_ahorramas`

---

## Restricciones absolutas

- **NO modificar**: `productos_catalogo`, `categorias_maestras`, `productos_match`
- **NO modificar**: `precios_carrefour`, `precios_mercadona`
- **NO modificar**: ningún otro archivo del proyecto fuera de los tres scrapers
- Credenciales siempre desde `.env` en la raíz del proyecto
- Comandos con PowerShell (Windows) — sin `&&`, comandos separados

---

## Criterios de éxito

| Scraper | Mínimo aceptable | Objetivo |
|---|---|---|
| DIA | >6.000 productos | ~8.000+ |
| Alcampo | >3.000 productos | ~5.000+ |
| Ahorramas | >2.000 productos | ~3.500+ |

Todos los scrapers deben:
- Ejecutarse sin intervención manual (sin `input()`)
- Soportar `--dry-run` para pruebas
- Hacer upsert correcto en Supabase usando `id_api` como clave de conflicto
- Tener `precio_unidad` como TEXT en todos los registros donde el supermercado lo exponga
