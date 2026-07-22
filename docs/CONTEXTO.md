# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 22/07/2026)

## ⚠️ INSTRUCCIONES PARA CLAUDE
Lee este fichero COMPLETO antes de responder nada.
Respeta SIEMPRE las convenciones de nombres, arquitectura y reglas de oro.
NUNCA propongas cambiar la arquitectura de BBDD sin consultar.
NUNCA cambies nombres de ficheros sin preguntar.
NUNCA empieces a escribir código sin entender primero el estado real.
SIEMPRE pide los ficheros actuales antes de modificarlos.
NUNCA uses sed en PowerShell — usar python3 para manipular ficheros.
PowerShell NO soporta && — ejecutar comandos por separado.
NUNCA combines varios cambios en un solo paso — ir de uno en uno y confirmar.
SIEMPRE usar --dry-run antes de cualquier script que escriba en Supabase.

> 📌 NOTA DE ESTA ACTUALIZACIÓN (22/07/2026): el código real en GitHub iba
> MUY por delante de lo que decía el CONTEXTO anterior. Este fichero se ha
> reescrito contra el estado verificado del repo (`main`) y de la BBDD.
> Cambios grandes respecto a versiones previas: React 18 → 19, Carrefour y
> AhorraMas YA integrados en el frontend, matches reales muy distintos a los
> documentados, y un problema CONFIRMADO de calidad en los matches de Carrefour.

---

## 1. Qué es el proyecto
App web PWA de comparación de precios de supermercados españoles.
URL producción: https://mi-mejor-cesta.vercel.app
Repositorio: https://github.com/gpeligros/mi-mejor-cesta

---

## 2. Stack tecnológico
- Frontend: **React 19.2** + Tailwind CSS — Vercel  ⚠️ (antes React 18; migrado)
- Base de datos: Supabase (PostgreSQL) — scpuriaofisssalsbzqv.supabase.co
- Autenticación: Supabase Auth (email + Google OAuth)
- Backend admin: Flask (Python) — local / localhost:5000
- Scrapers: Python 3 — carpeta /scrapers
- IA (CESTITA): Anthropic Claude API (`claude-haiku-4-5-20251001`) — Vercel Serverless Function /api/cestita
- Pagos: Stripe (checkout + webhook) — /api/stripe-checkout y /api/stripe-webhook
- Monitorización errores: @sentry/react INSTALADO pero DESACTIVADO (comentado en index.js) ⚠️
- Analítica: Google Analytics GA4 real (G-2WJFBS3PW6) ✅
- Deploy: Vercel — git push a main despliega automáticamente
- DISABLE_ESLINT_PLUGIN=true en variables de entorno de Vercel

### Dependencias a revisar (deuda)
- `@google/generative-ai` está en package.json del frontend pero NO se usa en el bundle
  (el trabajo con Gemini está en scrapers Python). → Candidata a eliminar.
- `tesseract.js` instalado pero el escaneo OCR (handleFoto) sigue sin implementar
  (muestra un alert "pendiente de implementar"). → Implementar o eliminar.

---

## 3. Estructura de carpetas
```
mi-mejor-cesta/
  frontend/
    api/
      cestita.js                      ← Serverless Function proxy Anthropic API ✅
      cors_helper.js                  ← helper CORS para las serverless ✅
      stripe-checkout.js              ← Serverless Function Stripe checkout ✅
      stripe-webhook.js               ← Serverless Function Stripe webhook ✅
    src/
      App.js                          ← componente principal (5 supers cableados)
      supabaseClient.js               ← cliente Supabase (solo anon key, protegida por RLS) ✅
      index.js                        ← root React 19 + ErrorBoundary + Service Worker (Sentry comentado)
      components/
        AdminPanel.js
        AuthModal.js
        AvisoLegal.js
        Cestita.js                    ← asistente IA (backend ✅, manipula cesta ✅)
        CookieBanner.js / Cookies.js  ← ⚠️ posible duplicidad, revisar
        ErrorBoundary.js              ← captura de errores de render ✅
        Footer.js, Landing.js, Navbar.js, Privacidad.js, Terminos.js
        ListaColaborativa.js          ← listas compartidas en tiempo real
        MenuSemanal.js                ← modal menú semanal + recetas + nutricional ✅
        ModalUpgrade.js               ← modal de planes con pago Stripe real ✅
        Sidebar.js                    ← sidebar con historial + estadísticas ✅
        StoreSelector.js              ← selector supermercados compacto con visible flag
        SuperCard.js                  ← tarjeta por supermercado con reference_price
        SyncHeader.js                 ← cabecera de sincronización nube
        ToolBar.js                    ← barra herramientas: menú/recetas/nutricional ✅
        LogosSuper.js                 ← lista de supers con visible: true/false
      hooks/
        usePlan.js                    ← hook de planes (PLANES + FUNCIONALIDADES + límites)
  backend/admin/                      ← panel admin Flask (localhost:5000)
  scrapers/                           ← scripts Python (ver Sección 6)
  scripts/                            ← utilidades varias ⚠️ contiene supabase.exe (93 MB, sacar de git)
  old/                               ← código antiguo (16 MB) — limpiar
  docs/
    CONTEXTO.md                       ← este fichero
  vercel.json                         ← cabeceras de seguridad (CSP, HSTS, etc.) ✅
```

---

## 4. Variables de entorno
### Vercel (producción — confirmar si Stripe sigue en TEST o ya en LIVE)
- REACT_APP_SUPABASE_URL
- REACT_APP_SUPABASE_ANON_KEY
- ANTHROPIC_API_KEY (sin prefijo REACT_APP — es para serverless)
- STRIPE_SECRET_KEY (sk_test_... / sk_live_... según modo)
- STRIPE_WEBHOOK_SECRET (whsec_... del webhook — OJO: cambia entre test y live)
- STRIPE_PRICE_BASIC / STRIPE_PRICE_PREMIUM
- STRIPE_SECRET_KEY_PROD / STRIPE_PRICE_BASIC_PRO / STRIPE_PRICE_PREMIUM_PRO (guardadas para live)
- SUPABASE_SERVICE_KEY (service_role key — solo serverless webhook)
- APP_URL (https://mi-mejor-cesta.vercel.app)
- DISABLE_ESLINT_PLUGIN=true
- REACT_APP_SENTRY_DSN → pendiente de añadir si se activa Sentry

### Local (.env en raíz — está en .gitignore ✅)
- SUPABASE_URL, SUPABASE_KEY (service role)
- ANTHROPIC_API_KEY
- REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY

---

## 5. Arquitectura de BBDD — INAMOVIBLE

### Tablas principales (filas VERIFICADAS 22/07/2026)
| Tabla | Descripción | Filas |
|-------|-------------|-------|
| `productos_catalogo` | Catálogo genérico. Solo admin escribe. | ≈ 9.999 (creció desde 4.173) |
| `categorias_maestras` | 87 categorías fijas. NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados. | ≈ 9.999 filas |
| `precios_mercadona` | IDs ME-xxxx. | ~8.327 |
| `precios_dia` | IDs DI-xxxx. | ~4.786 |
| `precios_alcampo` | IDs AL-xxxx. | 727 |
| `precios_carrefour` | IDs CF-xxxx. | ~7.241 |
| `precios_ahorramas` | IDs AH-xxxx. | poblada |
| `vista_productos` | VIEW que une catálogo + categorías. | — |
| `profiles` | Plan de suscripción por usuario. PK = id (no user_id) | activa |
| `cestas_online` | Cestas guardadas en la nube. | activa |
| `compras` / `compras_detalle` | Historial de compras por usuario. | activas |
| `listas_colaborativas` | Listas compartidas en tiempo real. | — |

### ⚠️ El catálogo creció → Mercadona YA NO cubre el 100%
Al incorporar productos desde Carrefour (`construir_catalogo_desde_carrefour.py`,
`agregar_carrefour_faltantes.py`) el catálogo pasó de 4.173 a ≈ 9.999. Por tanto
la vieja afirmación "Mercadona 100%" es FALSA: ningún super cubre ya todo el catálogo.

### Matches reales por supermercado (VERIFICADO — COUNT sobre productos_match)
| Supermercado | Matches (id_* no nulo) | Marcados revisado=true |
|---|---|---|
| Carrefour | 4.691 | 0 |
| Mercadona | 3.991 | 0 |
| DIA | 1.140 | 0 |
| AhorraMas | 568 | 0 |
| Alcampo | 201 | 0 |
| Hipercor | columna existe, sin datos | 0 |

> 🔴 IMPORTANTE: el flag `revisado` está a 0 en TODAS las filas y la puntuación
> (`id_carrefour_score`, `id_alcampo_score`) está sin poblar (NULL). Los matches
> se insertaron en bloque sin revisión. Ver problema CONFIRMADO en Sección 11.

### Columnas productos_match (VERIFICADO 22/07/2026)
- id, id_catalogo, created_at, revisado
- id_mercadona, id_dia, id_alcampo, id_ahorramas, id_carrefour, id_hipercor, id_lidl, id_aldi
- id_alcampo_score, id_carrefour_score  ← el ALTER TABLE de score YA está hecho
- (id_lidl, id_aldi, id_hipercor existen como columnas pero el frontend NO las consulta)

### Columnas profiles (VERIFICADO)
- id (UUID, PK — igual que auth.users.id)
- plan (text) → 'free' | 'free_reg' | 'basic' | 'premium'
- stripe_id (text), plan_desde (timestamptz), plan_hasta (timestamptz)
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
- Antes de cualquier TRUNCATE verificar backup _old (Supabase free NO tiene backups automáticos)
- RLS: usar siempre auth.uid() = id (NO políticas recursivas sobre profiles — causan error 500)
- Service role key requerida para escrituras de scrapers; puede ser necesario deshabilitar
  RLS en productos_match antes de ejecutar scripts de matching
- El frontend SOLO expone la anon key (protegida por RLS). NUNCA meter service_role en el frontend.

### ⚠️ REGLA SUPABASE — GRANT obligatorio en tablas nuevas (desde oct 2026)
A partir del **30/10/2026**, cualquier tabla nueva en el esquema `public` NO será accesible
vía Data API (supabase-js / PostgREST) sin un GRANT explícito.
**Aplicar siempre este bloque al crear cualquier tabla nueva:**

```sql
-- 1. Permisos explícitos (OBLIGATORIO desde oct 2026)
GRANT SELECT ON public.nueva_tabla TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.nueva_tabla TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.nueva_tabla TO service_role;

-- 2. RLS (como siempre)
ALTER TABLE public.nueva_tabla ENABLE ROW LEVEL SECURITY;

-- 3. Políticas necesarias
CREATE POLICY "..." ON public.nueva_tabla FOR SELECT TO authenticated USING (...);
```

Las tablas EXISTENTES NO se ven afectadas. Revisar Security Advisor antes de octubre.
Referencia: https://github.com/orgs/supabase/discussions/45329

---

## 6. Estado de supermercados (22/07/2026)

### ✅ Integrados en el frontend y con matches
Los 5 están cableados en App.js y con `visible: true` en LogosSuper.js:
Mercadona, DIA, Alcampo, AhorraMas, Carrefour.

| Supermercado | Matches | Estado calidad |
|---|---|---|
| Mercadona | 3.991 | Base fiable (histórico) |
| DIA | 1.140 | Limpiado con IA en su día; revisar |
| Alcampo | 201 | Limpiado con IA en su día; revisar |
| AhorraMas | 568 | ⚠️ Sin verificar (revisado=0) |
| Carrefour | 4.691 | 🔴 CON EMPAREJAMIENTOS MALOS CONFIRMADOS (ver Sección 11) |

### ❌ Sin datos / columna preparada sin poblar
| Supermercado | Estado |
|---|---|
| Hipercor | scraper_hipercor.py falla con HTTP 520 — columna id_hipercor vacía |
| Lidl | columna id_lidl existe, sin datos (SPA dinámica) |
| Eroski | scraper_eroski.py + match_eroski.py existen; sin datos en prod |
| Aldi | columna id_aldi existe; sin tienda online en España |
| La Despensa | scraper_despensa.py existe; sin datos en prod |

---

## 7. Convención de nombres de ficheros
- Scrapers: `scraper_{supermercado}.py`
- Matching: `match_{supermercado}.py`
- Matching con IA: `match_{supermercado}_ia.py`
- SQL de setup: `{supermercado}_setup.sql`
- Scripts de enriquecimiento: `enriquecer_{tabla}.py`
- Scripts de revisión: `revisar_matches_{supermercado}.py`

### Scrapers y scripts de matching presentes en /scrapers
scraper_mercadona.py, scraper_dia.py, scraper_alcampo.py, scraper_carrefour.py,
scraper_ahorramas.py, scraper_hipercor.py, scraper_eroski.py, scraper_despensa.py,
scraper_openprices.py, scraper_carrefour_gemini.py, scraper_mercadona_gemini.py,
match_mercadona.py, match_dia.py, match_alcampo.py, match_alcampo_ia.py,
match_carrefour.py, match_ahorramas.py, match_hipercor.py, match_eroski.py, match_ean.py,
revisar_matches_dia.py, revisar_matches_alcampo.py,
construir_catalogo_desde_carrefour.py, agregar_carrefour_faltantes.py, carrefour_setup.sql

---

## 8. Planes de suscripción (según usePlan.js — VERIFICADO)

| Plan | Precio | Límites |
|---|---|---|
| free (sin registro) | 0€ | 2 supers, 20 productos |
| free_reg (con registro) | 0€ | 2 supers, 20 productos + guardar/compartir listas |
| basic | 2,99€/mes | ilimitado + CESTITA full + historial (3m) + estadísticas basic + escaneo |
| premium | 6,99€/mes | + menú semanal + recetas IA + nutricional + estadísticas full + 30 menús guardados |

### Menús guardados (MAX_MENUS_GUARDADOS)
- free/free_reg/basic = 0 · premium = 30

### IDs Stripe
- prod_UHT4B2MREHH2nE → Plan Básico
- prod_UHT7TEyO5Iv4SC → Plan Premium
- price_1TIu8THqX5envLqIAn8ZDQh0 → Precio Básico (live)
- price_1TIuBcHqX5envLqIBIpWBKTQ → Precio Premium (live)

### ⚠️ Bug latente en usePlan.js
Las claves de FUNCIONALIDADES para CESTITA están mal escritas: `cestivaBasic` /
`cestivaFull` (falta la "t", debería ser *cestita*). Ahora es inocuo porque ningún
componente llama a esas claves, pero si se cablea el gating de CESTITA esperando
`cestitaBasic`, fallará en silencio. Corregir cuando se toque el fichero.

---

## 9. Funcionalidades implementadas ✅

### Frontend
- Comparador con 5 supermercados cableados (Mercadona, DIA, Alcampo, AhorraMas, Carrefour)
- Sidebar con 87 categorías en acordeón, buscador en tiempo real
- Filtro marca blanca y filtro categoría General
- Auth completa (email + Google OAuth)
- Lista colaborativa en tiempo real, Exportar PDF, PWA instalable
- CESTITA — asistente IA vía serverless (/api/cestita), manipula cesta real ✅
- ModalUpgrade con pago Stripe real ✅, usePlan con límites ✅
- SuperCard con reference_price (€/L, €/kg)
- Guardar compras + historial + estadísticas en sidebar
- cestas_online sincronización en nube
- ToolBar: Menú semanal / Sugerir recetas / Nutricional (premium)
- ErrorBoundary + Service Worker (PWA) + cabeceras de seguridad en vercel.json
- Carga de datos paginada (helper cargarTodo) en App.js

### Backend/Scrapers
- scraper_mercadona.py — con reference_price y reference_format
- scraper_carrefour.py — StealthyFetcher + solve_cloudflare=True ✅ (~7.241 productos)
- Amplio arsenal de scrapers/matching (ver Sección 7)

---

## 10. Estado de "cambios pendientes" antiguos — YA RESUELTOS
- ✅ Cambio 1 (props de MenuSemanal): `limiteMenusGuardados` YA está en el destructuring
  de usePlan (App.js ~L69) y se pasa a `<MenuSemanal>` (~L1030). HECHO.
- ✅ Cambio 2 (integrar Carrefour en frontend): HECHO. App.js carga precios_carrefour
  y precios_ahorramas, incluye id_carrefour/id_ahorramas en la query de matches, los
  indexa y los pinta. HECHO (aunque los datos de Carrefour están mal — ver Sección 11).
- ✅ ALTER TABLE id_carrefour_score: la columna YA existe.

---

## 11. Problemas conocidos / Deuda técnica

### 🔴 Críticos (bloquean lanzamiento limpio)
1. **Carrefour muestra precios ERRÓNEOS al usuario.** 4.691 matches con muchos
   emparejamientos cruzados CONFIRMADOS. Ejemplos reales de la BBDD:
   - "Cerveza San Miguel" ↔ "Pan de molde Bimbo"
   - "Jamón cocido lonchas" ↔ "Coca Cola Zero Cereza"
   - "Pañales Dodot talla 4" ↔ "Batido Cola Cao"
   - "Toallitas bebé" ↔ "Hogaza masa madre"
   Puntuación NULL, revisado=0. Como Carrefour está `visible: true`, esto es visible en producción.
   **ACCIÓN:** poner Carrefour en `visible: false` en LogosSuper.js hasta re-ejecutar
   `match_carrefour.py --dry-run` con filtrado por categoría. Aplicar la misma cautela
   a AhorraMas (568 matches sin verificar).
2. **Stripe:** confirmar si sigue en modo TEST. Pasar a producción (keys/price/webhook live)
   es la puerta final de monetización.

### 🟡 Importantes
- Ningún super cubre el 100% del catálogo tras su crecimiento a ≈9.999.
- Sentry instalado pero DESACTIVADO → sin monitorización de errores en producción.
- `@google/generative-ai` dependencia muerta en el bundle → eliminar.
- `tesseract.js` instalado pero OCR sin implementar → implementar o eliminar.
- EAN no capturado por la API de Mercadona en el endpoint de categorías.
- Hipercor: scraper falla con HTTP 520.
- CESTITA no encuentra productos que no estén exactamente en el catálogo.
- Posible duplicidad CookieBanner.js / Cookies.js → revisar.

### 🟢 Menores / Higiene de repo
- `scripts/supabase.exe` (93 MB) commiteado a git → sacar del repo y del historial.
- `frontend/build/` está trackeada en git (26 ficheros) → dejar de trackear + .gitignore.
- Carpeta `old/` (16 MB) → limpiar.
- 8 console.log en frontend/src (no rompe build por DISABLE_ESLINT_PLUGIN).

### 🔵 Infraestructura — Supabase breaking change
- Fecha límite: 30/10/2026 — tablas nuevas sin GRANT explícito dejan de ser accesibles.
- Tablas existentes: NO afectadas. Aplicar bloque GRANT al crear tablas nuevas (Sección 5).
- Revisar Security Advisor en el dashboard antes de octubre.

---

## 12. Comandos útiles
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

# Scrapers / matching (SIEMPRE --dry-run primero)
python scrapers/scraper_mercadona.py
python scrapers/scraper_carrefour.py
python scrapers/match_carrefour.py --dry-run    ← RE-EJECUTAR con filtro por categoría
python scrapers/match_ahorramas.py --dry-run    ← revisar calidad
python scrapers/revisar_matches_dia.py --dry-run
python scrapers/revisar_matches_alcampo.py --dry-run
```

---

## 13. Pendientes por orden de prioridad hacia el 100%

### FASE A — Estabilización ✅ COMPLETADA
### FASE B — Monetización (Stripe checkout+webhook ✅; pasar a LIVE ⏳ pendiente)
### FASE D — Funcionalidades Premium ✅ COMPLETADA

### FASE C — Calidad de datos de supers visibles (PRIORIDAD ACTUAL)
1. ⏳ Ocultar Carrefour (visible:false) hasta arreglar sus matches.
2. ⏳ Re-ejecutar match_carrefour.py --dry-run con filtrado por categoría (objetivo: matches limpios).
3. ⏳ Revisar calidad de AhorraMas (568 matches sin verificar); ocultar si hace falta.
4. ⏳ Volver a poner visible:true cuando estén limpios.

### FASE F — Puerta de lanzamiento
5. ⏳ Confirmar estado de Stripe y pasar a producción (keys/price/webhook live + transacción real de prueba).

### FASE G — Endurecimiento para producción
6. ⏳ Activar Sentry (env var REACT_APP_SENTRY_DSN + descomentar index.js).
7. ⏳ Eliminar dependencia @google/generative-ai; decidir sobre tesseract.js.
8. ⏳ Verificar que GA4 registra eventos en producción.

### FASE H — Higiene de repo (no bloquea lanzamiento)
9. ⏳ Sacar supabase.exe del historial de git; dejar de trackear build/; limpiar old/.

### FASE E — Calidad de datos (mejora continua)
10. Revisar inconsistencias del catálogo.
11. Mejorar matches DIA (1.140) y Alcampo (201).
12. EAN vía endpoint individual Mercadona (opcional, costoso) / vía OpenPrices.
