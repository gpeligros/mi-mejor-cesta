"""
agrupar_productos.py — Mi Mejor Cesta
=======================================
FASE 3a de la reconstrucción del catálogo (parte SIN COSTE — solo fuzzy
matching local, sin llamadas a IA).

Lee el CSV más reciente de normalizar_productos.py (old/) y agrupa productos
en dos PASADAS:

  PASADA A — Dedup intra-super:
    Cada supermercado se depura consigo mismo primero (colapsa variantes de
    formato/SKU del mismo producto, ej. los miles de SKUs de Carrefour que
    son el mismo producto en distinto pack). Nunca cruza supers en esta fase.

  PASADA B — Bridging cross-super:
    Los clusters YA LIMPIOS de la Pasada A (muchos menos que las filas
    originales) se comparan ENTRE supers, con Mercadona como ancla (se
    procesa primero). Esto evita que un producto de Carrefour se "quede
    pegado" a otro Carrefour en vez de cruzar a su equivalente en Mercadona.

Cada bridge cross-super se clasifica en tres bandas según el score:
  >= UMBRAL_AUTO     (88)   -> automático, se acepta sin revisión
  UMBRAL_DUDOSO..AUTO (75-87) -> dudoso, requiere revisión (Fase 3b con IA)
  < UMBRAL_DUDOSO             -> no hace bridge, sigue siendo cluster propio

No toca la BBDD. Solo lee/escribe CSVs locales.

USO:
  python scrapers/agrupar_productos.py
  python scrapers/agrupar_productos.py --umbral-auto 90 --umbral-dudoso 78

SALIDA (en old/):
  resumen_clusters_<fecha>.csv   -> 1 fila por cluster final (catálogo propuesto)
  clusters_dudosos_<fecha>.csv   -> detalle de bridges en banda dudosa (Fase 3b)
"""

import argparse
import csv
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from rapidfuzz import fuzz, process

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"

UMBRAL_AUTO_DEFAULT = 88
UMBRAL_DUDOSO_DEFAULT = 75
UMBRAL_DEDUP_INTRA_DEFAULT = 95  # estricto: evitar fusionar variantes de sabor/ingrediente
                                   # (ej. "con leche desnatada" vs "con nueces y leche
                                   # desnatada" daba score 91 y se fusionaba mal con 90)
UMBRAL_RESCATE_C_DEFAULT = 90  # Pasada C: verificado que 85 mete falsos positivos
                                 # (ej. "Agua mineral Evian" vs "Agua mineral Dia" = 89)

ORDEN_SUPERS = ["Mercadona", "Carrefour", "DIA", "AhorraMas", "Alcampo"]


def csv_normalizado_mas_reciente():
    candidatos = sorted(glob.glob(str(CARPETA_OLD / "normalizado_*.csv")))
    return candidatos[-1] if candidatos else None


class ClusterIntra:
    __slots__ = ("marca", "nombre_canonico", "texto_bruto", "texto_bridge", "miembros")

    def __init__(self, marca, nombre_canonico, primer_miembro, texto_bruto=""):
        self.marca = marca
        self.nombre_canonico = nombre_canonico
        self.texto_bruto = texto_bruto  # nombre normalizado SIN quitar marca (solo formato) — para Pasada C
        self.texto_bridge = nombre_canonico  # se recalcula tras detectar marcas genéricas, antes de Pasada B
        self.miembros = [primer_miembro]


class ClusterFinal:
    __slots__ = ("id", "marca", "nombre_canonico", "sub_clusters")

    def __init__(self, cid, marca, nombre_canonico, primer_sub_cluster):
        self.id = cid
        self.marca = marca
        self.nombre_canonico = nombre_canonico
        self.sub_clusters = [primer_sub_cluster]


def clave_bucket(marca, marcas_genericas=None):
    m = (marca or "").strip().lower()
    if not m:
        return "__sin_marca__"
    if marcas_genericas and m in marcas_genericas:
        # Marca blanca o exclusiva de un super -> mismo cubo que "sin marca",
        # para poder comparar "Pan de molde sin corteza Hacendado" con
        # "Pan de molde sin corteza Dia" por descripción, no por fabricante.
        # Petición de David 20/08/2026: la marca blanca de un super SÍ debe
        # poder comparar precio con la marca blanca equivalente de otro.
        return "__sin_marca__"
    return m


def texto_comparacion(marca, nombre_base, marcas_genericas=None):
    m = (marca or "").strip().lower()
    if marcas_genericas and m in marcas_genericas:
        # No incluir la marca blanca en el texto de comparación: si dejáramos
        # "hacendado pan de molde" vs "dia pan de molde", el propio nombre de
        # la marca hace bajar el score de similitud y nunca cruzarían.
        t = nombre_base.strip().lower()
    else:
        t = f"{marca} {nombre_base}".strip().lower()
    return unificar_numeros(t)


# ── Para la Pasada C: normalizar el nombre ORIGINAL quitando solo
# formato/cantidad, pero SIN tocar la marca (a diferencia de nombre_base,
# que puede tener la marca quitada de forma asimétrica entre supers según
# si el campo 'marca' de origen estaba bien poblado o no) ─────────────────
import re as _re
import unicodedata as _unicodedata

NUMEROS_PALABRA_A_CIFRA = {
    "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
    "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10",
}
_RE_NUMERO_PALABRA = _re.compile(
    r"\b(" + "|".join(NUMEROS_PALABRA_A_CIFRA.keys()) + r")\b"
)


def unificar_numeros(texto):
    """Convierte números en palabra (dos..diez) a cifra, para que 'Mahou
    Cinco Estrellas' y 'Mahou 5 Estrellas' se comparen como el mismo
    texto. Sin esto son productos idénticos que nunca se agrupan porque
    el texto literal no coincide (bug real detectado por David, 11/08/2026)."""
    return _RE_NUMERO_PALABRA.sub(lambda m: NUMEROS_PALABRA_A_CIFRA[m.group(1)], texto)

_UNIDADES = (
    r"(?:kg|g|gr|ml|l|cl|ud|uds|unidades?|unid|pack|lata|latas|bote|botes|"
    r"sobre|sobres|botella|botellas|frasco|tubo|brik|brick|envase|bandeja|"
    r"paquete|bolsa|caja|tarro|garrafa|spray|docena|piezas?|rebanadas?)"
)
_RE_FORMATO = _re.compile(
    rf"(?:pack\s+de\s+)?\d+[\.,]?\d*\s*{_UNIDADES}(?:\s+de\s+\d+[\.,]?\d*\s*{_UNIDADES})?"
    rf"|\d+[\.,]?\d*\s*x\s*\d+[\.,]?\d*\s*{_UNIDADES}",
    _re.IGNORECASE,
)


def normalizar_para_rescate(nombre_original):
    """Normaliza + quita SOLO formato/cantidad, conserva la marca tal cual
    esté escrita (para poder comparar cuando un lado no detectó marca)."""
    t = (nombre_original or "").lower()
    t = _unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if _unicodedata.category(c) != "Mn")
    t = unificar_numeros(t)
    t = _RE_FORMATO.sub("", t)
    t = _re.sub(r"\s+\d+\s*$", "", t)
    t = _re.sub(r"\s+", " ", t).strip(" -,.")
    return t


# ── Guardia de conflicto: bloquea fusiones aunque el score fuzzy sea alto,
# si los dos textos difieren en un atributo excluyente conocido. El score
# de similitud por sí solo no distingue "desnatada" de "entera" cuando el
# resto de la frase es idéntica y larga (ej. "Leche ... Central Lechera
# Asturiana Sin Lactosa" con solo esa palabra distinta puntúa >90). ────────
_GRUPOS_EXCLUYENTES = [
    {"desnatada", "semidesnatada", "entera"},
    {"integral", "refinado", "refinada"},
    {"blanco", "tostado", "integral"},
]
_PATRON_SIN_X = _re.compile(r"\bsin\s+(\w+)")


def hay_conflicto(texto_a, texto_b):
    """True si los textos tienen atributos excluyentes distintos -> NO fusionar."""
    palabras_a = set(texto_a.split())
    palabras_b = set(texto_b.split())

    for grupo in _GRUPOS_EXCLUYENTES:
        presentes_a = grupo & palabras_a
        presentes_b = grupo & palabras_b
        if presentes_a and presentes_b and presentes_a != presentes_b:
            return True

    sin_a = set(_PATRON_SIN_X.findall(texto_a))
    sin_b = set(_PATRON_SIN_X.findall(texto_b))
    if sin_a != sin_b:
        return True

    return False


def pasada_a_dedup_intra_super(filas_super, umbral_dedup):
    buckets = defaultdict(list)
    for fila in filas_super:
        marca = fila.get("marca_detectada", "")
        nombre_base = fila.get("nombre_base", "")
        texto = texto_comparacion(marca, nombre_base)
        bucket_key = clave_bucket(marca)

        candidatos = buckets[bucket_key]
        mejor_cluster, mejor_score = None, 0
        if candidatos:
            nombres = [c.nombre_canonico for c in candidatos]
            resultado = process.extractOne(texto, nombres, scorer=fuzz.token_sort_ratio)
            if resultado:
                _, mejor_score, idx = resultado
                candidato = candidatos[idx]
                if not hay_conflicto(texto, candidato.nombre_canonico):
                    mejor_cluster = candidato
                else:
                    mejor_score = 0  # forzado a crear cluster nuevo

        if mejor_cluster and mejor_score >= umbral_dedup:
            mejor_cluster.miembros.append(fila)
        else:
            texto_bruto = normalizar_para_rescate(fila.get("nombre_original", ""))
            buckets[bucket_key].append(ClusterIntra(marca, texto, fila, texto_bruto))

    return [c for lista in buckets.values() for c in lista]


def detectar_marcas_genericas(filas):
    """Una marca se considera 'genérica' (blanca o de un supermercado) SOLO
    si cumple DOS condiciones a la vez:
      1. Aparece en un único supermercado de los 5 (señal de exclusividad)
      2. Y además PARECE una marca blanca de verdad: está en la lista de
         marcas blancas conocidas, O contiene el nombre del propio
         supermercado (así nombran sus marcas propias: "Carrefour Classic",
         "Dia Vegecampo", "PRODUCTO ALCAMPO"...)

    Solo la condición 1 no basta — lo probamos y fallaba: "Eucerin" y
    "Schwarzkopf" son marcas reales de fabricante, pero cada una solo se
    scrapeó bien en un super (no porque sean exclusivas, sino porque el
    scraper de ese super concreto las captó y el otro no). Con solo la
    condición 1 se fusionaban como si fueran equivalentes (score 93,8,
    por encima del umbral automático, sin pasar por revisión de IA).
    Detectado con datos reales de David, 20/08/2026."""
    NOMBRES_SUPERS = {"dia", "carrefour", "alcampo", "ahorramas", "mercadona", "auchan"}
    MARCAS_BLANCAS_CONOCIDAS = {
        "hacendado", "deliplus", "bosque verde", "compy", "baysi",
        "alvita", "granja penate", "casa tarradellas", "alipende",
    }

    def parece_marca_blanca(m):
        if m in MARCAS_BLANCAS_CONOCIDAS:
            return True
        palabras = set(m.split())
        return bool(palabras & NOMBRES_SUPERS)

    marca_a_supers = defaultdict(set)
    for f in filas:
        m = (f.get("marca_detectada") or "").strip().lower()
        if m:
            marca_a_supers[m].add(f["super"])

    return {
        m for m, supers in marca_a_supers.items()
        if len(supers) <= 1 and parece_marca_blanca(m)
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral-auto", type=int, default=UMBRAL_AUTO_DEFAULT)
    ap.add_argument("--umbral-dudoso", type=int, default=UMBRAL_DUDOSO_DEFAULT)
    ap.add_argument("--umbral-dedup-intra", type=int, default=UMBRAL_DEDUP_INTRA_DEFAULT)
    ap.add_argument("--umbral-rescate-c", type=int, default=UMBRAL_RESCATE_C_DEFAULT)
    args = ap.parse_args()
    UMBRAL_AUTO = args.umbral_auto
    UMBRAL_DUDOSO = args.umbral_dudoso
    UMBRAL_DEDUP = args.umbral_dedup_intra
    UMBRAL_RESCATE_C = args.umbral_rescate_c

    print("=" * 60)
    print("  🔗 AGRUPAR PRODUCTOS — Fase 3a (fuzzy, dos pasadas, sin IA)")
    print(f"  Dedup intra-super: {UMBRAL_DEDUP} | Auto cross-super: {UMBRAL_AUTO} | Dudoso: {UMBRAL_DUDOSO}")
    print("=" * 60)

    ruta = csv_normalizado_mas_reciente()
    if not ruta:
        print(f"\n❌ No se encontró ningún normalizado_*.csv en {CARPETA_OLD}")
        print("   Ejecuta primero: python scrapers/normalizar_productos.py")
        return

    with open(ruta, encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if (r.get("nombre_base") or "").strip()]
    print(f"\n📥 {ruta}")
    print(f"  {len(filas):,} filas cargadas")

    filas_por_super = defaultdict(list)
    for f in filas:
        filas_por_super[f["super"]].append(f)

    print("\n🔧 PASADA A — Depurando cada super consigo mismo...")
    clusters_intra_por_super = {}
    for super_name in ORDEN_SUPERS:
        filas_s = filas_por_super.get(super_name, [])
        if not filas_s:
            continue
        clusters = pasada_a_dedup_intra_super(filas_s, UMBRAL_DEDUP)
        clusters_intra_por_super[super_name] = clusters
        print(f"  {super_name:12s} {len(filas_s):>6,} filas -> {len(clusters):>6,} clusters propios")

    # ── Detectar marcas genéricas (blancas o exclusivas de un super) y
    # recalcular el texto de comparación de cada cluster SIN esa marca,
    # para que puedan cruzar entre supers por descripción ─────────────────
    marcas_genericas = detectar_marcas_genericas(filas)
    print(f"\n🏷️  {len(marcas_genericas):,} marcas detectadas como genéricas "
          f"(blancas o exclusivas de un solo super) — se compararán por descripción")

    for clusters in clusters_intra_por_super.values():
        for sc in clusters:
            nombre_base_repr = sc.miembros[0].get("nombre_base", "")
            sc.texto_bridge = texto_comparacion(sc.marca, nombre_base_repr, marcas_genericas)

    print("\n🔗 PASADA B — Cruzando entre supers (Mercadona como ancla)...")
    buckets_finales = defaultdict(list)
    contador_id = 0
    stats = {"auto": 0, "dudoso": 0, "nuevo": 0}
    clusters_dudosos_detalle = []

    for super_name in ORDEN_SUPERS:
        subclusters = clusters_intra_por_super.get(super_name, [])
        for sc in subclusters:
            bucket_key = clave_bucket(sc.marca, marcas_genericas)
            todos_candidatos = buckets_finales[bucket_key]
            # CLAVE: excluir clusters que YA tienen un miembro de este mismo
            # super — así la Pasada B solo puede tender puentes CROSS-super,
            # nunca volver a fusionar dentro del mismo super (eso ya lo hizo
            # la Pasada A). Sin este filtro, Carrefour sigue pegándose a
            # Carrefour aquí y el bridging real queda enmascarado.
            candidatos = [c for c in todos_candidatos
                          if super_name not in {s for s, _, _ in c.sub_clusters}]

            mejor_cluster, mejor_score = None, 0
            if candidatos:
                nombres = [c.nombre_canonico for c in candidatos]
                resultado = process.extractOne(sc.texto_bridge, nombres, scorer=fuzz.token_sort_ratio)
                if resultado:
                    _, mejor_score, idx = resultado
                    candidato = candidatos[idx]
                    if not hay_conflicto(sc.texto_bridge, candidato.nombre_canonico):
                        mejor_cluster = candidato
                    else:
                        mejor_score = 0

            if mejor_cluster and mejor_score >= UMBRAL_AUTO:
                mejor_cluster.sub_clusters.append((super_name, sc, mejor_score))
                stats["auto"] += 1
            elif mejor_cluster and mejor_score >= UMBRAL_DUDOSO:
                mejor_cluster.sub_clusters.append((super_name, sc, mejor_score))
                stats["dudoso"] += 1
                clusters_dudosos_detalle.append((mejor_cluster, super_name, sc, mejor_score))
            else:
                contador_id += 1
                nuevo = ClusterFinal(contador_id, sc.marca, sc.texto_bridge, (super_name, sc, 100))
                buckets_finales[bucket_key].append(nuevo)
                stats["nuevo"] += 1

    todos = [c for lista in buckets_finales.values() for c in lista]
    print(f"\n✅ Bridging completo (Pasada B).")
    print(f"  Clusters tras Pasada B:      {len(todos):,}")
    print(f"  Bridges automáticos:         {stats['auto']:,}")
    print(f"  Bridges dudosos:             {stats['dudoso']:,}  (requieren Fase 3b / IA)")
    print(f"  Clusters nuevos (sin match): {stats['nuevo']:,}")

    # ── PASADA C: rescate cross-super SIN restricción de marca ───────────
    # La Pasada B solo compara dentro del mismo bucket de marca. Si el campo
    # 'marca' falló en detectar una marca real de fabricante (ej. "El
    # Caserío", "Dr. Oetker") en un lado pero no en el otro, dos productos
    # idénticos nunca se comparan. Aquí se rescatan esos casos SOLO entre
    # clusters que siguen huérfanos (1 solo super) tras la Pasada B, usando
    # bucket por primera palabra significativa del nombre en vez de marca.
    # Umbral 90 verificado manualmente: por debajo aparecen falsos positivos
    # reales (ej. "Agua mineral Evian" vs "Agua mineral Dia" score 89).
    print(f"\n🆓 PASADA C — Rescate cross-super sin restricción de marca (umbral {UMBRAL_RESCATE_C})...")

    STOP_WORDS = {"de", "con", "y", "sin", "para", "a", "en", "del", "la", "el", "los", "las"}

    def primera_palabra_significativa(texto):
        for w in texto.split():
            if w not in STOP_WORDS and len(w) > 2:
                return w
        return texto.split()[0] if texto.split() else ""

    huerfanos = [c for c in todos if len(c.sub_clusters) == 1]
    buckets_c = defaultdict(list)
    for c in huerfanos:
        # el texto_bruto está en el ClusterIntra original (sub_clusters[0][1])
        sc_intra = c.sub_clusters[0][1]
        texto_c = sc_intra.texto_bruto or c.nombre_canonico
        buckets_c[primera_palabra_significativa(texto_c)].append((c, texto_c))

    rescatados = 0
    ya_fusionados = set()
    for key, grupo in buckets_c.items():
        if len(grupo) < 2:
            continue
        for i in range(len(grupo)):
            c_a, texto_a = grupo[i]
            if c_a.id in ya_fusionados:
                continue
            for j in range(i + 1, len(grupo)):
                c_b, texto_b = grupo[j]
                if c_b.id in ya_fusionados:
                    continue
                super_a = c_a.sub_clusters[0][0]
                super_b = c_b.sub_clusters[0][0]
                if super_a == super_b:
                    continue
                score = fuzz.token_sort_ratio(texto_a, texto_b)
                if score >= UMBRAL_RESCATE_C and not hay_conflicto(texto_a, texto_b):
                    c_a.sub_clusters.append((super_b, c_b.sub_clusters[0][1], round(score, 1)))
                    ya_fusionados.add(c_b.id)
                    rescatados += 1
                    break  # 'c_a' ya no está huérfano, pasar al siguiente

    todos = [c for c in todos if c.id not in ya_fusionados]
    print(f"  Clusters rescatados (fusionados en Pasada C): {rescatados:,}")

    n_multi = sum(1 for c in todos if len(c.sub_clusters) >= 2)
    print(f"\n📊 Clusters con cobertura en ≥2 supers (tras Pasadas B+C): {n_multi:,} / {len(todos):,}")

    fecha = datetime.now().strftime("%Y%m%d_%H%M")

    resumen = []
    for c in todos:
        supers_presentes = {sup for sup, _, _ in c.sub_clusters}
        n_filas_totales = sum(len(sc.miembros) for _, sc, _ in c.sub_clusters)
        min_score = min((s for _, _, s in c.sub_clusters if s < 100), default=100)
        resumen.append({
            "cluster_id": c.id,
            "marca": c.marca,
            "nombre_canonico": c.nombre_canonico,
            "n_supers": len(supers_presentes),
            "n_filas_originales": n_filas_totales,
            "tiene_mercadona": "Mercadona" in supers_presentes,
            "tiene_dia": "DIA" in supers_presentes,
            "tiene_alcampo": "Alcampo" in supers_presentes,
            "tiene_carrefour": "Carrefour" in supers_presentes,
            "tiene_ahorramas": "AhorraMas" in supers_presentes,
            "min_score_bridge": min_score,
        })
    resumen.sort(key=lambda r: (-r["n_supers"], r["min_score_bridge"]))

    ruta_resumen = CARPETA_OLD / f"resumen_clusters_{fecha}.csv"
    with open(ruta_resumen, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "marca", "nombre_canonico", "n_supers", "n_filas_originales",
                "tiene_mercadona", "tiene_dia", "tiene_alcampo", "tiene_carrefour",
                "tiene_ahorramas", "min_score_bridge"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(resumen)

    ruta_dudosos = CARPETA_OLD / f"clusters_dudosos_{fecha}.csv"
    with open(ruta_dudosos, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "nombre_canonico_cluster", "marca", "super_candidato",
                "nombre_candidato", "score_bridge"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for cluster_final, super_name, sc, score in clusters_dudosos_detalle:
            w.writerow({
                "cluster_id": cluster_final.id,
                "nombre_canonico_cluster": cluster_final.nombre_canonico,
                "marca": cluster_final.marca,
                "super_candidato": super_name,
                "nombre_candidato": sc.nombre_canonico,
                "score_bridge": round(score, 1),
            })

    # ── NUEVO: detalle completo fila a fila, necesario para la Fase 5 ────
    # (qué id_super concreto de cada supermercado pertenece a qué cluster
    # final; el resumen de arriba solo tiene agregados/booleanos)
    ruta_miembros = CARPETA_OLD / f"miembros_clusters_{fecha}.csv"
    with open(ruta_miembros, "w", newline="", encoding="utf-8") as f:
        cols = ["cluster_id", "super", "id_super", "nombre_original",
                "marca_detectada", "formato", "precio", "score_bridge_super"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for c in todos:
            for super_name, sc, score in c.sub_clusters:
                for miembro in sc.miembros:
                    w.writerow({
                        "cluster_id": c.id,
                        "super": super_name,
                        "id_super": miembro.get("id_super", ""),
                        "nombre_original": miembro.get("nombre_original", ""),
                        "marca_detectada": miembro.get("marca_detectada", ""),
                        "formato": miembro.get("formato", ""),
                        "precio": miembro.get("precio", ""),
                        "score_bridge_super": round(score, 1) if score < 100 else "",
                    })

    print(f"\n✅ CSVs generados en {CARPETA_OLD}:")
    print(f"  {ruta_resumen.name}")
    print(f"  {ruta_dudosos.name}  ({len(clusters_dudosos_detalle):,} bridges dudosos)")
    print(f"  {ruta_miembros.name}  (detalle completo, para la Fase 5)")
    print(f"\nSiguiente paso: revisar muestra de resumen_clusters y decidir si lanzamos")
    print(f"la Fase 3b (revisión con IA de los bridges dudosos).")


if __name__ == "__main__":
    main()
