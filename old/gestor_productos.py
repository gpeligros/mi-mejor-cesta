"""
🛒 MI MEJOR CESTA - GESTOR DE PRODUCTOS
Mini aplicación web para gestionar la base de datos de productos

Funcionalidades:
1. ✅ Añadir productos nuevos
2. ✅ Actualizar productos existentes
3. ✅ Ver categorías disponibles
4. ✅ Generar SQLs automáticamente
5. ✅ Validar integridad de datos

Uso:
    python gestor_productos.py

Luego abre: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import csv
import os
from datetime import datetime

app = Flask(__name__)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Rutas de archivos
MERCADONA_CSV = 'MERCADONA_FINAL.csv'
GENERICOS_CSV = 'PRODUCTOS_GENERICOS_FIXED.csv'
OUTPUT_DIR = 'output_sqls'

# Crear carpeta de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def cargar_categorias():
    """Carga categorías únicas desde el CSV de Mercadona"""
    categorias = {}
    
    if not os.path.exists(MERCADONA_CSV):
        return {}
    
    with open(MERCADONA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            cat = row['categoria']
            subcat = row['subcategoria']
            
            if cat not in categorias:
                categorias[cat] = set()
            categorias[cat].add(subcat)
    
    # Convertir sets a listas ordenadas
    return {cat: sorted(list(subcats)) for cat, subcats in categorias.items()}

def obtener_ultimo_id():
    """Obtiene el último ID usado"""
    if not os.path.exists(MERCADONA_CSV):
        return 'ME-0000'
    
    with open(MERCADONA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        productos = list(reader)
        
        if productos:
            ultimo = productos[-1]['id_producto']
            return ultimo
    
    return 'ME-0000'

def calcular_siguiente_id(ultimo_id):
    """Calcula el siguiente ID disponible"""
    numero = int(ultimo_id.split('-')[1])
    return f"ME-{numero + 1:04d}"

def generar_nombre_generico(nombre_mercadona):
    """Elimina marcas del nombre"""
    import re
    
    marcas = [
        'hacendado', 'deliplus', 'bosque verde', 'compy', 'granzoo', 'nuske',
        'nestlé', 'danone', 'president', 'pascual'
    ]
    
    nombre = nombre_mercadona
    for marca in marcas:
        patron = re.compile(rf'\b{re.escape(marca)}\b', re.IGNORECASE)
        nombre = patron.sub('', nombre)
    
    # Limpiar espacios
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    if len(nombre) < 3:
        nombre = nombre_mercadona
    
    return nombre

def escapar_sql(texto):
    """Escapa comillas simples para SQL"""
    return texto.replace("'", "''")

def generar_sql_añadir(productos):
    """Genera SQLs para añadir productos"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # SQL Mercadona
    sql_merc = []
    sql_merc.append("-- ============================================================================")
    sql_merc.append(f"-- AÑADIR PRODUCTOS A productos_mercadona")
    sql_merc.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_merc.append("-- ============================================================================")
    sql_merc.append("")
    sql_merc.append("BEGIN;")
    sql_merc.append("")
    
    for p in productos:
        id_p = p['id_producto']
        nombre = escapar_sql(p['nombre_mercadona'])
        precio = p['precio']
        cat = escapar_sql(p['categoria'])
        subcat = escapar_sql(p['subcategoria'])
        
        sql_merc.append(
            f"INSERT INTO productos_mercadona (id_producto, nombre, precio, categoria, subcategoria, imagen, url) "
            f"VALUES ('{id_p}', '{nombre}', '{precio}', '{cat}', '{subcat}', '', '');"
        )
    
    sql_merc.append("")
    sql_merc.append("COMMIT;")
    sql_merc.append("")
    sql_merc.append("SELECT COUNT(*) FROM productos_mercadona;")
    
    archivo_merc = os.path.join(OUTPUT_DIR, f'AÑADIR_MERCADONA_{timestamp}.sql')
    with open(archivo_merc, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_merc))
    
    # SQL Genéricos
    sql_gen = []
    sql_gen.append("-- ============================================================================")
    sql_gen.append(f"-- AÑADIR PRODUCTOS A productos_genericos")
    sql_gen.append(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_gen.append("-- ============================================================================")
    sql_gen.append("")
    sql_gen.append("BEGIN;")
    sql_gen.append("")
    
    for p in productos:
        id_p = p['id_producto']
        nombre = escapar_sql(p['nombre_generico'])
        cat = escapar_sql(p['categoria'])
        subcat = escapar_sql(p['subcategoria'])
        
        sql_gen.append(
            f"INSERT INTO productos_genericos (id_producto, nombre, categoria, subcategoria) "
            f"VALUES ('{id_p}', '{nombre}', '{cat}', '{subcat}');"
        )
    
    sql_gen.append("")
    sql_gen.append("COMMIT;")
    sql_gen.append("")
    sql_gen.append("SELECT COUNT(*) FROM productos_genericos;")
    
    archivo_gen = os.path.join(OUTPUT_DIR, f'AÑADIR_GENERICOS_{timestamp}.sql')
    with open(archivo_gen, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_gen))
    
    return archivo_merc, archivo_gen

# =============================================================================
# RUTAS WEB
# =============================================================================

@app.route('/')
def index():
    """Página principal"""
    categorias = cargar_categorias()
    ultimo_id = obtener_ultimo_id()
    siguiente_id = calcular_siguiente_id(ultimo_id)
    
    return render_template_string(HTML_TEMPLATE, 
                                 categorias=categorias, 
                                 siguiente_id=siguiente_id,
                                 ultimo_id=ultimo_id)

@app.route('/api/categorias', methods=['GET'])
def api_categorias():
    """API: Obtener categorías"""
    return jsonify(cargar_categorias())

@app.route('/api/siguiente_id', methods=['GET'])
def api_siguiente_id():
    """API: Obtener siguiente ID"""
    ultimo = obtener_ultimo_id()
    siguiente = calcular_siguiente_id(ultimo)
    return jsonify({'ultimo': ultimo, 'siguiente': siguiente})

@app.route('/api/generar_nombre_generico', methods=['POST'])
def api_generar_nombre():
    """API: Generar nombre genérico desde nombre con marca"""
    data = request.json
    nombre_mercadona = data.get('nombre', '')
    nombre_generico = generar_nombre_generico(nombre_mercadona)
    return jsonify({'nombre_generico': nombre_generico})

@app.route('/api/añadir_productos', methods=['POST'])
def api_añadir():
    """API: Añadir productos y generar SQLs"""
    data = request.json
    productos = data.get('productos', [])
    
    if not productos:
        return jsonify({'error': 'No hay productos'}), 400
    
    # Validar productos
    errores = []
    categorias_validas = cargar_categorias()
    
    for i, p in enumerate(productos):
        # Validar campos obligatorios
        if not p.get('id_producto'):
            errores.append(f"Producto {i+1}: Falta ID")
        if not p.get('nombre_mercadona'):
            errores.append(f"Producto {i+1}: Falta nombre Mercadona")
        if not p.get('precio'):
            errores.append(f"Producto {i+1}: Falta precio")
        if not p.get('categoria'):
            errores.append(f"Producto {i+1}: Falta categoría")
        if not p.get('subcategoria'):
            errores.append(f"Producto {i+1}: Falta subcategoría")
        
        # Validar categoría existe
        if p.get('categoria') not in categorias_validas:
            errores.append(f"Producto {i+1}: Categoría '{p.get('categoria')}' no existe")
        elif p.get('subcategoria') not in categorias_validas.get(p.get('categoria'), []):
            errores.append(f"Producto {i+1}: Subcategoría '{p.get('subcategoria')}' no existe")
        
        # Validar formato precio
        if p.get('precio') and not p['precio'].endswith('€'):
            errores.append(f"Producto {i+1}: Precio debe terminar en €")
    
    if errores:
        return jsonify({'error': 'Errores de validación', 'detalles': errores}), 400
    
    # Generar SQLs
    try:
        archivo_merc, archivo_gen = generar_sql_añadir(productos)
        
        return jsonify({
            'success': True,
            'mensaje': f'{len(productos)} producto(s) procesado(s)',
            'archivos': {
                'mercadona': os.path.basename(archivo_merc),
                'genericos': os.path.basename(archivo_gen)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/descargar/<filename>')
def descargar(filename):
    """Descargar archivo SQL generado"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Archivo no encontrado'}), 404

# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛒 Gestor de Productos - Mi Mejor Cesta</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f4f7f5 0%, #e8f5e9 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #037623 0%, #025a1a 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 32px;
            font-weight: 900;
            margin-bottom: 10px;
        }
        
        header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .info-bar {
            background: #f9f9f9;
            padding: 20px 30px;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .info-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .info-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            font-weight: 600;
        }
        
        .info-value {
            font-size: 16px;
            font-weight: 900;
            color: #037623;
        }
        
        .content {
            padding: 30px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .tab {
            padding: 12px 24px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 700;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #037623;
            border-bottom-color: #037623;
        }
        
        .tab:hover {
            color: #037623;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 700;
            color: #333;
            font-size: 14px;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: all 0.3s;
        }
        
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #037623;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            font-weight: 800;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #037623;
            color: white;
        }
        
        .btn-primary:hover {
            background: #025a1a;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(3, 118, 35, 0.3);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .btn-danger {
            background: #d32f2f;
            color: white;
        }
        
        .btn-danger:hover {
            background: #b71c1c;
        }
        
        .producto-item {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 15px;
            border: 2px solid #e0e0e0;
        }
        
        .producto-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .producto-number {
            font-size: 18px;
            font-weight: 900;
            color: #037623;
        }
        
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert.show {
            display: block;
        }
        
        .alert-success {
            background: #e8f5e9;
            border: 2px solid #4caf50;
            color: #2e7d32;
        }
        
        .alert-error {
            background: #ffebee;
            border: 2px solid #f44336;
            color: #c62828;
        }
        
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        
        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }
            
            .info-bar {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛒 Gestor de Productos</h1>
            <p>Mi Mejor Cesta - Administración de Base de Datos</p>
        </header>
        
        <div class="info-bar">
            <div class="info-item">
                <div>
                    <div class="info-label">Último ID</div>
                    <div class="info-value">{{ ultimo_id }}</div>
                </div>
            </div>
            <div class="info-item">
                <div>
                    <div class="info-label">Siguiente ID</div>
                    <div class="info-value" id="siguiente-id">{{ siguiente_id }}</div>
                </div>
            </div>
            <div class="info-item">
                <div>
                    <div class="info-label">Categorías</div>
                    <div class="info-value">{{ categorias|length }}</div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="tabs">
                <button class="tab active" onclick="cambiarTab('añadir')">➕ Añadir Productos</button>
                <button class="tab" onclick="cambiarTab('categorias')">📁 Ver Categorías</button>
                <button class="tab" onclick="cambiarTab('ayuda')">❓ Ayuda</button>
            </div>
            
            <div id="alert-container"></div>
            
            <!-- TAB AÑADIR PRODUCTOS -->
            <div id="tab-añadir" class="tab-content active">
                <h2 style="margin-bottom: 20px;">➕ Añadir Nuevos Productos</h2>
                
                <div id="productos-container">
                    <!-- Los productos se añaden dinámicamente -->
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button class="btn btn-secondary" onclick="añadirProducto()">+ Añadir otro producto</button>
                    <button class="btn btn-primary" onclick="generarSQLs()">✅ Generar SQLs</button>
                </div>
            </div>
            
            <!-- TAB CATEGORÍAS -->
            <div id="tab-categorias" class="tab-content">
                <h2 style="margin-bottom: 20px;">📁 Categorías Disponibles</h2>
                
                {% for categoria, subcategorias in categorias.items() %}
                <div style="margin-bottom: 25px;">
                    <h3 style="color: #037623; margin-bottom: 10px;">{{ categoria }}</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        {% for subcat in subcategorias %}
                        <span style="background: #f0f0f0; padding: 6px 12px; border-radius: 8px; font-size: 13px;">{{ subcat }}</span>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- TAB AYUDA -->
            <div id="tab-ayuda" class="tab-content">
                <h2 style="margin-bottom: 20px;">❓ Ayuda</h2>
                
                <h3>🎯 Cómo usar</h3>
                <ol style="line-height: 2;">
                    <li>Completa los datos del producto (nombre con marca, precio, categoría)</li>
                    <li>El nombre genérico se genera automáticamente (puedes editarlo)</li>
                    <li>Click en "Generar SQLs" para crear los archivos SQL</li>
                    <li>Descarga y ejecuta los SQLs en Supabase SQL Editor</li>
                </ol>
                
                <h3 style="margin-top: 30px;">⚠️ Reglas importantes</h3>
                <ul style="line-height: 2;">
                    <li><strong>Mismo ID:</strong> Ambas tablas usan el mismo id_producto</li>
                    <li><strong>Formato precio:</strong> Debe terminar en € (ej: 4.50€)</li>
                    <li><strong>Categoría válida:</strong> Debe existir en categorías disponibles</li>
                </ul>
                
                <h3 style="margin-top: 30px;">📝 Orden de ejecución en Supabase</h3>
                <ol style="line-height: 2;">
                    <li>Ejecutar AÑADIR_MERCADONA_XXXXXX.sql</li>
                    <li>Ejecutar AÑADIR_GENERICOS_XXXXXX.sql</li>
                </ol>
            </div>
        </div>
    </div>
    
    <script>
        let categorias = {{ categorias|tojson }};
        let contadorProductos = 0;
        
        function cambiarTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById('tab-' + tab).classList.add('active');
        }
        
        function añadirProducto() {
            contadorProductos++;
            
            fetch('/api/siguiente_id')
                .then(r => r.json())
                .then(data => {
                    const siguienteId = calcularIdPorNumero(contadorProductos);
                    
                    const html = `
                        <div class="producto-item" id="producto-${contadorProductos}">
                            <div class="producto-header">
                                <span class="producto-number">Producto #${contadorProductos}</span>
                                <button class="btn btn-danger" style="padding: 8px 16px;" onclick="eliminarProducto(${contadorProductos})">🗑️ Eliminar</button>
                            </div>
                            
                            <div class="form-group">
                                <label>ID Producto</label>
                                <input type="text" id="id-${contadorProductos}" value="${siguienteId}" readonly style="background: #f9f9f9;">
                            </div>
                            
                            <div class="grid-2">
                                <div class="form-group">
                                    <label>Nombre Mercadona (con marca)</label>
                                    <input type="text" id="nombre-merc-${contadorProductos}" placeholder="Ej: Leche desnatada Hacendado" onblur="generarNombreGenerico(${contadorProductos})">
                                </div>
                                
                                <div class="form-group">
                                    <label>Nombre Genérico (sin marca)</label>
                                    <input type="text" id="nombre-gen-${contadorProductos}" placeholder="Ej: Leche desnatada">
                                    <div class="help-text">Se genera automáticamente, pero puedes editarlo</div>
                                </div>
                            </div>
                            
                            <div class="grid-2">
                                <div class="form-group">
                                    <label>Precio</label>
                                    <input type="text" id="precio-${contadorProductos}" placeholder="Ej: 0.80€">
                                    <div class="help-text">Debe terminar en €</div>
                                </div>
                                
                                <div class="form-group">
                                    <label>Categoría</label>
                                    <select id="categoria-${contadorProductos}" onchange="actualizarSubcategorias(${contadorProductos})">
                                        <option value="">Selecciona categoría...</option>
                                        ${Object.keys(categorias).map(cat => `<option value="${cat}">${cat}</option>`).join('')}
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label>Subcategoría</label>
                                <select id="subcategoria-${contadorProductos}" disabled>
                                    <option value="">Primero selecciona una categoría...</option>
                                </select>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('productos-container').insertAdjacentHTML('beforeend', html);
                });
        }
        
        function calcularIdPorNumero(numero) {
            fetch('/api/siguiente_id')
                .then(r => r.json())
                .then(data => {
                    const baseNum = parseInt(data.siguiente.split('-')[1]);
                    return `ME-${String(baseNum + numero - 1).padStart(4, '0')}`;
                });
            
            // Temporal mientras carga
            return `ME-${String(3899 + numero - 1).padStart(4, '0')}`;
        }
        
        function eliminarProducto(id) {
            document.getElementById('producto-' + id).remove();
        }
        
        function generarNombreGenerico(id) {
            const nombreMerc = document.getElementById('nombre-merc-' + id).value;
            
            if (!nombreMerc) return;
            
            fetch('/api/generar_nombre_generico', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({nombre: nombreMerc})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('nombre-gen-' + id).value = data.nombre_generico;
            });
        }
        
        function actualizarSubcategorias(id) {
            const categoria = document.getElementById('categoria-' + id).value;
            const selectSubcat = document.getElementById('subcategoria-' + id);
            
            selectSubcat.innerHTML = '<option value="">Selecciona subcategoría...</option>';
            
            if (categoria && categorias[categoria]) {
                selectSubcat.disabled = false;
                categorias[categoria].forEach(subcat => {
                    selectSubcat.innerHTML += `<option value="${subcat}">${subcat}</option>`;
                });
            } else {
                selectSubcat.disabled = true;
            }
        }
        
        function mostrarAlerta(tipo, mensaje) {
            const html = `
                <div class="alert alert-${tipo} show">
                    ${mensaje}
                </div>
            `;
            document.getElementById('alert-container').innerHTML = html;
            
            setTimeout(() => {
                document.querySelector('.alert').classList.remove('show');
            }, 5000);
        }
        
        function generarSQLs() {
            const productos = [];
            
            // Recopilar datos de todos los productos
            document.querySelectorAll('.producto-item').forEach((item, index) => {
                const id = item.id.split('-')[1];
                
                const producto = {
                    id_producto: document.getElementById('id-' + id).value,
                    nombre_mercadona: document.getElementById('nombre-merc-' + id).value,
                    nombre_generico: document.getElementById('nombre-gen-' + id).value,
                    precio: document.getElementById('precio-' + id).value,
                    categoria: document.getElementById('categoria-' + id).value,
                    subcategoria: document.getElementById('subcategoria-' + id).value
                };
                
                productos.push(producto);
            });
            
            if (productos.length === 0) {
                mostrarAlerta('error', '⚠️ No hay productos para procesar. Añade al menos uno.');
                return;
            }
            
            // Enviar a API
            fetch('/api/añadir_productos', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({productos})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    let detalles = '';
                    if (data.detalles) {
                        detalles = '<br><br><strong>Detalles:</strong><br>' + data.detalles.join('<br>');
                    }
                    mostrarAlerta('error', '❌ ' + data.error + detalles);
                } else {
                    mostrarAlerta('success', `
                        ✅ ${data.mensaje}<br><br>
                        <strong>SQLs generados:</strong><br>
                        <a href="/api/descargar/${data.archivos.mercadona}" style="color: #037623; text-decoration: underline;">📥 Descargar SQL Mercadona</a><br>
                        <a href="/api/descargar/${data.archivos.genericos}" style="color: #037623; text-decoration: underline;">📥 Descargar SQL Genéricos</a>
                    `);
                    
                    // Limpiar formulario
                    document.getElementById('productos-container').innerHTML = '';
                    contadorProductos = 0;
                    añadirProducto();
                }
            })
            .catch(err => {
                mostrarAlerta('error', '❌ Error: ' + err.message);
            });
        }
        
        // Inicializar con un producto
        añadirProducto();
    </script>
</body>
</html>
'''

# =============================================================================
# EJECUTAR APP
# =============================================================================

if __name__ == '__main__':
    print("="*80)
    print("🛒 MI MEJOR CESTA - GESTOR DE PRODUCTOS")
    print("="*80)
    print("\n✅ Servidor iniciando...")
    print("\n📍 Abre en tu navegador: http://localhost:5000")
    print("\n⚠️  Presiona CTRL+C para detener")
    print("="*80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
