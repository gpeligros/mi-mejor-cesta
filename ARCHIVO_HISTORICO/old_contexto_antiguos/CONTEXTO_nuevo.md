# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 21/04/2026)

## ⚠️ INSTRUCCIONES PARA CLAUDE
Lee este fichero COMPLETO antes de responder nada.
Respeta SIEMPRE las convenciones de nombres, arquitectura y reglas de oro.
NUNCA propongas cambiar la arquitectura de BBDD sin consultar.
NUNCA cambies nombres de ficheros sin preguntar.
NUNCA empieces a escribir código sin entender primero el estado real.
SIEMPRE pide los ficheros actuales antes de modificarlos.
NUNCA uses sed en PowerShell — usar python3 para manipular ficheros.
PowerShell NO soporta && — ejecutar comandos por separado.

---

## 1. Qué es el proyecto
App web PWA de comparación de precios de supermercados españoles.
URL producción: https://mi-mejor-cesta.vercel.app
Repositorio: https://github.com/gpeligros/mi-mejor-cesta

---

## 2. Stack tecnológico
- Frontend: React 18 + Tailwind CSS — Vercel
- Base de datos: Supabase (PostgreSQL) — scpuriaofisssalsbzqv.supabase.co
- Autenticación: Supabase Auth (email + Google OAuth)
- Backend admin: Flask (Python) — local / localhost:5000
- Scrapers: Python 3 — carpeta /scrapers
- **Scraping avanzado: Scrapling 0.4.1** (Camoufox + StealthyFetcher) — usado para Carrefour
- IA (CESTITA): Anthropic Claude API — Vercel Serverless Function /api/cestita
- Pagos: Stripe (checkout + webhook) — /api/stripe-checkout y /api/stripe-webhook
- Deploy: Vercel — git push a main despliega automáticamente
- DISABLE_ESLINT_PLUGIN=true en variables de entorno de Vercel

---

## 3. Estructura de carpetas
```
mi-mejor-cesta/
  frontend/
    api/
      cestita.js                      ← Serverless Function proxy Anthropic API
      stripe-checkout.js              ← Serverless Function Stripe checkout
      stripe-webhook.js               ← Serverless Function Stripe webhook
    src/
      App.js                          ← componente principal
      components/
        Cestita.js                    ← asistente IA
        MenuSemanal.js                ← modal menú semanal + recetas + nutricional
        ModalUpgrade.js               ← modal planes con Stripe
        Sidebar.js                    ← sidebar historial + estadísticas
        SuperCard.js                  ← tarjeta super con reference_price
        StoreSelector.js              ← selector supers con visible flag
        ToolBar.js                    ← barra herramientas
        LogosSuper.js                 ← lista supers con visible: true/false
        Navbar.js, Footer.js...
      hooks/
        usePlan.js                    ← hook de planes
  backend/admin/                      ← panel admin Flask (localhost:5000)
  scrapers/                           ← scripts Python
  docs/
    CONTEXTO.md                       ← este fichero
```

---

## 4. Variables de entorno
### Vercel (producción — en TEST hasta ir a live)
- REACT_APP_SUPABASE_URL
- REACT_APP_SUPABASE_ANON_KEY
- ANTHROPIC_API_KEY (sin prefijo REACT_APP — es para serverless)
- STRIPE_SECRET_KEY (sk_test_... hasta producción)
- STRIPE_WEBHOOK_SECRET (whsec_...)
- STRIPE_PRICE_BASIC (price_test_...)
- STRIPE_PRICE_PREMIUM (price_test_...)
- STRIPE_SECRET_KEY_PROD (sk_live_... guardada)
- STRIPE_PRICE_BASIC_PRO (price_live_... guardada)
- STRIPE_PRICE_PREMIUM_PRO (price_live_... guardada)
- SUPABASE_SERVICE_KEY (service_role key — solo para serverless webhook)
- APP_URL (https://mi-mejor-cesta.vercel.app)
- DISABLE_ESLINT_PLUGIN=true

### Local (.env en raíz)
- SUPABASE_URL, SUPABASE_KEY (service role)
- ANTHROPIC_API_KEY
- REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY

---

## 5. Arquitectura de BBDD — INAMOVIBLE

### Tablas principales (estado 21/04/2026)
| Tabla | Descripción | Filas |
|-------|-------------|-------|
| `productos_catalogo` | Catálogo genérico. Solo admin escribe. | 3.977 |
| `categorias_maestras` | 87 categorías fijas. NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados. | 3.977 |
| `precios_mercadona` | IDs ME-xxxx. | ~8.327 |
| `precios_dia` | IDs DI-xxxx. | ~4.786 |
| `precios_alcampo` | IDs AL-xxxx. | 727 |
| **`precios_carrefour`** | **IDs CF-xxxxxx (nuevo 21/04/2026)** | **7.241** |
| `precios_ahorramas` | IDs AH-xxxx. | ~1.400 |
| `vista_productos` | VIEW catálogo + categorías. | — |
| `profiles` | Plan suscripción por usuario. PK = id (no user_id) | trigger creado |
| `cestas_online` | Cestas guardadas en la nube. | creada |
| `compras` | Historial compras por usuario. | activa |
| `compras_detalle` | Detalle productos por compra. | activa |
| `listas_colaborativas` | Listas compartidas tiempo real. | — |

### Columnas productos_match (verificadas 21/04/2026)
- id_catalogo (FK → productos_catalogo)
- id_mercadona, id_dia, id_alcampo, id_ahorramas, **id_carrefour** (la columna ya existe)

### Columnas precios_carrefour (verificadas 21/04/2026)
- id (TEXT, PK, formato CF-xxxxxx)
- id_api (TEXT, código interno Carrefour)
- nombre_comercial (TEXT)
- precio (NUMERIC)
- marca (TEXT)
- url (TEXT)
- imagen (TEXT)
- disponible (BOOL)
- formato (TEXT)
- ean (TEXT) — añadido con ALTER TABLE, actualmente vacío
- actualizado (TIMESTAMPTZ)

### Columnas profiles (VERIFICADO)
- id (UUID, PK — igual que auth.users.id)
- plan (text) → 'free' | 'basic' | 'premium'
- stripe_id (text) — customer ID de Stripe
- plan_desde (timestamptz)
- plan_hasta (timestamptz)
- created_at, updated_at

### Query estándar para ver usuarios con email
```sql
SELECT p.id, p.plan, p.stripe_id, u.email 
FROM profiles p
JOIN auth.users u ON p.id = u.id;
```

### Cambiar plan de usuario manualmente
```sql
UPDATE profiles SET plan = 'basic' WHERE id = 'UUID_DEL_USUARIO';
UPDATE profiles SET plan = 'free', stripe_id = null WHERE id = 'UUID_DEL_USUARIO';
```

### Reglas de oro
- NUNCA scrapers escriben en productos_catalogo ni categorias_maestras
- NUNCA borrar CAT-xxxx, solo desactivar con activo=false
- NUNCA subir .env a Git
- Antes de cualquier TRUNCATE verificar backup _old

---

## 6. Estado de supermercados

### ✅ En producción con datos
| Supermercado | Tabla | Productos | Matches | Cobertura vs catálogo |
|---|---|---|---|---|
| Mercadona | precios_mercadona | ~8.327 | 3.977 | 100% |
| **Carrefour** | **precios_carrefour** | **7.241** | **pendiente matching** | **por medir** |
| DIA | precios_dia | ~4.786 | 608 (limpiados IA) | 15% |
| Alcampo | precios_alcampo | 727 | 121 (limpiados IA) | 3% |
| AhorraMas | precios_ahorramas | ~1.400 | parcial | — |

### ❌ Tablas creadas sin datos
precios_aldi, precios_despensa, precios_eroski, precios_hipercor, precios_lidl

### 🟡 En desarrollo
| Supermercado | Estado | Notas |
|---|---|---|
| Hipercor | scraper_hipercor.py escrito | Falla en ejecución, pendiente depurar |
| Lidl | Pendiente | Candidato Scrapling DynamicFetcher |
| Eroski | Pendiente | Candidato Scrapling DynamicFetcher |

### ❌ Bloqueados
| Supermercado | Bloqueador |
|---|---|
| Aldi | Sin tienda online en España |
| La Despensa | Sin scraper |

---

## 7. Convención de nombres de ficheros
- Scrapers: `scraper_{supermercado}.py`
- Matching: `match_{supermercado}.py`
- Matching con IA: `revisar_matches_{supermercado}.py`
- SQL de setup: `{supermercado}_setup.sql`
- Scripts de enriquecimiento: `enriquecer_{tabla}.py`

---

## 8. Planes de suscripción

| Plan | Precio | Límites | Estado |
|---|---|---|---|
| Gratuito sin registro | 0€ | 2 supers, 20 productos | ✅ funcionando |
| Gratuito con registro | 0€ | 2 supers, 20 productos | ✅ funcionando |
| Básico | 2,99€/mes | Todo ilimitado + CESTITA + historial + estadísticas | ✅ Stripe test |
| Premium | 6,99€/mes | + menú semanal IA + nutricional + recetas IA | ✅ Stripe test |

### IDs Stripe
- prod_UHT4B2MREHH2nE → Plan Básico
- prod_UHT7TEyO5Iv4SC → Plan Premium
- price_1TIu8THqX5envLqIAn8ZDQh0 → Precio Básico (live)
- price_1TIuBcHqX5envLqIBIpWBKTQ → Precio Premium (live)

### Funcionalidades por plan (usePlan.js)
- maxSupers: free=2, basic/premium=999
- maxProductos: free=20, basic/premium=999
- CESTITA básico: todos los planes
- CESTITA avanzado (manipula cesta): todos los planes autenticados
- guardarCompras: basic+
- historialCompras: basic+ (3 meses), premium (ilimitado)
- estadísticas: basic+
- menuSemanal: premium
- recetasIA: premium
- nutricional: premium

---

## 9. Funcionalidades implementadas ✅

### Frontend
- Comparador con 3.977 productos en catálogo
- Sidebar con 87 categorías en acordeón
- Buscador en tiempo real
- Filtro marca blanca
- Filtro categoría General
- Auth completa (email + Google OAuth)
- Lista colaborativa en tiempo real
- Exportar PDF
- PWA instalable
- CESTITA IA
- CESTITA manipula cesta real
- ModalUpgrade con Stripe
- usePlan — límites funcionando
- StoreSelector compacto
- SuperCard con reference_price (€/L, €/kg)
- Guardar compras realizadas
- Historial en sidebar
- Estadísticas gasto (basic+)
- cestas_online sincronización nube
- ToolBar 3 botones
- MenuSemanal premium
- Sugerir recetas premium
- Análisis nutricional premium
- Stripe checkout + webhook → profiles

### Backend/Scrapers
- scraper_mercadona.py — con reference_price
- **scraper_carrefour.py — híbrido API+Scrapling, 7.241 productos extraídos** ✅ NUEVO
- scraper_hipercor.py — creado, pendiente de depurar
- enriquecer_catalogo.py — tipo, formato, nombre_normalizado, marca
- revisar_matches_dia.py — IA
- revisar_matches_alcampo.py — IA
- match_alcampo.py v3 — fuzzy mejorado

---

## 10. Problemas conocidos / Deuda técnica

### 🔴 Críticos
- Stripe en modo TEST — pendiente pasar a producción

### 🟡 Importantes
- EAN no capturado aún en Carrefour (columna existe pero vacía — Carrefour no lo expone en listing)
- EAN no capturado en Mercadona (misma razón)
- Matches DIA al 15% del catálogo (608/3.977)
- Matches Alcampo al 3% del catálogo (121/3.977)
- **Carrefour matching pendiente de ejecutar**
- CESTITA no puede buscar productos fuera del catálogo exacto
- Google OAuth ventana pequeña al volver del login
- scraper_hipercor.py falla con HTTP 520 / 0 productos
- **App.js solo carga Mercadona, DIA, Alcampo, AhorraMas — Carrefour no integrado aún**

### 🟡 Pendiente implementar
- CESTITA: búsqueda por palabras clave
- Alertas de precio (requiere historial_precios)
- Datos nutricionales en BBDD (ahora IA en tiempo real)
- Integrar Carrefour en App.js + LogosSuper.js

### 🟢 Menores
- Warning icono manifest PWA
- ID GA4 placeholder en index.html

---

## 11. Comandos útiles
```bash
# Local (PowerShell — NO usar &&, ejecutar por separado)
cd frontend
npm start

# Deploy
git add .
git commit -m "descripción"
git push origin main

# Panel admin
cd backend/admin
python app.py

# Scrapers
python scrapers/scraper_mercadona.py
python scrapers/scraper_carrefour.py --dry-run --cat bebidas
python scrapers/scraper_carrefour.py --stealth
python scrapers/enriquecer_catalogo.py --dry-run
python scrapers/revisar_matches_dia.py --dry-run

# Scrapling (una sola vez tras pip install)
pip install "scrapling[fetchers]"
scrapling install
```

---

## 12. Pendientes por orden de prioridad hacia el 100%

### FASE A — Estabilización ✅ COMPLETADA

### FASE B — Monetización ✅ COMPLETADA (en test)
- ⏳ Pasar Stripe a producción (cambiar keys test → live) — LO ÚLTIMO

### FASE C — Más supermercados (🟡 EN CURSO)
1. ✅ Scraper Carrefour con Scrapling (7.241 productos)
2. ⏳ match_carrefour.py (pendiente dry-run)
3. ⏳ revisar_matches_carrefour.py (IA)
4. ⏳ Integrar Carrefour en App.js y LogosSuper.js
5. ⏳ Scraper Lidl con Scrapling DynamicFetcher
6. ⏳ Scraper Eroski con Scrapling DynamicFetcher
7. ⏳ Depurar scraper_hipercor.py (HTTP 520 / 0 productos)
8. ⏳ Completar AhorraMas 2 categorías faltantes

### FASE D — Funcionalidades Premium ✅ COMPLETADA
- ⏳ Alertas subida/bajada precio (requiere historial_precios)

### FASE E — Calidad de datos
- Revisar errores/inconsistencias catálogo
- Mejorar matches DIA (608 → objetivo 2.000+)
- Mejorar matches Alcampo (121 → objetivo 500+)
- Ejecutar matches Carrefour (estimado 1.500–2.500 finales)
- EAN vía endpoint individual Mercadona (opcional, costoso)

---

## 13. Patrón Scrapling (aprendido 21/04/2026)

### Cuándo usar cada fetcher
- `Fetcher` → HTTP directo con impersonate TLS. Equivalente a curl_cffi. Sitios sin Cloudflare.
- `DynamicFetcher` → Playwright Chromium. SPAs sin anti-bot (Lidl, Eroski).
- `StealthyFetcher` → Camoufox (Firefox modificado). Sitios con Cloudflare (Carrefour).

### Patrón de scraper híbrido (validado en Carrefour)
1. Intentar API HTTP rápida con curl_cffi (30s)
2. Si falla con 5xx/403 → fallback a StealthySession con solve_cloudflare=True
3. Usar page_action async para scroll infinito
4. Extraer de JSON-LD embebido como primera opción, fallback a selectores CSS
5. Parar si HTTP 403 consecutivos (rate limit) y esperar 60s

### Aprendizajes clave
- HTTP 520 de Cloudflare = el servidor devolvió algo raro, normalmente bloqueo anti-bot. Señal clara para usar StealthyFetcher.
- `StealthySession` abre el navegador UNA vez y lo reutiliza (lazy init importante para no perder 5s por categoría).
- `wait_selector` con varios selectores alternativos separados por coma es útil si el sitio cambia el DOM.
- Límite de rate en Carrefour: ~1.000 productos seguidos antes de HTTP 403. Solución: delay ≥ 2.5s + backoff tras 403.
