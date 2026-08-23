# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 23/08/2026)

## ⚠️ INSTRUCCIONES PARA CLAUDE
Lee este fichero COMPLETO antes de responder nada.
Respeta SIEMPRE las convenciones de nombres, arquitectura y reglas de oro.
NUNCA propongas cambiar la arquitectura de BBDD sin consultar.
NUNCA cambies nombres de ficheros sin preguntar.
NUNCA empieces a escribir código sin entender primero el estado real.
SIEMPRE pide los ficheros actuales antes de modificarlos.
NUNCA uses sed en PowerShell — usar python3 para manipular ficheros.
PowerShell NO soporta && — ejecutar comandos por separado.
**SIEMPRE que actualices CONTEXTO.md, guárdalo en las DOS copias a la vez y nunca solo en una:** el Proyecto de Claude (`project_write`) Y `docs/CONTEXTO.md` en el ordenador de David (vía el puente de acceso al dispositivo — stage del fichero actual para coger su mtime, luego SendUserFile + `device_commit_files` con ese mtime). Quedaron desincronizadas una vez (23/08/2026) porque solo se actualizó la copia del Proyecto — no debe volver a pasar.

---

## 0. ⚠️ ESTADO CRÍTICO — LEER PRIMERO

**23/08/2026 — Bug de "nombres sucios" encontrado, corregido y YA APLICADO A PRODUCCIÓN.** Esta era la tarea "Pendiente URGENTE" que quedó anotada el 21/08 (los fallos que David reportó tras la Fase 5 del 20/08, sin detallar cuáles). Diagnóstico hecho releyendo el código + simulando la Fase 5 contra los CSV reales que se usaron el 20/08 (`miembros_finales_20260820_1345.csv` + `categorias_asignadas_20260820_1346.csv`), sin tocar la BBDD (Supabase no es alcanzable desde el entorno cloud de esta sesión).

- **Causa:** `elegir_nombre_representativo()` en `construir_catalogo_v2.py` usaba el nombre tal cual lo escribió cada supermercado (`nombre_original`, sin limpiar) cada vez que un cluster no tenía ningún miembro de Mercadona. Como la mayoría del catálogo no tiene Mercadona (12.497 de 16.727 clusters), el nombre que ve el usuario en la app arrastraba el formato/cantidad pegado: p. ej. "Leche Desnatada Carrefour Botella 1,5 L" en vez de "Leche Desnatada Carrefour".
- **Impacto medido sobre los datos reales de producción (20/08):** 12.021 de 16.727 productos (**71,9%** del catálogo) tenían el nombre sucio de esta forma.
- **Fix aplicado:** `elegir_nombre_representativo()` ahora reutiliza `quitar_marca()` + `extraer_formato()` de `normalizar_productos.py` (Fase 2) — las mismas funciones ya probadas — para construir el nombre limpio y volver a añadir la marca al final (mismo patrón que ya usaba `clasificar_categoria.py` en su columna `nombre_representativo`, ej. "Aceite de oliva 0,4º Hacendado"). Probado antes en `--dry-run` contra los mismos CSV reales: baja de 71,9% a 0,1% (11 casos residuales, sin regresión en ninguno de los ~4.230 clusters que sí tenían Mercadona).
- **✅ Aplicado a producción el 23/08/2026:** David ejecutó `construir_catalogo_v2.py` de verdad desde su ordenador (backup automático hecho antes de tocar nada, tablas reconstruidas, log final "CATÁLOGO NUEVO EN PRODUCCIÓN" confirmado). El catálogo en Supabase ya usa la lógica de nombre limpio.
- **Pendiente de verificar:** confirmar visualmente en la app (o en el panel admin) que los nombres salen limpios ahora con algún ejemplo real, y anotar aquí las cifras finales de la ejecución (total de productos, marca blanca vs. fabricante, cuántos comparan en ≥2 supers) si David las pega — no se han registrado todavía en este documento.
- Se revisó también `App.js`: ya está adaptado a la tabla nueva (`vista_productos`, `id_categoria`, `tipo`), no se encontró ninguna suposición rota sobre la estructura vieja del catálogo.
- `vista_productos` no se pudo verificar en vivo (vive solo en Supabase, no hay ningún `.sql` en el repo que la defina — no está versionada, posible mejora futura documentarla).
- El propio script termina sugiriendo "re-ejecutar matching de los supers no cubiertos todavía" — es un mensaje genérico del script, no un paso obligatorio: `CONTEXTO.md` ya lo marcaba como opcional porque el catálogo reconstruido trae sus propios matches (sección 6). Solo tendría sentido si se quiere seguir exprimiendo cobertura.

**Fase 5 EJECUTADA en producción el 20/08/2026** (con el bug de nombres de arriba, ya corregido el 23/08). Catálogo: 16.727 productos, **2.104 comparando precio en ≥2 supers** (2,5x respecto a la reconstrucción del 10/08). Reemplaza la versión del 10/08/2026, que ya quedó obsoleta tras los arreglos de esa sesión.

**Arreglos aplicados el 20/08/2026 en el pipeline de reconstrucción:**
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
| `productos_catalogo` | Catálogo genérico. Solo admin escribe. | 16.727 (reconstruido en Fase 5, 20/08; nombres corregidos 23/08) |
| `categorias_maestras` | 87 categorías fijas (id 85-171). NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados. | Reconstruida entera en la Fase 5 del 20/08 |
| `precios_mercadona` | IDs ME-xxxx. Tiene `categoria_mercadona`/`subcategoria_mercadona` (~53% poblado). | ~8.371 |
| `precios_dia` | IDs DI-xxxx. **Tiene `categoria_dia`/`subcategoria_dia` (nuevo, 10/08/2026, 6.055 filas pobladas).** | ~6.055 actualizados hoy |
| `precios_alcampo` | IDs AL-xxxx. Campo `categoria` = código interno (ej. `OC1701`), decodificable vía `MAPPING_ALCAMPO` en `clasificar_categoria.py`. ⚠️ 61,7% de filas con `nombre_comercial` vacío — diagnosticado 23/08/2026: son 1.397 filas huérfanas del 27/04/2026, no un bug del scraper actual (ver sección 5). Falta el re-scrape de verdad para limpiarlas. | 2.264 |
| `precios_carrefour` | IDs CF-xxxx. Sin categoría propia. **Scraper roto** (ver sección 5). | 7.241 (datos de antes de que la web cambiase — desactualizados) |
| `precios_ahorramas` | IDs AH-xxxx. Campo `categoria_ahorramas` (genérico, 98% poblado, útil solo como pista amplia). | 1.529 |
| `supermercados` | **Nueva, 20/08/2026.** Config de supermercados para el panel admin (nombre, color, orden, activo, tabla_precios, columna_match). El frontend/admin ya la usa dinámicamente. Ver sección 10. | 5 |
| `historico_precios` | **Nueva, 23/08/2026 (P1 #4), SQL escrito pero SIN EJECUTAR TODAVÍA en Supabase.** Un registro por cada cambio de precio detectado (super, id_producto_super, precio, fecha). Poblada por diff en los propios scrapers, no por trigger — ver sección 12. | 0 (tabla aún no creada) |

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
| Alcampo | ✅ Funciona, código corregido 23/08 | Sí, decodificable (`MAPPING_ALCAMPO`) | 61,7% de filas con `nombre_comercial` vacío en la BBDD — diagnosticado como datos huérfanos del 27/04, no bug del scraper actual (ver detalle abajo). Falta re-scrape real para limpiarlas |
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

### Bug de Alcampo con nombres vacíos — diagnosticado y corregido en código el 23/08/2026 (P0 #3)
**El diagnóstico inicial ("un selector de nombre que falla") era incorrecto.** Se analizó `old/export_precios_alcampo_20260810_2148.csv` (export real de `precios_alcampo`, 2.264 filas) sin acceso a la BBDD en vivo, y los datos cuentan otra historia:

- Las 1.397 filas vacías (61,7%) **NO tienen solo el nombre vacío** — tienen TAMBIÉN `precio`, `marca`, `imagen`, `ean` y `categoria` vacíos. Solo conservan `id`, `id_api`, `url` y `disponible`.
- Las 1.397 comparten EXACTAMENTE la misma fecha de `actualizado`: **27/04/2026**, y ninguna se ha vuelto a tocar desde entonces (el export es del 10/08/2026, casi 4 meses después). Las filas con datos completos son de fechas distintas (22/03 y 07/04/2026).
- Conclusión: no es un bug del scraper actual — `scraper_alcampo.py` (tal y como está hoy) nunca construye una fila con nombre vacío sin que también le falte el precio, así que este patrón no puede venir de su lógica de parseo. Son 1.397 filas "esqueleto" que dejó algún proceso puntual el 27/04/2026 (probablemente una versión antigua del scraper o un paso de descubrimiento de URLs que nunca se completó con los detalles), y que el scraper actual no ha vuelto a encontrar/sobrescribir desde entonces. Además, una fila sin nombre Y sin precio no sirve para comparar precios aunque se le rellene el nombre — el problema real es que están "huérfanas", no que les falte un dato.

**Corregido en el código de todas formas (dos bugs reales, aunque no eran la causa principal del 61,7%):** en `scraper_alcampo.py`, dos de las tres rutas de extracción de nombre (`_parse_jsonld_alcampo()` y `_parse_html_card_alcampo()`, usadas como fallback cuando la API principal falla) subían el producto igual aunque no encontraran nombre, dejando `nombre_comercial=""` — a diferencia de `parse_api_product()` (la ruta principal), que si no encuentra nombre descarta el producto entero. Ahora las tres rutas se comportan igual: si no hay nombre, se descarta la fila en vez de subirla vacía. De paso, `_parse_html_card_alcampo()` ahora también prueba `aria-label` y el `alt` de la imagen del producto como nombre de repuesto cuando el selector de texto no encuentra nada, y `extract_products_from_html()` ya no se rinde en el primer selector de tarjetas que encuentre ALGO aunque resulte inservible — prueba el siguiente. Sin acceso a la web en vivo para confirmarlo con datos reales.

**Pendiente, acción de David:**
1. Ejecutar `scraper_alcampo.py` de verdad (no `--dry-run`) — como usa upsert por `id_api`, cualquiera de esos 1.397 productos que Alcampo siga vendiendo hoy se sobrescribirá solo con datos completos al volver a encontrarse en el listado de categorías.
2. Después, comprobar cuántas quedan: `SELECT count(*) FROM precios_alcampo WHERE nombre_comercial IS NULL OR nombre_comercial = '';` — las que sigan vacías tras el re-scrape son casi con toda seguridad productos descatalogados por Alcampo, candidatas a desactivar o borrar (decisión de David, no se toca la BBDD desde aquí).

---

## 6. Reconstrucción completa del catálogo — pipeline nuevo (agosto 2026)

Motivo: el catálogo se construyó originalmente solo desde Mercadona, arrastrando duplicados masivos y contaminación de marca blanca, con solo ~93% de productos con cobertura en un único supermercado.

### Scripts, en orden de ejecución
1. **`exportar_todos_precios.py`** (Fase 1) — exporta las 5 tablas `precios_*` completas a CSV.
2. **`normalizar_productos.py`** (Fase 2) — separa nombre base / marca / formato de cada producto.
3. **`agrupar_productos.py`** (Fase 3a, sin coste) — agrupa productos en clusters en tres pasadas (dedup intra-super, bridging cross-super con Mercadona de ancla, rescate sin restricción de marca), con guardia de conflicto contra atributos excluyentes (desnatada/entera, sin X). Salida: `resumen_clusters_*.csv`, `clusters_dudosos_*.csv`, `miembros_clusters_*.csv`.
4. **`revisar_clusters_dudosos.py`** (Fase 3b, con IA, coste mínimo) — Haiku puntúa 0-10 los bridges dudosos.
5. **`construir_propuesta_final.py`** (Fase 4) — aplica decisiones de la IA, genera catálogo propuesto + muestra de revisión.
6. **`clasificar_categoria.py`** (Fase 4b) — categoriza en 3 capas: Mercadona real → Alcampo real (decodificado) → palabras clave. Capa "vecino más cercano" desactivada por defecto (poco fiable incluso a umbral 85). Residual cae en "Bazar y Varios".
7. **`construir_catalogo_v2.py`** (Fase 5, única que toca la BBDD) — lee `miembros_finales_*.csv` + `categorias_asignadas_*.csv` y reconstruye `productos_catalogo`/`productos_match` en Supabase. **Corregido 23/08/2026 y re-ejecutado en producción ese mismo día** (ver sección 0) — antes del fix generaba nombres sucios en el 71,9% del catálogo.

### Resultado de la última ejecución completa en producción
- **20/08/2026** (construcción del catálogo): 16.727 productos en catálogo, 2.104 comparando precio en ≥2 supers
- **23/08/2026** (mismo catálogo, solo con el fix de nombres aplicado): re-ejecutado con éxito según confirmó David ("CATÁLOGO NUEVO EN PRODUCCIÓN"). Pendiente registrar aquí las cifras exactas de esta segunda ejecución si difieren de las del 20/08 (no deberían, el fix solo toca el texto del nombre, no el agrupamiento).

### Pendiente
- Verificar en la app / panel admin que los nombres se ven limpios ahora — ver sección 0
- Re-ejecutar matching de los 5 supers contra el catálogo nuevo — sigue siendo opcional, no obligatorio (el catálogo ya trae matches de la propia reconstrucción)
- Documentar (o versionar en un `.sql`) la definición de la VIEW `vista_productos` — hoy solo vive en Supabase, no hay forma de revisarla fuera del dashboard

---

## 7. Planes de suscripción
Sin cambios esta sesión. Ver histórico. Pendiente pasar Stripe test → live.

---

## 8. Problemas conocidos / Deuda técnica

### 🔴 Críticos
- Stripe en modo TEST
- `match_mercadona.py` sin `--dry-run` real — no ejecutar hasta reescribir

### 🟡 Importantes
- Carrefour: scraper roto, sin arreglar (sesión 23/08: no se pudo investigar la API nueva por falta de acceso a internet/navegador en vivo desde esta sesión — ver sección 5)
- Alcampo: 61,7% de filas sin `nombre_comercial` en la BBDD — código ya corregido 23/08, pero falta el re-scrape real para limpiar los datos existentes (ver sección 5)

### 🟢 Menores
- `precios_carrefour` con datos desactualizados hasta que se arregle el scraper
- `vista_productos` no versionada (vive solo en Supabase, sin `.sql` en el repo)

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
python scrapers/construir_catalogo_v2.py --dry-run   # revisar antes de re-ejecutar
python scrapers/construir_catalogo_v2.py
```

---

## 10. Pendientes por orden de prioridad

### 🔴 Alto impacto / bloqueantes
1. Reescribir `scraper_carrefour.py` (mismo método que se usó para DIA: DevTools → capturar API real → reconstruir; ver sección 5). **Bloqueado el 23/08/2026**: esta sesión no tiene acceso a internet ni a un navegador conectado para hacer el descubrimiento en vivo con DevTools — necesita que David haga esa parte (o una sesión futura con el navegador de Chrome conectado) y comparta el endpoint encontrado.
2. ✅ **Bug de `nombre_comercial` vacío en `scraper_alcampo.py` — código corregido el 23/08/2026** (ver sección 5). Falta solo que David ejecute el scraper de verdad para limpiar los datos existentes.
3. Pasar Stripe a producción (test → live)

### ✅ Git — al día (actualizado 23/08/2026)
- La limpieza de `scripts/supabase.exe`, `frontend/build/` y `.playwright-cli/` (que en sesiones anteriores quedó como "pendiente de decidir") **ya está comiteada** — quedó resuelta en algún momento entre sesiones sin que este documento se actualizara. Confirmado con `git log`: commits `Dejar de trackear binarios y artefactos de build`, `Dejar de trackear frontend/build, .playwright-cli y scripts/supabase.exe` y `Reorganizar ficheros del proyecto: archivar legacy en ARCHIVO_HISTORICO/`.
- **Comiteado hoy, 23/08/2026, en 2 commits locales (sin `git push` todavía — pendiente de que David lo revise y decida cuándo subirlo):**
  1. `fix(catalogo): corregir nombres sucios en Fase 5` — solo `construir_catalogo_v2.py`.
  2. `feat(P1): buscador con acentos, cobertura por super, ...` — los 5 ficheros de frontend de P1, los 5 scrapers + los 2 ficheros nuevos del histórico de precios, y este mismo `CONTEXTO.md`.
- **Quedaron FUERA de estos commits, a propósito, un grupo de ficheros con cambios que no se hicieron en esta sesión y cuyo origen no se ha podido verificar** (no forman parte de ningún trabajo documentado en este archivo): `backend/admin/requirements.txt`, `backend/api/app_gestion.py` (758 líneas cambiadas — el más grande con diferencia), `frontend/postcss.config`, `frontend/public/icon`, `frontend/public/icon.svg`, `frontend/public/index_backup.html`, `frontend/public/robots.txt`, `frontend/src/analytics/Googleanalytics.js`, `frontend/src/components/Footer.js`, `frontend/tailwind.config.js`, `scrapers/scraper_openprices.py`, `scripts/clasificador.py`, `scripts/discover_endpoint.py`, `scripts/generar_codigos_v3.py`, `scripts/requirements_gestor.txt`. Probablemente sean cambios locales de David hechos con otro editor/herramienta en otro momento — **David debe revisarlos y decidir si los quiere comitear** (por separado, no mezclados con el trabajo de hoy). También quedaron sin tocar unos ficheros/carpetas sin trackear (`.claude/`, `ARCHIVO_HISTORICO/restos_tecnicos_git/`, `old/`, los PDF nuevos en `docs/`) por el mismo motivo.
- Nota técnica sin impacto para David: al comitear desde esta sesión (vía el puente de acceso al dispositivo) Git no pudo borrar sus propios ficheros temporales de bloqueo (`.git/index.lock`, `.git/HEAD.lock`, cientos de `tmp_obj_*` en `.git/objects/`) por una restricción de permisos del propio puente — se comprobó con `git fsck` que el repositorio queda íntegro (los commits y objetos reales se escriben bien, son solo restos cosméticos). Si algún día le apetece, puede borrarlos a mano o con `git gc`; no es urgente.

### 🔴 Histórico de precios — ejecutar el SQL antes de que funcione (23/08/2026)
- `scrapers/historico_precios.sql` está escrito pero SIN ejecutar en Supabase — la tabla `historico_precios` no existe todavía en producción. Hasta que se ejecute, los scrapers seguirán subiendo precios con normalidad (el registro de histórico falla en silencio y se ignora), simplemente no se guardará ningún histórico. Ver sección 12, "Punto 4", para los pasos de prueba recomendados.

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

---

## 11. Organización de ficheros del proyecto (21/08/2026)

Hoy se ha limpiado la carpeta raíz del proyecto en el ordenador de David. Objetivo: quitar de en medio todo lo que ya no se usa, sin borrar nada (todo se ha movido, nada se ha eliminado).

### Qué se ha hecho
- Carpeta nueva **`ARCHIVO_HISTORICO/`** en la raíz. Ahí han ido a parar 128 ficheros/carpetas que ya no se usan pero que no se han querido borrar por si acaso: CSVs sueltos de la raíz, versiones antiguas de scripts, datos de pruebas superadas, copias viejas de `CONTEXTO.md`, prototipos descartados (`old/scraping`, `old/templates`) y restos de scrapers de supermercados descartados (Eroski, Hipercor, versiones antiguas con Gemini).
- Dentro de `ARCHIVO_HISTORICO/` hay subcarpetas para saber qué es cada cosa: `raiz_suelta/`, `scripts/`, `old_scripts_legacy/`, `old_datos_legacy/`, `old_contexto_antiguos/`, `scrapers_restos/`, `revisar_datos_viejos/`, más `output_sqls/`, `old_scraping_prototipo/` y `old_templates_flask/` (carpetas enteras movidas tal cual).
- 7 documentos `.docx` que estaban sueltos en `old/Revisar/` (plan estratégico, análisis, especificaciones, traspaso...) se movieron a `docs/`, que es donde tiene sentido que estén.
- Se depuró `scrapers/`: solo quedan los ficheros que de verdad se usan hoy.

### Qué NO se ha tocado (a propósito)
- **`old/` sigue existiendo con ese nombre y en ese sitio.** Aunque el nombre suena a "descartable", es la carpeta de trabajo activa del pipeline de reconstrucción del catálogo (sección 6) — varios scripts la usan por nombre fijo (`CARPETA_OLD`). Solo se sacaron de ahí los ficheros sueltos que sobraban (scripts antiguos, CSVs de pruebas, copias de CONTEXTO). Los CSVs con fecha que sí usa el pipeline se dejaron dentro.
- Dentro de `old/` quedan todavía varias versiones con fecha de un mismo tipo de fichero (p. ej. varios `clusters_dudosos_*.csv`). No se tocaron porque decidir cuál es "la buena" de cada tipo requiere más cuidado — pendiente para una sesión futura.
- El lado de Git no se tocó en esta limpieza de ficheros — ver el punto "Git — pendiente de decidir" en la sección 10.

### Dos carpetas vacías sueltas
Al mover ficheros, `old/Revisar/` y una carpeta temporal `_to_delete/` (usada durante la propia limpieza) quedaron vacías. No se pudieron borrar automáticamente por una limitación técnica de la herramienta usada para tocar el ordenador de David — se pueden borrar a mano en el Explorador de Windows cuando quiera, no es urgente.

---

## 12. P1 — Mejoras de frontend (23/08/2026)

Tras el fix de Fase 5 (sección 0), se repasó `PLAN_PRIORIZADO.md` (cruce de `Análisis de app web.pdf` + `Propuestas_GPT.pdf` contra el código real) y David pidió ejecutar **todo el bloque P1, los 8 puntos en orden, uno detrás de otro**. Los 8 puntos están implementados en código. **El punto 4 (histórico de precios) necesitó parar a consultar arquitectura de BBDD primero** (regla de oro) — David eligió el enfoque "diff en los scrapers" y con su aprobación se implementó también, pero con un paso manual pendiente antes de que funcione de verdad: ver más abajo.

### Hecho y aplicado al repo real (vía puente de acceso al dispositivo)
1. **Normalización de acentos reutilizada en el buscador** (`Sidebar.js`) — se extrajo la misma lógica de quitar acentos que ya usaba el chat IA (`Cestita.js`) a una función `normalizarBusqueda()` y se aplicó en los dos filtros de búsqueda por nombre de producto, que antes hacían `.toLowerCase().includes(...)` a pelo (buscar "cafe" no encontraba "café").
2. **Cobertura por supermercado en cada SuperCard** (`SuperCard.js`) — badge nuevo junto al logo, `X/Y productos` (verde si están todos, ámbar si falta alguno), calculado sobre los productos de la cesta actual.
3. **Límite configurable de supermercados en la cesta inteligente** (`App.js` + `Sidebar.js`) — nuevo control "🏪 Comprar en como máximo" (selector 1..N supers activos) para evitar que la cesta óptima se fragmente en 4-5 tiendas distintas cuando el ahorro extra es mínimo. Nueva función `combinacionesDeTamano()` que prueba combinaciones de supers hasta el límite elegido y se queda con la más barata; persiste en `localStorage` (`limiteFragmentacion_v1`).
4. **Histórico de precios real** (`scrapers/historico_precios.sql` + `scrapers/historico_precios.py`, más un cambio pequeño en `scraper_mercadona.py`, `scraper_dia.py`, `scraper_alcampo.py`, `scraper_ahorramas.py` y `scraper_carrefour.py`) — David eligió el enfoque "diff en los scrapers" (sin trigger de BBDD). Cada scraper, justo antes de subir un precio, consulta el precio que ya había en Supabase; si es distinto (o el producto es nuevo), se inserta una fila en `historico_precios` con el precio nuevo y la fecha de hoy — si no ha cambiado, no se inserta nada. Ver detalle más abajo, incluyendo el paso manual pendiente.
5. **Cantidades en la cesta** (`App.js`, `SuperCard.js`, `Cestita.js`) — stepper −/+ por producto en cada fila de SuperCard y en el modo tienda. Todos los totales (por super, cesta multi-tienda, PDF, guardar compra, contexto que recibe la IA) multiplican ya por la cantidad. **No se ha tocado la BBDD**: `compras_detalle` no tiene columna `cantidad`, así que se guarda como antes (precio = importe total de la línea) y se añade `×N` al nombre del producto para que se entienda al mirar el histórico. Persiste en `localStorage` (`cantidades_v1`).
6. **Señal visual "misma marca" vs. "alternativa equivalente"** (`SuperCard.js`) — badge ámbar "≈ alternativa equivalente" cuando `producto.tipo === 'marca_blanca'`, con tooltip explicando que se compara por tipo de producto y no es literalmente la misma marca en cada super. No hizo falta tocar la BBDD ni `App.js`: el campo `tipo` ya venía cargado en `db` y llega vía `getProdFull(id)`.
7. **Cifras desactualizadas en la Landing corregidas** (`Landing.js`) — la lista `SUPERS` incluía Lidl/Aldi (no existen en el catálogo) y le faltaba AhorraMas; se corrigió a los 5 reales. Se quitó la afirmación "ahorra hasta 100€/mes" (sin ningún dato que la respalde) y se sustituyeron las cifras `+4.000 / 6 / 100€` por las reales del catálogo: **16.727 productos, 5 supermercados, 2.104 comparando en 2+ tiendas**.
8. **Sección "Cómo funciona" añadida a la Landing** (`Landing.js`) — 3 pasos (Añade productos → Comparamos → Elige la mejor opción) entre las estadísticas y los beneficios, para que la landing no pase directa del hero a los beneficios sin explicar el flujo.

### Pendiente de este bloque, importante
- **Frontend (puntos 1,2,3,5,6,7,8): nada se ha probado en un `npm start` real ni en navegador** — solo se validó que cada fichero compila (sintaxis JS/JSX correcta vía esbuild). `App.js` pasa props nuevas a `Sidebar`, `SuperCard` y `Cestita`, así que antes de desplegar conviene abrir la app en local y probar: buscador con acentos, badge de cobertura, selector de límite de supers, cantidades (stepper, PDF, guardar compra), badge de marca blanca y la landing.
- **Backend (punto 4): la tabla `historico_precios` todavía no existe en Supabase** — hay que ejecutar el SQL a mano primero. Ver el detalle y los pasos de prueba en "Punto 4" más abajo.
- **Ya comiteado en local (no subido a GitHub todavía)** — ver sección 10, "Git — al día", con el detalle de los 2 commits.
- Nuevas claves de `localStorage`: `limiteFragmentacion_v1`, `cantidades_v1`.

### Punto 4 — Histórico de precios real: qué se implementó y qué falta a mano
Era el único punto de P1 que toca la arquitectura de BBDD (tabla nueva), así que se propuso primero y David aprobó explícitamente el enfoque "diff en los scrapers" antes de escribir nada (regla de oro: nunca cambiar arquitectura de BBDD sin consultar).

**Diseño:**
- Tabla nueva `historico_precios` (super, id_producto_super, precio, fecha, con índice único por super+producto+fecha para que no se pueda duplicar un mismo día). SQL en `scrapers/historico_precios.sql`.
- Módulo nuevo `scrapers/historico_precios.py` con la lógica de comparar precio nuevo vs. precio guardado y decidir si hay que insertar fila. Dos funciones: una para los 4 scrapers que usan el cliente `supabase-py` (DIA, Alcampo, Ahorramas, Carrefour) y otra en REST puro para Mercadona (que sube precios con `urllib`, no con ese cliente).
- Los 5 scrapers (`scraper_mercadona.py`, `scraper_dia.py`, `scraper_alcampo.py`, `scraper_ahorramas.py`, `scraper_carrefour.py`) ahora llaman a esa función justo antes de subir los precios nuevos. Si `historico_precios.py` no está disponible por lo que sea, el `import` falla en silencio y el scraper sigue funcionando exactamente igual que antes (nunca puede romper la subida de precios normal).
- Pensado para alimentar tanto las alertas de bajada de precio como el gráfico "evolución de precio" que ya se vende en el modal de Premium pero no existe todavía (hueco detectado en la auditoría P0) — ninguna de las dos está construida todavía, esto solo prepara los datos.

**⚠️ Pendiente OBLIGATORIO antes de que esto funcione, y sin probar de verdad (escrito sin acceso a la BBDD real):**
1. Ejecutar `scrapers/historico_precios.sql` una vez en el SQL Editor de Supabase — la tabla `historico_precios` todavía NO existe en producción.
2. Probar un scraper cualquiera con `--dry-run` primero y comprobar el mensaje `[dry-run] historico_precios: N cambios detectados` (mercadona no tiene `--dry-run`, tiene confirmación manual s/n — probar con precaución o en una copia).
3. Después de eso, un run pequeño de verdad (una categoría, por ejemplo) y revisar en el SQL Editor que las filas de `historico_precios` tienen sentido antes de confiar en runs completos.
4. Ya comiteado en local (commit `feat(P1): ...`, ver sección 10) — falta ejecutar el SQL y probar, y falta hacer `git push` cuando David decida.
