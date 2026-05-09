# MATCHES_PLAN.md - Mi Mejor Cesta

Plan de ejecucion del matching de los supermercados pendientes.
Lee esto antes de ejecutar nada y ve marcando los pasos a medida que avanzas.

> Importante: ejecuta TODO desde la raiz del proyecto en PowerShell, en
> este orden, y no saltes pasos. Cada matching deja un CSV de "dudosos"
> que conviene revisar manualmente antes de aplicar el siguiente.

---

## PASO 0 - Estado actual

```powershell
python scrapers/verificar_estado.py
```

El script imprime cuantos productos hay en cada tabla `precios_*` y cuantos
matches hay en `productos_match`. Al final te dice exactamente que comandos
ejecutar a continuacion.

---

## PASO 1 - Carrefour (matching basico)

Memory del proyecto indica ~7.241 productos en `precios_carrefour` con 0 matches.
El script ya esta probado (v5) y la columna `id_carrefour` ya existe en
`productos_match`. App.js ya esta enchufado para mostrar Carrefour en el frontend.

```powershell
# 1.1 Dry-run (no escribe nada, solo muestra que matches haria)
python scrapers/match_carrefour.py --dry-run

# 1.2 Mira la salida:
#     - Cuantos automaticos (>=83%)
#     - Cuantos dudosos (60-82%)
#     - Sample de los primeros 20

# 1.3 Si los automaticos pintan bien, ejecutar real:
python scrapers/match_carrefour.py
# Te pedira confirmacion (s/n) antes de aplicar.

# 1.4 Revisar el CSV de dudosos generado en la raiz:
#     carrefour_dudosos_YYYYMMDD_HHMM.csv
#     Abrir en Excel, marcar columna "ok" con 1 los validos
#     y luego importar manualmente los buenos.
```

Resultado esperado: subir de ~0 a 1.500-2.500 matches automaticos de Carrefour.

---

## PASO 2 - Ahorramas (rematch tras rebuild de catalogo)

Memory dice que tras la reconstruccion del catalogo Ahorramas paso de
muchos matches a 0. App.js ya consulta `precios_ahorramas` y mapea
`id_ahorramas`, asi que en cuanto haya matches reales se vera en
frontend automaticamente.

```powershell
# 2.1 Dry-run
python scrapers/match_ahorramas.py --dry-run

# 2.2 Si pinta bien, real
python scrapers/match_ahorramas.py
```

Resultado esperado: similar a Mercadona en cobertura (Ahorramas tiene catalogo
mas pequeno, ~500-800 matches).

---

## PASO 3 - Hipercor (scraping desde cero + matching)

Hipercor no esta en BBDD aun. Hay que:

1. Anadir columna `id_hipercor` a `productos_match`.
2. Ejecutar el scraper.
3. Ejecutar el matching.
4. Anadir Hipercor a `LogosSuper.js` y a App.js (consulta + mapeo).

```sql
-- En el SQL Editor de Supabase, una vez:
ALTER TABLE productos_match ADD COLUMN id_hipercor TEXT;
```

```powershell
# 3.1 Scraping (puede tardar 30-60 min, scrapea hipercor.es)
python scrapers/scraper_hipercor.py

# 3.2 Verificar que se ha llenado precios_hipercor
python scrapers/verificar_estado.py

# 3.3 Matching dry-run
python scrapers/match_hipercor.py --dry-run

# 3.4 Si pinta bien, real
python scrapers/match_hipercor.py
```

Una vez con datos, se anade Hipercor a `frontend/src/components/LogosSuper.js`
(con su logo en `frontend/src/assets/`) y al array `SUPERS_VALIDOS` en App.js.
Tambien hay que anadir las consultas a `precios_hipercor` y mapear `id_hipercor`
analogamente a como esta hecho con Carrefour.

---

## Antes de relanzar la app en local

Cierra todas las terminales con `npm start` corriendo y vuelve a abrir:

```powershell
cd frontend
npm start
```

Si `npm start` ya esta corriendo en otra ventana, basta con guardar los cambios:
React recargara solo. Pero si has tocado `index.html` o `manifest.json` hace
falta cerrar y reabrir para que se sirva la version nueva.

---

## Si algo falla

- `403 Forbidden` o `Permission denied` en Supabase: tu `.env` no tiene la
  service_role key correcta. Verifica que `SUPABASE_KEY` empieza por `eyJ...`
  y al decodificar tiene `"role":"service_role"`.
- `ImportError` con `socksio`: ejecuta `pip install httpx[socks]`.
- `psycopg2` u otro modulo: `pip install -r requirements.txt` (en `scrapers/`
  o donde tengas tu fichero de dependencias).
- Si `match_*.py` no encuentra `rapidfuzz`: `pip install rapidfuzz`.

---

## Resumen visual de progreso

| Supermercado  | Frontend | BBDD precios | Match BBDD | Listo? |
|---------------|----------|--------------|------------|--------|
| Mercadona     | OK       | OK           | 4.173      | Si     |
| DIA           | OK       | OK           | 608        | Si     |
| Alcampo       | OK       | OK           | 121        | Si     |
| Ahorramas     | OK       | OK           | 0 -> ?     | Paso 2 |
| Carrefour     | OK       | ~7.241       | 0 -> ?     | Paso 1 |
| Hipercor      | NO       | NO           | NO         | Paso 3 |

