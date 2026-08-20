"""
construir_propuesta_final.py — Mi Mejor Cesta
================================================
FASE 4 de la reconstrucción del catálogo.

Combina:
  - miembros_clusters_<fecha>.csv     (de agrupar_productos.py — Fase 3a)
  - bridges_rechazados_<fecha>.csv    (de revisar_clusters_dudosos.py — Fase 3b)

Aplica los rechazos de la IA: para cada bridge rechazado, separa esos
miembros de su cluster y les da un cluster_id propio (dejan de comparar
precio con ese cluster). El resto (automáticos + aceptados) se mantiene.

Como cada super contribuye como máximo UN sub-cluster a cada cluster final
(agrupar_productos.py lo garantiza), identificar qué separar es inambiguo:
simplemente (cluster_id, super) del rechazo.

No toca la BBDD. Solo lee/escribe CSVs locales.

USO:
  python scrapers/construir_propuesta_final.py

SALIDA (en old/):
  miembros_finales_<fecha>.csv    -> membresía definitiva (cluster_id corregido)
  resumen_final_<fecha>.csv       -> 1 fila por cluster final definitivo
  muestra_revision_<fecha>.csv    -> muestra amplia de clusters multi-super
                                      para que David la revise antes de la Fase 5
"""

import csv
import glob
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"


def mas_reciente(patron):
    candidatos = sorted(glob.glob(str(CARPETA_OLD / patron)))
    return candidatos[-1] if candidatos else None


def main():
    print("=" * 60)
    print("  📋 CONSTRUIR PROPUESTA FINAL — Fase 4")
    print("=" * 60)

    ruta_miembros = mas_reciente("miembros_clusters_*.csv")
    ruta_rechazados = mas_reciente("bridges_rechazados_*.csv")

    if not ruta_miembros:
        print(f"\n❌ No se encontró miembros_clusters_*.csv en {CARPETA_OLD}")
        print("   Ejecuta primero: python scrapers/agrupar_productos.py")
        return
    if not ruta_rechazados:
        print(f"\n❌ No se encontró bridges_rechazados_*.csv en {CARPETA_OLD}")
        print("   Ejecuta primero: python scrapers/revisar_clusters_dudosos.py")
        return

    print(f"\n📥 Miembros:   {ruta_miembros}")
    print(f"📥 Rechazados: {ruta_rechazados}")

    with open(ruta_miembros, encoding="utf-8") as f:
        miembros = list(csv.DictReader(f))
    with open(ruta_rechazados, encoding="utf-8") as f:
        rechazados = list(csv.DictReader(f))

    print(f"\n  {len(miembros):,} filas de membresía")
    print(f"  {len(rechazados):,} bridges rechazados a separar")

    # ── Separar los rechazados en clusters propios ──────────────────────
    pares_rechazados = {(r["cluster_id"], r["super_candidato"]) for r in rechazados}

    max_cluster_id = max(int(m["cluster_id"]) for m in miembros)
    siguiente_id = max_cluster_id + 1

    nuevos_ids = {}  # (cluster_id_original, super) -> nuevo cluster_id
    separados = 0
    for m in miembros:
        clave = (m["cluster_id"], m["super"])
        if clave in pares_rechazados:
            if clave not in nuevos_ids:
                nuevos_ids[clave] = siguiente_id
                siguiente_id += 1
            m["cluster_id"] = str(nuevos_ids[clave])
            separados += 1

    print(f"\n✅ {separados:,} filas separadas a {len(nuevos_ids):,} clusters nuevos independientes")

    # ── Reconstruir resumen final ────────────────────────────────────────
    por_cluster = defaultdict(list)
    for m in miembros:
        por_cluster[m["cluster_id"]].append(m)

    resumen = []
    for cid, filas in por_cluster.items():
        supers_presentes = {f["super"] for f in filas}
        marca = next((f["marca_detectada"] for f in filas if f["marca_detectada"]), "")
        # nombre representativo: el más frecuente entre las filas del cluster
        nombres = [f["nombre_original"] for f in filas]
        nombre_repr = max(set(nombres), key=nombres.count)
        resumen.append({
            "cluster_id": cid,
            "marca": marca,
            "nombre_representativo": nombre_repr,
            "n_supers": len(supers_presentes),
            "n_filas_originales": len(filas),
            "supers": ", ".join(sorted(supers_presentes)),
        })
    resumen.sort(key=lambda r: -r["n_supers"])

    fecha = datetime.now().strftime("%Y%m%d_%H%M")

    ruta_miembros_final = CARPETA_OLD / f"miembros_finales_{fecha}.csv"
    with open(ruta_miembros_final, "w", newline="", encoding="utf-8") as f:
        cols = list(miembros[0].keys())
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(miembros)

    ruta_resumen_final = CARPETA_OLD / f"resumen_final_{fecha}.csv"
    with open(ruta_resumen_final, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "marca", "nombre_representativo", "n_supers",
                 "n_filas_originales", "supers"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(resumen)

    # ── Muestra de revisión: TODOS los clusters con 3+ supers, más una
    # muestra aleatoria grande de los de 2 supers ────────────────────────
    multi3 = [r for r in resumen if r["n_supers"] >= 3]
    multi2 = [r for r in resumen if r["n_supers"] == 2]
    random.seed(7)
    muestra_multi2 = random.sample(multi2, min(150, len(multi2)))

    ruta_muestra = CARPETA_OLD / f"muestra_revision_{fecha}.csv"
    filas_muestra = []
    for r in sorted(multi3, key=lambda x: -x["n_supers"]) + muestra_multi2:
        detalle = por_cluster[r["cluster_id"]]
        nombres_por_super = "; ".join(
            f"[{m['super']}] {m['nombre_original']}" for m in detalle
        )
        filas_muestra.append({
            "cluster_id": r["cluster_id"],
            "marca": r["marca"],
            "n_supers": r["n_supers"],
            "nombres_por_super": nombres_por_super,
        })
    with open(ruta_muestra, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "marca", "n_supers", "nombres_por_super"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas_muestra)

    # ── Resumen en consola ────────────────────────────────────────────────
    n_total = len(resumen)
    n_multi = sum(1 for r in resumen if r["n_supers"] >= 2)
    n_solo1 = n_total - n_multi

    print(f"\n{'='*60}")
    print("  CATÁLOGO PROPUESTO — RESUMEN")
    print(f"{'='*60}")
    print(f"  Clusters totales (= futuros productos de catálogo): {n_total:,}")
    print(f"  Con cobertura en ≥2 supers (comparan precio):       {n_multi:,}")
    print(f"    - de ellos, en ≥3 supers:                         {len(multi3):,}")
    print(f"  Solo en 1 super (no comparan, pero sí muestran):    {n_solo1:,}")
    print(f"\n✅ CSVs generados en {CARPETA_OLD}:")
    print(f"  {ruta_miembros_final.name}")
    print(f"  {ruta_resumen_final.name}")
    print(f"  {ruta_muestra.name}  <- REVISA ESTE antes de la Fase 5")
    print(f"     ({len(filas_muestra)} clusters: todos los de 3+ supers + muestra de 150 de 2 supers)")


if __name__ == "__main__":
    main()
