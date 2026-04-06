"""
construir_catalogo.py — Mi Mejor Cesta
=======================================
Construye productos_catalogo desde cero usando precios_mercadona
con las categorías reales de la API de Mercadona.

Pasos:
  1. TRUNCATE productos_catalogo y productos_match
  2. Lee precios_mercadona con categoria_mercadona
  3. Agrupa productos similares (marca blanca → nombre genérico)
  4. Asigna id_categoria correcto según mapping Mercadona→nuestras categorías
  5. Inserta en productos_catalogo y productos_match

Uso:
  python scrapers/construir_catalogo.py --dry-run   # solo muestra, no guarda
  python scrapers/construir_catalogo.py             # construye el catálogo

NUNCA ejecutar sin --dry-run primero.
"""

import os, re, json, unicodedata, argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
except ImportError:
    pass

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://scpuriaofisssalsbzqv.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_KEY:
    print("❌ SUPABASE_KEY no encontrada en .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ══════════════════════════════════════════════════════════════════════════════
# MAPPING: categoría Mercadona → id_categoria de categorias_maestras
# ══════════════════════════════════════════════════════════════════════════════
# Formato: "categoria_mercadona|subcategoria_mercadona" → id_categoria

MAPPING = {
    "aceite, especias y salsas|aceite, vinagre y sal": 133,
    "aceite, especias y salsas|mayonesa, ketchup y mostaza": 140,
    "aceite, especias y salsas|especias": 136,
    "aceite, especias y salsas|otras salsas": 140,
    "aceite, especias y salsas|vinagre": 141,
    "agua y refrescos|agua": 94,
    "agua y refrescos|refresco de cola": 97,
    "agua y refrescos|refresco de naranja y de limon": 97,
    "agua y refrescos|tonica y bitter": 97,
    "agua y refrescos|refresco de te y sin gas": 97,
    "agua y refrescos|isotonico y energetico": 97,
    "aperitivos|patatas fritas y snacks": 131,
    "aperitivos|aceitunas y encurtidos": 140,
    "aperitivos|frutos secos y fruta desecada": 127,
    "arroz, legumbres y pasta|arroz": 134,
    "arroz, legumbres y pasta|legumbres": 138,
    "arroz, legumbres y pasta|pasta y fideos": 134,
    "azucar, caramelos y chocolate|chocolate": 87,
    "azucar, caramelos y chocolate|azucar y edulcorante": 135,
    "azucar, caramelos y chocolate|mermelada y miel": 130,
    "azucar, caramelos y chocolate|chicles y caramelos": 86,
    "azucar, caramelos y chocolate|golosinas": 88,
    "bebe|toallitas y panales": 92,
    "bebe|biberon y chupete": 91,
    "bebe|alimentacion infantil": 90,
    "bebe|higiene y cuidado": 91,
    "bodega|vino tinto": 98,
    "bodega|vino blanco": 98,
    "bodega|vino rosado": 98,
    "bodega|vino lambrusco y espumoso": 98,
    "bodega|sidra y cava": 98,
    "bodega|tinto de verano y sangria": 98,
    "bodega|cerveza": 95,
    "bodega|cerveza sin alcohol": 95,
    "bodega|licores": 96,
    "cacao, cafe e infusiones|cafe capsula y monodosis": 125,
    "cacao, cafe e infusiones|cafe molido y en grano": 125,
    "cacao, cafe e infusiones|cafe soluble y otras bebidas": 125,
    "cacao, cafe e infusiones|cacao soluble y chocolate a la taza": 125,
    "cacao, cafe e infusiones|te e infusiones": 132,
    "carne|aves y pollo": 105,
    "carne|cerdo": 101,
    "carne|vacuno": 106,
    "carne|conejo y cordero": 103,
    "carne|hamburguesas y picadas": 100,
    "carne|empanados y elaborados": 100,
    "carne|arreglos": 100,
    "carne|embutido": 102,
    "carne|carne congelada": 100,
    "cereales y galletas|cereales": 126,
    "cereales y galletas|galletas": 128,
    "cereales y galletas|tortitas": 128,
    "charcuteria y quesos|aves y jamon cocido": 102,
    "charcuteria y quesos|bacon y salchichas": 102,
    "charcuteria y quesos|chopped y mortadela": 102,
    "charcuteria y quesos|jamon serrano": 102,
    "charcuteria y quesos|embutido curado": 102,
    "charcuteria y quesos|pate y sobrasada": 102,
    "charcuteria y quesos|queso curado, semicurado y tierno": 157,
    "charcuteria y quesos|queso lonchas, rallado y en porciones": 157,
    "charcuteria y quesos|queso untable, fresco y especialidades": 157,
    "congelados|pescado": 108,
    "congelados|marisco": 108,
    "congelados|verdura": 109,
    "congelados|helados": 107,
    "congelados|tartas y churros": 107,
    "congelados|pizzas": 108,
    "congelados|rebozados": 108,
    "congelados|arroz y pasta": 108,
    "congelados|hielo": 107,
    "conservas, caldos y cremas|atun y otras conservas de pescado": 110,
    "conservas, caldos y cremas|berberechos y mejillones": 110,
    "conservas, caldos y cremas|conservas de verdura y frutas": 113,
    "conservas, caldos y cremas|tomate": 113,
    "conservas, caldos y cremas|sopa y caldo": 112,
    "conservas, caldos y cremas|gazpacho y cremas": 112,
    "cuidado del cabello|champu": 115,
    "cuidado del cabello|acondicionador y mascarilla": 115,
    "cuidado del cabello|coloracion cabello": 115,
    "cuidado del cabello|fijacion cabello": 115,
    "cuidado facial y corporal|gel y jabon de manos": 118,
    "cuidado facial y corporal|cuidado corporal": 118,
    "cuidado facial y corporal|higiene bucal": 117,
    "cuidado facial y corporal|desodorante": 116,
    "cuidado facial y corporal|afeitado y cuidado para hombre": 124,
    "cuidado facial y corporal|perfume y colonia": 123,
    "cuidado facial y corporal|manicura y pedicura": 121,
    "cuidado facial y corporal|depilacion": 121,
    "cuidado facial y corporal|higiene intima": 119,
    "cuidado facial y corporal|cuidado e higiene facial": 114,
    "cuidado facial y corporal|protector solar y aftersun": 114,
    "fitoterapia y parafarmacia|parafarmacia": 122,
    "fitoterapia y parafarmacia|fitoterapia": 122,
    "fruta y verdura|fruta": 142,
    "fruta y verdura|verdura": 144,
    "fruta y verdura|lechuga y ensalada preparada": 144,
    "huevos, leche y mantequilla|huevos": 153,
    "huevos, leche y mantequilla|leche y bebidas vegetales": 154,
    "huevos, leche y mantequilla|mantequilla y margarina": 155,
    "limpieza y hogar|detergente y suavizante ropa": 146,
    "limpieza y hogar|limpieza cocina": 149,
    "limpieza y hogar|insecticida y ambientador": 145,
    "limpieza y hogar|menaje y conservacion de alimentos": 151,
    "limpieza y hogar|papel y bolsas": 151,
    "limpieza y hogar|limpieza bano": 149,
    "limpieza y hogar|limpieza suelos y hogar": 149,
    "limpieza y hogar|lavavajillas": 147,
    "limpieza y hogar|lejia y desinfectante": 148,
    "maquillaje|labios": 120,
    "maquillaje|ojos": 120,
    "maquillaje|bases de maquillaje y corrector": 120,
    "maquillaje|unas": 121,
    "maquillaje|rostro": 120,
    "marisco y pescado|pescado fresco": 168,
    "marisco y pescado|marisco fresco": 166,
    "marisco y pescado|moluscos": 167,
    "mascotas|perro": 162,
    "mascotas|gato": 161,
    "mascotas|otros animales": 161,
    "mascotas|arena para gatos": 160,
    "mascotas|accesorios": 159,
    "panaderia y pasteleria|pan de horno": 164,
    "panaderia y pasteleria|bolleria de horno": 163,
    "panaderia y pasteleria|bolleria envasada": 163,
    "panaderia y pasteleria|pasteles y tartas": 165,
    "panaderia y pasteleria|pan de molde y otras especialidades": 164,
    "panaderia y pasteleria|pan sin gluten": 164,
    "panaderia y pasteleria|harina y preparado reposteria": 137,
    "pizzas y platos preparados|platos preparados calientes": 171,
    "pizzas y platos preparados|pizzas": 108,
    "pizzas y platos preparados|ensaladas y platos frios": 170,
    "pizzas y platos preparados|bocadillos": 169,
    "pizzas y platos preparados|pasta y arroces preparados": 171,
    "postres y yogures|yogur natural": 158,
    "postres y yogures|yogur con frutas y sabores": 158,
    "postres y yogures|yogur griego y skyr": 158,
    "postres y yogures|yogures liquidos": 158,
    "postres y yogures|postres lacteos": 156,
    "postres y yogures|nata y crema": 155,
    "postres y yogures|kefir y otros fermentados": 158,
    "panaderia y pasteleria|picos, rosquilletas y picatostes": 129,
    "panaderia y pasteleria|pan tostado y rallado": 164,
    "limpieza y hogar|utensilios de limpieza y calzado": 151,
    "limpieza y hogar|estropajo, bayeta y guantes": 151,
    "limpieza y hogar|lejia y liquidos fuertes": 148,
    "limpieza y hogar|limpieza vajilla": 147,
    "limpieza y hogar|limpiahogar y friegasuelos": 149,
    "limpieza y hogar|papel higienico y celulosa": 151,
    "limpieza y hogar|limpieza bano y wc": 149,
    "limpieza y hogar|limpieza muebles y multiusos": 149,
    "maquillaje|colorete y polvos": 120,
    "zumos|fruta variada": 99,
    "postres y yogures|gelatina y otros postres": 156,
    "postres y yogures|yogures naturales y sabores": 158,
    "postres y yogures|bifidus": 158,
    "postres y yogures|yogures desnatados": 158,
    "postres y yogures|flan y natillas": 156,
    "pizzas y platos preparados|listo para comer": 171,
    "marisco y pescado|salazones y ahumados": 168,
    "panaderia y pasteleria|velas y decoracion": 89,
    "pizzas y platos preparados|platos preparados frios": 171,
    "marisco y pescado|marisco": 166,
    "limpieza y hogar|pilas y bolsas de basura": 151,
    "zumos|naranja": 99,
    "zumos|melocoton y pina": 99,
    "zumos|tomate y otros sabores": 99,
    "postres y yogures|yogures griegos": 158,
    "postres y yogures|postres de soja": 156,
    "postres y yogures|yogures y postres infantiles": 158,
    "mascotas|otros": 161,
    "limpieza y hogar|limpiacristales": 149,
    "panaderia y pasteleria|tartas y pasteles": 165,
    "maquillaje|pinceles y brochas": 121,
}

# Marcas blancas de Mercadona — sus productos son genéricos en el catálogo
MARCAS_BLANCAS = {
    "hacendado", "deliplus", "bosque verde", "compy",
    "baysi", "alvita", "granja penate", "casa tarradellas",
}

# Marcas de Mercadona que son de fabricante (no blancas)
# Si el nombre contiene estas marcas Y están en solo Mercadona, igual entran
# porque son marcas exclusivas de calidad comparable

def normalizar(texto):
    if not texto:
        return ""
    t = texto.lower().strip()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    # Normalizar espacios múltiples
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def es_marca_blanca(nombre, marca=None):
    """Detecta si un producto es marca blanca de Mercadona."""
    nombre_n = normalizar(nombre or "")
    marca_n  = normalizar(marca or "")
    for mb in MARCAS_BLANCAS:
        if mb in nombre_n or mb in marca_n:
            return True
    return False

def generar_nombre_generico(nombre_comercial):
    """
    Genera el nombre genérico quitando la marca y el formato/peso.
    Ej: 'Aceite de oliva virgen extra Hacendado botella 1L' → 'Aceite de oliva virgen extra'
    """
    nombre = nombre_comercial.strip()

    # Quitar marca blanca del final o principio
    for mb in sorted(MARCAS_BLANCAS, key=len, reverse=True):
        # Quitar del principio (capitalizado o no)
        patron = re.compile(re.escape(mb), re.IGNORECASE)
        nombre = patron.sub("", nombre).strip()

    # Quitar peso/volumen y formato del final
    nombre = re.sub(
        r'\s+\d+[\.,]?\d*\s*(g|kg|ml|l|cl|ud|uds|unidades?|pack|lata|bote|sobre|botella|frasco|tubo|brik|brick|envase|bandeja|paquete|bolsa|caja|tarro|garrafa|spray|brick)\s*[\d,\.]*\s*$',
        '', nombre, flags=re.IGNORECASE
    ).strip()

    # Quitar números solos al final
    nombre = re.sub(r'\s+\d+$', '', nombre).strip()

    # Quitar palabras sueltas sobrantes al final
    palabras_fin = ['botella', 'garrafa', 'spray', 'bote', 'lata', 'tarro', 'bolsa', 'brick', 'brik', 'pack', 'sobre']
    for p in palabras_fin:
        if nombre.lower().endswith(p):
            nombre = nombre[:-(len(p))].strip()

    # Normalizar espacios múltiples y limpiar
    nombre = re.sub(r'\s+', ' ', nombre).strip(" -,.")

    return nombre

def obtener_id_categoria(cat_merc, subcat_merc):
    """Mapea categoría Mercadona → id_categoria de categorias_maestras."""
    clave = f"{normalizar(cat_merc)}|{normalizar(subcat_merc)}"
    return MAPPING.get(clave)

def fetch_all(tabla, columnas="*"):
    rows, offset = [], 0
    while True:
        res = supabase.table(tabla).select(columnas).range(offset, offset + 999).execute()
        rows.extend(res.data)
        if len(res.data) < 1000:
            break
        offset += 1000
    return rows

def main(dry_run=False):
    print("=" * 60)
    print("  🏗️  CONSTRUIR CATÁLOGO DESDE CERO")
    print(f"  Modo: {'DRY-RUN (sin guardar)' if dry_run else '⚠️  PRODUCCIÓN'}")
    print("=" * 60)

    # ── 1. Cargar productos de Mercadona con categoría ────────────
    print("\n📥 Cargando precios_mercadona...")
    mercadona = fetch_all("precios_mercadona",
        "id, nombre_comercial, marca, categoria_mercadona, subcategoria_mercadona, precio")
    print(f"  {len(mercadona)} productos Mercadona")

    con_categoria = [p for p in mercadona if p.get("categoria_mercadona")]
    sin_categoria = [p for p in mercadona if not p.get("categoria_mercadona")]
    print(f"  Con categoría: {len(con_categoria)}")
    print(f"  Sin categoría: {len(sin_categoria)} (se omiten)")

    # ── 2. Construir catálogo ────────────────────────────────────
    print("\n🔧 Construyendo catálogo...")

    catalogo = []       # filas para productos_catalogo
    matches  = []       # filas para productos_match
    sin_mapping = {}    # categorías sin mapping para debug

    # ── 3. Deduplicar: solo productos exactamente iguales (mismo nombre comercial)
    print("\n🔍 Procesando productos...")
    vistos = {}  # clave: nombre_comercial_normalizado → datos

    for prod in con_categoria:
        cat_merc    = prod.get("categoria_mercadona", "")
        subcat_merc = prod.get("subcategoria_mercadona", "")
        id_cat = obtener_id_categoria(cat_merc, subcat_merc)

        if not id_cat:
            clave = f"{cat_merc}|{subcat_merc}"
            sin_mapping[clave] = sin_mapping.get(clave, 0) + 1
            continue

        nombre_comercial = (prod.get("nombre_comercial") or "").strip()
        if not nombre_comercial or len(nombre_comercial) < 3:
            continue

        mb   = es_marca_blanca(nombre_comercial, prod.get("marca"))
        tipo = "marca_blanca" if mb else "marca_fabricante"

        # Para marca blanca: usar nombre genérico (sin marca) como nombre en catálogo
        # Para marca fabricante: usar nombre comercial completo con formato
        if mb:
            nombre_catalogo = generar_nombre_generico(nombre_comercial)
            if not nombre_catalogo or len(nombre_catalogo) < 3:
                nombre_catalogo = nombre_comercial
            # Deduplicar marcas blancas por nombre genérico + categoría
            clave_dedup = (normalizar(nombre_catalogo), id_cat)
        else:
            # Marca fabricante: mantener nombre completo con formato, deduplicar exactos
            nombre_catalogo = nombre_comercial
            clave_dedup = (normalizar(nombre_comercial), id_cat)

        if clave_dedup not in vistos:
            vistos[clave_dedup] = {
                "nombre_gen": nombre_catalogo,
                "id_cat":     id_cat,
                "tipo":       tipo,
                "id_merc":    prod["id"],
                "marca":      prod.get("marca"),
            }

    print(f"  {len(vistos)} productos únicos (de {len(con_categoria)} con categoría)")

    # ── 4. Construir listas finales ───────────────────────────────
    for i, (_, v) in enumerate(vistos.items(), 1):
        cat_id = f"CAT-{i:04d}"
        catalogo.append({
            "id":               cat_id,
            "nombre_generico":  v["nombre_gen"],
            "marca":            v["marca"],
            "id_categoria":     v["id_cat"],
            "tipo":             v["tipo"],
            "activo":           True,
            "orden":            i,
        })
        matches.append({
            "id_catalogo":  cat_id,
            "id_mercadona": v["id_merc"],
        })

    print(f"  ✅ Productos a insertar: {len(catalogo)}")
    print(f"     Marca blanca:     {sum(1 for c in catalogo if c['tipo'] == 'marca_blanca')}")
    print(f"     Marca fabricante: {sum(1 for c in catalogo if c['tipo'] == 'marca_fabricante')}")

    if sin_mapping:
        print(f"\n  ⚠️  Categorías sin mapping ({len(sin_mapping)}):")
        for k, v in sorted(sin_mapping.items(), key=lambda x: -x[1])[:20]:
            print(f"     {v:3d} productos → {k}")

    # ── 3. Mostrar muestra ───────────────────────────────────────
    print("\n📋 Muestra de los primeros 20 productos:")
    for c in catalogo[:20]:
        print(f"  {c['id']} | {c['tipo'][:2].upper()} | cat:{c['id_categoria']:3d} | {c['nombre_generico']}")

    if dry_run:
        print("\n[dry-run] No se guarda nada.")
        print(f"\nPara construir el catálogo real ejecuta sin --dry-run")
        return

    # ── 4. Confirmar ─────────────────────────────────────────────
    print(f"\n⚠️  Se van a BORRAR todos los datos de:")
    print(f"   - productos_catalogo ({len(catalogo)} nuevos a insertar)")
    print(f"   - productos_match ({len(matches)} nuevos a insertar)")
    resp = input("\n¿Continuar? Escribe 'SI' para confirmar: ")
    if resp.strip().upper() != "SI":
        print("Cancelado.")
        return

    # ── 5. TRUNCATE ──────────────────────────────────────────────
    print("\n🗑️  Vaciando tablas...")
    try:
        supabase.table("compras_detalle").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("compras").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("productos_match").delete().neq("id_catalogo", "").execute()
        supabase.table("productos_catalogo").delete().neq("id", "").execute()
        print("  ✅ Tablas vaciadas")
    except Exception as e:
        print(f"  ❌ Error al vaciar: {e}")
        return

    # ── 6. Insertar catálogo ─────────────────────────────────────
    print(f"\n📤 Insertando {len(catalogo)} productos en productos_catalogo...")
    BATCH = 100
    ok = err = 0
    for i in range(0, len(catalogo), BATCH):
        lote = catalogo[i:i+BATCH]
        try:
            supabase.table("productos_catalogo").insert(lote).execute()
            ok += len(lote)
            print(f"  Lote {i//BATCH+1}/{(len(catalogo)+BATCH-1)//BATCH} ({ok} OK)", end="\r")
        except Exception as e:
            err += len(lote)
            print(f"\n  ❌ Error lote {i//BATCH+1}: {e}")
    print(f"\n  ✅ Catálogo: {ok} OK | ❌ {err} errores")

    # ── 7. Insertar matches ──────────────────────────────────────
    print(f"\n📤 Insertando {len(matches)} matches...")
    ok = err = 0
    for i in range(0, len(matches), BATCH):
        lote = matches[i:i+BATCH]
        try:
            supabase.table("productos_match").insert(lote).execute()
            ok += len(lote)
        except Exception as e:
            err += len(lote)
            print(f"  ❌ Error: {e}")
    print(f"  ✅ Matches: {ok} OK | ❌ {err} errores")

    print("\n" + "="*60)
    print(f"  ✅ CATÁLOGO CONSTRUIDO: {len(catalogo)} productos")
    print("="*60)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
