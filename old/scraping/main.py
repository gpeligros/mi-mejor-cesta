# main.py - VERSIÓN SIMPLIFICADA
"""
Script principal para scrapear productos de Mercadona
Funciona con tu mercadona.py actual
"""

import json
import os
from datetime import datetime
from scrapers.mercadona import MercadonaScraper

def ensure_data_dir():
    """Crear carpeta data/ si no existe"""
    os.makedirs('data', exist_ok=True)

def scrape_products(productos_list, codigo_postal="28001"):
    """
    Scrapea una lista de productos
    """
    scraper = MercadonaScraper(codigo_postal=codigo_postal)
    
    resultados = {}
    
    print("=" * 60)
    print(f"🛒 SCRAPING {len(productos_list)} PRODUCTOS")
    print("=" * 60)
    
    for i, query in enumerate(productos_list, 1):
        print(f"\n[{i}/{len(productos_list)}] 🔍 Buscando: {query}")
        
        try:
            # Usar tu método search_product actual
            productos = scraper.search_product(query)
            resultados[query] = productos
            
            if productos:
                print(f"✅ {len(productos)} productos encontrados")
                for p in productos:
                    print(f"   • {p.get('nombre', 'N/A')} - {p.get('precio', 0)}€")
            else:
                print("❌ Sin resultados")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            resultados[query] = []
    
    return resultados


def save_results(resultados):
    """Guarda resultados en JSON y CSV"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON
    json_file = f"data/mercadona_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 JSON guardado: {json_file}")
    
    # CSV simple
    csv_file = f"data/mercadona_{timestamp}.csv"
    
    import csv
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Query', 'Nombre', 'Precio', 'Supermercado'])
        
        for query, productos in resultados.items():
            for prod in productos:
                writer.writerow([
                    query,
                    prod.get('nombre', ''),
                    prod.get('precio', 0),
                    prod.get('supermercado', 'Mercadona')
                ])
    
    print(f"💾 CSV guardado: {csv_file}")
    
    return json_file, csv_file


if __name__ == "__main__":
    # Crear carpeta data
    ensure_data_dir()
    
    # Lista de productos a scrapear
    PRODUCTOS = [
        "leche entera",
        "aceite oliva",
        "arroz",
        "huevos",
        "pan de molde"
    ]
    
    # Pedir código postal
    print("\n📮 Código Postal")
    cp = input("Introduce tu CP (Enter para 28001-Madrid): ").strip()
    if not cp:
        cp = "28001"
    
    print(f"\n✅ Usando código postal: {cp}")
    
    # Scrapear
    resultados = scrape_products(PRODUCTOS, codigo_postal=cp)
    
    # Guardar
    json_file, csv_file = save_results(resultados)
    
    # Resumen
    total_productos = sum(len(prods) for prods in resultados.values())
    
    print("\n" + "=" * 60)
    print("✅ SCRAPING COMPLETADO")
    print("=" * 60)
    print(f"📊 Productos buscados: {len(PRODUCTOS)}")
    print(f"📦 Productos encontrados: {total_productos}")
    print(f"💾 Archivos generados:")
    print(f"   - {json_file}")
    print(f"   - {csv_file}")
    print("=" * 60)