import React from 'react';

const Sidebar = ({ 
  stats, 
  cestasGuardadas, 
  setCestasGuardadas, 
  seleccionados, 
  setSeleccionados, 
  setComprados, 
  escaneando, 
  fileInputRef, 
  handleFoto, 
  busqueda, 
  setBusqueda, 
  db, 
  acordeon, 
  setAcordeon, 
  toggleProd, 
  vaciarCesta
}) => {

  const categoriasOrdenadas = Object.keys(db).sort();

  return (
    <aside className="no-print" style={{ width: '340px' }}>
      {/* PANEL AHORRO */}
      <div style={{ background: '#037623', color: 'white', padding: '25px', borderRadius: '25px', marginBottom: '15px' }}>
        <h3 style={{ margin: '0', fontSize: '11px', fontWeight: '900', color: '#13ec49' }}>ESTÁS AHORRANDO</h3>
        <div style={{ fontSize: '42px', fontWeight: '900' }}>{stats.ahorro.toFixed(2)}€</div>
        <p style={{ fontSize: '11px', marginTop: '5px', opacity: 0.9 }}>Diferencia entre el súper más barato y el más caro.</p>
      </div>

      {/* MI MEJOR CESTA */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '20px', border: '2px solid #037623', marginBottom: '15px' }}>
        <h3 style={{ fontSize: '12px', marginBottom: '5px', fontWeight: '900' }}>💡 MI MEJOR CESTA: {stats.multi.toFixed(2)}€</h3>
        <p style={{ fontSize: '11px', color: '#666' }}>Precio mínimo comprando cada cosa en su sitio más barato.</p>
      </div>

      {/* BOTONES ACCIÓN */}
      <div style={{ marginBottom: '20px', display: 'grid', gap: '8px' }}>
        <button 
          onClick={() => window.print()} 
          style={{ background: '#102215', color: 'white', border: 'none', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}
        >
          📄 EXPORTAR PDF
        </button>
        
        <button 
          onClick={() => {
            const n = window.prompt("Nombre de la lista favorita:");
            if(n) setCestasGuardadas(prev => ({...prev, [n]: seleccionados}));
          }} 
          style={{ background: '#e8fdf0', color: '#037623', border: '1px solid #037623', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}
        >
          ⭐ GUARDAR FAVORITA
        </button>

        {seleccionados.length > 0 && (
          <button 
            onClick={() => { 
              if(window.confirm("¿Vaciar cesta?")){ 
                vaciarCesta(); 
              } 
            }} 
            style={{ color: '#ff4b4b', background: 'none', border: 'none', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}
          >
            🗑️ VACIAR CESTA
          </button>
        )}
      </div>

      {/* LISTAS GUARDADAS */}
      {Object.keys(cestasGuardadas).length > 0 && (
        <div style={{ marginBottom: '20px', padding: '15px', background: '#fff', borderRadius: '15px', border: '1px solid #eee' }}>
          <h4 style={{ fontSize: '10px', fontWeight: '900', color: '#bbb', marginBottom: '10px' }}>MIS FAVORITOS:</h4>
          {Object.keys(cestasGuardadas).map(nombre => (
            <div key={`cesta-${nombre}`} style={{ display: 'flex', gap: '5px', marginBottom: '5px' }}>
              <button 
                onClick={() => setSeleccionados(cestasGuardadas[nombre])} 
                style={{ flex: 1, textAlign: 'left', padding: '8px', borderRadius: '8px', border: '1px solid #f0f0f0', background: '#fafafa', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}
              >
                🛒 {nombre}
              </button>
              <button 
                onClick={() => { 
                  const nvas = {...cestasGuardadas}; 
                  delete nvas[nombre]; 
                  setCestasGuardadas(nvas); 
                }} 
                style={{ padding: '8px', color: '#d32f2f', border:'none', background:'none', cursor:'pointer', fontSize: '14px' }}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ESCÁNER */}
      <div style={{ background: 'linear-gradient(135deg, #102215 0%, #037623 100%)', color: 'white', padding: '20px', borderRadius: '20px', marginBottom: '20px' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', fontWeight: '900' }}>📸 ESCANEAR LISTA</h4>
        <input 
          type="file" 
          accept="image/*" 
          ref={fileInputRef} 
          onChange={handleFoto} 
          style={{ display: 'none' }} 
        />
        <button 
          onClick={() => fileInputRef?.current?.click()} 
          disabled={escaneando} 
          style={{ 
            width: '100%', 
            background: escaneando ? '#999' : '#13ec49', 
            color: '#102215', 
            border: 'none', 
            padding: '10px', 
            borderRadius: '10px', 
            fontWeight: '900', 
            cursor: escaneando ? 'not-allowed' : 'pointer' 
          }}
        >
          {escaneando ? "PROCESANDO..." : "SUBIR FOTO"}
        </button>
      </div>

      {/* BUSCADOR Y LISTADO DE PRODUCTOS */}
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '25px', border: '1px solid #e0e6e1' }}>
        <input 
          type="text" 
          placeholder="🔍 Buscar productos..." 
          value={busqueda} 
          onChange={(e) => setBusqueda(e.target.value)} 
          style={{ 
            width: '100%', 
            padding: '12px', 
            borderRadius: '12px', 
            border: '1px solid #ddd', 
            marginBottom: '15px', 
            boxSizing: 'border-box' 
          }} 
        />
        
        <div style={{ maxHeight: '800px', overflowY: 'auto' }}>
          {categoriasOrdenadas.map(categoria => {
            const subcategoriasFiltradas = Object.keys(db[categoria] || {}).filter(subcategoria => {
              return db[categoria][subcategoria].some(producto => 
                producto.nombre.toLowerCase().includes(busqueda.toLowerCase())
              );
            });
            
            if (subcategoriasFiltradas.length === 0) return null;

            return (
              <div key={`cat-${categoria}`} style={{ marginBottom: '10px' }}>
                <div 
                  onClick={() => setAcordeon(acordeon === categoria ? null : categoria)} 
                  style={{ 
                    cursor: 'pointer', 
                    fontWeight: '900', 
                    fontSize: '13px', 
                    padding: '8px 0', 
                    borderBottom: '1px solid #eee', 
                    display: 'flex', 
                    justifyContent: 'space-between' 
                  }}
                >
                  {categoria.toUpperCase()} 
                  <span>{(acordeon === categoria || busqueda) ? '−' : '+'}</span>
                </div>
                
                {(acordeon === categoria || busqueda) && subcategoriasFiltradas.sort().map(subcategoria => {
                  const productosFiltrados = db[categoria][subcategoria]
                    .filter(producto => producto.nombre.toLowerCase().includes(busqueda.toLowerCase()))
                    .sort((a, b) => a.nombre.localeCompare(b.nombre));
                  
                  return (
                    <div key={`sub-${categoria}-${subcategoria}`} style={{ paddingLeft: '15px', marginTop: '8px' }}>
                      <div style={{ fontSize: '10px', color: '#037623', fontWeight: '900', marginBottom: '5px' }}>
                        {subcategoria.toUpperCase()}
                      </div>
                      
                      {productosFiltrados.map(producto => {
                        // ✅ CORRECCIÓN: Usar id_producto
                        const productoId = producto.id_producto;
                        
                        if (!productoId) {
                          console.warn('⚠️ Producto sin id_producto:', producto);
                          return null;
                        }
                        
                        return (
                          <label 
                            key={`prod-${productoId}`}
                            htmlFor={`checkbox-${productoId}`}
                            style={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: '8px', 
                              padding: '5px 0', 
                              fontSize: '13px', 
                              cursor: 'pointer' 
                            }}
                          >
                            <input 
                              type="checkbox"
                              id={`checkbox-${productoId}`}
                              checked={seleccionados.includes(productoId)} 
                              onChange={() => toggleProd(productoId)}
                              style={{ cursor: 'pointer' }}
                            />
                            <span>{producto.nombre}</span>
                          </label>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;