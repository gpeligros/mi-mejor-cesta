"""
Mi Mejor Cesta — Panel de Administración
=========================================
UN solo fichero Flask con TODAS las funciones de gestión.
Solo para el administrador. Corre en localhost:5000.
NUNCA es público — no lo ve el usuario final.

Arrancar:
    cd backend/admin
    pip install -r requirements.txt
    python app.py
    Abrir http://localhost:5000
"""

import os, subprocess, threading, time, csv, io
from flask import Flask, jsonify, request, render_template, Response, send_file
from datetime import datetime

# ── Cargar .env desde la raíz del proyecto ─────────────────────────────────
from pathlib import Path
env_path = Path(__file__).resolve().parents[2] / '.env'
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SCRAPERS_DIR = str(Path(__file__).resolve().parents[2] / 'scrapers')

if not SUPABASE_KEY:
    print("\n⚠️  SUPABASE_KEY no configurada.")
    print("   Añade SUPABASE_KEY=tu_service_role_key en el fichero .env de la raíz\n")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
app = Flask(__name__)

# ── Buffer de logs para scrapers ───────────────────────────────────────────
scraper_logs    = {}
scraper_status  = {}

SCRAPERS = {
    "mercadona":          "scraper_mercadona_v2.py",
    "dia":                "scraper_dia_v3.py",
    "match_dia":          "match_dia.py",
    "matching_dia_v2":    "matching_dia_v2.py",
    "gestor_masivo":      "gestor_masivo_fixed.py",
    "aplicar_dudosos":    "aplicar_dudosos.py",
    "aplicar_revisados":  "aplicar_matches_revisados.py",
    "carrefour":          "scraper_carrefour.py",
    "lidl":               "scraper_lidl.py",
}
for k in SCRAPERS:
    scraper_status[k] = {"estado": "idle", "ultimo": None, "duracion": None}

# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════════════════════

def fetch_all(tabla, columnas="*"):
    """Descarga todos los registros de una tabla paginando."""
    rows, offset = [], 0
    while True:
        res = supabase.table(tabla).select(columnas).range(offset, offset + 999).execute()
        rows.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    return rows

# ══════════════════════════════════════════════════════════════════════════════
# FRONTEND (sirve el panel)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    return send_file(html_path, mimetype="text/html")

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — ESTADÍSTICAS / DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/stats")
def stats():
    try:
        cat    = supabase.table("productos_catalogo").select("id", count="exact").execute()
        merc   = supabase.table("precios_mercadona").select("id", count="exact").execute()
        dia    = supabase.table("precios_dia").select("id", count="exact").execute()
        match  = supabase.table("productos_match").select(
            "id_catalogo,id_mercadona,id_dia", count="exact").execute()

        con_merc = sum(1 for r in match.data if r.get("id_mercadona"))
        con_dia  = sum(1 for r in match.data if r.get("id_dia"))
        revisados = sum(1 for r in
            supabase.table("productos_match").select("revisado").execute().data
            if r.get("revisado"))

        usuarios = supabase.table("cestas_online").select("user_id", count="exact").execute()

        return jsonify({
            "catalogo":       cat.count,
            "mercadona":      merc.count,
            "dia":            dia.count,
            "matches":        match.count,
            "con_mercadona":  con_merc,
            "con_dia":        con_dia,
            "sin_mercadona":  match.count - con_merc,
            "sin_dia":        match.count - con_dia,
            "revisados":      revisados,
            "usuarios":       usuarios.count,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CATÁLOGO (productos_catalogo)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/catalogo")
def get_catalogo():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    q        = request.args.get("q", "")
    categoria = request.args.get("categoria", "")
    start = (page - 1) * per_page

    query = supabase.table("productos_catalogo").select("*", count="exact")
    if q:        query = query.ilike("nombre_generico", f"%{q}%")
    if categoria: query = query.eq("categoria", categoria)

    res = query.range(start, start + per_page - 1).order("id").execute()
    return jsonify({"data": res.data, "total": res.count})

@app.route("/api/catalogo/<id>", methods=["PATCH"])
def update_catalogo(id):
    body   = request.json
    campos = ["nombre_generico", "marca", "categoria", "subcategoria"]
    update = {k: v for k, v in body.items() if k in campos}
    res    = supabase.table("productos_catalogo").update(update).eq("id", id).execute()
    return jsonify(res.data)

@app.route("/api/categorias")
def get_categorias():
    res = supabase.table("categorias_maestra").select("*").order("orden").execute()
    return jsonify(res.data)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — PRECIOS (precios_mercadona / precios_dia)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/precios/<super_>")
def get_precios(super_):
    tabla    = "precios_mercadona" if super_ == "mercadona" else "precios_dia"
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    q        = request.args.get("q", "")
    start    = (page - 1) * per_page

    query = supabase.table(tabla).select("*", count="exact")
    if q: query = query.ilike("nombre_comercial", f"%{q}%")
    res = query.range(start, start + per_page - 1).order("id").execute()
    return jsonify({"data": res.data, "total": res.count})

@app.route("/api/precios/<super_>/<id>", methods=["PATCH"])
def update_precio(super_, id):
    tabla  = "precios_mercadona" if super_ == "mercadona" else "precios_dia"
    body   = request.json
    campos = ["nombre_comercial", "precio", "precio_unidad", "marca", "disponible"]
    update = {k: v for k, v in body.items() if k in campos}
    res    = supabase.table(tabla).update(update).eq("id", id).execute()
    return jsonify(res.data)

@app.route("/api/buscar_precio")
def buscar_precio():
    q      = request.args.get("q", "")
    super_ = request.args.get("super", "mercadona")
    tabla  = "precios_mercadona" if super_ == "mercadona" else "precios_dia"
    res    = supabase.table(tabla).select("id,nombre_comercial,precio,marca")\
               .ilike("nombre_comercial", f"%{q}%").limit(20).execute()
    return jsonify(res.data)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — MATCHES (productos_match)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/matches")
def get_matches():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    filtro   = request.args.get("filtro", "todos")
    q        = request.args.get("q", "")
    start    = (page - 1) * per_page

    query = supabase.table("productos_match").select(
        "id_catalogo,id_mercadona,id_dia,revisado,"
        "productos_catalogo(nombre_generico,categoria,subcategoria)",
        count="exact"
    )
    if filtro == "sin_dia":       query = query.is_("id_dia", "null")
    elif filtro == "sin_mercadona": query = query.is_("id_mercadona", "null")
    elif filtro == "revisados":   query = query.eq("revisado", True)
    elif filtro == "pendientes":  query = query.eq("revisado", False)

    res = query.range(start, start + per_page - 1).execute()
    return jsonify({"data": res.data, "total": res.count})

@app.route("/api/matches/<id_catalogo>", methods=["PATCH"])
def update_match(id_catalogo):
    body   = request.json
    campos = ["id_mercadona", "id_dia", "id_carrefour", "id_lidl", "id_aldi", "id_alcampo", "revisado"]
    update = {k: v for k, v in body.items() if k in campos}
    res    = supabase.table("productos_match").update(update).eq("id_catalogo", id_catalogo).execute()
    return jsonify(res.data)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — USUARIOS (cestas_online)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/usuarios")
def get_usuarios():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    start    = (page - 1) * per_page
    res      = supabase.table("cestas_online").select(
        "user_id,updated_at,productos,comprados", count="exact"
    ).range(start, start + per_page - 1).order("updated_at", desc=True).execute()

    data = []
    for r in res.data:
        data.append({
            "user_id":       r["user_id"],
            "updated_at":    r["updated_at"],
            "num_productos": len(r.get("productos") or []),
            "num_comprados": len(r.get("comprados") or []),
        })
    return jsonify({"data": data, "total": res.count})

@app.route("/api/usuarios/<user_id>")
def get_usuario(user_id):
    res = supabase.table("cestas_online").select("*").eq("user_id", user_id).execute()
    return jsonify(res.data[0] if res.data else {})

@app.route("/api/usuarios/<user_id>", methods=["DELETE"])
def delete_usuario(user_id):
    supabase.table("cestas_online").delete().eq("user_id", user_id).execute()
    return jsonify({"ok": True})

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — EXPORTAR / IMPORTAR CSV
# ══════════════════════════════════════════════════════════════════════════════

TABLAS_EXPORTABLES = {
    "catalogo":   ("productos_catalogo", "*"),
    "mercadona":  ("precios_mercadona",  "*"),
    "dia":        ("precios_dia",        "*"),
    "matches":    ("productos_match",    "*"),
    "categorias": ("categorias_maestra", "*"),
}

@app.route("/api/exportar/<nombre>")
def exportar_csv(nombre):
    if nombre not in TABLAS_EXPORTABLES:
        return jsonify({"error": "Tabla no válida"}), 400
    tabla, cols = TABLAS_EXPORTABLES[nombre]
    rows = fetch_all(tabla, cols)
    if not rows:
        return jsonify({"error": "Sin datos"}), 404

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)

    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{tabla}_{fecha}.csv"
    )

@app.route("/api/importar/categorias", methods=["POST"])
def importar_categorias():
    """Importa CSV de categorías desde tmp_categorias (ya subido a Supabase)."""
    try:
        res = supabase.rpc("pg_temp_to_catalogo").execute()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — SCRAPERS (lanzar y ver logs)
# ══════════════════════════════════════════════════════════════════════════════

def _run_scraper(name, script):
    scraper_status[name]["estado"]  = "running"
    scraper_status[name]["ultimo"]  = datetime.now().isoformat()
    scraper_logs[name] = []
    t0 = time.time()

    path = os.path.join(SCRAPERS_DIR, script)
    if not os.path.exists(path):
        scraper_logs[name].append(f"ERROR: Fichero no encontrado → {path}")
        scraper_status[name]["estado"] = "error"
        return

    try:
        env = os.environ.copy()
        proc = subprocess.Popen(
            ["python", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, bufsize=1,
            env=env
        )
        for line in proc.stdout:
            scraper_logs[name].append(line.rstrip())
        proc.wait()
        scraper_status[name]["estado"]   = "ok" if proc.returncode == 0 else "error"
        scraper_status[name]["duracion"] = f"{int(time.time()-t0)}s"
    except Exception as e:
        scraper_logs[name].append(f"ERROR: {e}")
        scraper_status[name]["estado"] = "error"

@app.route("/api/scrapers")
def get_scrapers():
    resultado = {}
    for k, script in SCRAPERS.items():
        path = os.path.join(SCRAPERS_DIR, script)
        resultado[k] = {
            **scraper_status[k],
            "script":   script,
            "existe":   os.path.exists(path),
        }
    return jsonify(resultado)

@app.route("/api/scrapers/<name>/run", methods=["POST"])
def run_scraper(name):
    if name not in SCRAPERS:
        return jsonify({"error": "Scraper no encontrado"}), 404
    if scraper_status[name]["estado"] == "running":
        return jsonify({"error": "Ya está ejecutándose"}), 409
    t = threading.Thread(target=_run_scraper, args=(name, SCRAPERS[name]), daemon=True)
    t.start()
    return jsonify({"ok": True, "mensaje": f"{name} iniciado"})

@app.route("/api/scrapers/<name>/logs")
def get_logs(name):
    return jsonify(scraper_logs.get(name, []))

@app.route("/api/scrapers/<name>/stream")
def stream_logs(name):
    def generate():
        idx = 0
        while True:
            logs = scraper_logs.get(name, [])
            while idx < len(logs):
                yield f"data: {logs[idx]}\n\n"
                idx += 1
            if scraper_status.get(name, {}).get("estado") != "running" and idx >= len(logs):
                yield "data: __END__\n\n"
                break
            time.sleep(0.3)
    return Response(generate(), mimetype="text/event-stream")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Mi Mejor Cesta — Panel Admin")
    print("="*55)
    print(f"  Supabase: {SUPABASE_URL}")
    print(f"  Scrapers: {SCRAPERS_DIR}")
    print(f"  URL:      http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=True, port=5000, threaded=True)
