"""
normalizar_productos.py — Mi Mejor Cesta
==========================================
FASE 2 de la reconstrucción del catálogo.

Lee los 5 CSVs generados por exportar_todos_precios.py (carpeta old/) y para
cada producto extrae:
  - nombre_base   : nombre sin marca ni formato/cantidad (para agrupar)
  - marca_detectada : la marca (del campo 'marca' de la fila, o extraída
                       del nombre si 'marca' viene vacía)
  - formato       : cantidad/formato detectado (ej. "33 Cl", "1 L", "Pack 6")

No toca la BBDD. Solo lee los CSVs locales y escribe CSVs nuevos.

A diferencia del script viejo (construir_catalogo.py), esto SIEMPRE quita
formato, tanto si es marca blanca como si es marca de fabricante — ese era
el bug que generaba duplicados tipo "Mahou 5 Estrellas Lata 33cl" vs
"Mahou 5 Estrellas Pack 6" como productos de catálogo distintos.

USO:
  python scrapers/normalizar_productos.py

Requiere que ya hayas ejecutado exportar_todos_precios.py y que los CSVs
existan en old/export_precios_<super>_<fecha>.csv (coge el más reciente
de cada super automáticamente).

SALIDA:
  old/normalizado_<fecha>.csv   — todas las filas de los 5 supers juntas,
                                   con columnas nuevas: super, nombre_base,
                                   marca_detectada, formato
"""

import csv
import re
import unicodedata
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_OLD = RAIZ / "old"

SUPERS = {
    "precios_mercadona": "Mercadona",
    "precios_dia":        "DIA",
    "precios_alcampo":    "Alcampo",
    "precios_carrefour":  "Carrefour",
    "precios_ahorramas":  "AhorraMas",
}

# ── Unidades / formato a detectar y extraer ──────────────────────────────
UNIDADES = (
    r"(?:kg|g|gr|ml|l|cl|ud|uds|unidades?|unid|pack|lata|latas|bote|botes|"
    r"sobre|sobres|botella|botellas|frasco|tubo|brik|brick|envase|bandeja|"
    r"paquete|bolsa|caja|tarro|garrafa|spray|docena|piezas?|rebanadas?)"
)

# Patrón: número (con o sin decimales) + unidad, opcionalmente repetido
# (para casos "Pack de 6 botellas de 25 cl")
RE_FORMATO = re.compile(
    rf"(?:pack\s+de\s+)?\d+[\.,]?\d*\s*{UNIDADES}(?:\s+de\s+\d+[\.,]?\d*\s*{UNIDADES})?"
    rf"|\d+[\.,]?\d*\s*x\s*\d+[\.,]?\d*\s*{UNIDADES}",
    re.IGNORECASE,
)

RE_NUMERO_SUELTO = re.compile(r"\b\d+[\.,]?\d*\b")

# ── Red de seguridad: marcas blancas conocidas que el campo 'marca' de la
# fila NO siempre captura bien (a veces viene vacío o como "Marca propia") ──
MARCAS_BLANCAS_CONOCIDAS = [
    "hacendado", "deliplus", "bosque verde", "compy", "baysi",
    "alvita", "granja penate", "casa tarradellas",
]

# Valores placeholder inútiles que a veces trae el campo 'marca'
MARCA_PLACEHOLDER_INVALIDA = {"marca propia", "marca blanca", ""}


NUMEROS_PALABRA_A_CIFRA = {
    "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
    "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10",
}
_RE_NUMERO_PALABRA = re.compile(
    r"\b(" + "|".join(NUMEROS_PALABRA_A_CIFRA.keys()) + r")\b"
)


def unificar_numeros(texto):
    """Convierte números en palabra (uno..diez) a cifra, para que 'Cinco
    Estrellas' y '5 Estrellas' se traten como el mismo texto al comparar.
    Sin esto, productos idénticos con el número escrito de forma distinta
    (ej. Mahou Cinco Estrellas vs Mahou 5 Estrellas) nunca se agrupan."""
    return _RE_NUMERO_PALABRA.sub(lambda m: NUMEROS_PALABRA_A_CIFRA[m.group(1)], texto)


def normalizar_texto(texto):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = unificar_numeros(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extraer_formato(nombre):
    """Devuelve (nombre_sin_formato, formato_detectado)."""
    formatos = RE_FORMATO.findall(nombre)
    nombre_limpio = RE_FORMATO.sub("", nombre)
    # Limpiar números sueltos residuales al final (ej. "Producto 2" restante)
    nombre_limpio = re.sub(r"\s+\d+\s*$", "", nombre_limpio)
    nombre_limpio = re.sub(r"\s+", " ", nombre_limpio).strip(" -,.")
    formato_str = " + ".join(formatos) if formatos else ""
    return nombre_limpio, formato_str


def quitar_marca(nombre, marca):
    """
    Quita la marca del nombre. Usa dos fuentes, combinadas:
    1. El campo 'marca' de la fila (si trae un valor real, no un placeholder)
    2. La lista fija de marcas blancas conocidas, SIEMPRE se comprueba,
       porque el campo 'marca' de origen no es fiable (a veces vacío o
       "Marca propia" incluso cuando el nombre sí lleva "Hacendado" etc.)
    Devuelve el nombre resultante Y la marca final considerada válida.
    """
    resultado = nombre
    marca_final = ""

    marca_normalizada = normalizar_texto(marca)
    if marca and marca_normalizada not in MARCA_PLACEHOLDER_INVALIDA:
        patron = re.compile(re.escape(marca), re.IGNORECASE)
        nuevo = patron.sub("", resultado)
        if nuevo != resultado:
            marca_final = marca
        resultado = nuevo

    # Red de seguridad: marcas blancas conocidas, se comprueban siempre
    for mb in MARCAS_BLANCAS_CONOCIDAS:
        patron = re.compile(re.escape(mb), re.IGNORECASE)
        nuevo = patron.sub("", resultado)
        if nuevo != resultado and not marca_final:
            marca_final = mb.title()
        resultado = nuevo

    resultado = re.sub(r"\s+", " ", resultado).strip(" -,.")
    return (resultado if resultado else nombre), marca_final


def csv_mas_reciente(prefijo):
    candidatos = sorted(glob.glob(str(CARPETA_OLD / f"export_{prefijo}_*.csv")))
    return candidatos[-1] if candidatos else None


def procesar_super(tabla, nombre_super):
    ruta = csv_mas_reciente(tabla)
    if not ruta:
        print(f"  ⚠️  No se encontró CSV para {tabla} en old/. Se omite.")
        return []

    filas_out = []
    with open(ruta, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nombre_original = (row.get("nombre_comercial") or "").strip()
            if not nombre_original:
                continue
            marca_original = (row.get("marca") or "").strip()
            precio = row.get("precio") or ""

            sin_marca, marca_final = quitar_marca(nombre_original, marca_original)
            nombre_base, formato = extraer_formato(sin_marca)

            filas_out.append({
                "super":            nombre_super,
                "id_super":         row.get("id", ""),
                "nombre_original":  nombre_original,
                "marca_detectada":  marca_final,
                "nombre_base":      nombre_base,
                "formato":          formato,
                "precio":           precio,
            })

    print(f"  {nombre_super:12s} {len(filas_out):>6,} filas procesadas  (fuente: {Path(ruta).name})")
    return filas_out


def construir_vocabulario_marcas(todas_filas, min_apariciones=2):
    """Construye la lista de marcas 'conocidas' a partir de lo que YA se
    detectó bien en el conjunto (campo marca de origen, o marca blanca).
    Se usa como red de seguridad para rescatar filas donde 'marca' venía
    vacía en origen — problema detectado en Mercadona: vende Activia,
    Danone, Puleva, Dove, Milka... pero el campo marca está vacío en ~50%
    de esos productos, y además Mercadona escribe la marca en medio del
    nombre en vez de al principio, así que ni el bucket por marca ni el
    rescate por primera palabra (agrupar_productos.py Pasada C) los
    encontraban. 11/08/2026, diagnóstico con datos reales de David.

    Exclusión: palabras genéricas que en algún producto puntual vinieron
    mal metidas en el campo 'marca' de origen (ej. 'Blanco' en unas pastas
    de almendra) pero que son adjetivos/colores comunes que colisionarían
    con productos reales ("Vino Blanco", "Chocolate Blanco"...). Verificado
    caso a caso con los datos reales antes de excluir — Conejo, Flor,
    Estola, Elegido SÍ son marcas reales y se mantienen."""
    PALABRAS_GENERICAS_EXCLUIDAS = {
        "blanco", "blanca", "negro", "negra", "rojo", "roja", "verde",
        "azul", "rosa", "amarillo", "amarilla", "natural", "clasico",
        "clasica", "original", "especial", "premium", "extra", "grande",
        "pequeno", "pequena", "mini", "maxi", "nuevo", "nueva",
    }
    contador = Counter()
    for f in todas_filas:
        m = f["marca_detectada"].strip().lower()
        if m and len(m) >= 3 and m not in PALABRAS_GENERICAS_EXCLUIDAS:
            contador[m] += 1
    vocabulario = {m for m, n in contador.items() if n >= min_apariciones}
    return vocabulario


def rescatar_marca_con_vocabulario(fila, vocabulario_ordenado):
    """Si la fila no tiene marca detectada, busca si alguna marca del
    vocabulario aparece como palabra completa en el nombre original
    (en cualquier posición, no solo al principio)."""
    if fila["marca_detectada"]:
        return fila  # ya tiene marca, no tocar

    texto_norm = normalizar_texto(fila["nombre_original"])
    for marca in vocabulario_ordenado:  # ya viene ordenado de más larga a más corta
        patron = r"\b" + re.escape(marca) + r"\b"
        if re.search(patron, texto_norm):
            # Reconstruir nombre_base quitando esta marca del nombre_original
            sin_marca, _ = quitar_marca(fila["nombre_original"], marca)
            nombre_base, formato_extra = extraer_formato(sin_marca)
            fila["marca_detectada"] = marca.title()
            fila["nombre_base"] = nombre_base
            if formato_extra and not fila["formato"]:
                fila["formato"] = formato_extra
            break
    return fila


def main():
    print("=" * 60)
    print("  🧹 NORMALIZAR PRODUCTOS — Fase 2")
    print("=" * 60)

    if not CARPETA_OLD.exists():
        print(f"\n❌ No existe la carpeta {CARPETA_OLD}")
        print("   Ejecuta primero: python scrapers/exportar_todos_precios.py")
        return

    print("\n📥 Procesando cada supermercado...")
    todas = []
    for tabla, nombre_super in SUPERS.items():
        todas.extend(procesar_super(tabla, nombre_super))

    if not todas:
        print("\n❌ No se procesó ninguna fila. Revisa que existan los CSVs en old/.")
        return

    # ── Rescate de marca con vocabulario aprendido del propio catálogo ───
    print("\n🔍 Construyendo vocabulario de marcas conocidas (a partir de lo ya detectado)...")
    vocabulario = construir_vocabulario_marcas(todas)
    # Ordenar de más larga a más corta para que "leche pascual" (si existiera)
    # no se coma antes que "pascual" suelto, evita matches parciales raros
    vocabulario_ordenado = sorted(vocabulario, key=len, reverse=True)
    print(f"  {len(vocabulario_ordenado):,} marcas en el vocabulario (aparecen ≥2 veces en el catálogo)")

    sin_marca_antes = sum(1 for f in todas if not f["marca_detectada"])
    todas = [rescatar_marca_con_vocabulario(f, vocabulario_ordenado) for f in todas]
    sin_marca_despues = sum(1 for f in todas if not f["marca_detectada"])
    rescatadas = sin_marca_antes - sin_marca_despues
    print(f"  {rescatadas:,} filas rescatadas (tenían marca real pero el campo de origen venía vacío)")

    # clave_agrupacion se calcula AHORA, después del rescate
    for f in todas:
        f["clave_agrupacion"] = normalizar_texto(f"{f['marca_detectada']} {f['nombre_base']}")

    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    destino = CARPETA_OLD / f"normalizado_{fecha}.csv"

    columnas = ["super", "id_super", "nombre_original", "marca_detectada",
                "nombre_base", "formato", "precio", "clave_agrupacion"]
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(todas)

    # ── Estadística rápida: cuántas claves de agrupación se repiten entre supers ──
    grupos = defaultdict(set)
    for fila in todas:
        grupos[fila["clave_agrupacion"]].add(fila["super"])

    multi_super = sum(1 for supers in grupos.values() if len(supers) > 1)

    print(f"\n✅ {len(todas):,} filas normalizadas → {destino}")
    print(f"\n📊 Vista previa de agrupación (exacta, sin fuzzy todavía):")
    print(f"   Claves únicas de nombre+marca: {len(grupos):,}")
    print(f"   De ellas, ya coinciden en ≥2 supers EXACTAMENTE: {multi_super:,}")
    print(f"   (el resto necesitará fuzzy matching en la Fase 3 — muchas variantes")
    print(f"    de escritura entre supers no van a coincidir exactas todavía)")
    print("\nSiguiente paso: Fase 3 — agrupación con fuzzy matching + revisión IA.")


if __name__ == "__main__":
    main()
