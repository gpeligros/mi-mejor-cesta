# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 05/04/2026)

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
      cestita.js                      ← Serverless Function proxy Anthropic API ✅
      stripe-checkout.js              ← Serverless Function Stripe checkout ✅
      stripe-webhook.js               ← Serverless Function Stripe webhook ✅
    src/
      App.js                          ← componente principal
      components/
        Cestita.js                    ← asistente IA (backend ✅, manipula cesta ✅)
        MenuSemanal.js                ← modal menú semanal + recetas + nutricional ✅
        ModalUpgrade.js               ← modal de planes con pago Stripe real ✅
        Sidebar.js                    ← sidebar con historial + estadísticas ✅
        SuperCard.js                  ← tarjeta por supermercado con reference_price
        StoreSelector.js              ← selector supermercados compacto con visible flag
        ToolBar.js                    ← barra herramientas: menú/recetas/nutricional ✅
        LogosSuper.js                 ← lista de supers con visible: true/false
        Navbar.js, Footer.js...
      hooks/
        usePlan.js                    ← hook de planes (funcionando)
  backend/admin/                      ← panel admin Flask (localhost:5000)
  scrapers/                           ← scripts Python
  docs/
    CONTEXTO.md                       ← este fichero
```

---

## 4. Variables de entorno
### Vercel (producción — actualmente en TEST hasta ir a live)
- REACT_APP_SUPABASE_URL
- REACT_APP_SUPABASE_ANON_KEY
- ANTHROPIC_API_KEY (sin prefijo REACT_APP — es para serverless)
- STRIPE_SECRET_KEY (sk_test_... hasta pasar a producción)
- STRIPE_WEBHOOK_SECRET (whsec_... del webhook de Stripe)
- STRIPE_PRICE_BASIC (price_test_... del plan básico)
- STRIPE_PRICE_PREMIUM (price_test_... del plan premium)
- STRIPE_SECRET_KEY_PROD (sk_live_... guardada para cuando se active producción)
- STRIPE_PRICE_BASIC_PRO (price_live_... guardada para producción)
- STRIPE_PRICE_PREMIUM_PRO (price_live_... guardada para producción)
- SUPABASE_SERVICE_KEY (service_role key — solo para serverless webhook)
- APP_URL (https://mi-mejor-cesta.vercel.app)
- DISABLE_ESLINT_PLUGIN=true

### Local (.env en raíz)
- SUPABASE_URL, SUPABASE_KEY (service role)
- ANTHROPIC_API_KEY
- REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY

---

## 5. Arquitectura de BBDD — INAMOVIBLE

### Tablas principales
| Tabla | Descripción | Filas |
|-------|-------------|-------|
| `productos_catalogo` | Catálogo genérico. Solo admin escribe. | 4.173 |
| `categorias_maestras` | 87 categorías fijas. NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados. | 4.173 |
| `precios_mercadona` | IDs ME-xxxx. | ~8.327 |
| `precios_dia` | IDs DI-xxxx. | ~4.786 |
| `precios_alcampo` | IDs AL-xxxx. | 727 |
| `vista_productos` | VIEW que une catálogo + categorías. | — |
| `profiles` | Plan de suscripción por usuario. PK = id (no user_id) | trigger creado |
| `cestas_online` | Cestas guardadas en la nube. | creada |
| `compras` | Historial de compras por usuario. | activa |
| `compras_detalle` | Detalle de productos por compra. | activa |
| `listas_colaborativas` | Listas compartidas en tiempo real. | — |

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

### ✅ En producción con datos limpios
| Supermercado | Tabla | Productos | Matches válidos |
|---|---|---|---|
| Mercadona | precios_mercadona | ~8.327 | 4.173 (100%) |
| DIA | precios_dia | ~4.786 | 608 (limpiados con IA) |
| Alcampo | precios_alcampo | 727 | 121 (limpiados con IA) |

### ❌ Tablas creadas sin datos
precios_ahorramas, precios_aldi, precios_carrefour, precios_despensa,
precios_eroski, precios_hipercor, precios_lidl

### ❌ Pendientes de scraper
| Supermercado | Bloqueador |
|---|---|
| Carrefour | SPA + Cloudflare |
| Lidl | SPA |
| Eroski | SPA con JS |
| Hipercor | API pública disponible — pendiente scraper |
| Aldi | Sin tienda online en España |
| AhorraMas, La Despensa | Sin scraper |

---

## 7. Convención de nombres de ficheros
- Scrapers: `scraper_{supermercado}.py`
- Matching: `match_{supermercado}.py`
- Matching con IA: `match_{supermercado}_ia.py`
- SQL de setup: `{supermercado}_setup.sql`
- Scripts de enriquecimiento: `enriquecer_{tabla}.py`
- Scripts de revisión: `revisar_matches_{supermercado}.py`

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
- Comparador con 4.173 productos (Mercadona 100%, DIA y Alcampo parciales)
- Sidebar con 87 categorías en acordeón
- Buscador en tiempo real
- Filtro marca blanca (oculta productos marca_blanca del catálogo)
- Filtro categoría General (productos sin categoría no aparecen)
- Auth completa (email + Google OAuth)
- Lista colaborativa en tiempo real
- Exportar PDF
- PWA instalable (con screenshots en manifest)
- CESTITA — asistente IA vía Vercel Serverless (/api/cestita) ✅
- CESTITA — manipula cesta real (añadir/quitar/vaciar) ✅
- ModalUpgrade — modal de planes con pago Stripe real ✅
- usePlan — límites de plan funcionando
- StoreSelector compacto con logos y flag visible
- SuperCard con reference_price (€/L, €/kg)
- Guardar compras realizadas con detalle
- Historial de compras en sidebar (🧾 MIS COMPRAS)
- Estadísticas de gasto en sidebar (📊 MIS ESTADÍSTICAS) — basic+
- cestas_online sincronización en nube
- ToolBar con 3 botones: Menú semanal / Sugerir recetas / Nutricional
- MenuSemanal — generador de menú 7 días con IA — premium
- Sugerir recetas — basado en cesta actual — premium
- Análisis nutricional de la cesta con IA — premium
- Stripe checkout + webhook → actualiza profiles en Supabase ✅

### Backend/Scrapers
- scraper_mercadona.py — con reference_price y reference_format
- enriquecer_catalogo.py — tipo, formato, nombre_normalizado, marca
- revisar_matches_dia.py — revisión con IA
- revisar_matches_alcampo.py — revisión con IA
- match_alcampo.py v3 — fuzzy matching mejorado (pendiente ejecutar)

---

## 10. Problemas conocidos / Deuda técnica

### 🔴 Críticos
- Stripe en modo TEST — pendiente pasar a producción (cambiar keys live)

### 🟡 Importantes
- EAN no capturado — API Mercadona no lo expone en endpoint de categorías
- Matches DIA al 24% del catálogo (608/4173)
- Matches Alcampo al 3% del catálogo (121/4173)
- CESTITA no puede buscar productos que no están en el catálogo exactamente
- Google OAuth abre ventana pequeña al volver del login (comportamiento Chrome, sin solución limpia)
- Errores/inconsistencias en el catálogo de productos — pendiente revisión

### 🟡 Pendiente implementar
- CESTITA: sistema de acciones estructuradas mejorado (busca por palabras clave, no solo nombre exacto)
- Alertas de precio (requiere tabla historial_precios — no existe aún)
- Datos nutricionales en BBDD (ahora son estimaciones IA en tiempo real)

### 🟢 Menores
- Warning icono manifest PWA — pendiente verificar si sigue tras screenshots
- Google Analytics configurado pero ID de GA4 es placeholder en index.html

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
python scrapers/enriquecer_catalogo.py --dry-run
python scrapers/revisar_matches_dia.py --dry-run
python scrapers/revisar_matches_alcampo.py --dry-run
python scrapers/match_alcampo.py --dry-run
```

---

## 12. Pendientes por orden de prioridad hacia el 100%

### FASE A — Estabilización ✅ COMPLETADA
1. ✅ Limpiar console.logs de debug
2. ✅ Mover CESTITA al backend
3. ✅ Screenshots PWA manifest

### FASE B — Monetización ✅ COMPLETADA (en test)
4. ✅ Stripe checkout + webhook
5. ✅ Webhook Stripe → actualizar profiles en Supabase
6. ⏳ Pasar Stripe a producción (cambiar keys test → live) — LO ÚLTIMO

### FASE C — Más supermercados
7. Scraper Hipercor (API pública El Corte Inglés)
8. Scraper AhorraMas
9. Scraper La Despensa
10. Intentar Carrefour/Lidl con datos externos

### FASE D — Funcionalidades Premium ✅ COMPLETADA
11. ✅ Generador de menú semanal con IA
12. ✅ Estadísticas de gasto del usuario
13. ✅ Datos nutricionales de la cesta (estimaciones IA)
14. ✅ CESTITA manipula la cesta real
15. ⏳ Alertas de subida/bajada de precio (requiere historial_precios)

### FASE E — Calidad de datos
16. Revisar errores e inconsistencias en catálogo de productos
17. Mejorar matches DIA (608 → objetivo 2.000+)
18. Mejorar matches Alcampo (121 → objetivo 500+)
19. EAN vía endpoint individual Mercadona (opcional, costoso)
