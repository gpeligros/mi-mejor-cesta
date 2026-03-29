"""
enriquecer_catalogo.py
======================
Enriquece la tabla productos_catalogo con tres campos nuevos:
  - tipo            → 'marca_fabricante' | 'marca_blanca'
  - formato         → "1L", "500g", "pack 6x33cl", etc. (o None si no aplica)
  - nombre_normalizado → nombre limpio y verdaderamente genérico
  - marca           → nombre de la marca si es marca_fabricante (o None)

USO:
  python scrapers/enriquecer_catalogo.py --dry-run    # simula sin escribir en BBDD
  python scrapers/enriquecer_catalogo.py              # ejecuta de verdad
  python scrapers/enriquecer_catalogo.py --desde 500  # empieza desde el producto 500
  python scrapers/enriquecer_catalogo.py --limite 100 # procesa solo 100 productos

REQUISITOS:
  - pip install anthropic supabase python-dotenv
  - .env con SUPABASE_URL, SUPABASE_KEY (service role), ANTHROPIC_API_KEY
  - Ejecutar PRIMERO la migración SQL: enriquecer_catalogo.sql

COSTE ESTIMADO:
  ~4.173 productos × ~200 tokens input + ~80 tokens output por producto
  (procesados en lotes de 30) → aprox. 0,80–1,20 $ con claude-3-5-haiku
"""

import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv
import anthropic
from supabase import create_client, Client

# ── Configuración ──────────────────────────────────────────────────────────────
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")          # service role key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

BATCH_SIZE = 30          # productos por llamada a la API (óptimo coste/velocidad)
SLEEP_ENTRE_LOTES = 1.5  # segundos entre lotes (evita rate limit)
MODEL = "claude-haiku-4-5-20251001"  # modelo más económico, suficiente para esta tarea

# ── Prompt del sistema ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un experto en clasificación de productos de supermercado español.
Tu tarea es analizar nombres de productos y devolver SIEMPRE un JSON válido, sin texto adicional.

Para cada producto debes determinar:

1. "tipo": 
   - "marca_fabricante" si el nombre incluye una marca comercial conocida (Coca-Cola, Milka,
     Nestlé, Valor, Halls, Huesitos, Actimel, Danone, Hellmann's, Mahou, Estrella, etc.)
   - "marca_blanca" si es un producto genérico sin marca o con marca del supermercado
     (Hacendado, Alteza, etc. también cuentan como marca_blanca)

2. "marca": 
   - El nombre exacto de la marca si tipo="marca_fabricante" (ej: "Milka", "Nestlé", "Valor")
   - null si tipo="marca_blanca"

3. "formato":
   - El formato/cantidad del producto extraído del nombre si aparece explícitamente
     Ejemplos: "1L", "500g", "330ml", "pack 6x33cl", "2kg", "200g", "gragea"
   - null si no hay formato explícito en el nombre

4. "nombre_normalizado":
   - El nombre genérico del producto SIN marca, SIN formato, limpio y neutro
   - En minúsculas excepto nombres propios
   - Sin referencias específicas a un supermercado
   - Ejemplos:
     "Chocolate con leche Milka galleta" → "chocolate con leche con galleta"
     "Caramelos sabor lima 0% azúcares" → "caramelos sabor lima sin azúcar"
     "Barritas de barquillo Huesitos bañadas de chocolate con leche" → "barritas de barquillo con chocolate con leche"
     "Aceite de girasol 0,2º 1L" → "aceite de girasol 0,2°"
     "Cerveza Mahou 5 Estrellas lata 33cl" → "cerveza rubia"

Devuelve ÚNICAMENTE un array JSON con un objeto por producto, en el mismo orden recibido.
Formato exacto:
[
  {"id": "CAT-xxxx", "tipo": "...", "marca": "...", "formato": "...", "nombre_normalizado": "..."},
  ...
]"""

# ── Funciones principales ──────────────────────────────────────────────────────

def construir_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ ERROR: Faltan SUPABASE_URL o SUPABASE_KEY en .env")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def construir_anthropic() -> anthropic.Anthropic:
    if not ANTHROPIC_API_KEY:
        print("❌ ERROR: Falta ANTHROPIC_API_KEY en .env")
        sys.exit(1)
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def fetch_productos(supabase: Client, desde: int = 0, limite: int = None) -> list:
    """Obtiene productos que aún no han sido enriquecidos (tipo IS NULL)."""
    query = (
        supabase.table("productos_catalogo")
        .select("id, nombre_generico, id_categoria")
        .is_("tipo", "null")  # solo los que faltan
        .eq("activo", True)
        .order("id")
        .offset(desde)
    )
    if limite:
        query = query.limit(limite)
    else:
        query = query.limit(10000)  # máximo seguro

    resultado = query.execute()
    return resultado.data


def clasificar_lote(cliente: anthropic.Anthropic, productos: list) -> list:
    """Envía un lote de productos a Claude y devuelve la clasificación."""
    
    # Construir el texto del lote
    lineas = []
    for p in productos:
        lineas.append(f'{p["id"]}: {p["nombre_generico"]}')
    texto_lote = "\n".join(lineas)
    
    mensaje = cliente.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Clasifica estos {len(productos)} productos:\n\n{texto_lote}"
            }
        ]
    )
    
    respuesta_texto = mensaje.content[0].text.strip()
    
    # Limpiar posibles marcadores de código markdown
    if respuesta_texto.startswith("```"):
        respuesta_texto = respuesta_texto.split("\n", 1)[1]
        respuesta_texto = respuesta_texto.rsplit("```", 1)[0]
    
    return json.loads(respuesta_texto)


def actualizar_producto(supabase: Client, clasificacion: dict) -> bool:
    """Actualiza un producto en la BBDD con los datos clasificados."""
    producto_id = clasificacion["id"]
    
    datos = {
        "tipo": clasificacion.get("tipo"),
        "formato": clasificacion.get("formato"),
        "nombre_normalizado": clasificacion.get("nombre_normalizado"),
    }
    
    # Solo actualizar marca si es marca_fabricante (la columna ya existe)
    if clasificacion.get("tipo") == "marca_fabricante" and clasificacion.get("marca"):
        datos["marca"] = clasificacion.get("marca")
    
    resultado = (
        supabase.table("productos_catalogo")
        .update(datos)
        .eq("id", producto_id)
        .execute()
    )
    return len(resultado.data) > 0


# ── Función principal ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Enriquece productos_catalogo con IA")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sin escribir en la BBDD")
    parser.add_argument("--desde", type=int, default=0,
                        help="Offset: empieza desde el producto N")
    parser.add_argument("--limite", type=int, default=None,
                        help="Procesa solo N productos")
    args = parser.parse_args()

    modo = "🔍 DRY-RUN (sin escritura)" if args.dry_run else "✍️  PRODUCCIÓN (escribe en BBDD)"
    print(f"\n{'='*60}")
    print(f"  enriquecer_catalogo.py — {modo}")
    print(f"{'='*60}\n")

    # Conectar
    supabase = construir_supabase()
    cliente_ai = construir_anthropic()

    # Obtener productos pendientes
    print(f"🔎 Buscando productos sin enriquecer (tipo IS NULL)...")
    productos = fetch_productos(supabase, desde=args.desde, limite=args.limite)
    total = len(productos)
    
    if total == 0:
        print("✅ No hay productos pendientes de enriquecer. ¡Todo al día!")
        return

    print(f"📦 Productos a procesar: {total}")
    print(f"🤖 Modelo: {MODEL} | Lotes de {BATCH_SIZE} productos\n")

    # Estadísticas
    procesados = 0
    errores = 0
    marcas_fabricante = 0
    marcas_blancas = 0

    # Procesar en lotes
    for i in range(0, total, BATCH_SIZE):
        lote = productos[i:i + BATCH_SIZE]
        num_lote = (i // BATCH_SIZE) + 1
        total_lotes = (total + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"📤 Lote {num_lote}/{total_lotes} ({len(lote)} productos)...", end=" ", flush=True)
        
        try:
            clasificaciones = clasificar_lote(cliente_ai, lote)
            
            # Validar que la respuesta tiene el mismo número de productos
            if len(clasificaciones) != len(lote):
                print(f"\n⚠️  AVISO: Se enviaron {len(lote)} pero se recibieron {len(clasificaciones)} clasificaciones")
            
            # Procesar cada clasificación
            for clasificacion in clasificaciones:
                tipo = clasificacion.get("tipo", "desconocido")
                if tipo == "marca_fabricante":
                    marcas_fabricante += 1
                elif tipo == "marca_blanca":
                    marcas_blancas += 1
                
                if not args.dry_run:
                    ok = actualizar_producto(supabase, clasificacion)
                    if not ok:
                        errores += 1
                        print(f"\n  ⚠️  No se actualizó: {clasificacion.get('id')}")
                else:
                    # En dry-run, imprimir los primeros 3 de cada lote como muestra
                    if clasificaciones.index(clasificacion) < 3:
                        print(f"\n  [{clasificacion['id']}] {clasificacion.get('tipo')} | "
                              f"marca={clasificacion.get('marca')} | "
                              f"formato={clasificacion.get('formato')} | "
                              f"→ {clasificacion.get('nombre_normalizado')}")
                
                procesados += 1
            
            print(f"✅ ({procesados}/{total})")
            
        except json.JSONDecodeError as e:
            print(f"\n❌ Error parseando JSON del lote {num_lote}: {e}")
            errores += len(lote)
        except anthropic.APIError as e:
            print(f"\n❌ Error de API Anthropic en lote {num_lote}: {e}")
            errores += len(lote)
            print("   Esperando 10 segundos antes de continuar...")
            time.sleep(10)
        except Exception as e:
            print(f"\n❌ Error inesperado en lote {num_lote}: {e}")
            errores += len(lote)
        
        # Pausa entre lotes (excepto el último)
        if i + BATCH_SIZE < total:
            time.sleep(SLEEP_ENTRE_LOTES)

    # Resumen final
    print(f"\n{'='*60}")
    print(f"  RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"  Procesados:        {procesados}")
    print(f"  Marca fabricante:  {marcas_fabricante}")
    print(f"  Marca blanca:      {marcas_blancas}")
    print(f"  Errores:           {errores}")
    if args.dry_run:
        print(f"\n  ⚠️  DRY-RUN: No se escribió nada en la BBDD.")
        print(f"      Ejecuta sin --dry-run para aplicar los cambios.")
    else:
        print(f"\n  ✅ Cambios aplicados en Supabase.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
