"""
match_ean.py — Mi Mejor Cesta
==============================
Crea matches automáticos en productos_match usando el EAN como clave.

Lógica:
  1. Para cada producto en precios_mercadona con EAN → busca en el catálogo
     si ya hay un CAT-xxxx con ese EAN → confirma el match
  2. Para cada EAN en precios_dia/precios_alcampo → busca en precios_mercadona
     si hay coincidencia → actualiza productos_match con el id_dia/id_alcampo

Solo actúa sobre productos marca_fabricante (los de marca_blanca no tienen EAN común).

USO:
  python scrapers/match_ean.py --dry-run    # muestra matches sin escribir
  python scrapers/match_ean.py              # aplica los matches

REQUISITOS:
  - Haber ejecutado la migración fase3_ean.sql
  - Haber ejecutado el scraper de Mercadona actualizado (con EAN)
  - pip install supabase python-dotenv
"""

import argparse
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def construir_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def cargar_tabla_ean(supabase: Client, tabla: str, campo_id: str) -> dict:
    """Carga un mapa EAN → id para una tabla de precios."""
    print(f"  → Cargando EANs de {tabla}...")
    resultado = {}
    offset = 0
    while True:
        res = (
            supabase.table(tabla)
            .select(f"id, ean")
            .not_.is_("ean", "null")
            .range(offset, offset + 999)
            .execute()
        )
        for r in res.data:
            if r.get("ean"):
                resultado[r["ean"]] = r["id"]
        if len(res.data) < 1000:
            break
        offset += 1000
    print(f"     {len(resultado)} productos con EAN")
    return resultado


def cargar_matches_actuales(supabase: Client) -> dict:
    """Carga el estado actual de productos_match."""
    print("  → Cargando productos_match actuales...")
    resultado = {}
    offset = 0
    while True:
        res = (
            supabase.table("productos_match")
            .select("id_catalogo, id_mercadona, id_dia, id_alcampo")
            .range(offset, offset + 999)
            .execute()
        )
        for r in res.data:
            resultado[r["id_catalogo"]] = r
        if len(res.data) < 1000:
            break
        offset += 1000
    print(f"     {len(resultado)} filas en productos_match")
    return resultado


def cargar_catalogo_mercadona(supabase: Client) -> dict:
    """Carga mapa id_mercadona → id_catalogo para cruzar con EANs."""
    print("  → Cargando relación catálogo ↔ Mercadona...")
    resultado = {}
    offset = 0
    while True:
        res = (
            supabase.table("productos_match")
            .select("id_catalogo, id_mercadona")
            .not_.is_("id_mercadona", "null")
            .range(offset, offset + 999)
            .execute()
        )
        for r in res.data:
            resultado[r["id_mercadona"]] = r["id_catalogo"]
        if len(res.data) < 1000:
            break
        offset += 1000
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Match por EAN entre supermercados")
    parser.add_argument("--dry-run", action="store_true",
                        help="Muestra los matches sin escribir en la BBDD")
    args = parser.parse_args()

    modo = "🔍 DRY-RUN" if args.dry_run else "✍️  PRODUCCIÓN"
    print(f"\n{'='*60}")
    print(f"  match_ean.py — {modo}")
    print(f"{'='*60}\n")

    supabase = construir_supabase()

    # Cargar datos
    print("📦 Cargando datos...")
    eans_mercadona = cargar_tabla_ean(supabase, "precios_mercadona", "id")
    eans_dia       = cargar_tabla_ean(supabase, "precios_dia", "id")
    eans_alcampo   = cargar_tabla_ean(supabase, "precios_alcampo", "id")
    matches        = cargar_matches_actuales(supabase)
    me_a_cat       = cargar_catalogo_mercadona(supabase)

    # Estadísticas iniciales
    print(f"\n📊 EANs disponibles:")
    print(f"   Mercadona: {len(eans_mercadona)}")
    print(f"   DIA:       {len(eans_dia)}")
    print(f"   Alcampo:   {len(eans_alcampo)}")

    # ── Cruzar EANs ────────────────────────────────────────────────────────────
    # Para cada EAN de Mercadona, buscar si existe en DIA y/o Alcampo
    nuevos_dia     = []
    nuevos_alcampo = []

    print(f"\n🔍 Cruzando EANs...")

    for ean, id_mercadona in eans_mercadona.items():
        id_catalogo = me_a_cat.get(id_mercadona)
        if not id_catalogo:
            continue  # producto Mercadona sin match en catálogo todavía

        match_actual = matches.get(id_catalogo, {})

        # Cruzar con DIA
        id_dia_nuevo = eans_dia.get(ean)
        if id_dia_nuevo and match_actual.get("id_dia") != id_dia_nuevo:
            nuevos_dia.append({
                "id_catalogo": id_catalogo,
                "id_dia":      id_dia_nuevo,
                "ean":         ean,
                "id_mercadona": id_mercadona,
            })

        # Cruzar con Alcampo
        id_alcampo_nuevo = eans_alcampo.get(ean)
        if id_alcampo_nuevo and match_actual.get("id_alcampo") != id_alcampo_nuevo:
            nuevos_alcampo.append({
                "id_catalogo":   id_catalogo,
                "id_alcampo":    id_alcampo_nuevo,
                "ean":           ean,
                "id_mercadona":  id_mercadona,
            })

    print(f"\n✅ Matches nuevos encontrados por EAN:")
    print(f"   DIA:     {len(nuevos_dia)}")
    print(f"   Alcampo: {len(nuevos_alcampo)}")

    if args.dry_run:
        print(f"\n--- Muestra DIA (primeros 10) ---")
        for m in nuevos_dia[:10]:
            print(f"  {m['id_catalogo']} ↔ {m['id_dia']} (EAN: {m['ean']})")
        print(f"\n--- Muestra Alcampo (primeros 10) ---")
        for m in nuevos_alcampo[:10]:
            print(f"  {m['id_catalogo']} ↔ {m['id_alcampo']} (EAN: {m['ean']})")
    else:
        # Aplicar matches DIA
        if nuevos_dia:
            print(f"\n🔄 Aplicando {len(nuevos_dia)} matches DIA...")
            ok = err = 0
            for m in nuevos_dia:
                try:
                    supabase.table("productos_match").update(
                        {"id_dia": m["id_dia"]}
                    ).eq("id_catalogo", m["id_catalogo"]).execute()
                    ok += 1
                except Exception as e:
                    err += 1
                    print(f"  ⚠️  Error {m['id_catalogo']}: {e}")
            print(f"  ✅ DIA: {ok} OK | {err} errores")

        # Aplicar matches Alcampo
        if nuevos_alcampo:
            print(f"\n🔄 Aplicando {len(nuevos_alcampo)} matches Alcampo...")
            ok = err = 0
            for m in nuevos_alcampo:
                try:
                    supabase.table("productos_match").update(
                        {"id_alcampo": m["id_alcampo"]}
                    ).eq("id_catalogo", m["id_catalogo"]).execute()
                    ok += 1
                except Exception as e:
                    err += 1
                    print(f"  ⚠️  Error {m['id_catalogo']}: {e}")
            print(f"  ✅ Alcampo: {ok} OK | {err} errores")

    # Resumen final
    print(f"\n{'='*60}")
    print(f"  RESUMEN")
    print(f"{'='*60}")
    print(f"  Matches DIA por EAN:     {len(nuevos_dia)}")
    print(f"  Matches Alcampo por EAN: {len(nuevos_alcampo)}")
    if args.dry_run:
        print(f"\n  ⚠️  DRY-RUN: ejecuta sin --dry-run para aplicar.")
    else:
        print(f"\n  ✅ Matches aplicados en Supabase.")
    print(f"{'='*60}\n")

    if len(eans_mercadona) == 0:
        print("⚠️  AVISO: No hay EANs en precios_mercadona.")
        print("   Ejecuta primero el scraper_mercadona.py actualizado.")


if __name__ == "__main__":
    main()
