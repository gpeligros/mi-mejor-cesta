# test_matching_completo.py - VERSIÓN MEJORADA
"""
Test del flujo completo - Busca JSONs automáticamente
"""

import json
import os
import glob
from utils.matcher import AIProductMatcher
from utils.supabase_client import SupabaseClient

def find_latest_json():
    """Encuentra el JSON más reciente en data/"""
    json_files = glob.glob('data/mercadona_*.json')
    
    if not json_files:
        return None
    
    # Ordenar por fecha de modificación (más reciente primero)
    json_files.sort(key=os.path.getmtime, reverse=True)
    return json_files[0]

def test_flujo_completo():
    print("=" * 60)
    print("🧪 TEST FLUJO COMPLETO: SCRAPING → MATCHING → UPDATE")
    print("=" * 60)
    
    # 1. Buscar JSON automáticamente
    json_file = find_latest_json()
    
    if not json_file:
        print("❌ No se encontró archivo JSON de scraping en data/")
        print("\n💡 SOLUCIÓN:")
        print("   1. Ejecuta: python main.py")
        print("   2. Espera a que genere: data/mercadona_XXXXXXXX.json")
        print("   3. Vuelve a ejecutar este script")
        return
    
    print(f"✅ Encontrado: {json_file}")
    
    # 2. Cargar datos
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data_scrapeada = json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo JSON: {e}")
        return
    
    print(f"✅ Cargadas {len(data_scrapeada)} queries")
    
    # 3. Conectar a Supabase
    print("\n📊 Conectando a Supabase...")
    try:
        sb = SupabaseClient()
        productos_bd = sb.get_all_products()
        print(f"✅ Productos en BD: {len(productos_bd)}")
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return
    
    # Estadísticas de marcas
    con_marca = len([p for p in productos_bd if p.get('marca')])
    print(f"   Con marca: {con_marca} ({con_marca/len(productos_bd)*100:.1f}%)")
    
    # 4. Crear matcher
    matcher = AIProductMatcher()
    
    # 5. Seleccionar query para test
    # Buscar la que tenga más productos
    queries_con_productos = [(q, prods) for q, prods in data_scrapeada.items() if prods]
    
    if not queries_con_productos:
        print("❌ No hay productos en el JSON")
        return
    
    # Ordenar por cantidad de productos
    queries_con_productos.sort(key=lambda x: len(x[1]), reverse=True)
    
    test_query, productos_web_completos = queries_con_productos[0]
    productos_web = productos_web_completos[:3]  # Solo 3 para test rápido
    
    print(f"\n🧪 TEST CON: '{test_query}'")
    print(f"📦 Productos web totales: {len(productos_web_completos)}")
    print(f"📦 Procesando: {len(productos_web)} (primeros 3)")
    
    # Filtrar productos BD relevantes
    palabras = test_query.lower().split()
    productos_bd_filtrados = [
        p for p in productos_bd
        if any(palabra in p['nombre'].lower() for palabra in palabras)
           or (p.get('marca') and any(palabra in p['marca'].lower() for palabra in palabras))
    ][:20]
    
    if not productos_bd_filtrados:
        print("⚠️  No se encontraron productos BD con ese nombre, usando primeros 20...")
        productos_bd_filtrados = productos_bd[:20]
    
    print(f"🗄️  Productos BD candidatos: {len(productos_bd_filtrados)}")
    
    # 6. Match + Update
    print(f"\n{'='*60}")
    print("🔄 INICIANDO MATCHING + UPDATE")
    print(f"{'='*60}")
    
    try:
        results = matcher.match_batch(
            productos_web,
            productos_bd_filtrados,
            supabase_client=sb
        )
    except Exception as e:
        print(f"❌ Error en matching: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. Resumen
    print(f"\n{'='*60}")
    print("📊 RESULTADOS")
    print(f"{'='*60}")
    
    total = len(results['success']) + len(results['review']) + len(results['no_match']) + len(results['errors'])
    
    print(f"\nTotal procesados: {total}")
    print(f"✅ Actualizados exitosamente: {len(results['success'])}")
    print(f"⚠️  Requieren revisión manual: {len(results['review'])}")
    print(f"❌ Sin match: {len(results['no_match'])}")
    print(f"💥 Errores: {len(results['errors'])}")
    
    # Detalles de exitosos
    if results['success']:
        print(f"\n{'='*60}")
        print("✅ PRODUCTOS ACTUALIZADOS EN SUPABASE:")
        print(f"{'='*60}")
        
        for i, item in enumerate(results['success'], 1):
            prod_web = item['producto_web']
            match = item['match']
            prod_bd = item['producto_bd']
            
            print(f"\n[{i}] WEB: {prod_web['nombre'][:50]}")
            print(f"    Precio: {prod_web['precio']}€")
            print(f"    ↓")
            print(f"    BD: {prod_bd['nombre']} | Marca: {prod_bd.get('marca', 'N/A')} | Formato: {prod_bd.get('formato', 'N/A')}")
            print(f"    ID: {match['id_producto']} | Confianza: {match['confianza']}%")
    
    # Sin match
    if results['no_match']:
        print(f"\n{'='*60}")
        print("❌ SIN MATCH (agregar manualmente):")
        print(f"{'='*60}")
        for prod in results['no_match']:
            print(f"   - {prod['nombre'][:60]}")
    
    # Errores
    if results['errors']:
        print(f"\n{'='*60}")
        print("💥 ERRORES:")
        print(f"{'='*60}")
        for err in results['errors']:
            print(f"   - {err.get('error', 'Unknown')}")
    
    # 8. Guardar resultados
    output_file = 'data/matching_test_results.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source_file': json_file,
                'query_tested': test_query,
                'timestamp': str(os.path.getmtime(json_file)),
                'total_processed': total,
                'summary': {
                    'success': len(results['success']),
                    'review': len(results['review']),
                    'no_match': len(results['no_match']),
                    'errors': len(results['errors'])
                },
                'success_details': [
                    {
                        'web_nombre': item['producto_web']['nombre'],
                        'web_precio': item['producto_web']['precio'],
                        'bd_id': item['match']['id_producto'],
                        'bd_nombre': item['producto_bd']['nombre'],
                        'bd_marca': item['producto_bd'].get('marca'),
                        'confianza': item['match']['confianza']
                    }
                    for item in results['success']
                ]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados guardados: {output_file}")
    except Exception as e:
        print(f"⚠️  No se pudo guardar resultados: {e}")
    
    # 9. Verificar en Supabase
    if results['success']:
        print(f"\n{'='*60}")
        print("🔍 VERIFICACIÓN EN SUPABASE")
        print(f"{'='*60}")
        
        primer_match = results['success'][0]
        id_producto = primer_match['match']['id_producto']
        
        print(f"\n✅ Para verificar el primer producto actualizado:")
        print(f"   ID: {id_producto}")
        print(f"\n   SQL en Supabase:")
        print(f"   SELECT * FROM productos WHERE id_producto = '{id_producto}';")
        print(f"   SELECT * FROM precios_mercado WHERE id_producto = '{id_producto}';")
    
    print(f"\n{'='*60}")
    print("✅ TEST COMPLETADO")
    print(f"{'='*60}")
    
    # Resumen final
    tasa_exito = len(results['success']) / total * 100 if total > 0 else 0
    print(f"\n📊 TASA DE ÉXITO: {tasa_exito:.1f}%")
    
    if tasa_exito >= 80:
        print("🎉 ¡EXCELENTE! El sistema funciona muy bien")
    elif tasa_exito >= 60:
        print("👍 Bien. Necesita algunos ajustes")
    else:
        print("⚠️  Necesita revisión. Posibles problemas con nombres/marcas")
    
    return results


if __name__ == "__main__":
    test_flujo_completo()