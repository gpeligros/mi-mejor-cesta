# Mi Mejor Cesta — Contexto del proyecto

> Documento vivo. Se sobrescribe, no se versiona con fechas en el nombre.
> Última revisión: 07/09/2026 (reorganización de ficheros).
> El detalle sesión a sesión, con el porqué de cada decisión anterior, está en
> [`docs/historial-sesiones.md`](docs/historial-sesiones.md).

## 1. Qué es

PWA de comparación de precios de supermercados españoles. El usuario monta su
cesta y ve cuánto le cuesta en cada súper, con asistencia de IA para listas,
menús semanales y recetas.

- **Producción**: https://mi-mejor-cesta.vercel.app
- **Repositorio**: https://github.com/gpeligros/mi-mejor-cesta (rama `main`)
- **Supabase**: `scpuriaofisssalsbzqv.supabase.co`
- **Despliegue**: `git push origin main` → Vercel despliega solo

## 2. Stack, con versiones reales

Verificadas en `frontend/package.json` el 07/09/2026.

| Capa | Qué es | Versión |
|---|---|---|
| Frontend | **Create React App** (`react-scripts`), **no Next.js** | react-scripts 5.0.1 |
| UI | React + React DOM | 19.2.4 |
| Estilos | Tailwind CSS (devDependency) | 3.4.1 |
| Iconos | lucide-react | 1.33.0 |
| BBDD y auth | Supabase (PostgreSQL + Auth email/Google) | supabase-js 2.95.3 |
| Errores | Sentry | 10.52.0 |
| OCR | tesseract.js | 7.0.0 |
| IA | API de Anthropic vía `frontend/api/cestita.js`; también `@google/generative-ai` | 0.24.1 |
| Pagos | Stripe (`frontend/api/stripe-checkout.js`, `stripe-webhook.js`) | — |
| Scrapers | Python 3 (+ Scrapling para Cloudflare y SPAs) | — |
| Admin | Flask, `backend/admin/`, localhost:5000 | — |

**Ojo con dos errores que arrastraba la documentación vieja:** el `README.md`
decía "Next.js / API Routes" y el `CLAUDE.md` decía "React 18". Ninguna de las
dos cosas es cierta. Es CRA con React 19, y las funciones serverless viven en
`frontend/api/`, no en rutas de Next.

## 3. Dónde está todo

```
mi-mejor-cesta/
├── CONTEXTO.md          ← este fichero, el estado real
├── CLAUDE.md            ← resumen corto que apunta aquí
├── README.md            ← escaparate público del proyecto
├── vercel.json          ← rutas y cabeceras del despliegue
├── frontend/            ← la aplicación (CRA)
│   ├── src/components/  ← 23 componentes, uno por pantalla o pieza de UI
│   ├── src/assets/      ← logos de los supermercados
│   ├── src/analytics/   ← Google Analytics
│   └── api/             ← funciones serverless de Vercel (IA y Stripe)
├── scrapers/            ← Python: scraping, matching y pipeline del catálogo
│   └── tests/
├── datos/               ← CSV de trabajo del pipeline (antes se llamaba old/)
├── backend/
│   ├── admin/           ← panel Flask
│   └── api/             ← gestor de productos
├── scripts/             ← utilidades sueltas + binario supabase.exe (ignorado)
├── docs/                ← documentación de apoyo y el historial de sesiones
└── _to_delete/          ← cuarentena: nada se borra, se aparca aquí
```

**Por qué `datos/` se llama así y no `old/`.** Hasta el 07/09/2026 esta carpeta
se llamaba `old`, y el nombre engañaba: no es material descartado, es el
directorio de trabajo del pipeline de reconstrucción del catálogo. Nueve
scripts de `scrapers/` escriben y leen ahí con ruta fija. Se renombró a `datos/`
y se actualizaron las referencias (la variable pasó de `CARPETA_OLD` a
`CARPETA_DATOS`). Si un script vuelve a fallar buscando `old/`, es que se ha
colado una referencia sin actualizar.

**`_to_delete/` está en `.gitignore`.** Es la papelera de revisión: se mueve ahí
lo que sobra en vez de borrarlo, y David decide.

## 4. Arquitectura de BBDD — INAMOVIBLE

No se cambia sin consultar a David. Estas cifras vienen del historial, **no
están verificadas en vivo** (Supabase no es alcanzable desde las sesiones de
Claude, ver sección 9).

| Tabla | Qué guarda | Filas aprox. |
|---|---|---|
| `productos_catalogo` | Catálogo genérico (CAT-xxxx). Solo escribe el admin. | ~16.700 tras la reconstrucción del 20/08 |
| `categorias_maestras` | 87 categorías fijas. No se modifican. | 87 |
| `productos_match` | Tabla puente: `id_catalogo` + un `id_` por súper | — |
| `precios_mercadona` | ME-xxxx | ~8.300 |
| `precios_dia` | DI-xxxx | ~5.000 |
| `precios_alcampo` | AL-xxxx | ~2.264 |
| `precios_carrefour` | CR-xxxx | ~7.241 |
| `precios_ahorramas` | AH-xxxx | ~1.529 |
| `historico_precios` | Cambios de precio para gráficos y alertas | crece con cada run |
| `vista_productos` | VIEW catálogo + categorías | — |
| `profiles` | Plan de cada usuario. PK = `auth.users.id` | — |
| `cestas_online`, `compras`, `compras_detalle`, `menus_guardados` | — | — |

**Métrica que importa de verdad:** productos que comparan precio en **2 o más**
supermercados. En la última reconstrucción completa (20/08/2026) eran 2.104 de
16.727. Todo lo demás es catálogo que solo existe en un súper.

### Reglas de oro
- Los scrapers **nunca** escriben en `productos_catalogo` ni en `categorias_maestras`.
- Nunca se borra un CAT-xxxx: se desactiva con `activo=false`.
- Los cambios de esquema son SQL manual en el editor de Supabase. Nunca se asume
  el estado del esquema: se consulta.
- Antes de cualquier `TRUNCATE`, verificar que existe backup.
- `.env` nunca se sube a Git.
- `DISABLE_ESLINT_PLUGIN=true` en las variables de entorno de Vercel.

### Errores conocidos de Supabase
- Los joins con sintaxis de FK (`categorias_maestras(...)`) fallan si no hay FK
  definida. Hacer consultas separadas.
- RLS recursiva en `profiles` da errores 500. Usar `auth.uid() = id`.
- `AdminPanel.js` debe importar de `../supabaseClient`, no crear su propio `createClient`.
- Un `rpc()` a una función que no existe devuelve 404 en silencio.
- Auth redirige a producción salvo que `localhost` esté en las Redirect URLs.

## 5. Pipeline del catálogo

Ocho scripts en orden. Todos trabajan sobre CSV en `datos/`; **solo el último
toca la base de datos**.

| # | Script | Fase | Qué hace |
|---|---|---|---|
| 1 | `exportar_todos_precios.py` | 1 | Vuelca las 5 tablas `precios_*` a CSV |
| 2 | `normalizar_productos.py` | 2 | Separa nombre base / marca / formato |
| 3 | `agrupar_productos.py` | 3a | Agrupa en clusters (sin coste de IA) |
| 4 | `revisar_clusters_dudosos.py` | 3b | Haiku puntúa 0-10 los bridges dudosos |
| 5 | `construir_propuesta_final.py` | 4 | Aplica las decisiones de la IA |
| 6 | `clasificar_categoria.py` | 4b | Categoriza en 3 capas |
| 7 | `construir_catalogo_v2.py` | 5 | **Reconstruye `productos_catalogo` y `productos_match` en Supabase** |
| 8 | `subir_backup_dia.py` | — | Sube un backup JSON del scraper de DIA |

Ejecutar siempre el paso 7 antes con `--dry-run`.

### Lecciones que costaron caro
- Matching con rapidfuzz: usar **solo** `token_sort_ratio`. Combinar
  `partial_ratio` + `token_set_ratio` produjo matches falsos en masa.
- `process.extractOne` sin asignación 1-a-1 golosa asigna el mismo `id_super` a
  miles de CAT y corrompe la tabla puente.
- El nombre que ve el usuario sale de `productos_catalogo.nombre_generico`
  (limpio), con el nombre crudo del súper debajo en gris cuando difiere. Esa
  prioridad se invirtió a propósito en `SuperCard.js` el 25/08/2026.
- Marca blanca → nombre genérico. Marca de fabricante → solo si aparece en 2+ supers.
- Formatos distintos (33cl vs 50cl) son entradas separadas del catálogo.
- En `AdminPanel`, `SUPERS_CONFIG` va **fuera** del componente `Precios`, y las
  funciones se definen antes de los `useEffect` que las usan.

## 6. Estado de los supermercados

Del historial, sin verificar en vivo. Contrastar en el panel admin antes de
tomar decisiones sobre estas cifras.

| Súper | Estado |
|---|---|
| Mercadona | En producción |
| DIA | En producción. Scraper reescrito contra la API real (10/08/2026) |
| Carrefour | En producción, pero **el scraper está roto**: hay que redescubrir la API con DevTools |
| AhorraMás | En producción |
| Alcampo | En producción con huecos: el 61,7% de las filas venían sin `nombre_comercial`. El código ya está corregido; falta el re-scrape que limpie los datos viejos |
| Lidl, Eroski, Hipercor | Sin empezar. Hipercor tiene API pública |

## 7. Planes de suscripción

| Plan | Precio | maxSupers | maxProductos | Menú semanal | Recetas IA | Nutricional |
|---|---|---|---|---|---|---|
| free | 0 € | 2 | 20 | no | no | no |
| basic | 2,99 €/mes | 999 | 999 | no | no | no |
| premium | 6,99 €/mes | 999 | 999 | sí | sí | sí |

**Stripe sigue en modo TEST.** Pasarlo a producción es lo último de la lista.

## 8. Qué está pendiente, por prioridad

### Bloqueantes
1. **Reescribir `scraper_carrefour.py`.** Mismo método que se usó con DIA:
   DevTools → capturar la API real → reconstruir. Necesita a David o una sesión
   con navegador conectado; desde el entorno de Claude no hay acceso.
2. **Re-ejecutar `scraper_alcampo.py`** para limpiar los nombres vacíos que ya
   están en la BBDD. El código está arreglado desde el 23/08; falta el run real.
3. **Pasar Stripe de test a producción.** Lo último.

### Importante
4. Verificar en la app que los nombres del catálogo se ven limpios tras el fix
   del 23/08 y anotar aquí las cifras reales de esa ejecución.
5. Revisar el grupo de ficheros con cambios locales sin comitear de origen no
   verificado (`backend/api/app_gestion.py` es el mayor, 758 líneas) y decidir
   qué se queda. Están listados en `docs/historial-sesiones.md`, sección 10.
6. Versionar la definición de la VIEW `vista_productos` en un `.sql` del repo:
   hoy solo existe dentro de Supabase y no se puede revisar desde fuera.

### Funcionalidades pedidas, sin empezar
7. Puntuación nutricional tipo Yuka (Open Food Facts + EAN, semáforo 0-100).
   La mayoría de scrapers ya capturan el EAN.
8. Mejorar menús semanales y la parte nutricional actual.

### Menor
9. El gráfico de evolución de precios y las alertas no mostrarán nada hasta que
   algún producto acumule 2 fechas distintas en `historico_precios`. Se llena
   solo según se ejecuten los scrapers; no hace falta hacer nada.
10. Marcas reales sin etiquetar coladas en el matching de marca blanca (~0,3%).

## 9. Trampas del entorno — léelas antes de intentar nada

- **Supabase no es alcanzable** ni desde el entorno cloud de Claude ni desde la
  shell del puente al ordenador de David: la política de red solo deja pasar
  GitHub, npm, PyPI y poco más. Todo el SQL lo ejecuta David en el editor de
  Supabase, **una consulta por mensaje**.
- **Claude no puede ejecutar `git`** desde el puente: deja bloqueados ficheros
  `.git/index.lock` que solo David puede borrar. Todos los comandos de git los
  ejecuta él.
- **`npm` y `npx` fallan** desde la máquina del puente: los `node_modules` están
  instalados para Windows. Los ejecuta David y pega la salida.
- **Claude no puede borrar ficheros** en la carpeta conectada. `mv` sí funciona:
  todo lo que sobra va a `_to_delete/` y David lo borra desde su terminal.
- **Cada proyecto en su puerto.** Este se queda en el **3000**; `mi-mejor-ruta`
  usa el 3100. Comparten `localhost` y se pisan: con los dos servidores
  levantados, `localhost:3000` sirve el que arrancara primero.
- **La terminal de David es PowerShell**, no bash: no soporta `&&` ni tiene
  `wc`, `grep` ni `sed`. Los comandos que se le pasen van uno por mensaje y en
  sintaxis de PowerShell (`Measure-Object`, `Select-String`).
- **Claude sí tiene sed y python3** en la VM del puente, aunque el repositorio
  esté en Windows. La regla vieja de "nunca uses sed" venía de cuando los
  comandos se ejecutaban en PowerShell.

## 10. Historial

El detalle completo de cada sesión —diagnósticos, por qué se decidió cada cosa,
qué se probó y qué se descartó— está en
[`docs/historial-sesiones.md`](docs/historial-sesiones.md), que cubre hasta el
25/08/2026. Este `CONTEXTO.md` es el resumen vivo; el otro no se toca más, solo
se consulta.

### 07/09/2026 — Reorganización de ficheros
- `old/` renombrada a **`datos/`** y actualizadas las referencias en 8 scripts
  (`CARPETA_OLD` → `CARPETA_DATOS`). Verificado que los 30 ficheros de
  `scrapers/` siguen compilando.
- De los 88 CSV de esa carpeta se dejó **el más reciente de cada uno de los 19
  tipos**; los otros 69 (67 MB) están en `_to_delete/csv-antiguos/`.
- `docs/README_old.md` y los 8 logos `*_old.*` de `frontend/src/assets/`
  (comprobado: no los importaba nadie) movidos a `_to_delete/`.
- `.gitignore` ampliado con `.claude/` y `_to_delete/`.
- `docs/CONTEXTO.md` pasa a ser `docs/historial-sesiones.md`; el contexto vivo
  es este fichero, en la raíz.
- Los dos worktrees huérfanos de `.claude/worktrees/` (232 MB, copias de abril
  cuyo `.git` apuntaba a `C:/Users/ccash/...`, una ruta que ya no existe) se
  desregistraron con `git worktree prune` y se movieron a `_to_delete/`. Las
  ramas `claude/elastic-shamir-d7e3e0` y `claude/focused-banzai-3781da` siguen
  en el repositorio: aquel trabajo no se ha perdido.
- **`ARCHIVO_HISTORICO/` sacada del proyecto** a `C:\dev\_archivo\mi-mejor-cesta\`.
  Eran 23 MB y 138 ficheros trackeados; el commit que los quita deja el
  contenido en el historial de git por si algún día hace falta.
- `_to_delete/` acumula 299 MB en cuatro carpetas (`worktrees-huerfanos/`,
  `csv-antiguos/`, `assets-antiguos/`, `docs/`). Está en `.gitignore`; la borra
  David cuando la haya revisado.
- **Pendiente menor:** hay dos entornos virtuales, `.venv` y `.venv-1`. Sobra
  uno, pero no se ha tocado porque no se sabe cuál usa David.
