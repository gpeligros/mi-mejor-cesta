"""
auditar_catalogo.py - Mi Mejor Cesta
====================================
Detecta problemas reales en productos_catalogo + productos_match + precios_*.

Genera 5 CSVs en la raiz del proyecto, cada uno con casos sospechosos
para revisar manualmente:

  audit_precios_anomalos.csv      - precios fuera de >3 desviaciones tipicas
                                    respecto a la mediana de su (categoria,
                                    subcategoria) en cada super
  audit_marcas_inconsistentes.csv - mismo CAT con marcas distintas en supers
                                    (ej. Polian en Mercadona y Asturiana en
                                    Carrefour para el mismo id_catalogo)
  audit_sin_categoria.csv         - productos en catalogo sin categoria o
                                    con categoria 'general' (no salen en UI)
  audit_huecos_cobertura.csv      - matches con productos en <=2 supers
                                    cuando podrian estar en mas
  audit_precios_extremos.csv      - precios <0,10EUR o >50EUR (probables
                                    errores tipograficos o de scraping)

Uso:
    python scrapers/auditar_catalogo.py
    python scrapers/auditar_catalogo.py --umbral-sigma 2.5

Lectura previa: docs/MATCHES_PLAN.md y MEMORY.md.
NO escribe en BBDD: solo lee y genera CSVs.
"""

import os, csv, argparse, statistics
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_KEY no encontrada en .env")
    exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_all(tabla, columnas="*"):
    """Pagina todas las filas (Supabase: limite 1000 por query)."""
    rows, offset = [], 0
    while True:
        res = sb.table(tabla).select(columnas).range(offset, offset + 999).execute()
        rows.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    return rows


def analizar_precios_anomalos(catalogo_idx, matches, precios_por_super, umbral_sigma):
    """Detecta precios que se desvian mucho de la mediana de su (cat, sub)."""
    print("\n[1/5] Analizando precios anomalos por categoria...")

    # Agrupa precios por (categoria, subcategoria, super)
    grupos = defaultdict(list)
    for m in matches:
        cat_info = catalogo_idx.get(m["id_catalogo"])
        if not cat_info:
            continue
        clave_cat = (cat_info.get("categoria") or "?", cat_info.get("subcategoria") or "?")
        for super_name, col in [
            ("Mercadona", "id_mercadona"),
            ("DIA", "id_dia"),
            ("Alcampo", "id_alcampo"),
            ("Carrefour", "id_carrefour"),
            ("AhorraMas", "id_ahorramas"),
        ]:
            id_super = m.get(col)
            if not id_super:
                continue
            precio_obj = precios_por_super.get(super_name, {}).get(id_super)
            if not precio_obj or not precio_obj.get("precio"):
                continue
            precio = float(precio_obj["precio"])
            grupos[(*clave_cat, super_name)].append({
                "id_catalogo": m["id_catalogo"],
                "nombre_cat": cat_info.get("nombre_generico", ""),
                "nombre_super": precio_obj.get("nombre_comercial", ""),
                "precio": precio,
            })

    anomalos = []
    for (cat, sub, super_name), items in grupos.items():
        if len(items) < 5:
            continue  # No tiene sentido sigma con muestra pequena
        precios = [it["precio"] for it in items]
        mediana = statistics.median(precios)
        desv = statistics.pstdev(precios)
        if desv == 0:
            continue
        for it in items:
            z = abs(it["precio"] - mediana) / desv
            if z > umbral_sigma:
                anomalos.append({
                    "categoria": cat,
                    "subcategoria": sub,
                    "super": super_name,
                    "id_catalogo": it["id_catalogo"],
                    "nombre_cat": it["nombre_cat"],
                    "nombre_super": it["nombre_super"],
                    "precio": round(it["precio"], 2),
                    "mediana_grupo": round(mediana, 2),
                    "desv_sigma": round(z, 1),
                })

    anomalos.sort(key=lambda x: -x["desv_sigma"])
    salvar_csv("audit_precios_anomalos.csv", anomalos,
               ["categoria", "subcategoria", "super", "id_catalogo",
                "nombre_cat", "nombre_super", "precio", "mediana_grupo",
                "desv_sigma"])
    print(f"  -> {len(anomalos)} precios anomalos detectados")


def analizar_marcas_inconsistentes(catalogo_idx, matches, precios_por_super):
    """Detecta CAT con nombres comerciales muy distintos entre supers."""
    print("\n[2/5] Analizando marcas inconsistentes entre supers...")
    inconsistentes = []
    for m in matches:
        cat_info = catalogo_idx.get(m["id_catalogo"])
        if not cat_info:
            continue
        nombres = {}
        for super_name, col in [
            ("Mercadona", "id_mercadona"),
            ("DIA", "id_dia"),
            ("Alcampo", "id_alcampo"),
            ("Carrefour", "id_carrefour"),
            ("AhorraMas", "id_ahorramas"),
        ]:
            id_super = m.get(col)
            if not id_super:
                continue
            obj = precios_por_super.get(super_name, {}).get(id_super)
            if obj and obj.get("nombre_comercial"):
                nombres[super_name] = obj["nombre_comercial"]

        if len(nombres) < 2:
            continue
        # Heuristica: dos primeras palabras significativas (>3 letras)
        def palabras_clave(txt):
            if not txt: return set()
            return {w.lower() for w in txt.split() if len(w) > 3}

        keywords = {s: palabras_clave(n) for s, n in nombres.items()}
        # Si dos supers no comparten ni una palabra >3 letras -> sospechoso
        supers_lista = list(keywords.keys())
        for i in range(len(supers_lista)):
            for j in range(i+1, len(supers_lista)):
                s1, s2 = supers_lista[i], supers_lista[j]
                if keywords[s1] and keywords[s2] and not (keywords[s1] & keywords[s2]):
                    inconsistentes.append({
                        "id_catalogo": m["id_catalogo"],
                        "nombre_cat": cat_info.get("nombre_generico", ""),
                        "categoria": cat_info.get("categoria", ""),
                        "super_1": s1,
                        "nombre_1": nombres[s1],
                        "super_2": s2,
                        "nombre_2": nombres[s2],
                    })
                    break  # un par ya basta para el CAT

    salvar_csv("audit_marcas_inconsistentes.csv", inconsistentes,
               ["id_catalogo", "nombre_cat", "categoria", "super_1",
                "nombre_1", "super_2", "nombre_2"])
    print(f"  -> {len(inconsistentes)} CAT con marcas inconsistentes")


def analizar_sin_categoria(catalogo):
    """Productos sin categoria o categoria 'general'."""
    print("\n[3/5] Analizando productos sin categoria...")
    sin_cat = [p for p in catalogo if not p.get("categoria") or
               (p.get("categoria") or "").lower() == "general"]
    salvar_csv("audit_sin_categoria.csv", sin_cat,
               ["id", "nombre_generico", "categoria", "subcategoria", "tipo"])
    print(f"  -> {len(sin_cat)} productos sin categoria valida")


def analizar_huecos_cobertura(catalogo_idx, matches):
    """Productos del catalogo con matches en <=2 supers."""
    print("\n[4/5] Analizando huecos de cobertura...")
    huecos = []
    for m in matches:
        n_supers = sum(1 for col in ["id_mercadona", "id_dia", "id_alcampo",
                                      "id_carrefour", "id_ahorramas"]
                       if m.get(col))
        if n_supers <= 2:
            cat_info = catalogo_idx.get(m["id_catalogo"], {})
            huecos.append({
                "id_catalogo": m["id_catalogo"],
                "nombre_cat": cat_info.get("nombre_generico", ""),
                "categoria": cat_info.get("categoria", ""),
                "n_supers": n_supers,
                "tiene_mercadona": bool(m.get("id_mercadona")),
                "tiene_dia": bool(m.get("id_dia")),
                "tiene_alcampo": bool(m.get("id_alcampo")),
                "tiene_carrefour": bool(m.get("id_carrefour")),
                "tiene_ahorramas": bool(m.get("id_ahorramas")),
            })
    huecos.sort(key=lambda x: x["n_supers"])
    salvar_csv("audit_huecos_cobertura.csv", huecos,
               ["id_catalogo", "nombre_cat", "categoria", "n_supers",
                "tiene_mercadona", "tiene_dia", "tiene_alcampo",
                "tiene_carrefour", "tiene_ahorramas"])
    print(f"  -> {len(huecos)} CAT con cobertura =< 2 supers")


def analizar_precios_extremos(catalogo_idx, matches, precios_por_super):
    """Precios <0.10 EUR o >50 EUR (probable error)."""
    print("\n[5/5] Analizando precios extremos...")
    extremos = []
    for m in matches:
        cat_info = catalogo_idx.get(m["id_catalogo"])
        if not cat_info:
            continue
        for super_name, col in [
            ("Mercadona", "id_mercadona"),
            ("DIA", "id_dia"),
            ("Alcampo", "id_alcampo"),
            ("Carrefour", "id_carrefour"),
            ("AhorraMas", "id_ahorramas"),
        ]:
            id_super = m.get(col)
            if not id_super:
                continue
            obj = precios_por_super.get(super_name, {}).get(id_super)
            if not obj or not obj.get("precio"):
                continue
            p = float(obj["precio"])
            if p < 0.10 or p > 50:
                extremos.append({
                    "id_catalogo": m["id_catalogo"],
                    "nombre_cat": cat_info.get("nombre_generico", ""),
                    "categoria": cat_info.get("categoria", ""),
                    "super": super_name,
                    "id_super": id_super,
                    "nombre_super": obj.get("nombre_comercial", ""),
                    "precio": round(p, 2),
                    "tipo": "muy_bajo" if p < 0.10 else "muy_alto",
                })
    extremos.sort(key=lambda x: x["precio"], reverse=True)
    salvar_csv("audit_precios_extremos.csv", extremos,
               ["id_catalogo", "nombre_cat", "categoria", "super",
                "id_super", "nombre_super", "precio", "tipo"])
    print(f"  -> {len(extremos)} precios extremos (<0.10 o >50 EUR)")


def salvar_csv(filename, rows, campos):
    if not rows:
        # Crear CSV vacio con cabecera para que se vea que se ejecuto
        with open(filename, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=campos).writeheader()
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in campos})


def main(umbral_sigma):
    print("=" * 60)
    print("  AUDITORIA DE CATALOGO - Mi Mejor Cesta")
    print(f"  Umbral sigma para precios anomalos: {umbral_sigma}")
    print("=" * 60)

    print("\nCargando datos de Supabase...")
    catalogo = fetch_all("vista_productos",
                         "id, nombre_generico, categoria, subcategoria")
    print(f"  catalogo: {len(catalogo)} entradas")

    tipos = fetch_all("productos_catalogo", "id, tipo")
    tipos_idx = {t["id"]: t.get("tipo") for t in tipos}
    catalogo_idx = {p["id"]: {**p, "tipo": tipos_idx.get(p["id"], "")} for p in catalogo}

    matches = fetch_all("productos_match",
                        "id_catalogo, id_mercadona, id_dia, id_alcampo, "
                        "id_carrefour, id_ahorramas")
    print(f"  matches: {len(matches)} filas")

    precios_por_super = {}
    for tabla, super_name in [
        ("precios_mercadona", "Mercadona"),
        ("precios_dia", "DIA"),
        ("precios_alcampo", "Alcampo"),
        ("precios_carrefour", "Carrefour"),
        ("precios_ahorramas", "AhorraMas"),
    ]:
        try:
            datos = fetch_all(tabla, "id, precio, nombre_comercial")
            precios_por_super[super_name] = {p["id"]: p for p in datos}
            print(f"  {tabla}: {len(datos)} entradas")
        except Exception as e:
            print(f"  {tabla}: ERROR {e}")
            precios_por_super[super_name] = {}

    analizar_precios_anomalos(catalogo_idx, matches, precios_por_super, umbral_sigma)
    analizar_marcas_inconsistentes(catalogo_idx, matches, precios_por_super)
    analizar_sin_categoria(catalogo)
    analizar_huecos_cobertura(catalogo_idx, matches)
    analizar_precios_extremos(catalogo_idx, matches, precios_por_super)

    print("\n" + "=" * 60)
    print("  AUDITORIA COMPLETA. Revisa los CSVs en la raiz del proyecto:")
    print("    audit_precios_anomalos.csv")
    print("    audit_marcas_inconsistentes.csv")
    print("    audit_sin_categoria.csv")
    print("    audit_huecos_cobertura.csv")
    print("    audit_precios_extremos.csv")
    print()
    print("  Sugerencia: empieza por audit_precios_extremos.csv (los")
    print("  errores mas obvios) y audit_marcas_inconsistentes.csv")
    print("  (matches falsos como Polian/Asturiana).")
    print("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral-sigma", type=float, default=3.0,
                    help="Desviaciones tipicas para considerar un precio anomalo")
    args = ap.parse_args()
    main(args.umbral_sigma)
