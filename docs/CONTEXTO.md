# MI MEJOR CESTA — Contexto del Proyecto

## ⚠️ INSTRUCCIONES PARA CLAUDE
Lee este fichero COMPLETO antes de responder nada.
Respeta SIEMPRE las convenciones de nombres, arquitectura y reglas de oro.
NUNCA propongas cambiar la arquitectura de BBDD sin consultar.
NUNCA cambies nombres de ficheros sin preguntar.
NUNCA empieces a escribir código sin entender primero el estado real.

---

## 1. Qué es el proyecto
App web PWA de comparación de precios de supermercados españoles.
URL producción: https://mi-mejor-cesta.vercel.app
Repositorio: https://github.com/gpeligros/mi-mejor-cesta

## 2. Stack tecnológico
- Frontend: React 18 + Tailwind CSS — Vercel
- Base de datos: Supabase (PostgreSQL) — scpuriaofisssalsbzqv.supabase.co
- Autenticación: Supabase Auth (email + Google OAuth)
- Backend admin: Flask (Python) — local / localhost:5000
- Scrapers: Python 3 — carpeta /scrapers
- IA (CESTITA): Anthropic Claude API (ANTHROPIC_API_KEY en .env)
- Deploy: Vercel — git push a main despliega automáticamente

## 3. Estructura de carpetas
```
mi-mejor-cesta/
  frontend/src/
    App.js                          ← componente principal
    components/
      Cestita.js                    ← asistente IA (funcionando)
      ModalUpgrade.js               ← modal de planes (integrado)
      Sidebar.js, SuperCard.js...   ← componentes principales
    hooks/
      usePlan.js                    ← hook de planes (integrado, pendiente validar)
  backend/admin/                    ← panel admin Flask (localhost:5000)
  scrapers/                         ← scripts Python
  docs/
    CONTEXTO.md                     ← este fichero
    planes_funcionalidades.md       ← tabla de planes
    BBDD_Diseño_MiMejorCesta.docx  ← diseño de BBDD
```

## 4. Variables de entorno
- SUPABASE_URL, SUPABASE_KEY (service role)
- ANTHROPIC_API_KEY
- REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY
- REACT_APP_ANTHROPIC_API_KEY (para CESTITA en frontend)

## 5. Arquitectura de BBDD — INAMOVIBLE
Patrón: catálogo genérico + precios por supermercado + tabla puente.

### Tablas principales
| Tabla | Descripción | Filas |
|-------|-------------|-------|
| `productos_catalogo` | Catálogo genérico. Solo admin escribe. | 4.173 |
| `categorias_maestra` | 87 categorías fijas. NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados. | 4.173 |
| `precios_mercadona` | IDs ME-xxxx. Solo scraper escribe. | ~8.215 |
| `precios_dia` | IDs DI-xxxx. Solo scraper escribe. | ~4.786 |
| `precios_alcampo` | IDs AL-xxxx. Solo scraper escribe. | 727 |
| `vista_productos` | VIEW que une catálogo + categorías. | — |
| `profiles` | Plan de suscripción por usuario. | creada |
| `cestas_online` | Cestas guardadas en la nube. | — |
| `listas_colaborativas` | Listas compartidas en tiempo real. | — |

### Columnas reales de productos_catalogo (VERIFICADO)
- id (text, PK formato CAT-xxxx)
- nombre_generico (text)
- marca (text) — actualmente NULL en todos los productos
- imagen (text)
- orden (integer)
- created_at (timestamptz)
- activo (boolean)
- id_categoria (integer, FK a categorias_maestra)

### ⚠️ IMPORTANTE: lo que NO existe todavía
- NO hay campo `formato` en productos_catalogo
- NO hay campo `tipo` (marca_fabricante / marca_blanca)
- NO hay campo `ean`
- NO hay campo `nombre_normalizado`

### Columnas de productos_match
id_catalogo, id_mercadona, id_dia, id_alcampo, id_alcampo_score,
id_aldi, id_carrefour, id_lidl, revisado, created_at

### Reglas de oro
- NUNCA scrapers escriben en productos_catalogo ni categorias_maestra
- NUNCA borrar CAT-xxxx, solo desactivar con activo=false
- NUNCA subir .env a Git
- Antes de cualquier TRUNCATE verificar backup _old

## 6. Convención de nombres de ficheros
- Scrapers: `scraper_{supermercado}.py`
- Matching: `match_{supermercado}.py`
- Matching con IA: `match_{supermercado}_ia.py`
- SQL de setup: `{supermercado}_setup.sql`

## 7. Estado de supermercados

### ✅ En producción
| Supermercado | Tabla | Productos | Match |
|---|---|---|---|
| Mercadona | precios_mercadona | ~8.215 | 4.173 (100%) |
| DIA | precios_dia | ~4.786 | 986 (24%) — muchos incorrectos |
| Alcampo | precios_alcampo | 727 | 207 (28%) |

### ❌ Pendientes
| Supermercado | Bloqueador |
|---|---|
| Carrefour | SPA + Cloudflare — necesita datos externos |
| Lidl | SPA — necesita datos externos |
| Eroski | SPA con JS |
| AhorraMas, Hipercor, La Despensa | Pendientes |
| Aldi | Sin tienda online en España |

### Proveedores contactados (sin respuesta)
- DataMarket.es — email enviado
- Mercadinámica — email enviado

## 8. Problemas críticos identificados (PRIORIDAD MÁXIMA)

### Problema 1 — Catálogo basado en Mercadona
El catálogo se creó exportando productos de Mercadona y limpiando los nombres.
Los nombres_generico son específicos de Mercadona, no verdaderamente genéricos.
El campo marca está NULL en los 4.173 productos.
No se puede distinguir si un producto es marca blanca o de fabricante.

### Problema 2 — Matches DIA incorrectos
De 986 matches con DIA, la mayoría son incorrectos.
Ejemplos reales verificados:
- "Aceite de girasol 0,2º" Mercadona 8,45€ ↔ DIA "Aceite girasol Diasol 1L" 1,75€ (distintos formatos)
- "Chocolate blanco" 1,05€ ↔ DIA "Galletas rellenas chocolate blanco Príncipe" 2,75€ (¡distintos productos!)
- "Yogur líquido fresa" 2€ ↔ DIA "Actimel fresa plátano pack 6" 3,99€ (distintos)
Solo 1 de 15 analizados era correcto: Mayonesa Hellmann's.

### Problema 3 — Sin normalización de formato
No hay campo formato. Se comparan productos de distinto volumen/peso.
Una comparativa honesta solo puede hacerse entre el mismo formato.

## 9. PLAN APROBADO — Reconstrucción del catálogo

### Fase 1 — Enriquecer productos_catalogo con IA (SIGUIENTE PASO)
Añadir columnas SIN borrar nada:
- `tipo` → 'marca_fabricante' o 'marca_blanca'
- `formato` → "33cl", "1L", "500g" extraído del nombre
- `nombre_normalizado` → nombre limpio y neutro

Script con Claude API analiza 4.173 nombres y rellena automáticamente.
Coste estimado: ~1$ de API.
⚠️ PENDIENTE: ejecutar estas queries antes de escribir el script:
```sql
SELECT c.categoria, c.subcategoria, COUNT(*) as productos
FROM vista_productos c
GROUP BY c.categoria, c.subcategoria
ORDER BY c.categoria, productos DESC LIMIT 30;

SELECT id, nombre_generico, id_categoria
FROM productos_catalogo ORDER BY id_categoria, id LIMIT 50;
```

### Fase 2 — Revisar matches DIA
Con catálogo enriquecido, identificar matches incorrectos automáticamente.
Revisar desde panel admin. Corregir los 986.

### Fase 3 — Matching con EAN
Añadir campo `ean` al catálogo.
Mercadona ya devuelve EAN en su API.
Matching automático perfecto para marcas de fabricante.
Marca blanca: matching por tipo + formato + categoría.

### Fase 4 — Scrapers con EAN
Modificar scrapers para capturar EAN.
Matching instantáneo y sin errores.

## 10. Lógica de tipos de producto (CLAVE)
**Marca de fabricante** (Coca-Cola, Hellmann's, Mahou...):
- Mismo producto físico en varios supermercados
- Mismo EAN en todos → matching perfecto
- Se compara directamente: precio en Mercadona vs Carrefour vs DIA

**Marca blanca** (Hacendado, DIA Láctea, Aliada...):
- Cada supermercado tiene su versión propia
- Sin EAN común
- Se compara por: categoría + formato + tipo equivalente
- Ejemplo: "Leche semidesnatada 1L" → Hacendado vs DIA Láctea vs Alteza

## 11. Funcionalidades implementadas
- Comparador con 4.173 productos (Mercadona + DIA parcial + Alcampo parcial)
- Sidebar con 87 categorías en acordeón
- Buscador en tiempo real, toggle marca blanca
- Auth completa (email + Google OAuth)
- Lista colaborativa en tiempo real
- Exportar PDF
- PWA instalable
- Panel admin Flask (localhost:5000)
- CESTITA — asistente IA funcionando (requiere créditos Anthropic)
- ModalUpgrade — modal de planes integrado (límites pendientes de validar)
- Tabla profiles — plan de suscripción por usuario

## 12. Planes de suscripción
| Plan | Precio | Clave |
|---|---|---|
| Gratuito sin registro | 0€ | 2 supers, 20 productos máx |
| Gratuito con registro | 0€ | + guardar 1 lista, PDF |
| Básico | 2,99€/mes | Todo ilimitado, alertas, CESTITA avanzado |
| Premium | 6,99€/mes | + estadísticas, menús IA, nutricional |

## 13. Comandos útiles
```bash
# Local
cd frontend && npm start

# Deploy
git add . && git commit -m "descripción" && git push origin main

# Panel admin
cd backend/admin && python app.py

# Matching Alcampo con IA (necesita créditos Anthropic)
python scrapers/match_alcampo_ia.py --dry-run
python scrapers/match_alcampo_ia.py

# Enriquecimiento catálogo (PENDIENTE — Fase 1)
python scrapers/enriquecer_catalogo.py --dry-run
```

## 14. Pendientes por orden de prioridad
1. Ejecutar queries de diagnóstico (ver sección Fase 1) antes de escribir scripts
2. Escribir y ejecutar script enriquecer_catalogo.py (Fase 1)
3. Revisar matches DIA incorrectos (Fase 2)
4. Añadir EAN al catálogo y scrapers (Fase 3 y 4)
5. Integrar Stripe para monetización
6. Resolver límites de plan (usePlan.js — pendiente de validar en producción)
7. Guardar compras realizadas
8. Generador de menú semanal (Premium)
