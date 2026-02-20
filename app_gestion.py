"""
Mini App de Gestion de Base de Datos - Mi Mejor Cesta
Gestiona productos, precios y codigos libres
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime
import json

# IMPORTANTE: Instalar dependencias primero
# pip install flask supabase

try:
    from supabase import create_client, Client
except ImportError:
    print("ERROR: Instala supabase primero")
    print("Ejecuta: pip install supabase")
    exit()

app = Flask(__name__)

# =====================================================
# CONFIGURACION SUPABASE
# =====================================================

# IMPORTANTE: Reemplaza con tus credenciales
SUPABASE_URL = "https://scpuriaofisssalsbzqv.supabase.co"
SUPABASE_KEY = "sb_secret_izhTc9q5TA_p4ItbeDB-UA_9zCDAYvi"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# FUNCIONES DE GESTION
# =====================================================

def obtener_todos_productos():
    """Obtiene todos los productos de Supabase"""
    try:
        response = supabase.table('productos').select('*').execute()
        return response.data
    except Exception as e:
        print(f"Error: {e}")
        return []

def obtener_codigos_usados():
    """Obtiene conjunto de codigos en uso"""
    productos = obtener_todos_productos()
    return set(p['id_producto'] for p in productos)

def detectar_codigos_libres():
    """Detecta huecos en la numeracion"""
    productos = obtener_todos_productos()
    
    # Agrupar por categoria-subcategoria
    grupos = {}
    for p in productos:
        codigo = p['id_producto']
        if '-' in codigo:
            partes = codigo.split('-')
            if len(partes) == 3:
                clave = f"{partes[0]}-{partes[1]}"
                numero = int(partes[2])
                
                if clave not in grupos:
                    grupos[clave] = []
                grupos[clave].append(numero)
    
    # Detectar huecos
    codigos_libres = []
    for clave, numeros in grupos.items():
        numeros.sort()
        maximo = max(numeros)
        
        for i in range(1, maximo + 1):
            if i not in numeros:
                codigo_libre = f"{clave}-{str(i).zfill(3)}"
                codigos_libres.append({
                    'codigo': codigo_libre,
                    'categoria': clave
                })
    
    return codigos_libres

def eliminar_producto(id_producto):
    """Elimina producto y sus precios"""
    try:
        # Eliminar precios
        supabase.table('precios_mercado').delete().eq('id_producto', id_producto).execute()
        
        # Eliminar producto
        supabase.table('productos').delete().eq('id_producto', id_producto).execute()
        
        return True
    except Exception as e:
        print(f"Error eliminando: {e}")
        return False

def obtener_productos_sin_precio():
    """Detecta productos que no tienen precio en algun supermercado"""
    productos = obtener_todos_productos()
    response_precios = supabase.table('precios_mercado').select('*').execute()
    precios = response_precios.data
    
    # Agrupar precios por producto
    precios_por_producto = {}
    for precio in precios:
        id_prod = precio['id_producto']
        if id_prod not in precios_por_producto:
            precios_por_producto[id_prod] = []
        precios_por_producto[id_prod].append(precio['supermercado'])
    
    # Detectar faltantes
    sin_precio = []
    supermercados = ['Mercadona', 'Lidl', 'Carrefour']
    
    for producto in productos:
        id_prod = producto['id_producto']
        supers_con_precio = precios_por_producto.get(id_prod, [])
        faltantes = [s for s in supermercados if s not in supers_con_precio]
        
        if faltantes:
            sin_precio.append({
                'producto': producto,
                'faltantes': faltantes
            })
    
    return sin_precio

# =====================================================
# RUTAS DE LA APP
# =====================================================

@app.route('/')
def index():
    """Dashboard principal"""
    productos = obtener_todos_productos()
    codigos_libres = detectar_codigos_libres()
    sin_precio = obtener_productos_sin_precio()
    
    stats = {
        'total_productos': len(productos),
        'codigos_libres': len(codigos_libres),
        'sin_precio': len(sin_precio)
    }
    
    return render_template('dashboard.html', 
                         stats=stats,
                         codigos_libres=codigos_libres[:10],
                         sin_precio=sin_precio[:10])

@app.route('/productos')
def productos():
    """Lista todos los productos"""
    todos = obtener_todos_productos()
    return render_template('productos.html', productos=todos)

@app.route('/api/eliminar/<id_producto>', methods=['DELETE'])
def api_eliminar(id_producto):
    """API para eliminar producto"""
    exito = eliminar_producto(id_producto)
    return jsonify({'success': exito})

@app.route('/api/codigos-libres')
def api_codigos_libres():
    """API que devuelve codigos libres"""
    codigos = detectar_codigos_libres()
    return jsonify(codigos)

@app.route('/api/stats')
def api_stats():
    """API con estadisticas"""
    productos = obtener_todos_productos()
    codigos_libres = detectar_codigos_libres()
    sin_precio = obtener_productos_sin_precio()
    
    return jsonify({
        'total_productos': len(productos),
        'codigos_libres': len(codigos_libres),
        'sin_precio': len(sin_precio)
    })

# =====================================================
# TEMPLATES HTML
# =====================================================

def crear_templates():
    """Crea carpeta templates con archivos HTML"""
    os.makedirs('templates', exist_ok=True)
    
    # Dashboard
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mi Mejor Cesta - Gestion BD</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-success">
        <div class="container">
            <span class="navbar-brand">Mi Mejor Cesta - Gestion</span>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2>Dashboard</h2>
        
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <h5 class="card-title">Total Productos</h5>
                        <h2>{{ stats.total_productos }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-warning">
                    <div class="card-body">
                        <h5 class="card-title">Codigos Libres</h5>
                        <h2>{{ stats.codigos_libres }}</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-white bg-danger">
                    <div class="card-body">
                        <h5 class="card-title">Sin Precio</h5>
                        <h2>{{ stats.sin_precio }}</h2>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <h4>Codigos Libres (Top 10)</h4>
                <ul class="list-group">
                    {% for codigo in codigos_libres %}
                    <li class="list-group-item">
                        <strong>{{ codigo.codigo }}</strong> - {{ codigo.categoria }}
                    </li>
                    {% endfor %}
                </ul>
            </div>
            
            <div class="col-md-6">
                <h4>Productos sin Precio (Top 10)</h4>
                <ul class="list-group">
                    {% for item in sin_precio %}
                    <li class="list-group-item">
                        <strong>{{ item.producto.nombre }}</strong><br>
                        <small>Falta: {{ item.faltantes|join(', ') }}</small>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        
        <div class="mt-4">
            <a href="/productos" class="btn btn-success">Ver Todos los Productos</a>
        </div>
    </div>
</body>
</html>
        ''')
    
    # Lista productos
    with open('templates/productos.html', 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Productos - Gestion BD</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-success">
        <div class="container">
            <a class="navbar-brand" href="/">← Dashboard</a>
            <span class="navbar-text">Gestion de Productos</span>
        </div>
    </nav>
    
    <div class="container mt-4">
        <h2>Todos los Productos ({{ productos|length }})</h2>
        
        <input type="text" id="buscar" class="form-control mt-3" placeholder="Buscar producto...">
        
        <table class="table table-striped mt-3" id="tabla-productos">
            <thead>
                <tr>
                    <th>Codigo</th>
                    <th>Nombre</th>
                    <th>Categoria</th>
                    <th>Formato</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for p in productos %}
                <tr>
                    <td><strong>{{ p.id_producto }}</strong></td>
                    <td>{{ p.nombre }}</td>
                    <td>{{ p.categoria }}</td>
                    <td>{{ p.formato }}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="eliminar('{{ p.id_producto }}')">
                            Eliminar
                        </button>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <script>
        // Busqueda
        document.getElementById('buscar').addEventListener('input', function(e) {
            const busqueda = e.target.value.toLowerCase();
            const filas = document.querySelectorAll('#tabla-productos tbody tr');
            
            filas.forEach(fila => {
                const texto = fila.textContent.toLowerCase();
                fila.style.display = texto.includes(busqueda) ? '' : 'none';
            });
        });
        
        // Eliminar producto
        function eliminar(id_producto) {
            if (confirm('¿Eliminar producto ' + id_producto + '?')) {
                fetch('/api/eliminar/' + id_producto, { method: 'DELETE' })
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            alert('Producto eliminado');
                            location.reload();
                        }
                    });
            }
        }
    </script>
</body>
</html>
        ''')

# =====================================================
# MAIN
# =====================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("MI MEJOR CESTA - MINI APP DE GESTION")
    print("=" * 60)
    
    # Verificar credenciales
    if "TU_PROYECTO" in SUPABASE_URL:
        print("\n⚠️  IMPORTANTE: Configura tus credenciales de Supabase")
        print("Edita este archivo y reemplaza:")
        print("  SUPABASE_URL = 'https://scpuriaofisssalsbzqv.supabase.co'")
        print("  SUPABASE_KEY = 'sb_secret_izhTc9q5TA_p4ItbeDB-UA_9zCDAYvi'")
        print("\nEncuentra tus credenciales en:")
        print("  Supabase → Settings → API")
        exit()
    
    # Crear templates
    print("\nCreando templates HTML...")
    crear_templates()
    
    print("\n✅ App lista")
    print("\nAbre en tu navegador:")
    print("  http://localhost:5000")
    print("\nPresiona Ctrl+C para detener\n")
    
    app.run(debug=True, port=5000)