# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 10/08/2026)

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

## 0. ⚠️ ESTADO CRÍTICO — LEER PRIMERO

**Fase 5 EJECUTADA en producción el 20/08/2026.** Catálogo: 16.727 productos, **2.104 comparando precio en ≥2 supers** (2,5x respecto a la reconstrucción del 10/08). Reemplaza la versión del 10/08/2026, que ya quedó obsoleta tras los arreglos de esta sesión.

**Arreglos aplicados hoy (20/08/2026) en el pipeline de reconstrucción:**
1. **Equivalencia numeral↔palabra** (`unificar_numeros()` en `normalizar_productos.py`, `agrupar_productos.py`, `clasificar_categoria.py`) — "Mahou 5 Estrellas" y "Mahou Cinco Estrellas" ahora se tratan como el mismo texto. Bug detectado por David con capturas reales de la app.
2. **Vocabulario de marcas aprendido del propio catálogo** (`construir_vocabulario_marcas()` en `normalizar_productos.py`) — Mercadona tenía el campo `marca` vacío en ~50% de sus productos de marca real (Danone, Puleva, Dove, Milka confirmado con datos reales), rompiendo el matching cross-super. Se rescatan 3.000+ filas por sesión comparando contra marcas ya detectadas en el resto del catálogo. Exclusión de palabras genéricas (colores, "original", "especial"...) para evitar falsos positivos.
3. **Comparación de marca blanca por descripción** (`detectar_marcas_genericas()`, `clave_bucket()`, `texto_comparacion()` en `agrupar_productos.py`) — petición explícita de David: Hacendado, Dia Vegecampo, Carrefour Classic, Alipende... ahora se comparan entre sí por tipo de producto, no se quedan aislados por fabricante. Es el cambio de mayor impacto del día (+1.246 clusters comparando). Una marca se considera "genérica" solo si (a) aparece en un único supermercado en todo el catálogo Y (b) está en una lista de marcas blancas conocidas o contiene el nombre de un supermercado — el filtro (b) se añadió tras detectar que marcas reales infrarrepresentadas (ej. "Eucerin" solo scrapeado en Carrefour) se colaban como si fueran blancas y fusionaban con productos de otra marca real distinta (ej. "Schwarzkopf").

**Limitación conocida, sin resolver — bajo impacto (~0,3% medido):** marcas reales que JAMÁS aparecieron etiquetadas como `marca` en ningún scraper (ej. "Café Climent", empresa cafetera real de Gandía desde 1950) pueden colarse en el matching de marca blanca porque no hay ningún dato de origen del que "aprender" esa marca. Estructural — necesitaría una base de datos externa de marcas para resolverse del todo. 396 de 2.446 clusters comparando precio tienen un lado con marca detectada y otro sin ella (no todos son errores, es donde se concentra el riesgo si los hay).

**`match_mercadona.py` sigue sin `--dry-run` real.** No usar — irrelevante ya que `productos_match` se reconstruye entero en cada Fase 5.

---

## 1. Qué es el proyecto
App web PWA de comparación de precios de supermercados españoles.
URL producción: https://mi-mejor-cesta.vercel.app
Repositorio: https://github.com/gpeligros/mi-mejor-cesta

---

## 2. Stack tecnológico
- Frontend: React 19.2 + Tailwind CSS — Vercel
- Base de datos: Supabase (PostgreSQL) — scpuriaofisssalsbzqv.supabase.co
- Autenticación: Supabase Auth (email + Google OAuth)
- Backend admin: Flask (Python) — local / localhost:5000
- Scrapers: Python 3 — carpeta /scrapers
- IA (CESTITA + revisión de matches/categorías): Anthropic Claude API (Haiku) — /api/cestita y varios scripts de scrapers/
- Pagos: Stripe (checkout + webhook) — /api/stripe-checkout y /api/stripe-webhook
- Deploy: Vercel — git push a main despliega automáticamente
- DISABLE_ESLINT_PLUGIN=true en variables de entorno de Vercel

---

## 3. Arquitectura de BBDD — INAMOVIBLE

### Tablas principales
| Tabla | Descripción | Filas (última verificación) |
|-------|-------------|-------|
| `productos_catalogo` | Catálogo genérico. Solo admin escribe. | ~9.999 (ANTIGUO, pendiente de sustituir por Fase 5) |
| `categorias_maestras` | 87 categorías fijas (id 85-171). NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados. | ~9.999 (ANTIGUO — contaminado por bug de match_mercadona.py, se sustituye en Fase 5) |
| `precios_mercadona` | IDs ME-xxxx. Tiene `categoria_mercadona`/`subcategoria_mercadona` (~53% poblado). | ~8.371 |
| `precios_dia` | IDs DI-xxxx. **Tiene `categoria_dia`/`subcategoria_dia` (nuevo, 10/08/2026, 6.055 filas pobladas).** | ~6.055 actualizados hoy |
| `precios_alcampo` | IDs AL-xxxx. Campo `categoria` = código interno (ej. `OC1701`), decodificable vía `MAPPING_ALCAMPO` en `clasificar_categoria.py`. ⚠️ 61,7% de filas con `nombre_comercial` vacío (bug de scraper pendiente). | 2.264 |
| `precios_carrefour` | IDs CF-xxxx. Sin categoría propia. **Scraper roto** (ver sección 5). | 7.241 (datos de antes de que la web cambiase — desactualizados) |
| `precios_ahorramas` | IDs AH-xxxx. Campo `categoria_ahorramas` (genérico, 98% poblado, útil solo como pista amplia). | 1.529 |
| `supermercados` | **Nueva, 20/08/2026.** Config de supermercados para el panel admin (nombre, color, orden, activo, tabla_precios, columna_match). El frontend/admin ya la usa dinámicamente. Ver sección 10. | 5 |

### Reglas de oro
- NUNCA scrapers escriben en productos_catalogo ni categorias_maestras
- NUNCA borrar CAT-xxxx, solo desactivar con activo=false
- NUNCA subir .env a Git
- Antes de cualquier TRUNCATE verificar backup _old / CSV
- RLS: usar siempre auth.uid() = id (NO políticas recursivas sobre profiles — causan error 500)
- Toda tabla nueva creada después del 30/10/2026 necesita GRANT explícito. Tablas existentes no afectadas.
- **Todo script que escriba en Supabase debe implementar `--dry-run` DE VERDAD (con `argparse`, comprobado) antes de poder ejecutarse en real.**

---

## 4. Convención de nombres de ficheros
- Scrapers: `scraper_{supermercado}.py`
- Matching: `match_{supermercado}.py`
- SQL de setup/migración: `{descripcion}.sql`
- Scripts de revisión con IA: `revisar_{cosa}.py`
- Scripts de la reconstrucción del catálogo: ver sección 6 (nombres fijos, no renombrar)

---

## 5. Estado de scrapers (actualizado 10/08/2026)

| Super | Estado | Categoría nativa | Notas |
|---|---|---|---|
| Mercadona | ✅ Funciona | Sí (~53% poblado) | Sin cambios esta sesión |
| Alcampo | ✅ Funciona, sin tocar | Sí, decodificable (`MAPPING_ALCAMPO`) | Bug pendiente: 61,7% de filas con `nombre_comercial` vacío |
| AhorraMas | ✅ Funciona, sin tocar | Parcial (genérica) | Sin cambios esta sesión |
| DIA | ✅ **Reescrito completo 10/08/2026** | Sí, nueva y granular (28 categorías / 246 subcategorías) | 6.055 productos subidos correctamente |
| Carrefour | ❌ **Roto** — misma causa que tenía DIA (web rediseñada) | No | **Pendiente de reescribir con el mismo método que DIA** |

### DIA — qué se hizo y por qué (10/08/2026)
DIA rehizo su web entera desde que se escribió el scraper original (URLs y API antiguas ya no existen — redirigían a la home, causando scrapeo de productos aleatorios en vez de la categoría pedida).

Se descubrió la API real navegando con DevTools (Network tab, filtro `domain:www.dia.es`) hasta encontrar:
```
GET https://www.dia.es/api/v1/plp-back/l1/all/{L1}/reduced?category_id={L2}&page={N}
```
Se extrajo el árbol completo de categorías real (28 L1 / 246 L2) desde el payload `menu_analytics`. El scraper nuevo:
- Reutiliza `curl_cffi` con `impersonate="chrome124"`
- "Calienta" la sesión visitando la home antes de llamar a la API
- Guarda `categoria_dia` y `subcategoria_dia` por fila (antes NUNCA se guardaban)
- Guarda un **backup local JSON** (`backup_dia_<fecha>.json`) antes de subir, con reintentos automáticos
- Excluye categorías transversales que duplican producto: Sin gluten, Novedades, Verano, Ofertas

**Incidencias de esta sesión ya resueltas:**
- Faltaban columnas `categoria_dia`/`subcategoria_dia` en `precios_dia` → añadidas
- Faltaba restricción `UNIQUE(id_api)` en `precios_dia` → añadida
- Fallo de red a mitad de subida → resuelto con backup local + reintentos

**Script de apoyo nuevo:** `scrapers/subir_backup_dia.py <ruta_backup.json>` — sube un backup JSON sin repetir el scrape si la subida falla.

### Carrefour — pendiente, mismo problema que tenía DIA
Confirmado el síntoma (0 productos) pero no investigada la API nueva todavía. Cuando se retome: DevTools → Network → filtrar por dominio → buscar endpoint tipo `/api/.../products` tras hacer scroll → capturar árbol de categorías → reescribir con el mismo patrón que `scraper_dia.py`.

### Bug pendiente: Alcampo con nombres vacíos
1.397 de 2.264 filas de `precios_alcampo` (61,7%) tienen `nombre_comercial` vacío. No abordado esta sesión.

---

## 6. Reconstrucción completa del catálogo — pipeline nuevo (agosto 2026)

Motivo: el catálogo se construyó originalmente solo desde Mercadona, arrastrando duplicados masivos y contaminación de marca blanca, con solo ~93% de productos con cobertura en un único supermercado.

**Todo lo de esta sección vive en CSVs dentro de `old/`, en local. Nada se ha aplicado todavía a la BBDD real (Fase 5 pendiente).**

### Scripts, en orden de ejecución
1. **`exportar_todos_precios.py`** (Fase 1) — exporta las 5 tablas `precios_*` completas a CSV.
2. **`normalizar_productos.py`** (Fase 2) — separa nombre base / marca / formato de cada producto.
3. **`agrupar_productos.py`** (Fase 3a, sin coste) — agrupa productos en clusters en tres pasadas (dedup intra-super, bridging cross-super con Mercadona de ancla, rescate sin restricción de marca), con guardia de conflicto contra atributos excluyentes (desnatada/entera, sin X). Salida: `resumen_clusters_*.csv`, `clusters_dudosos_*.csv`, `miembros_clusters_*.csv`.
4. **`revisar_clusters_dudosos.py`** (Fase 3b, con IA, coste mínimo) — Haiku puntúa 0-10 los bridges dudosos.
5. **`construir_propuesta_final.py`** (Fase 4) — aplica decisiones de la IA, genera catálogo propuesto + muestra de revisión.
6. **`clasificar_categoria.py`** (Fase 4b) — categoriza en 3 capas: Mercadona real → Alcampo real (decodificado) → palabras clave. Capa "vecino más cercano" desactivada por defecto (poco fiable incluso a umbral 85). Residual cae en "Bazar y Varios".

### Resultado de la última ejecución completa (08/08/2026, ANTES del arreglo de DIA)
- 17.154 clusters totales, 746 comparan precio en ≥2 supers (37 en ≥3), 16.408 solo en 1 super
- Categorización: 80,8% fiable (Mercadona real + palabra clave), 19,3% en "Bazar y Varios"

⚠️ **Pendiente re-ejecutar todo el pipeline con los datos de DIA ya actualizados** (categoría nueva y más productos) — los números de arriba están desactualizados.

### Pendiente antes de la Fase 5
~~1. Añadir `MAPPING_DIA` + Capa 1c en `clasificar_categoria.py`~~ ✅ hecho 10/08/2026
~~2. Re-ejecutar pipeline completo (pasos 1-6) con datos de DIA frescos~~ ✅ hecho 10/08/2026
~~3. Revisar de nuevo la muestra final con David~~ ✅ hecho 10/08/2026
~~4. Escribir el script de Fase 5~~ ✅ `construir_catalogo_v2.py`, hecho y EJECUTADO 10/08/2026
5. Re-ejecutar matching de los 5 supers contra el catálogo nuevo — no hecho, opcional (el catálogo ya trae matches de la propia reconstrucción)

### 🔴 Pendiente URGENTE — próxima sesión
**David reportó fallos en el catálogo nuevo tras la Fase 5 (10/08/2026, noche), sin detallar cuáles.** Primera tarea de la próxima sesión: preguntarle qué está viendo exactamente (capturas, ejemplos de productos concretos) antes de tocar nada. Posibles sospechosos a revisar primero:
- `nombre_generico` de marca_fabricante puede llevar el nombre completo con formato si no había ningún miembro de Mercadona en el cluster (revisar `elegir_nombre_representativo()` en `construir_catalogo_v2.py`)
- Verificar que el frontend (`App.js`, `vista_productos`) no tenga alguna suposición sobre la estructura vieja del catálogo que ya no se cumpla
- Revisar si `vista_productos` (la VIEW que une catálogo + categorías) sigue funcionando bien con los `id_categoria` nuevos

---

## 7. Planes de suscripción
Sin cambios esta sesión. Ver histórico. Pendiente pasar Stripe test → live.

---

## 8. Problemas conocidos / Deuda técnica

### 🔴 Críticos
- Catálogo en producción sigue siendo el antiguo — Fase 5 pendiente
- Stripe en modo TEST
- `match_mercadona.py` sin `--dry-run` real — no ejecutar hasta reescribir

### 🟡 Importantes
- Carrefour: scraper roto, sin arreglar
- Alcampo: 61,7% de filas sin `nombre_comercial`
- `MAPPING_DIA` no existe todavía
- Falta script de Fase 5

### 🟢 Menores
- `precios_carrefour` con datos desactualizados hasta que se arregle el scraper

---

## 9. Comandos útiles

```powershell
cd frontend
npm start

git add .
git commit -m "descripcion"
git push origin main

# Scraper DIA (reescrito 10/08/2026)
python scrapers/scraper_dia.py --dry-run --cat verduras
python scrapers/scraper_dia.py --dry-run
python scrapers/scraper_dia.py
python scrapers/subir_backup_dia.py backup_dia_<fecha>.json

# Pipeline de reconstrucción del catálogo (en orden)
python scrapers/exportar_todos_precios.py
python scrapers/normalizar_productos.py
python scrapers/agrupar_productos.py
python scrapers/revisar_clusters_dudosos.py --dry-run
python scrapers/revisar_clusters_dudosos.py
python scrapers/construir_propuesta_final.py
python scrapers/clasificar_categoria.py
# Fase 5: script todavia no existe
```

---

## 10. Pendientes por orden de prioridad

### 🔴 Alto impacto / bloqueantes
1. Reescribir `scraper_carrefour.py` (mismo método que se usó para DIA: DevTools → capturar API real → reconstruir; ver sección 5)
2. Arreglar bug de `nombre_comercial` vacío en `scraper_alcampo.py` (61,7% de filas afectadas — visible ahora en el panel de admin, pestaña Precios, filtro "solo vacíos", y en el Dashboard con barra de calidad de datos)
3. Pasar Stripe a producción (test → live)

### 🟡 Funcionalidades nuevas solicitadas (20/08/2026, sin empezar)
4. **Funcionalidad tipo Yuka** (escaneo/puntuación nutricional 0-100 con semáforo, vía Open Food Facts API + EAN). Investigado: metodología = Nutri-Score + aditivos + ecológico. La mayoría de scrapers ya capturan EAN. Pendiente: diseñar esquema de datos, integrar API externa, UI del semáforo.
5. Mejorar menús semanales y funcionalidad nutricional existente (CESTITA/MenuSemanal) — sin concretar todavía qué mejoras exactas.

### 🟢 Panel de administración — hecho el 20/08/2026, revisar próxima sesión
- Carrefour integrado en Dashboard/Matches/Precios (antes ausente)
- Tabla `supermercados` en Supabase + pestaña de gestión (activar/desactivar, renombrar, color, orden) — **límite conocido**: añadir un supermercado nuevo de verdad sigue necesitando scraper + columna en `productos_match`, esta tabla no lo evita
- Métrica núcleo destacada en Dashboard: productos que comparan precio en ≥2 supers, con desglose visual 1-5 supers
- Sección "Calidad de datos por supermercado": barra de progreso % nombre correcto vs. filas rotas por super (responde directamente a por qué Alcampo tiene huecos)
- Sección "Calidad de categorización": categorizados vs. Bazar y Varios
- Precios ahora editable (nombre, precio, marca, disponible) + filtro "solo filas vacías"
- Pendiente de verificar por David: que los números cuadren tras desplegar, y decidir si hace falta ir más allá (gráficos más elaborados, exportar datos, log de cambios/auditoría — no implementado)

### 🟢 Diseño visual — hecho el 20/08/2026, pendiente de ver desplegado
- `StoreSelector.js` y `ToolBar.js` (zona superior de la app, "Mis tiendas" + botones Menú/Recetas/Nutricional) rediseñados con gradientes, sombras, transiciones — sin tocar logos. Pendiente confirmar que se ve bien en producción.
- El resto de la app (SuperCard, Sidebar, etc.) no se ha tocado — si "un poco pobre" se refería a más partes, especificar cuáles en la próxima sesión.

### 🔵 Bajo impacto / opcional
- Mitigar el caso tipo "Café Climent" — marcas reales nunca etiquetadas en ningún scraper coladas en matching de marca blanca (~0,3% medido, ver sección 6)
- Re-ejecutar matching completo si se quiere seguir exprimiendo la cobertura de comparación tras los arreglos de hoy

