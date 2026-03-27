from playwright.sync_api import sync_playwright
import csv
import time

def extraer_carrefour_final():
    with sync_playwright() as p:
        # Usamos el canal de Chrome instalado si es posible, si no, usa el de defecto
        browser = p.chromium.launch(headless=False) 
        
        # Configuramos un contexto que parezca 100% humano
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-ES",
            timezone_id="Europe/Madrid"
        )
        
        page = context.new_page()
        resultados = []

        def interceptar(response):
            if "search-api/queries/v1/search" in response.url:
                try:
                    data = response.json()
                    docs = data.get('content', {}).get('docs', [])
                    resultados.extend(docs)
                    print(f"✨ Capturados {len(docs)} productos de la API.")
                except: pass

        page.on("response", interceptar)

        try:
            print("🚀 Navegando a Carrefour...")
            # Bajamos la exigencia de espera a 'commit' (cuando el servidor responde)
            page.goto("https://www.carrefour.es", wait_until="domcontentloaded", timeout=60000)
            
            # Esperamos a que aparezca cualquier botón (normalmente el de cookies)
            print("⏳ Esperando interacción inicial...")
            time.sleep(5)

            # Intentar cerrar el banner de cookies si aparece
            try:
                # Buscamos por ID común o texto
                page.click("#onetrust-accept-btn-handler", timeout=5000)
                print("✅ Cookies aceptadas.")
            except:
                print("⚠️ No se encontró botón de cookies, procediendo...")

            # Buscamos y escribimos
            print("⌨️ Buscando producto...")
            search_box = page.locator("input[name='query']").first
            search_box.fill("coca cola")
            search_box.press("Enter")

            # Esperamos a que la API responda tras la búsqueda
            time.sleep(8)

        except Exception as e:
            print(f"❌ Error durante la navegación: {e}")

        if resultados:
            with open('carrefour_final.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['EAN', 'Nombre', 'Precio'])
                writer.writeheader()
                for prod in resultados:
                    writer.writerow({
                        'EAN': prod.get('ean', 'N/A'),
                        'Nombre': prod.get('display_name', 'S/N'),
                        'Precio': f"{prod.get('active_price', 0)}€"
                    })
            print(f"💾 Guardado con éxito en 'carrefour_final.csv'.")
        else:
            print("❌ No se capturaron productos. Comprueba si la ventana del navegador muestra un error de acceso.")

        browser.close()

if __name__ == "__main__":
    extraer_carrefour_final()