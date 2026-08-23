"""
scrapers/historico_precios.py — Mi Mejor Cesta
================================================
Helper compartido para registrar el histórico de precios (P1 #4, propuesto y
aprobado por David el 23/08/2026 — enfoque "diff en los scrapers", sin
triggers en la BBDD).

Cada vez que un scraper va a subir precios nuevos, llama a una de las dos
funciones de aquí ANTES (o en vez) de hacer el upsert normal:
- `registrar_cambios_precio()`      → scrapers que usan el cliente supabase-py
                                       (scraper_dia.py, scraper_alcampo.py,
                                       scraper_ahorramas.py, scraper_carrefour.py)
- `registrar_cambios_precio_rest()` → scraper_mercadona.py, que sube precios
                                       con peticiones REST directas (urllib),
                                       no con el cliente supabase-py

Cada función compara el precio nuevo de cada producto con el que ya había en
`precios_<super>` y SOLO si ha cambiado (o el producto es nuevo) inserta una
fila en `historico_precios`. Si el precio es igual que la última vez, no se
inserta nada — así la tabla crece solo con cambios reales, no con una foto
diaria de todo el catálogo.

Requiere la tabla `historico_precios` ya creada en Supabase — ver
`scrapers/historico_precios.sql` (ejecutar una vez en el SQL Editor).

Diseñado para no poder romper nunca la subida de precios normal: cualquier
error al leer o escribir el histórico se avisa por consola y se ignora — el
upsert de precios_* de cada scraper sigue su curso igual.

⚠️ Sin probar contra Supabase real (este fichero se escribió sin acceso a
red desde el entorno donde se generó). Antes de confiar en él: ejecutar
primero cualquier scraper con --dry-run y revisar el mensaje
"[dry-run] historico_precios: N cambios detectados", y solo después dejar
que escriba de verdad con un run pequeño (--cat de una sola categoría, por
ejemplo) y comprobar en el SQL Editor que las filas de historico_precios
tienen sentido.
"""

import datetime


def _hoy_iso():
    return datetime.date.today().isoformat()


def _detectar_cambios(precios_actuales, super_nombre, productos):
    """precios_actuales: dict {id: precio_actual_en_bbdd}.
    productos: lista de dicts con al menos 'id' y 'precio' (el precio que se
    va a subir ahora). Devuelve las filas a insertar en historico_precios:
    solo productos nuevos (no estaban en precios_actuales) o con precio
    distinto al que ya había."""
    hoy = _hoy_iso()
    cambios = []
    for p in productos:
        pid = p.get("id")
        precio_nuevo = p.get("precio")
        if not pid or precio_nuevo is None:
            continue
        precio_anterior = precios_actuales.get(pid)
        try:
            distinto = precio_anterior is None or float(precio_anterior) != float(precio_nuevo)
        except (TypeError, ValueError):
            distinto = True
        if distinto:
            cambios.append({
                "super": super_nombre,
                "id_producto_super": pid,
                "precio": precio_nuevo,
                "fecha": hoy,
            })
    # Defensa añadida 23/08/2026 tras un caso real en Alcampo: si la misma
    # id_producto_super llega repetida dentro de "productos" (p.ej. un
    # scraper con un bug de paginación que devuelve el mismo producto dos
    # veces), aquí se generarían dos filas idénticas para el mismo
    # (super, id_producto_super, fecha) y el INSERT en historico_precios
    # fallaría entero por su índice único. Se deduplica por
    # id_producto_super quedándose con la última aparición.
    por_id = {}
    for c in cambios:
        por_id[c["id_producto_super"]] = c
    return list(por_id.values())


def registrar_cambios_precio(client, tabla_precios, super_nombre, productos, dry_run=False):
    """Para scrapers que usan el cliente supabase-py: scraper_dia.py,
    scraper_alcampo.py, scraper_ahorramas.py, scraper_carrefour.py.

    client:         cliente supabase-py ya conectado (el mismo que usa upsert()).
    tabla_precios:  tabla precios_* de origen, ej. "precios_dia".
    super_nombre:   nombre corto para guardar en historico_precios, ej. "dia".
    productos:      lista de dicts que se van a subir a tabla_precios
                     (cada uno con al menos 'id' y 'precio').
    dry_run:        si es True, no escribe nada — solo cuenta y avisa
                     cuántos cambios detectaría.

    Devuelve el número de cambios detectados (o insertados, si no es dry_run).
    """
    ids = [p["id"] for p in productos if p.get("id")]
    if not ids:
        return 0
    try:
        precios_actuales = {}
        # PostgREST limita el tamaño de "in.(...)" — se consulta en bloques
        for i in range(0, len(ids), 500):
            lote_ids = ids[i:i + 500]
            res = client.table(tabla_precios).select("id,precio").in_("id", lote_ids).execute()
            for row in (res.data or []):
                precios_actuales[row["id"]] = row.get("precio")

        cambios = _detectar_cambios(precios_actuales, super_nombre, productos)
        if not cambios:
            return 0
        if dry_run:
            print(f"    [dry-run] historico_precios: {len(cambios)} cambios de precio detectados (no se escriben)")
            return len(cambios)

        for i in range(0, len(cambios), 500):
            client.table("historico_precios").insert(cambios[i:i + 500]).execute()
        print(f"    📈 historico_precios: {len(cambios)} cambios de precio registrados")
        return len(cambios)
    except Exception as e:
        print(f"    ⚠️  historico_precios: no se pudo registrar ({e}) — no afecta a la subida de precios")
        return 0


def registrar_cambios_precio_rest(supabase_url, headers_sb, tabla_precios, super_nombre, productos, dry_run=False):
    """Para scraper_mercadona.py, que sube precios con peticiones REST directas
    (urllib) en vez del cliente supabase-py. Misma lógica que
    registrar_cambios_precio(), adaptada a REST.

    supabase_url: SUPABASE_URL del scraper.
    headers_sb:   HEADERS_SB del scraper (debe tener 'apikey' y 'Authorization').
    """
    import json
    import urllib.request
    import urllib.error

    ids = [p["id"] for p in productos if p.get("id")]
    if not ids:
        return 0
    try:
        precios_actuales = {}
        read_headers = {
            "apikey": headers_sb["apikey"],
            "Authorization": headers_sb["Authorization"],
        }
        for i in range(0, len(ids), 200):
            lote_ids = ids[i:i + 200]
            filtro = ",".join(lote_ids)
            url = f"{supabase_url}/rest/v1/{tabla_precios}?select=id,precio&id=in.({filtro})"
            req = urllib.request.Request(url, headers=read_headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                for row in json.loads(resp.read().decode()):
                    precios_actuales[row["id"]] = row.get("precio")

        cambios = _detectar_cambios(precios_actuales, super_nombre, productos)
        if not cambios:
            return 0
        if dry_run:
            print(f"  [dry-run] historico_precios: {len(cambios)} cambios de precio detectados (no se escriben)")
            return len(cambios)

        insert_headers = {
            "apikey": headers_sb["apikey"],
            "Authorization": headers_sb["Authorization"],
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        for i in range(0, len(cambios), 200):
            lote = cambios[i:i + 200]
            req = urllib.request.Request(
                f"{supabase_url}/rest/v1/historico_precios",
                data=json.dumps(lote).encode(),
                headers=insert_headers,
                method="POST",
            )
            urllib.request.urlopen(req, timeout=30)
        print(f"  📈 historico_precios: {len(cambios)} cambios de precio registrados")
        return len(cambios)
    except Exception as e:
        print(f"  ⚠️  historico_precios: no se pudo registrar ({e}) — no afecta a la subida de precios")
        return 0
