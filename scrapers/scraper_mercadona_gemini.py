import requests

def get_mercadona_products(query="leche"):
    # El 'warehouse' depende del código postal. 
    # Ejemplo: 41001 (Sevilla) suele ser 'sevilla-1'
    url = f"https://queries.mercadona.es/v1/search/?q={query}&limit=10"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for product in data.get('results', []):
            print(f"Producto: {product['display_name']} - Precio: {product['price_instructions']['unit_price']}€")
    else:
        print(f"Error: {response.status_code}")

get_mercadona_products("yogur")