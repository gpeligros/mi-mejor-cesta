# CLAUDE.md — Mi Mejor Cesta

## Proyecto
PWA de comparación de precios de supermercados españoles.
- **Producción**: https://mi-mejor-cesta.vercel.app
- **Repo**: https://github.com/gpeligros/mi-mejor-cesta
- **Supabase**: scpuriaofisssalsbzqv.supabase.co

## Stack
- Frontend: React 18 + Tailwind CSS → Vercel
- BBDD: Supabase (PostgreSQL)
- Auth: Supabase Auth (email + Google OAuth)
- Scrapers: Python 3 → carpeta /scrapers
- Scraping avanzado: Scrapling (StealthyFetcher para Cloudflare, DynamicFetcher para SPAs)
- IA: Anthropic Claude API → Vercel Serverless `/api/cestita`
- Pagos: Stripe (checkout + webhook) → `/api/stripe-checkout` y `/api/stripe-webhook`
- Deploy: `git push origin main` → Vercel autodeploy
- Admin: Flask (Python) → `backend/admin/` → localhost:5000

## Reglas OBLIGATORIAS
- **NUNCA** usar `sed` — estamos en Windows/PowerShell. Usar `python3` para manipular ficheros.
- **PowerShell NO soporta `&&`** — ejecutar comandos por separado.
- **NUNCA** cambiar arquitectura de BBDD sin consultar al usuario.
- **NUNCA** cambiar nombres de ficheros sin preguntar.
- **SIEMPRE** leer los ficheros actuales antes de modificarlos — nunca asumir estado.
- **NUNCA** scrapers escriben en `productos_catalogo` ni `categorias_maestras`.
- **NUNCA** borrar CAT-xxxx, solo desactivar con `activo=false`.
- **NUNCA** subir `.env` a Git.
- Schema changes → SQL manual en Supabase SQL Editor. NUNCA asumir estado del schema.
- Antes de cualquier TRUNCATE → verificar backup `_old`.
- `DISABLE_ESLINT_PLUGIN=true` en Vercel env vars.

## Arquitectura BBDD (INAMOVIBLE)

### Tablas principales
| Tabla | Descripción | Filas |
|---|---|---|
| `productos_catalogo` | Catálogo genérico (CAT-xxxx). Solo admin escribe. | ~4.173 |
| `categorias_maestras` | 87 categorías fijas. NUNCA modificar. | 87 |
| `productos_match` | Tabla puente: id_catalogo, id_mercadona, id_dia, id_alcampo, id_ahorramas, id_carrefour | ~4.173 |
| `precios_mercadona` | ME-xxxx | ~8.327 |
| `precios_dia` | DI-xxxx | ~4.786 |
| `precios_alcampo` | AL-xxxx | 727 |
| `precios_carrefour` | CR-xxxx (scraper OK, matching 0) | ~7.241 |
| `precios_ahorramas` | AH-xxxx (scraper OK, matching 0) | ~1.427 |
| `vista_productos` | VIEW catálogo + categorías | — |
| `profiles` | Planes usuario. PK=id (=auth.users.id) | — |
| `cestas_online` | Cestas en la nube | — |
| `compras` / `compras_detalle` | Historial de compras | — |
| `menus_guardados` | Menús semanales guardados (premium) | — |

### Bugs conocidos de Supabase
- Joins con FK syntax (`categorias_maestras(...)`) fallan sin FK definida → usar queries separadas
- RLS recursiva en `profiles` → 500 errors → usar `auth.uid() = id`
- `AdminPanel.js` DEBE importar de `../supabaseClient`, NO crear su propio `createClient`
- `rpc()` a funciones inexistentes → 404 silencioso
- Auth redirige a producción salvo que localhost esté en Redirect URLs

## Estado de supermercados

| Super | Tabla | Productos | Matches | Estado |
|---|---|---|---|---|
| Mercadona | precios_mercadona | ~8.327 | ~10.064 (99%) | ✅ En producción |
| DIA | precios_dia | ~5.076 | ~10.064 (99%) | ✅ En producción |
| Alcampo | precios_alcampo | 2.264 | 0 | ⚠️ Se resetó, pendiente re-matching |
| Carrefour | precios_carrefour | ~7.241 | ~7.241 | ✅ En producción |
| AhorraMas | precios_ahorramas | ~1.529 | ~331 | ⚠️ Matching parcial (22%) |
| Lidl | precios_lidl | 0 | 0 | ❌ Pendiente (Scrapling DynamicFetcher) |
| Eroski | precios_eroski | 0 | 0 | ❌ Pendiente |
| Hipercor | precios_hipercor | 0 | 0 | ❌ API pública disponible |

## Convención de nombres
- Scrapers: `scraper_{supermercado}.py`
- Matching: `match_{supermercado}.py`
- Matching con IA: `match_{supermercado}_ia.py`
- Enriquecimiento: `enriquecer_{tabla}.py`
- Revisión: `revisar_matches_{supermercado}.py`
- Catálogo: `construir_catalogo.py` o `construir_catalogo_desde_{super}.py`

## Planes de suscripción
| Plan | Precio | maxSupers | maxProductos | menuSemanal | recetasIA | nutricional |
|---|---|---|---|---|---|---|
| free | 0€ | 2 | 20 | ❌ | ❌ | ❌ |
| basic | 2,99€/mes | 999 | 999 | ❌ | ❌ | ❌ |
| premium | 6,99€/mes | 999 | 999 | ✅ | ✅ | ✅ |

### IDs Stripe (LIVE)
- price_1TIu8THqX5envLqIAn8ZDQh0 → Básico
- price_1TIuBcHqX5envLqIBIpWBKTQ → Premium

## ⚠️ CAMBIOS PENDIENTES EN App.js

### CAMBIO 1 — Props MenuSemanal ✅ COMPLETADO
Props session, plan y limiteMenusGuardados añadidas a MenuSemanal.

### CAMBIO 2 — Integrar Carrefour ✅ COMPLETADO
Matching 7.241/7.241. App.js ya carga precios_carrefour, índices y supersActivos incluyen Carrefour.

## Prioridades actuales (en orden)
1. **Re-matching AhorraMas** → matches a 0 tras rebuild catálogo
2. **Aplicar Cambio 1 en App.js** (MenuSemanal props)
3. **Mejorar matches DIA** (608 → 2.000+) y Alcampo (121 → 500+)
4. Pasar Stripe a producción (LO ÚLTIMO)

## Lecciones aprendidas
- `SUPERS_CONFIG` DEBE definirse FUERA del componente `Precios` en AdminPanel
- Definiciones de funciones DEBEN preceder a sus `useEffect`
- Bug core supersActivos: `StoreSelector` llamaba `setSupersActivos` directamente, bypaseando `setSupersActivosConLimite`
- Matching rapidfuzz al 85% produce cross-matches de marca (Coca-Cola ↔ Hola Cola) — deprioritizado
- Marca blanca → nombre genérico en sidebar; marca fabricante → solo si 2+ supermercados
- Formatos distintos (33cl vs 50cl) = entradas separadas en catálogo

## Comandos frecuentes
```bash
# Frontend local
cd frontend
npm start

# Deploy
git add .
git commit -m "descripción"
git push origin main

# Scrapers
python scrapers/scraper_mercadona.py
python scrapers/scraper_carrefour.py
python scrapers/match_carrefour.py --dry-run

# Verificar matches
# En Supabase SQL Editor:
# SELECT COUNT(*) FROM productos_match WHERE id_carrefour IS NOT NULL;
```
