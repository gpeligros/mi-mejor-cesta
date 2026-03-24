# MI MEJOR CESTA — Contexto del Proyecto

## ⚠️ INSTRUCCIONES PARA CLAUDE
Lee este fichero COMPLETO al inicio de cada sesión antes de responder nada.
Respeta SIEMPRE las convenciones de nombres, arquitectura y reglas de oro definidas aquí.
NUNCA propongas cambiar la arquitectura de BBDD. NUNCA cambies nombres de ficheros sin preguntar.

---

## 1. Qué es el proyecto
App web PWA de comparación de precios de supermercados españoles.
URL producción: https://mi-mejor-cesta.vercel.app
Repositorio: https://github.com/gpeligros/mi-mejor-cesta

## 2. Stack tecnológico
- **Frontend**: React 18 + Tailwind CSS — desplegado en Vercel
- **Base de datos**: Supabase (PostgreSQL) — scpuriaofisssalsbzqv.supabase.co
- **Autenticación**: Supabase Auth (email/contraseña + Google OAuth)
- **Backend admin**: Flask (Python) — local / localhost:5000
- **Scrapers**: Python 3 — carpeta /scrapers
- **Deploy**: Vercel — git push a main despliega automáticamente
- **IA (CESTITA)**: Anthropic Claude API (ANTHROPIC_API_KEY en .env)

## 3. Estructura de carpetas
```
mi-mejor-cesta/
  frontend/          ← App React (src/App.js es el principal)
  backend/admin/     ← Panel admin Flask — localhost:5000
  scrapers/          ← Scripts Python de obtención de precios
  scripts/           ← SQLs y scripts de mantenimiento BD
  docs/              ← Documentación del proyecto
```

## 4. Variables de entorno (.env en /scrapers)
- SUPABASE_URL
- SUPABASE_KEY (service role — nunca a Git)
- ANTHROPIC_API_KEY
- REACT_APP_SUPABASE_URL (frontend)
- REACT_APP_SUPABASE_ANON_KEY (frontend)

## 5. Arquitectura de BBDD — INAMOVIBLE
Patrón: catálogo genérico + precios por supermercado + tabla puente de matches.
**NUNCA proponer cambiar esta arquitectura.**

### Tablas principales
| Tabla | Descripción |
|-------|-------------|
| `productos_catalogo` | Catálogo genérico. IDs CAT-xxxx. Solo admin escribe. |
| `categorias_maestras` | 87 categorías fijas. NUNCA modificar. |
| `productos_match` | Tabla puente CAT↔supermercados. Una fila por producto. |
| `precios_mercadona` | IDs ME-xxxx. Solo scraper escribe. |
| `precios_dia` | IDs DI-xxxx. Solo scraper escribe. |
| `precios_alcampo` | IDs AL-xxxx. Solo scraper escribe. |
| `vista_productos` | VIEW que une productos_catalogo + categorias_maestras. |
| `listas_colaborativas` | Listas compartidas en tiempo real. |
| `cestas_online` | Cestas guardadas por usuario autenticado. |

### Columnas de productos_match
id_catalogo, id_mercadona, id_dia, id_alcampo, id_alcampo_score,
id_aldi, id_carrefour, id_lidl, revisado, created_at

### Reglas de oro — NUNCA violar
- NUNCA scrapers escriben en productos_catalogo ni categorias_maestras
- NUNCA borrar CAT-xxxx, solo desactivar con activo=false
- NUNCA subir .env a Git
- id_api es el puente entre nuestro sistema y el supermercado — no modificar
- Antes de cualquier TRUNCATE verificar que existe tabla _old de backup

## 6. Convención de nombres de ficheros
- Scrapers: `scraper_{supermercado}.py` (ej: scraper_mercadona.py)
- Scripts de matching: `match_{supermercado}.py` (ej: match_alcampo.py)
- Scripts de matching con IA: `match_{supermercado}_ia.py`
- SQL de setup: `{supermercado}_setup.sql`
- **NUNCA cambiar esta convención sin preguntar**

## 7. Estado de supermercados

### ✅ Funcionando en producción
| Supermercado | Tabla | Prefijo | Productos | Match |
|---|---|---|---|---|
| Mercadona | precios_mercadona | ME- | ~4.173 | 100% (4.173) |
| DIA | precios_dia | DI- | ~4.786 | 24% (986) |

### ⚙️ Scraper listo, matching pendiente
| Supermercado | Tabla | Prefijo | Productos | Match |
|---|---|---|---|---|
| Alcampo | precios_alcampo | AL- | 727 | 1 producto |

### ❌ Pendientes
| Supermercado | Bloqueador |
|---|---|
| Carrefour | SPA React + Cloudflare — necesita Selenium o datos comprados |
| Lidl | SPA Angular — necesita Selenium o datos comprados |
| Eroski | SPA con JS — scraper HTML no funciona |
| AhorraMas | Subcategorías no descubiertas |
| Hipercor | Pendiente validación |
| La Despensa | Pendiente validación |

### Proveedores de datos contactados
- DataMarket.es — email enviado, sin respuesta aún
- Mercadinámica — email enviado, sin respuesta aún

## 8. Matching de productos — cómo funciona
- El matching de Mercadona se hizo **manualmente desde el panel admin Flask**
- Los id_api de Alcampo son IDs internos (ej: 524477) — NO son EAN
- Los id_api de Mercadona son IDs internos (ej: 10005) — NO son EAN
- El script `match_alcampo.py` (similitud de nombres) solo encontró 5 matches — inviable
- El script `match_alcampo_ia.py` (Claude API) encontró buenos matches pero se quedó sin créditos en el lote 30/140
- **Pendiente**: recargar créditos en console.anthropic.com (5$ suficiente) y relanzar

## 9. Funcionalidades implementadas en la app
- Comparador de precios con 4.173 productos
- Sidebar con 87 categorías/subcategorías en acordeón
- Buscador en tiempo real
- Toggle marca blanca (Hacendado, etc.)
- SuperCard por supermercado con precio mínimo en verde
- Autenticación completa (email + Google OAuth)
- Lista colaborativa en tiempo real (Supabase Realtime)
- Exportar PDF con la cesta
- PWA instalable en móvil
- Panel admin Flask (localhost:5000)

## 10. Planes de suscripción (modelo freemium)
| Plan | Precio | Funcionalidades clave |
|---|---|---|
| Gratuito sin registro | 0€ | 2 supermercados, 20 productos máx |
| Gratuito con registro | 0€ | + guardar 1 lista, compartir, PDF |
| Básico | 2,99€/mes | Todo ilimitado, alertas precio, escaneo lista, CESTITA avanzado |
| Premium | 6,99€/mes | + estadísticas, recetas IA, datos nutricionales, CESTITA completo |

## 11. CESTITA — Asistente IA
- Nombre: CESTITA
- Modelo: Anthropic Claude API
- Plan mínimo: Básico (2,99€) funcionalidad avanzada
- Plan Premium (6,99€): acceso completo
- Plan gratuito: consultas básicas
- Estado: pendiente de desarrollo

## 12. Comandos útiles
```bash
# Ejecutar en local
cd frontend && npm start

# Deploy a Vercel
git add . && git commit -m "descripción" && git push origin main

# Build para verificar antes de push
cd frontend && npm run build

# Panel admin
cd backend/admin && python app.py

# Scrapers
python scrapers/scraper_mercadona.py
python scrapers/scraper_alcampo.py --dry-run

# Matching con IA (necesita créditos Anthropic)
python scrapers/match_alcampo_ia.py --dry-run
python scrapers/match_alcampo_ia.py
```

## 13. Pendientes prioritarios
1. Recargar créditos Anthropic y ejecutar match_alcampo_ia.py → Alcampo en la app
2. Revisar 1.339 matches DIA dudosos desde panel admin
3. Respuesta de DataMarket/Mercadinámica para Carrefour y Lidl
4. Desarrollar CESTITA (chat IA integrado en el frontend)
5. Implementar planes de suscripción con Stripe
