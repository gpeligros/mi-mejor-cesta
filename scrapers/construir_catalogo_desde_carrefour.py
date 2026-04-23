"""
construir_catalogo_desde_carrefour.py — Mi Mejor Cesta
=======================================================
Construye productos_catalogo DESDE CARREFOUR (7.241 productos)
como BASE del catálogo maestro.

Pasos:
  1. TRUNCATE productos_catalogo y productos_match
  2. Lee precios_carrefour con categorías mapeadas
  3. Agrupa productos similares (marca blanca → nombre genérico)
  4. Asigna id_categoria correcto según mapping Carrefour→nuestras categorías
  5. Inserta en productos_catalogo y productos_match
  6. Genera id_carrefour en matches

Uso:
  python scrapers/construir_catalogo_desde_carrefour.py --dry-run   
  python scrapers/construir_catalogo_desde_carrefour.py             

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
# MAPPING: Carrefour categories → categorias_maestras ID
# ══════════════════════════════════════════════════════════════════════════════

MAPPING_CARREFOUR = {
    # La despensa (alimentos básicos, conservas, etc.)
    "la-despensa": [
        (112, "conservas, caldos y cremas"),  # sopas, caldos
        (113, "conservas, caldos y cremas"),  # tomate, conservas
        (134, "arroz, legumbres y pasta"),    # arroz, pasta
        (138, "arroz, legumbres y pasta"),    # legumbres
        (125, "cacao, cafe e infusiones"),    # café, cacao
        (132, "cacao, cafe e infusiones"),    # té
        (130, "azucar, caramelos y chocolate"), # mermelada, miel
        (135, "azucar, caramelos y chocolate"), # azúcar
        (86, "azucar, caramelos y chocolate"),  # caramelos
        (87, "azucar, caramelos y chocolate"),  # chocolate
        (131, "aperitivos"),                   # snacks
        (127, "aperitivos"),                   # frutos secos
        (140, "aceite, especias y salsas"),   # salsas, condimentos
        (141, "aceite, especias y salsas"),   # vinagre
    ],
    
    # Frescos (carnes, pescados, frutas, verduras)
    "frescos": [
        (100, "carne"),                        # carne general
        (101, "carne"),                        # cerdo
        (102, "charcuteria y quesos"),        # embutidos
        (103, "carne"),                        # conejo, cordero
        (105, "carne"),                        # aves
        (106, "carne"),                        # vacuno
        (157, "charcuteria y quesos"),        # quesos
        (168, "marisco y pescado"),           # pescado fresco
        (166, "marisco y pescado"),           # marisco
        (167, "marisco y pescado"),           # moluscos
        (142, "fruta y verdura"),             # frutas
        (144, "fruta y verdura"),             # verduras
    ],
    
    # Bebidas (refrescos, agua, cerveza, vino)
    "bebidas": [
        (94, "agua y refrescos"),             # agua
        (97, "agua y refrescos"),             # refrescos
        (95, "bodega"),                       # cerveza
        (96, "bodega"),                       # licores
        (98, "bodega"),                       # vino
    ],
    
    # Perfumería e higiene
    "perfumeria-e-higiene": [
        (114, "cuidado facial y corporal"),   # cuidado facial
        (115, "cuidado del cabello"),         # champú
        (116, "cuidado facial y corporal"),   # desodorante
        (117, "cuidado facial y corporal"),   # higiene bucal
        (118, "cuidado facial y corporal"),   # gel y jabón
        (119, "cuidado facial y corporal"),   # higiene íntima
        (123, "cuidado facial y corporal"),   # perfume
        (120, "maquillaje"),                  # maquillaje
        (121, "maquillaje"),                  # depilación
    ],
    
    # Droguería y limpieza
    "drogueria-y-limpieza": [
        (145, "limpieza y hogar"),            # insecticida
        (146, "limpieza y hogar"),            # detergente
        (147, "limpieza y hogar"),            # lavavajillas
        (148, "limpieza y hogar"),            # lejía
        (149, "limpieza y hogar"),            # limpieza
        (151, "limpieza y hogar"),            # papel, bolsas
    ],
    
    # Congelados
    "congelados": [
        (107, "congelados"),                  # helados, tartas
        (108, "congelados"),                  # pescado, pizza, rebozados
        (109, "congelados"),                  # verdura
    ],
    
    # Bebé
    "bebe": [
        (90, "bebe"),                         # alimentación infantil
        (91, "bebe"),                         # biberon, cuidado
        (92, "bebe"),                         # toallitas, pañales
    ],
    
    # Mascotas
    "mascotas": [
        (159, "mascotas"),                    # accesorios
        (160, "mascotas"),                    # arena
        (161, "mascotas"),                    # comida
        (162, "mascotas"),                    # comida perro
    ],
    
    # Parafarmacia
    "parafarmacia": [
        (122, "fitoterapia y parafarmacia"),  # parafarmacia
    ],
}

# ── Funciones auxiliares ───────────────────────────────────────────────────────

def normalizar(s):
    """Normaliza string para comparaciones."""
    if not s:
        return ""
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', s)

def es_marca_blanca(nombre, marca):
    """Detecta si es marca blanca (Hacendado, Alteza, etc.)."""
    marcas_blancas = [
        "hacendado", "alteza", "alipende", "dia", "producto libre",
        "carrefour", "selection", "basico", "bien by carrefour",
        "mercadona", "marca blanca"
    ]
    
    nombre_norm = normalizar(nombre)
    marca_norm = normalizar(marca) if marca else ""
    
    for mb in marcas_blancas:
        if mb in nombre_norm or mb in marca_norm:
            return True
    return False

def generar_nombre_generico(nombre_comercial):
    """Extrae nombre genérico de una marca blanca."""
    # Eliminar marcas blancas conocidas
    marcas_a_quitar = [
        "hacendado", "alteza", "alipende", "marca blanca",
        "carrefour", "selection", "basico", "bien by carrefour",
        "dia marca blanca", "mercadona", "producto libre"
    ]
    
    nombre = nombre_comercial.lower()
    for marca in marcas_a_quitar:
        nombre = nombre.replace(marca, "").strip()
    
    # Quitar palabrillas finales
    palabras_fin = [
        "pack", "lata", "bote", "paquete", "bolsa", "caja", "envase",
        "botella", "frasco", "liter", "l.", "kg.", "gr.", "unidad",
        "ud.", "unid.", "unds.", "units", "piezas", "x 1", "x1"
    ]
    for p in palabras_fin:
        if nombre.lower().endswith(p):
            nombre = nombre[:-(len(p))].strip()
    
    # Normalizar espacios
    nombre = re.sub(r'\s+', ' ', nombre).strip(" -,.")
    return nombre

def obtener_id_categoria(url_categoria):
    """Mapea URL de categoría Carrefour → id_categoria de categorias_maestras."""
    # Extraer slug de URL si es necesario
    slug = url_categoria.lower().strip()
    
    # Si viene con URL completa, extraer el slug
    if "/" in slug:
        slug = slug.split("/")[-1].strip("/")
    
    # Buscar en el mapping
    if slug in MAPPING_CARREFOUR:
        # Devolver la categoría más general (primera del mapping)
        return MAPPING_CARREFOUR[slug][0][0]
    
    # Default a "Otros" (categoría genérica) si no está en mapping
    return None

def fetch_all(tabla, columnas="*"):
    """Obtiene todos los registros de una tabla."""
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
    print("  🏗️  CONSTRUIR CATÁLOGO DESDE CARREFOUR")
    print(f"  Modo: {'DRY-RUN (sin guardar)' if dry_run else '⚠️  PRODUCCIÓN'}")
    print("=" * 60)

    # ── 1. Cargar productos de Carrefour ──────────────────────────
    print("\n📥 Cargando precios_carrefour...")
    carrefour = fetch_all("precios_carrefour",
        "id, id_api, nombre_comercial, marca, precio, url")
    print(f"  {len(carrefour)} productos Carrefour")
    
    # Extraer categoría de la URL si existe
    # Como el scraper no guarda categoría, haremos un mapeo aproximado
    # por ahora asignaremos "la-despensa" como categoría default
    print(f"  ⚠️  Nota: Carrefour no tiene categorías en BBDD aún")
    print(f"      Se asignará categoría por defecto 'la-despensa' para todos")
    print(f"      (próximas versiones añadirán categorías al scraper)")

    # ── 2. Construir catálogo ────────────────────────────────────
    print("\n🔧 Construyendo catálogo...")

    catalogo = []       # filas para productos_catalogo
    matches  = []       # filas para productos_match

    # ── 3. Deduplicar: solo productos exactamente iguales
    print("\n🔍 Procesando productos...")
    vistos = {}  # clave: nombre_comercial_normalizado → datos

    for prod in carrefour:
        # Por ahora, categoría default
        id_cat = obtener_id_categoria("la-despensa")
        
        if not id_cat:
            print(f"  ⚠️  No se puede mapear categoría para {prod.get('id')}")
            continue

        nombre_comercial = (prod.get("nombre_comercial") or "").strip()
        if not nombre_comercial or len(nombre_comercial) < 3:
            continue

        marca = (prod.get("marca") or "").strip()
        mb   = es_marca_blanca(nombre_comercial, marca)
        tipo = "marca_blanca" if mb else "marca_fabricante"

        # Para marca blanca: usar nombre genérico
        # Para marca fabricante: usar nombre comercial completo
        if mb:
            nombre_catalogo = generar_nombre_generico(nombre_comercial)
            if not nombre_catalogo or len(nombre_catalogo) < 3:
                nombre_catalogo = nombre_comercial
            # Deduplicar marcas blancas por nombre genérico + categoría
            clave_dedup = (normalizar(nombre_catalogo), id_cat)
        else:
            # Marca fabricante: mantener nombre completo
            nombre_catalogo = nombre_comercial
            clave_dedup = (normalizar(nombre_comercial), id_cat)

        if clave_dedup not in vistos:
            vistos[clave_dedup] = {
                "nombre_gen": nombre_catalogo,
                "id_cat":     id_cat,
                "tipo":       tipo,
                "id_carr":    prod["id"],
                "marca":      marca,
            }

    print(f"  {len(vistos)} productos únicos (de {len(carrefour)} totales)")

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
            "id_carrefour": v["id_carr"],
        })

    print(f"  ✅ Productos a insertar: {len(catalogo)}")
    print(f"     Marca blanca:     {sum(1 for c in catalogo if c['tipo'] == 'marca_blanca')}")
    print(f"     Marca fabricante: {sum(1 for c in catalogo if c['tipo'] == 'marca_fabricante')}")

    # ── 5. Mostrar muestra ───────────────────────────────────────
    print("\n📋 Muestra de los primeros 20 productos:")
    for c in catalogo[:20]:
        print(f"  {c['id']} | {c['tipo'][:2].upper()} | cat:{c['id_categoria']:3d} | {c['nombre_generico']}")

    if dry_run:
        print("\n[dry-run] No se guarda nada.")
        print(f"\nPara construir el catálogo real ejecuta sin --dry-run")
        return

    # ── 6. Confirmar ─────────────────────────────────────────────
    print(f"\n⚠️  Se van a BORRAR todos los datos de:")
    print(f"   - productos_catalogo ({len(catalogo)} nuevos a insertar)")
    print(f"   - productos_match ({len(matches)} nuevos a insertar)")
    resp = input("\n¿Continuar? Escribe 'SI' para confirmar: ")
    if resp.strip().upper() != "SI":
        print("Cancelado.")
        return

    # ── 7. TRUNCATE ──────────────────────────────────────────────
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

    # ── 8. Insertar catálogo ─────────────────────────────────────
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

    # ── 9. Insertar matches ──────────────────────────────────────
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
    print(f"  ✅ CATÁLOGO CONSTRUIDO DESDE CARREFOUR: {len(catalogo)} productos")
    print("="*60)
    print(f"\n📋 Próximos pasos:")
    print(f"   1. Ejecutar: python scrapers/enriquecer_catalogo.py --dry-run")
    print(f"   2. Ejecutar: python scrapers/enriquecer_catalogo.py")
    print(f"   3. Matching desde Mercadona → nuevo catálogo")
    print(f"   4. Actualizar App.js con precios_carrefour")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    main(dry_run=args.dry_run)
