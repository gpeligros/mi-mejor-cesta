import React from 'react';

// Limpia el nombre quitando la parte redundante del slug
const limpiarNombre = (nombre) => {
  const match = nombre.match(/^(.+?)\s*\((.+)\)\s*$/);
  if (!match) return nombre;

  const base = match[1].trim();
  const slug = match[2].trim();

  const normalizar = (s) => s.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, '');

  const baseWords = normalizar(base).split(/\s+/).filter(w => w.length > 2);

  const diferenciador = slug.split(/\s+/)
    .filter(w => {
      const wn = normalizar(w);
      return wn.length > 0 && !baseWords.some(bw => wn === bw || bw.startsWith(wn) || wn.startsWith(bw));
    })
    .join(' ')
    .trim();

  if (!diferenciador) return base;
  return base + ' · ' + diferenciador;
};

const Sidebar = ({ 
  stats, cestasGuardadas, setCestasGuardadas, 
  seleccionados, setSeleccionados, setComprados, 
  escaneando, fileInputRef, handleFoto, 
  busqueda, setBusqueda, db, acordeon, setAcordeon, 
  toggleProd, vaciarCesta, exportarPDF, onCompartir,
  onVerHistorial, session,
  plan, onUpgrade,
}) => {

  const [subcatAbierta, setSubcatAbierta] = React.useState(null);
  const [mostrarMarcaBlanca, setMostrarMarcaBlanca] = React.useState(false);

  const categoriasOrdenadas = Object.keys(db).sort();

  return (
    <aside className="no-print" style={{ width: '100%', boxSizing: 'border-box' }}>
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
        <button onClick={exportarPDF} style={{ background: '#102215', color: 'white', border: 'none', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}>
          📄 EXPORTAR PDF
        </button>
        <button onClick={onCompartir} style={{ background: '#e8fdf0', color: '#037623', border: '1px solid #037623', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}>
          👥 LISTA COLABORATIVA
        </button>
        {session && (
          <button onClick={onVerHistorial} style={{ background: '#e8fdf0', color: '#037623', border: '1px solid #037623', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}>
            🧾 MIS COMPRAS
          </button>
        )}
        <button 
          onClick={() => { const n = window.prompt("Nombre de la lista favorita:"); if(n) setCestasGuardadas(prev => ({...prev, [n]: seleccionados})); }} 
          style={{ background: '#e8fdf0', color: '#037623', border: '1px solid #037623', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}
        >
          ⭐ GUARDAR FAVORITA
        </button>
        {seleccionados.length > 0 && (
          <button onClick={() => { if(window.confirm("¿Vaciar cesta?")){ vaciarCesta(); } }} style={{ color: '#ff4b4b', background: 'none', border: 'none', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}>
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
              <button onClick={() => setSeleccionados(cestasGuardadas[nombre])} style={{ flex: 1, textAlign: 'left', padding: '8px', borderRadius: '8px', border: '1px solid #f0f0f0', background: '#fafafa', fontSize: '11px', fontWeight: '700', cursor: 'pointer' }}>
                🛒 {nombre}
              </button>
              <button onClick={() => { const nvas = {...cestasGuardadas}; delete nvas[nombre]; setCestasGuardadas(nvas); }} style={{ padding: '8px', color: '#d32f2f', border:'none', background:'none', cursor:'pointer', fontSize: '14px' }}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* HISTORIAL DE COMPRAS */}
      {session && (
        <div style={{ marginBottom: '20px', background: 'white', borderRadius: '15px', border: '1px solid #eee', overflow: 'hidden' }}>
          <div
            onClick={toggleHistorial}
            style={{ padding: '14px 15px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
          >
            <span style={{ fontWeight: '800', fontSize: '12px' }}>🧾 MIS COMPRAS</span>
            <span style={{ color: '#037623', fontWeight: '900' }}>{historialAbierto ? '−' : '+'}</span>
          </div>

          {historialAbierto && (
            <div style={{ borderTop: '1px solid #f0f0f0', padding: '10px' }}>
              {cargandoHistorial ? (
                <div style={{ textAlign: 'center', padding: '15px', fontSize: '12px', color: '#999' }}>Cargando...</div>
              ) : historial.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '15px', fontSize: '12px', color: '#999' }}>
                  Aún no tienes compras guardadas.<br/>
                  <span style={{ fontSize: '11px' }}>Usa "Finalizar compra" en el modo tienda.</span>
                </div>
              ) : (
                historial.map(c => (
                  <div key={c.id} style={{ padding: '10px 5px', borderBottom: '1px solid #f8f8f8', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '12px' }}>{c.supermercado}</div>
                      <div style={{ fontSize: '10px', color: '#999' }}>
                        {new Date(c.fecha).toLocaleDateString('es-ES')} · {c.num_productos} productos
                      </div>
                    </div>
                    <div style={{ fontWeight: '900', fontSize: '14px', color: '#037623' }}>
                      {parseFloat(c.total).toFixed(2)}€
                    </div>
                  </div>
                ))
              )}
              {historial.length > 0 && (
                <div style={{ padding: '8px 5px 0', textAlign: 'right' }}>
                  <span style={{ fontSize: '10px', color: '#bbb' }}>Últimas {historial.length} compras</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ESCÁNER */}
      <div style={{ background: 'linear-gradient(135deg, #102215 0%, #037623 100%)', color: 'white', padding: '20px', borderRadius: '20px', marginBottom: '20px' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', fontWeight: '900' }}>📸 ESCANEAR LISTA</h4>
        <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFoto} style={{ display: 'none' }} />
        <button onClick={() => fileInputRef?.current?.click()} disabled={escaneando} style={{ width: '100%', background: escaneando ? '#999' : '#13ec49', color: '#102215', border: 'none', padding: '10px', borderRadius: '10px', fontWeight: '900', cursor: escaneando ? 'not-allowed' : 'pointer' }}>
          {escaneando ? "PROCESANDO..." : "SUBIR FOTO"}
        </button>
      </div>

      {/* BUSCADOR Y LISTADO */}
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '25px', border: '1px solid #e0e6e1' }}>
        <input
          type="text"
          placeholder="🔍 Buscar productos..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #ddd', marginBottom: '10px', boxSizing: 'border-box' }}
        />

        {/* Toggle marca blanca — usa campo tipo de la BBDD */}
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', color: '#666', marginBottom: '15px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={mostrarMarcaBlanca}
            onChange={() => setMostrarMarcaBlanca(v => !v)}
          />
          Mostrar marca blanca (Hacendado, etc.)
        </label>

        <div style={{ maxHeight: '800px', overflowY: 'auto' }}>
          {categoriasOrdenadas.map(categoria => {
            const subcategoriasFiltradas = Object.keys(db[categoria] || {}).filter(subcategoria => {
              return db[categoria][subcategoria].some(producto => {
                // Filtro marca blanca usando campo tipo de la BBDD
                if (!mostrarMarcaBlanca && producto.tipo === 'marca_blanca') return false;
                const nombreLimpio = limpiarNombre(producto.nombre);
                return nombreLimpio.toLowerCase().includes(busqueda.toLowerCase());
              });
            });
            if (subcategoriasFiltradas.length === 0) return null;

            return (
              <div key={`cat-${categoria}`} style={{ marginBottom: '10px' }}>
                <div
                  onClick={() => setAcordeon(acordeon === categoria ? null : categoria)}
                  style={{ cursor: 'pointer', fontWeight: '900', fontSize: '13px', padding: '8px 0', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}
                >
                  {categoria.toUpperCase()} <span>{(acordeon === categoria || busqueda) ? '−' : '+'}</span>
                </div>

                {(acordeon === categoria || busqueda) && subcategoriasFiltradas.sort().map(subcategoria => {
                  const subcatKey = `${categoria}__${subcategoria}`;
                  const subcatVisible = busqueda || subcatAbierta === subcatKey;
                  const productosFiltrados = db[categoria][subcategoria]
                    .filter(producto => {
                      if (!mostrarMarcaBlanca && producto.tipo === 'marca_blanca') return false;
                      const nombreLimpio = limpiarNombre(producto.nombre);
                      return nombreLimpio.toLowerCase().includes(busqueda.toLowerCase());
                    })
                    .sort((a, b) => limpiarNombre(a.nombre).localeCompare(limpiarNombre(b.nombre)));

                  return (
                    <div key={`sub-${categoria}-${subcategoria}`} style={{ paddingLeft: '15px', marginTop: '5px' }}>
                      <div
                        onClick={() => !busqueda && setSubcatAbierta(subcatAbierta === subcatKey ? null : subcatKey)}
                        style={{ fontSize: '10px', color: '#037623', fontWeight: '900', marginBottom: '5px', cursor: busqueda ? 'default' : 'pointer', display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}
                      >
                        <span>{subcategoria.toUpperCase()}</span>
                        {!busqueda && <span style={{ color: '#999' }}>{subcatVisible ? '−' : '+'}</span>}
                      </div>

                      {subcatVisible && productosFiltrados.map(producto => {
                        const productoId = producto.id_producto;
                        if (!productoId) return null;
                        const nombreMostrado = limpiarNombre(producto.nombre);
                        return (
                          <label key={`prod-${productoId}`} htmlFor={`checkbox-${productoId}`} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '5px 0', fontSize: '13px', cursor: 'pointer' }}>
                            <input type="checkbox" id={`checkbox-${productoId}`} checked={seleccionados.includes(productoId)} onChange={() => toggleProd(productoId)} style={{ cursor: 'pointer' }} />
                            <span>{nombreMostrado}</span>
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
