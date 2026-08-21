# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 01/04/2026)

## ⚠️ INSTRUCCIONES PARA CLAUDE
Lee este fichero COMPLETO antes de responder nada.
Respeta SIEMPRE las convenciones de nombres, arquitectura y reglas de oro.
NUNCA propongas cambiar la arquitectura de BBDD sin consultar.
NUNCA cambies nombres de ficheros sin preguntar.
NUNCA empieces a escribir código sin entender primero el estado real.
SIEMPRE pide los ficheros actuales antes de modificarlos.
NUNCA uses sed en PowerShell — usar python3 para manipular ficheros.

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
- IA (CESTITA): Anthropic Claude API (REACT_APP_ANTHROPIC_API_KEY en .env frontend)
- Deploy: Vercel — git push a main despliega automáticamente
- DISABLE_ESLINT_PLUGIN=true en variables de entorno de Vercel

---

## 3. Estructura de carpetas
```
mi-mejor-cesta/
  frontend/src/
    App.js                          ← componente principal
    components/
      Cestita.js                    ← asistente IA (funcionando, key en frontend — pendiente mover)
      ModalUpgrade.js               ← modal de planes
      Sidebar.js                    ← sidebar con historial de compras
      SuperCard.js                  ← tarjeta por supermercado con reference_price
      StoreSelector.js              ← selector supermercados compacto con visible flag
      LogosSuper.js                 ← lista de supers con visible: true/false
      Navbar.js, Footer.js...
    hooks/
      usePlan.js                    ← hook de planes (funcionando)
  backend/admin/                    ← panel admin Flask (localhost:5000)
  scrapers/                         ← scripts Python
  docs/
    CONTEXTO.md                     ← fichero de contexto anterior
```

---

## 4. Variables de entorno
### Vercel (producción)
- REACT_APP_SUPABASE_URL
- REACT_APP_SUPABASE_ANON_KEY
- REACT_APP_ANTHROPIC_API_KEY
- DISABLE_ESLINT_PLUGIN=true

### Local (.env en raíz)
- SUPABASE_URL, SUPABASE_KEY (service role)
- ANTHROPIC_API_KEY
- REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY
- REACT_APP_ANTHROPIC_API_KEY

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
| `profiles` | Plan de suscripción por usuario. | trigger creado |
| `cestas_online` | Cestas guardadas en la nube. | creada |
| `compras` | Historial de compras por usuario. | activa |
| `compras_detalle` | Detalle de productos por compra. | activa |
| `listas_colaborativas` | Listas compartidas en tiempo real. | — |

### Columnas productos_catalogo (VERIFICADO)
- id (text, PK formato CAT-xxxx)
- nombre_generico (text)
- marca (text) — rellena con enriquecimiento IA
- imagen (text)
- orden (integer)
- created_at (timestamptz)
- activo (boolean)
- id_categoria (integer, FK a categorias_maestra)
- tipo (text) → 'marca_fabricante' | 'marca_blanca' ✅ NUEVO
- formato (text) ✅ NUEVO
- nombre_normalizado (text) ✅ NUEVO
- ean (text) ✅ NUEVO (vacío — API Mercadona no lo expone en categorías)

### Columnas precios_mercadona (VERIFICADO)
- id, id_api, nombre_comercial, precio, precio_unidad
- marca, url, imagen, disponible, actualizado
- reference_price (numeric) ✅ NUEVO — precio €/L o €/kg
- reference_format (text) ✅ NUEVO — "L", "kg", "ud"
- ean (text) ✅ NUEVO (vacío — API no lo expone)

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
| Hipercor | Sin scraper |
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
| Básico | 2,99€/mes | Todo ilimitado + CESTITA + historial | ⏳ Stripe pendiente |
| Premium | 6,99€/mes | + menú semanal IA + nutricional | ⏳ Stripe pendiente |

### Funcionalidades por plan (usePlan.js)
- maxSupers: free=2, basic/premium=999
- maxProductos: free=20, basic/premium=999
- CESTITA básico: todos los planes
- CESTITA avanzado: basic+
- guardarCompras: basic+
- historialCompras: basic+ (3 meses), premium (ilimitado)
- menuSemanal: premium
- estadísticasFull: premium
- nutricional: premium

---

## 9. Funcionalidades implementadas ✅

### Frontend
- Comparador con 4.173 productos (Mercadona 100%, DIA y Alcampo parciales)
- Sidebar con 87 categorías en acordeón
- Buscador en tiempo real
- Filtro marca blanca (oculta productos marca_blanca del catálogo)
- Filtro categoría General (productos sin categoría no aparecen)
- Toggle marca blanca/fabricante en sidebar ❌ ELIMINADO (correcto — no debe aparecer)
- Auth completa (email + Google OAuth)
- Lista colaborativa en tiempo real
- Exportar PDF
- PWA instalable
- CESTITA — asistente IA (key en frontend — ⚠️ pendiente mover al backend)
- ModalUpgrade — modal de planes
- usePlan — límites de plan funcionando (2 supers, 20 productos para free)
- StoreSelector compacto con logos y flag visible
- SuperCard con reference_price (€/L, €/kg) bajo el precio de Mercadona
- Guardar compras realizadas con detalle
- Historial de compras en sidebar (🧾 MIS COMPRAS)
- cestas_online sincronización en nube
- Trigger en profiles para nuevos usuarios

### Backend/Scrapers
- scraper_mercadona.py — con reference_price y reference_format
- enriquecer_catalogo.py — tipo, formato, nombre_normalizado, marca
- revisar_matches_dia.py — revisión con IA
- revisar_matches_alcampo.py — revisión con IA

---

## 10. Problemas conocidos / Deuda técnica

### 🔴 Críticos
- CESTITA usa REACT_APP_ANTHROPIC_API_KEY expuesta en frontend → mover al backend

### 🟡 Importantes
- EAN no capturado — API Mercadona no lo expone en endpoint de categorías
  (sí está en endpoint individual /api/products/{id}/ pero requeriría 8.327 llamadas extra)
- Matches DIA al 24% del catálogo (608/4173) — muchos productos sin precio en DIA
- Matches Alcampo al 3% del catálogo (121/4173) — muy pocos productos

### 🟢 Menores
- console.log('PLAN DEBUG:...) en App.js — limpiar antes de producción final
- Warning icono manifest PWA en Vercel
- Los logs de cargarHistorial en Sidebar.js — limpiar antes de producción

---

## 11. Comandos útiles
```bash
# Local
cd frontend && npm start

# Deploy
git add . && git commit -m "descripción" && git push origin main

# Panel admin
cd backend/admin && python app.py

# Scrapers
python scrapers/scraper_mercadona.py
python scrapers/enriquecer_catalogo.py --dry-run
python scrapers/revisar_matches_dia.py --dry-run
python scrapers/revisar_matches_alcampo.py --dry-run
```

---

## 12. Pendientes por orden de prioridad hacia el 100%

### FASE A — Estabilización (antes de abrir al público)
1. Limpiar console.logs de debug en App.js y Sidebar.js
2. Mover CESTITA al backend (seguridad API key)
3. Fix warning icono manifest PWA

### FASE B — Monetización
4. Integrar Stripe (Básico 2,99€ y Premium 6,99€)
5. Webhook Stripe → actualizar profiles en Supabase
6. Validar límites de plan con Stripe (historial 3 meses vs ilimitado)

### FASE C — Más supermercados
7. Scraper Hipercor (El Corte Inglés tiene API pública)
8. Scraper AhorraMas
9. Scraper La Despensa
10. Intentar Carrefour/Lidl con datos externos o acuerdo comercial

### FASE D — Funcionalidades Premium
11. Generador de menú semanal con IA
12. Estadísticas de gasto del usuario
13. Datos nutricionales de la cesta
14. Alertas de subida/bajada de precio

### FASE E — Calidad de datos
15. Mejorar matches DIA (608 → objetivo 2.000+)
16. Mejorar matches Alcampo (121 → objetivo 500+)
17. EAN vía endpoint individual Mercadona (opcional, costoso en llamadas)

