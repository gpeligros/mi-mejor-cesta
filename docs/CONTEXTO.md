# MI MEJOR CESTA — Contexto del Proyecto (Actualizado 25/07/2026)

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
SIEMPRE --dry-run antes de cualquier script que escriba en Supabase.
SIEMPRE backup a CSV antes de cualquier operación destructiva (no hay backups automáticos).
La ruta local del repo es C:\dev\mi-mejor-cesta. El usuario es "gpeligros" (nunca "ccash").

---

## 🔥 NOVEDADES SESIÓN 25/07/2026 (leer primero)

Sesión larga centrada en calidad de datos. Resumen de lo hecho:

1. **CAUSA RAÍZ ENCONTRADA Y RESUELTA — IDs de catálogo duplicados.**
   18 IDs (CAT-1000 a CAT-1017) apuntaban a VARIOS productos a la vez (11 cada uno):
   1 producto original + 10 colisiones de una importación defectuosa de Carrefour.
   Esto era la raíz de dos misterios que arrastrábamos:
   - El score de Carrefour que solo se guardó en 626 de 4.376 filas (el
     `UPDATE ... WHERE id_catalogo = 'CAT-xxxx'` tocaba 11 filas a la vez).
   - Las "falsas alarmas" del reviewer de AhorraMas (el índice por CAT-id se
     quedaba con uno al azar de los 11 productos).
   **Arreglado:** backup completo → borrado quirúrgico de las 172 colisiones
   (conservando el original de cada ID, el de `nombre_normalizado` null) →
   verificado: 0 duplicados, catálogo a 9.999 IDs únicos.

2. **Limpieza de las 18 filas de match afectadas** (CAT-1000..1017):
   - Carrefour: los 18 estaban MAL (colisiones) → anulados (`id_carrefour = NULL`).
   - DIA: anulados 6 malos (CAT-1002,1004,1009,1010,1013,1014); 4 de cerveza correctos se conservan.
   - AhorraMas: anulados 2 malos (CAT-1003,1006); 4 correctos se conservan.

3. **Scripts nuevos creados** (ver Sección 7): `backup_catalogo.py`,
   `match_carrefour.py` v6, `match_ahorramas.py` v4, `revisar_matches_ahorramas.py`.

4. **AhorraMas congelado a mitad** (279 matches aplicados con v4): el reviewer de IA
   quedó listo pero NO ejecutado sobre el catálogo limpio. Es lo primero a retomar.

5. **Identificado el PRÓXIMO GRAN PROYECTO**: contaminación del catálogo por la
   importación de Carrefour (entradas demasiado específicas por SKU, marcas blancas
   que no se enfrentan entre sí). Ver Sección 11.

**Pendiente de commitear:** este CONTEXTO + los 4 scripts nuevos.

---

## 1. Qué es el proyecto
App web PWA de comparación de precios de supermercados españoles.
URL producción: https://mi-mejor-cesta.vercel.app
Repositorio: https://github.com/gpeligros/mi-mejor-cesta
Ruta local: C:\dev\mi-mejor-cesta

---

## 2. Stack tecnológico
- Frontend: **React 19.2** + Tailwind CSS — Vercel
- Base de datos: Supabase (PostgreSQL) — scpuriaofisssalsbzqv.supabase.co
- Autenticación: Supabase Auth (email + Google OAuth)
- Scrapers/matching: Python 3 — carpeta /scrapers
- IA (CESTITA y reviewers): Anthropic Claude API (`claude-haiku-4-5-20251001`)
- Pagos: Stripe (checkout + webhook)
- Monitorización errores: @sentry/react INSTALADO pero DESACTIVADO (comentado en index.js)
- Analítica: Google Analytics GA4 real (G-2WJFBS3PW6)
- Deploy: Vercel — git push a main despliega automáticamente
- DISABLE_ESLINT_PLUGIN=true en Vercel

### Dependencias a revisar (deuda)
- `@google/generative-ai`: en package.json del frontend pero NO se usa en el bundle → eliminar.
- `tesseract.js`: instalado pero el OCR (handleFoto) sigue sin implementar → implementar o eliminar.

---

## 3. Estructura de carpetas (resumen)
```
mi-mejor-cesta/
  frontend/
    api/            cestita.js, cors_helper.js, stripe-checkout.js, stripe-webhook.js
    src/            App.js (5 supers), supabaseClient.js (solo anon key), index.js (React 19 + ErrorBoundary)
      components/   Cestita, MenuSemanal, ModalUpgrade, Sidebar, SuperCard, StoreSelector,
                    ToolBar, LogosSuper, AuthModal, ErrorBoundary, CookieBanner/Cookies (posible duplicidad)...
      hooks/        usePlan.js
  scrapers/         scrapers + matching + reviewers (ver Sección 7)
  scripts/          utilidades ⚠️ contiene supabase.exe (93 MB, sacar de git)
  old/              backups CSV + código antiguo (16 MB)
  docs/CONTEXTO.md  este fichero
  vercel.json       cabeceras de seguridad (CSP, HSTS…)
```

---

## 4. Variables de entorno
### Vercel (confirmar si Stripe sigue en TEST o ya en LIVE)
REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY, ANTHROPIC_API_KEY,
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_BASIC/PREMIUM,
STRIPE_*_PROD (guardadas para live), SUPABASE_SERVICE_KEY, APP_URL,
DISABLE_ESLINT_PLUGIN=true, (REACT_APP_SENTRY_DSN pendiente si se activa Sentry)

### Local (.env en raíz — está en .gitignore ✅)
SUPABASE_URL, SUPABASE_KEY (**service_role** — necesaria para que los scripts escriban),
ANTHROPIC_API_KEY, REACT_APP_SUPABASE_URL, REACT_APP_SUPABASE_ANON_KEY

> ⚠️ Con la anon key los scripts NO escriben y NO dan error (RLS lo bloquea en
> silencio). Verificar siempre que SUPABASE_KEY es la service_role antes de aplicar.

---

## 5. Arquitectura de BBDD — INAMOVIBLE

### Tablas principales (VERIFICADO 25/07/2026, tras dedup del catálogo)
| Tabla | Descripción | Filas |
|-------|-------------|-------|
| `productos_catalogo` | Catálogo genérico. **Deduplicado el 25/07** (tenía 172 colisiones). | **9.999** IDs únicos |
| `categorias_maestras` | 87 categorías fijas. NUNCA modificar. | 87 |
| `productos_match` | Tabla puente CAT↔supermercados (1 fila por CAT-id). | 9.999 |
| `precios_mercadona` | IDs ME-xxxx. | ~8.327 |
| `precios_dia` | IDs DI-xxxx. | ~4.786 |
| `precios_alcampo` | IDs AL-xxxx. | 727 |
| `precios_carrefour` | IDs CF-xxxx. | ~7.241 |
| `precios_ahorramas` | IDs AH-xxxx **y AM-xxxx** (dos generaciones de scraper). | ~1.529 |
| `vista_productos` | VIEW catálogo + categorías. | — |
| `profiles`, `cestas_online`, `compras`, `compras_detalle`, `listas_colaborativas` | — | activas |

### Esquema productos_catalogo (VERIFICADO)
id, nombre_generico, marca, imagen, orden, created_at, activo, id_categoria,
tipo (marca_blanca/marca_fabricante), formato, **nombre_normalizado**, ean
> Nota: `nombre_normalizado` está a NULL en casi todo el catálogo (solo se rellenó
> en los productos importados de Carrefour). El matching usa `nombre_generico`,
> NO `nombre_normalizado`. Un reviewer que compare DEBE usar nombre_generico.

### Columnas productos_match (VERIFICADO)
id, id_catalogo, created_at, revisado,
id_mercadona, id_dia, id_alcampo, id_ahorramas, id_carrefour, id_hipercor, id_lidl, id_aldi,
id_alcampo_score, id_carrefour_score
(id_lidl/id_aldi/id_hipercor existen pero el frontend NO las consulta)
> NO existe id_ahorramas_score. `revisado` está a 0 en todas las filas.

### ⚠️ CAUSA RAÍZ 25/07 — IDs de catálogo duplicados (RESUELTO)
La importación de Carrefour (`construir_catalogo_desde_carrefour.py`,
`agregar_carrefour_faltantes.py`) generó IDs que CHOCARON con 18 que ya existían
(CAT-1000 a CAT-1017) en vez de crear nuevos. Cada uno acabó con 1 original + 10
colisiones (CAT-1017 solo 2). Se arregló borrando las 172 colisiones
(`DELETE ... WHERE id IN (18 ids) AND nombre_normalizado IS NOT NULL`),
conservando el original de cada ID. Verificado: 0 duplicados.
**Lección:** cualquier proceso que cree entradas en el catálogo DEBE garantizar IDs
únicos. Comprobar siempre con `COUNT(*) vs COUNT(DISTINCT id)` tras importar.

### Reglas de oro
- NUNCA scrapers escriben en productos_catalogo ni categorias_maestras
- NUNCA borrar CAT-xxxx activos a la ligera; el ID debe ser único (1 ID = 1 producto)
- NUNCA subir .env a Git
- Antes de cualquier DELETE/UPDATE masivo: backup CSV con `backup_catalogo.py` +
  SELECT COUNT de prueba que confirme exactamente cuántas filas se tocan
- RLS: usar siempre auth.uid() = id (NO políticas recursivas sobre profiles → error 500)
- El frontend SOLO expone la anon key (protegida por RLS). NUNCA service_role en el frontend.

### ⚠️ REGLA SUPABASE — GRANT obligatorio en tablas nuevas (desde 30/10/2026)
A partir del 30/10/2026, toda tabla nueva en `public` necesita GRANT explícito para
ser accesible vía Data API. Aplicar al crear cualquier tabla nueva:
```sql
GRANT SELECT ON public.nueva_tabla TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.nueva_tabla TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.nueva_tabla TO service_role;
ALTER TABLE public.nueva_tabla ENABLE ROW LEVEL SECURITY;
CREATE POLICY "..." ON public.nueva_tabla FOR SELECT TO authenticated USING (...);
```
Tablas existentes NO afectadas. Revisar Security Advisor antes de octubre.

---

## 6. Estado de supermercados (25/07/2026, tras las limpiezas)

| Supermercado | Matches aprox. | Estado / calidad |
|---|---|---|
| Mercadona | 3.991 | Base histórica fiable (sin tocar esta sesión) |
| Carrefour | ~4.358 (4.376 v6 − 18 anulados) | Filtro de FORMATO aplicado ✅, pero SIN revisión semántica IA (pendiente) |
| DIA | ~1.134 (1.140 − 6 anulados) | Limpiado con IA en su día |
| AhorraMas | ~277 (279 v4 − 2 anulados) | ⚠️ CONGELADO: reviewer IA listo pero sin ejecutar sobre catálogo limpio |
| Alcampo | 201 | Limpiado con IA en su día |
| Hipercor | 0 | scraper_hipercor.py falla con HTTP 520 |
| Lidl / Eroski / La Despensa / Aldi | 0 | scrapers existen (algunos) pero sin datos en prod |

> Ningún super cubre el 100% del catálogo (creció a 9.999). Mercadona ≈ 40%.
> Los 5 supers (Mercadona, DIA, Alcampo, AhorraMas, Carrefour) están `visible: true`
> en LogosSuper.js y cableados en App.js.

---

## 7. Scripts de scraping / matching / revisión

### Convención de nombres
scraper_{super}.py · match_{super}.py · match_{super}_ia.py ·
revisar_matches_{super}.py · {super}_setup.sql · enriquecer_{tabla}.py

### Scripts clave y su estado
- `backup_catalogo.py` **(NUEVO 25/07)** — descarga productos_catalogo COMPLETA a
  old/ paginando. Usar SIEMPRE antes de operaciones destructivas (el Download CSV
  del SQL Editor solo exporta ~100 filas de vista previa, NO sirve de backup).
- `match_carrefour.py` **v6 (NUEVO 25/07)** — token_sort_ratio 83% + filtro variantes
  + filtro tipo + **filtro de FORMATO** (extraer_formato/formatos_compatibles: descarta
  "4 Ud vs 6 Ud", packs; normaliza a g/ml/ud) + **escribe id_carrefour_score**.
- `match_ahorramas.py` **v4 (NUEVO 25/07)** — igual que Carrefour v6: filtro de formato
  + el dry-run muestra los 20 automáticos MÁS FLOJOS (banda de riesgo). Marca blanca = "Alipende".
- `revisar_matches_ahorramas.py` **(NUEVO 25/07)** — puntúa cada match 0-10 con Claude
  (haiku) para cazar errores SEMÁNTICOS (mismo tipo, distinto subtipo: bodegas, sabores,
  cerdo/pavo, tallas). Compara contra **nombre_generico**. Genera CSV de revisados,
  CSV de incorrectos y un **.sql de limpieza** listo para ejecutar a mano. NO escribe en BBDD.
- `revisar_matches_dia.py` / `revisar_matches_alcampo.py` — plantillas previas (solo CSV,
  sin generar SQL). El de AhorraMas es la versión mejorada.
- Otros presentes: scraper_mercadona/dia/alcampo/carrefour/ahorramas/hipercor/eroski/despensa,
  scraper_*_gemini.py (variantes Python con Gemini), match_hipercor/eroski/ean.py,
  scraper_openprices.py, construir_catalogo_desde_carrefour.py, agregar_carrefour_faltantes.py.

### Patrón de reparación de matches de un súper (probado con Carrefour y AhorraMas)
1. `python scrapers/backup_catalogo.py` (o backup de la columna concreta a CSV)
2. Vaciar los matches actuales del súper (`UPDATE ... SET id_X = NULL WHERE id_X IS NOT NULL`)
   — necesario porque el script SALTA los que ya tienen match
3. `python scrapers/match_X.py --dry-run` y revisar resumen + muestra flojos
4. Aplicar (sin --dry-run), confirmar con `s`
5. `python scrapers/revisar_matches_X.py --dry-run` → revisar → run completo → ejecutar el .sql de limpieza
6. Verificar con SELECT COUNT

---

## 8. Planes de suscripción (usePlan.js — VERIFICADO)
| Plan | Precio | Límites |
|---|---|---|
| free / free_reg | 0€ | 2 supers, 20 productos |
| basic | 2,99€/mes | ilimitado + CESTITA + historial (3m) + estadísticas + escaneo |
| premium | 6,99€/mes | + menú semanal + recetas IA + nutricional + 30 menús guardados |

IDs Stripe: prod_UHT4B2MREHH2nE (Básico), prod_UHT7TEyO5Iv4SC (Premium),
price_1TIu8THqX5envLqIAn8ZDQh0 (Básico live), price_1TIuBcHqX5envLqIBIpWBKTQ (Premium live).

⚠️ Bug latente: en usePlan.js las claves de CESTITA están mal escritas (`cestivaBasic`/
`cestivaFull`, falta la "t"). Inocuo ahora (ningún componente las llama). Corregir al tocar el fichero.

---

## 9. Funcionalidades implementadas ✅
Comparador 5 supers · sidebar 87 categorías · buscador · filtros marca blanca/General ·
Auth (email+Google) · lista colaborativa tiempo real · exportar PDF · PWA ·
CESTITA (serverless, manipula cesta) · ModalUpgrade con Stripe real · usePlan ·
SuperCard con reference_price · guardar compras + historial + estadísticas ·
cestas_online · ToolBar (menú/recetas/nutricional premium) · ErrorBoundary ·
cabeceras de seguridad en vercel.json · carga paginada en App.js.
Cambios antiguos "pendientes" (props MenuSemanal, integración Carrefour, ALTER id_carrefour_score): YA HECHOS.

---

## 10. Problemas conocidos / Deuda técnica

### 🔴 Críticos / próximos
- **Contaminación del catálogo por la importación de Carrefour** (ver Sección 11) — próximo gran proyecto.
- **AhorraMas congelado**: pasar el reviewer IA sobre catálogo limpio y aplicar limpieza.
- **Carrefour sin revisión semántica**: aplicado con filtro de formato pero le faltan
  los errores de subtipo (vinos/sabores). Conviene un `revisar_matches_carrefour.py`
  (adaptar el de AhorraMas, usa nombre_generico).
- **Stripe en TEST** (confirmar) → pasar a producción es la puerta final de monetización.

### 🟡 Importantes
- `id_carrefour_score` solo poblado en ~626 filas (secuela de los IDs duplicados,
  ya resueltos). Cosmético; se arreglaría en un re-run limpio de Carrefour.
- precios_ahorramas mezcla prefijos AH- (1.442) y AM- (87). Los AM- son productos
  distintos (0 duplicados con AH-), no molestan.
- Sentry instalado pero DESACTIVADO → sin monitorización real de errores.
- `@google/generative-ai` dep muerta; `tesseract.js` instalado sin usar (OCR sin implementar).
- Hipercor: scraper falla HTTP 520.
- Posible duplicidad CookieBanner.js / Cookies.js.

### 🟢 Higiene de repo
- `scripts/supabase.exe` (93 MB) commiteado → sacar del repo/historial.
- `frontend/build/` trackeada en git (26 ficheros) → dejar de trackear + .gitignore.
- `.claude/` y `.playwright-mcp/` sin trackear → añadir a .gitignore.
- old/ (16 MB) → limpiar (pero conservar los backups CSV recientes).

### 🔵 Infraestructura
- Supabase breaking change 30/10/2026 (ver Sección 5).

---

## 11. 🎯 PRÓXIMO GRAN PROYECTO — Sanear el catálogo (contaminación Carrefour)

Detectado el 25/07 por observación del usuario. Dos síntomas, una misma causa:

**Síntoma A — entradas demasiado específicas / duplicadas semánticas.**
Ej: hay ~20 entradas distintas de "Cerveza Mahou 5 Estrellas" (cada formato/pack como
entrada aparte), y además "5 Estrellas" vs "Cinco Estrellas" conviven sin unificar.
Resultado: los matches "no salen" porque compiten entradas hiper-específicas en vez de
una genérica.

**Síntoma B — productos específicos de Carrefour que no se pueden comparar.**
La importación metió miles de productos propios de Carrefour como entradas nuevas del
catálogo, sin genérico al que engancharse. Nunca se comparan con otros súper.

**Causa raíz:** `construir_catalogo_desde_carrefour.py` creó UNA ENTRADA NUEVA POR SKU
en vez de remapear cada producto a un genérico ya existente. (Misma importación
defectuosa que causó los IDs duplicados ya resueltos.)

**Modelo correcto del catálogo:** debe tener productos GENÉRICOS
(ej: "Aceite de oliva virgen extra", "Cerveza rubia lager") a los que se enganchan
el producto de cada súper (Hacendado, marca DIA, Alipende, Carrefour, marca...).
Las marcas blancas de distintos súper deben enfrentarse entre sí a través del genérico.

**Plan futuro (a diseñar con calma):**
1. Medir cuántas entradas del catálogo son "específicas de Carrefour" sin match cruzado.
2. Decidir estrategia: remapear a genéricos existentes / desactivar (activo=false) las
   sobrantes / normalizar variantes ("5 Estrellas"="Cinco Estrellas").
3. Backup obligatorio antes de nada.
4. Rehacer matches de Carrefour y AhorraMas sobre el catálogo saneado.

---

## 12. Comandos útiles
```powershell
# Local (PowerShell — NO usar &&, comandos por separado). Ruta: C:\dev\mi-mejor-cesta
cd frontend
npm start

# Deploy
git add .
git commit -m "descripcion"
git push origin main

# Backup del catálogo (SIEMPRE antes de operaciones destructivas)
python scrapers/backup_catalogo.py

# Matching / revisión (SIEMPRE --dry-run primero)
python scrapers/match_carrefour.py --dry-run
python scrapers/match_ahorramas.py --dry-run
python scrapers/revisar_matches_ahorramas.py --dry-run
```

---

## 13. Pendientes por orden de prioridad

### En curso / inmediato
1. ⏳ Retomar AhorraMas: reviewer IA (dry-run → completo → ejecutar .sql de limpieza) sobre catálogo limpio.
2. ⏳ Revisión semántica de Carrefour (crear revisar_matches_carrefour.py).

### Calidad de datos (el gran tema)
3. ⏳ Sanear el catálogo — contaminación Carrefour (Sección 11).
4. ⏳ Rehacer matches Carrefour/AhorraMas sobre catálogo saneado.
5. Mejorar cobertura DIA/Alcampo; minar los "dudosos" (60-82%).

### Monetización (puerta final)
6. ⏳ Confirmar Stripe y pasar a producción (keys/price/webhook live + transacción real de prueba).

### Endurecimiento
7. Activar Sentry (REACT_APP_SENTRY_DSN + descomentar index.js).
8. Eliminar @google/generative-ai; decidir sobre tesseract.js.
9. Verificar GA4 en producción.

### Higiene de repo
10. Sacar supabase.exe del historial; dejar de trackear build/; .gitignore de .claude/ y .playwright-mcp/.

### Otros súper
11. Fix scraper Hipercor (HTTP 520). Lidl/Eroski/La Despensa.
