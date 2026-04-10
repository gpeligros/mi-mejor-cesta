import React from 'react';
import { supabase } from '../supabaseClient';

const VERDE = '#037623';
const OSCURO = '#102215';

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

// ── Componente de barra de progreso ──────────────────────────────
const BarraProgreso = ({ valor, maximo, color = VERDE, label, cantidad }) => {
  const pct = maximo > 0 ? Math.round((valor / maximo) * 100) : 0;
  return (
    <div style={{ marginBottom: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px' }}>
        <span style={{ fontWeight: '700', color: OSCURO }}>{label}</span>
        <span style={{ fontWeight: '900', color: VERDE }}>{cantidad}</span>
      </div>
      <div style={{ background: '#f0f0f0', borderRadius: '6px', height: '6px', overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: '6px', transition: 'width 0.5s ease' }} />
      </div>
    </div>
  );
};

const Sidebar = ({ 
  stats, cestasGuardadas, setCestasGuardadas, 
  seleccionados, setSeleccionados, setComprados, 
  escaneando, fileInputRef, handleFoto, 
  busqueda, setBusqueda, db, acordeon, setAcordeon, 
  toggleProd, vaciarCesta, exportarPDF, onCompartir,
  plan, onUpgrade, session, onAdmin,
}) => {

  const [esAdmin, setEsAdmin] = React.useState(false);

  React.useEffect(() => {
    if (!session) { setEsAdmin(false); return; }
    supabase.from('profiles').select('rol').eq('id', session.user.id).single()
      .then(({ data }) => setEsAdmin(data?.rol === 'admin'));
  }, [session]);

  const [subcatAbierta, setSubcatAbierta] = React.useState(null);
  const [historial, setHistorial] = React.useState([]);
  const [historialAbierto, setHistorialAbierto] = React.useState(false);
  const [cargandoHistorial, setCargandoHistorial] = React.useState(false);

  // ── Estados estadísticas ──────────────────────────────────────
  const [estadisticas, setEstadisticas] = React.useState(null);
  const [estadisticasAbiertas, setEstadisticasAbiertas] = React.useState(false);
  const [cargandoStats, setCargandoStats] = React.useState(false);

  const cargarHistorial = async () => {
    if (!session) return;
    setCargandoHistorial(true);
    const { data } = await supabase
      .from('compras')
      .select('id, supermercado, total, num_productos, fecha')
      .eq('user_id', session.user.id)
      .order('fecha', { ascending: false })
      .limit(20);
    setHistorial(data || []);
    setCargandoHistorial(false);
  };

  const toggleHistorial = () => {
    const nuevoEstado = !historialAbierto;
    setHistorialAbierto(nuevoEstado);
    if (nuevoEstado) {
      setHistorial([]);
      cargarHistorial();
    }
  };

  // ── Cargar estadísticas ───────────────────────────────────────
  const cargarEstadisticas = async () => {
    if (!session) return;
    setCargandoStats(true);

    // Cargar compras del usuario
    const { data: compras } = await supabase
      .from('compras')
      .select('id, supermercado, total, num_productos, fecha')
      .eq('user_id', session.user.id)
      .order('fecha', { ascending: false });

    if (!compras || compras.length === 0) {
      setEstadisticas({ vacio: true });
      setCargandoStats(false);
      return;
    }

    // Cargar detalle de todas las compras
    const idsCompras = compras.map(c => c.id);
    const { data: detalle } = await supabase
      .from('compras_detalle')
      .select('compra_id, nombre_producto, precio, supermercado')
      .in('compra_id', idsCompras);

    // ── Calcular métricas ─────────────────────────────────────
    const totalGastado = compras.reduce((acc, c) => acc + parseFloat(c.total || 0), 0);
    const numCompras = compras.length;
    const ticketMedio = numCompras > 0 ? totalGastado / numCompras : 0;

    // Gasto por supermercado
    const porSuper = {};
    compras.forEach(c => {
      if (!porSuper[c.supermercado]) porSuper[c.supermercado] = 0;
      porSuper[c.supermercado] += parseFloat(c.total || 0);
    });
    const maxSuper = Math.max(...Object.values(porSuper));

    // Productos más comprados
    const frecuencia = {};
    (detalle || []).forEach(d => {
      const key = d.nombre_producto;
      if (!frecuencia[key]) frecuencia[key] = { nombre: d.nombre_producto, veces: 0, gasto: 0 };
      frecuencia[key].veces += 1;
      frecuencia[key].gasto += parseFloat(d.precio || 0);
    });
    const topProductos = Object.values(frecuencia)
      .sort((a, b) => b.veces - a.veces)
      .slice(0, 5);
    const maxVeces = topProductos[0]?.veces || 1;

    // Gasto último mes vs anterior
    const ahora = new Date();
    const inicioMesActual = new Date(ahora.getFullYear(), ahora.getMonth(), 1);
    const inicioMesAnterior = new Date(ahora.getFullYear(), ahora.getMonth() - 1, 1);

    const gastoMesActual = compras
      .filter(c => new Date(c.fecha) >= inicioMesActual)
      .reduce((acc, c) => acc + parseFloat(c.total || 0), 0);

    const gastoMesAnterior = compras
      .filter(c => new Date(c.fecha) >= inicioMesAnterior && new Date(c.fecha) < inicioMesActual)
      .reduce((acc, c) => acc + parseFloat(c.total || 0), 0);

    const tendencia = gastoMesAnterior > 0
      ? ((gastoMesActual - gastoMesAnterior) / gastoMesAnterior) * 100
      : null;

    setEstadisticas({
      totalGastado,
      numCompras,
      ticketMedio,
      porSuper,
      maxSuper,
      topProductos,
      maxVeces,
      gastoMesActual,
      gastoMesAnterior,
      tendencia,
    });
    setCargandoStats(false);
  };

  const toggleEstadisticas = () => {
    const esPlanBasic = plan === 'basic' || plan === 'premium';
    if (!esPlanBasic) {
      onUpgrade('estadisticas', 'basic');
      return;
    }
    const nuevoEstado = !estadisticasAbiertas;
    setEstadisticasAbiertas(nuevoEstado);
    if (nuevoEstado && !estadisticas) cargarEstadisticas();
  };

  React.useEffect(() => {
    if (session) cargarHistorial();
  }, [session]); // eslint-disable-line react-hooks/exhaustive-deps

  const categoriasOrdenadas = Object.keys(db).sort();
  const esPlanBasic = plan === 'basic' || plan === 'premium';

  return (
    <aside className="no-print" style={{ width: '100%', boxSizing: 'border-box' }}>
      {/* PANEL AHORRO */}
      <div style={{ background: VERDE, color: 'white', padding: '25px', borderRadius: '25px', marginBottom: '15px' }}>
        <h3 style={{ margin: '0', fontSize: '11px', fontWeight: '900', color: '#13ec49' }}>ESTÁS AHORRANDO</h3>
        <div style={{ fontSize: '42px', fontWeight: '900' }}>{stats.ahorro.toFixed(2)}€</div>
        <p style={{ fontSize: '11px', marginTop: '5px', opacity: 0.9 }}>Diferencia entre el súper más barato y el más caro.</p>
      </div>

      {/* MI MEJOR CESTA */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '20px', border: `2px solid ${VERDE}`, marginBottom: '15px' }}>
        <h3 style={{ fontSize: '12px', marginBottom: '5px', fontWeight: '900' }}>💡 MI MEJOR CESTA: {stats.multi.toFixed(2)}€</h3>
        <p style={{ fontSize: '11px', color: '#666' }}>Precio mínimo comprando cada cosa en su sitio más barato.</p>
      </div>

      {/* BOTONES ACCIÓN */}
      <div style={{ marginBottom: '20px', display: 'grid', gap: '8px' }}>
        <button onClick={exportarPDF} style={{ background: OSCURO, color: 'white', border: 'none', padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}>
          📄 EXPORTAR PDF
        </button>
        <button onClick={onCompartir} style={{ background: '#e8fdf0', color: VERDE, border: `1px solid ${VERDE}`, padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}>
          👥 LISTA COLABORATIVA
        </button>
        <button 
          onClick={() => { const n = window.prompt("Nombre de la lista favorita:"); if(n) setCestasGuardadas(prev => ({...prev, [n]: seleccionados})); }} 
          style={{ background: '#e8fdf0', color: VERDE, border: `1px solid ${VERDE}`, padding: '12px', borderRadius: '12px', fontWeight: '800', cursor: 'pointer', fontSize: '12px' }}
        >
          ⭐ GUARDAR FAVORITA
        </button>
        {seleccionados.length > 0 && (
          <button onClick={() => { if(window.confirm("¿Vaciar cesta?")){ vaciarCesta(); } }} style={{ color: '#ff4b4b', background: 'none', border: 'none', fontSize: '12px', fontWeight: '800', cursor: 'pointer' }}>
            🗑️ VACIAR CESTA
          </button>
        )}
        {esAdmin && (
          <button onClick={onAdmin} style={{ color: '#6200ea', background: 'none', border: 'none', fontSize: '12px', fontWeight: '800', cursor: 'pointer', marginTop: '4px' }}>
            ⚙️ PANEL ADMIN
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
      <div style={{ marginBottom: '20px', background: 'white', borderRadius: '15px', border: '1px solid #eee', overflow: 'hidden' }}>
        <div
          onClick={toggleHistorial}
          style={{ padding: '14px 15px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <span style={{ fontWeight: '800', fontSize: '12px' }}>🧾 MIS COMPRAS</span>
          <span style={{ color: VERDE, fontWeight: '900' }}>{historialAbierto ? '−' : '+'}</span>
        </div>
        {historialAbierto && (
          <div style={{ borderTop: '1px solid #f0f0f0', padding: '10px' }}>
            {!session ? (
              <div style={{ textAlign: 'center', padding: '15px', fontSize: '12px', color: '#999' }}>
                Inicia sesión para ver tus compras.
              </div>
            ) : cargandoHistorial ? (
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
                  <div style={{ fontWeight: '900', fontSize: '14px', color: VERDE }}>
                    {parseFloat(c.total).toFixed(2)}€
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* ── ESTADÍSTICAS DE GASTO ─────────────────────────────── */}
      <div style={{ marginBottom: '20px', background: 'white', borderRadius: '15px', border: '1px solid #eee', overflow: 'hidden' }}>
        <div
          onClick={toggleEstadisticas}
          style={{ padding: '14px 15px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <span style={{ fontWeight: '800', fontSize: '12px' }}>
            📊 MIS ESTADÍSTICAS
            {!esPlanBasic && <span style={{ marginLeft: '6px', fontSize: '9px', background: '#f0fdf4', color: VERDE, border: `1px solid ${VERDE}`, borderRadius: '4px', padding: '1px 5px', fontWeight: '900' }}>BÁSICO</span>}
          </span>
          <span style={{ color: VERDE, fontWeight: '900' }}>{estadisticasAbiertas ? '−' : '+'}</span>
        </div>

        {estadisticasAbiertas && (
          <div style={{ borderTop: '1px solid #f0f0f0', padding: '14px' }}>
            {!session ? (
              <div style={{ textAlign: 'center', padding: '15px', fontSize: '12px', color: '#999' }}>
                Inicia sesión para ver tus estadísticas.
              </div>
            ) : cargandoStats ? (
              <div style={{ textAlign: 'center', padding: '15px', fontSize: '12px', color: '#999' }}>Calculando...</div>
            ) : !estadisticas || estadisticas.vacio ? (
              <div style={{ textAlign: 'center', padding: '15px', fontSize: '12px', color: '#999' }}>
                Aún no tienes compras registradas.<br/>
                <span style={{ fontSize: '11px' }}>Finaliza una compra para ver tus estadísticas.</span>
              </div>
            ) : (
              <>
                {/* Métricas principales */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', marginBottom: '16px' }}>
                  {[
                    { label: 'Total gastado', valor: `${estadisticas.totalGastado.toFixed(2)}€` },
                    { label: 'Compras', valor: estadisticas.numCompras },
                    { label: 'Ticket medio', valor: `${estadisticas.ticketMedio.toFixed(2)}€` },
                  ].map(({ label, valor }) => (
                    <div key={label} style={{ background: '#f8faf9', borderRadius: '10px', padding: '10px 8px', textAlign: 'center' }}>
                      <div style={{ fontSize: '14px', fontWeight: '900', color: VERDE }}>{valor}</div>
                      <div style={{ fontSize: '9px', color: '#999', fontWeight: '700', marginTop: '2px' }}>{label.toUpperCase()}</div>
                    </div>
                  ))}
                </div>

                {/* Tendencia mes actual vs anterior */}
                {estadisticas.tendencia !== null && (
                  <div style={{ background: estadisticas.tendencia > 0 ? '#fff0f0' : '#f0fdf4', borderRadius: '10px', padding: '10px 12px', marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '10px', fontWeight: '900', color: '#999' }}>ESTE MES</div>
                      <div style={{ fontSize: '15px', fontWeight: '900', color: OSCURO }}>{estadisticas.gastoMesActual.toFixed(2)}€</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '10px', fontWeight: '900', color: '#999' }}>VS MES ANTERIOR</div>
                      <div style={{ fontSize: '13px', fontWeight: '900', color: estadisticas.tendencia > 0 ? '#d32f2f' : VERDE }}>
                        {estadisticas.tendencia > 0 ? '▲' : '▼'} {Math.abs(estadisticas.tendencia).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}

                {/* Gasto por supermercado */}
                {Object.keys(estadisticas.porSuper).length > 0 && (
                  <div style={{ marginBottom: '14px' }}>
                    <div style={{ fontSize: '10px', fontWeight: '900', color: '#999', marginBottom: '8px' }}>GASTO POR SUPERMERCADO</div>
                    {Object.entries(estadisticas.porSuper)
                      .sort((a, b) => b[1] - a[1])
                      .map(([super_, gasto]) => (
                        <BarraProgreso
                          key={super_}
                          valor={gasto}
                          maximo={estadisticas.maxSuper}
                          label={super_}
                          cantidad={`${gasto.toFixed(2)}€`}
                        />
                      ))
                    }
                  </div>
                )}

                {/* Top productos */}
                {estadisticas.topProductos.length > 0 && (
                  <div>
                    <div style={{ fontSize: '10px', fontWeight: '900', color: '#999', marginBottom: '8px' }}>PRODUCTOS MÁS COMPRADOS</div>
                    {estadisticas.topProductos.map((p, i) => (
                      <BarraProgreso
                        key={p.nombre}
                        valor={p.veces}
                        maximo={estadisticas.maxVeces}
                        label={p.nombre.length > 28 ? p.nombre.slice(0, 28) + '…' : p.nombre}
                        cantidad={`${p.veces}x · ${p.gasto.toFixed(2)}€`}
                        color={i === 0 ? VERDE : `hsl(${140 - i * 20}, 60%, 40%)`}
                      />
                    ))}
                  </div>
                )}

                <button
                  onClick={() => { setEstadisticas(null); cargarEstadisticas(); }}
                  style={{ marginTop: '10px', width: '100%', background: 'none', border: `1px solid #eee`, borderRadius: '8px', padding: '6px', fontSize: '10px', color: '#999', cursor: 'pointer', fontWeight: '700' }}
                >
                  🔄 Actualizar
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* ESCÁNER */}
      <div style={{ background: 'linear-gradient(135deg, #102215 0%, #037623 100%)', color: 'white', padding: '20px', borderRadius: '20px', marginBottom: '20px' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', fontWeight: '900' }}>📸 ESCANEAR LISTA</h4>
        <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFoto} style={{ display: 'none' }} />
        <button onClick={() => fileInputRef?.current?.click()} disabled={escaneando} style={{ width: '100%', background: escaneando ? '#999' : '#13ec49', color: OSCURO, border: 'none', padding: '10px', borderRadius: '10px', fontWeight: '900', cursor: escaneando ? 'not-allowed' : 'pointer' }}>
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

        <div style={{ maxHeight: '800px', overflowY: 'auto' }}>
          {categoriasOrdenadas.map(categoria => {
            const subcategoriasFiltradas = Object.keys(db[categoria] || {}).filter(subcategoria => {
              return db[categoria][subcategoria].some(producto => {
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
                      const nombreLimpio = limpiarNombre(producto.nombre);
                      return nombreLimpio.toLowerCase().includes(busqueda.toLowerCase());
                    })
                    .sort((a, b) => limpiarNombre(a.nombre).localeCompare(limpiarNombre(b.nombre)));

                  return (
                    <div key={`sub-${categoria}-${subcategoria}`} style={{ paddingLeft: '15px', marginTop: '5px' }}>
                      <div
                        onClick={() => !busqueda && setSubcatAbierta(subcatAbierta === subcatKey ? null : subcatKey)}
                        style={{ fontSize: '10px', color: VERDE, fontWeight: '900', marginBottom: '5px', cursor: busqueda ? 'default' : 'pointer', display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}
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
