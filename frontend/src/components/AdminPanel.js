import React, { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';

const VERDE = '#037623';
const OSCURO = '#102215';
const GRIS = '#f4f7f5';

// ── Mini componentes ──────────────────────────────────────────────────────────

const StatCard = ({ emoji, label, value, sub, color }) => (
  <div style={{
    background: 'white', borderRadius: 16, padding: '20px 24px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.06)', borderLeft: `4px solid ${color || VERDE}`,
  }}>
    <div style={{ fontSize: 28, marginBottom: 6 }}>{emoji}</div>
    <div style={{ fontSize: 28, fontWeight: 900, color: OSCURO }}>{value}</div>
    <div style={{ fontSize: 13, fontWeight: 700, color: '#666', marginTop: 2 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: '#aaa', marginTop: 4 }}>{sub}</div>}
  </div>
);

const Badge = ({ text, color }) => (
  <span style={{
    background: color + '20', color, padding: '3px 10px',
    borderRadius: 20, fontSize: 11, fontWeight: 700,
  }}>{text}</span>
);

const Btn = ({ children, onClick, variant = 'primary', size = 'md', disabled }) => {
  const styles = {
    primary: { background: VERDE, color: 'white', border: 'none' },
    secondary: { background: 'white', color: VERDE, border: `1.5px solid ${VERDE}` },
    danger: { background: 'white', color: '#d32f2f', border: '1.5px solid #d32f2f' },
    ghost: { background: GRIS, color: OSCURO, border: 'none' },
  };
  const sizes = { sm: '6px 12px', md: '8px 16px', lg: '12px 24px' };
  return (
    <button onClick={onClick} disabled={disabled} style={{
      ...styles[variant], padding: sizes[size], borderRadius: 10,
      fontSize: size === 'sm' ? 11 : 13, fontWeight: 800, cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1, transition: 'all 0.15s',
    }}>{children}</button>
  );
};

// ── Secciones ────────────────────────────────────────────────────────────────

const Dashboard = ({ stats, supers }) => {
  if (!stats) return <div style={{ padding: 40, textAlign: 'center', color: '#aaa' }}>Cargando...</div>;
  const pct = (n) => (n && stats.catalogo ? Math.round(n / stats.catalogo * 100) : 0);
  return (
    <div>
      <h2 style={{ margin: '0 0 24px', fontSize: 22, fontWeight: 900, color: OSCURO }}>📊 Dashboard</h2>

      {/* La métrica que de verdad importa: cuántos productos comparan precio de verdad */}
      <div style={{
        background: `linear-gradient(135deg, ${VERDE}, #025c1c)`, borderRadius: 16, padding: '24px 28px',
        marginBottom: 24, color: 'white', boxShadow: '0 4px 20px rgba(3,118,35,0.25)',
      }}>
        <div style={{ fontSize: 13, fontWeight: 700, opacity: 0.85, marginBottom: 6 }}>
          🎯 NÚCLEO DE LA APP — Productos que comparan precio de verdad (≥2 supermercados)
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ fontSize: 42, fontWeight: 900 }}>{stats.comparando?.toLocaleString()}</div>
          <div style={{ fontSize: 16, opacity: 0.85 }}>
            de {stats.catalogo?.toLocaleString()} ({pct(stats.comparando)}%)
          </div>
          {stats.comparando3mas > 0 && (
            <div style={{ fontSize: 12, opacity: 0.75, marginLeft: 'auto' }}>
              {stats.comparando3mas?.toLocaleString()} en 3+ supers
            </div>
          )}
        </div>

        {/* Desglose visual: cuántos productos en 1, 2, 3, 4, 5 supers */}
        {stats.distribucionSupers && (
          <div style={{ display: 'flex', gap: 6, marginTop: 16, height: 8, borderRadius: 4, overflow: 'hidden' }}>
            {[1, 2, 3, 4, 5].map(n => {
              const cantidad = stats.distribucionSupers[n] || 0;
              const anchoPct = stats.catalogo ? (cantidad / stats.catalogo * 100) : 0;
              if (anchoPct < 0.3) return null;
              const opacidad = 0.35 + (n - 1) * 0.16;
              return (
                <div key={n} title={`${cantidad.toLocaleString()} productos en ${n} super${n > 1 ? 's' : ''}`}
                  style={{ width: `${anchoPct}%`, background: `rgba(255,255,255,${opacidad})`, minWidth: 2 }} />
              );
            })}
          </div>
        )}
        <div style={{ display: 'flex', gap: 14, marginTop: 8, flexWrap: 'wrap', fontSize: 10, opacity: 0.75 }}>
          {[1, 2, 3, 4, 5].map(n => (
            <span key={n}>{n} super{n > 1 ? 's' : ''}: {(stats.distribucionSupers?.[n] || 0).toLocaleString()}</span>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard emoji="👥" label="Usuarios registrados" value={stats.usuarios} color={VERDE} />
        <StatCard emoji="💳" label="Suscriptores de pago" value={stats.pagos} sub={`${stats.basic} basic · ${stats.premium} premium`} color="#6200ea" />
        <StatCard emoji="🛒" label="Productos catálogo" value={stats.catalogo?.toLocaleString()} color="#0288d1" />
        {supers.map(s => (
          <StatCard key={s.id} emoji="🔗" label={`Matches ${s.nombre}`}
            value={stats.matchesPorSuper?.[s.id]?.toLocaleString()}
            sub={`${pct(stats.matchesPorSuper?.[s.id])}% del catálogo`} color={s.color} />
        ))}
        <StatCard emoji="📦" label="Compras guardadas" value={stats.compras?.toLocaleString()} color="#00796b" />
      </div>

      <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 900, color: OSCURO }}>📦 Precios en BBDD</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        {supers.map(s => (
          <StatCard key={s.id} emoji={s.emoji} label={s.nombre}
            value={stats.preciosPorSuper?.[s.id]?.toLocaleString()} color={s.color} />
        ))}
      </div>

      <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 900, color: OSCURO }}>
        🔍 Calidad de datos por supermercado
      </h3>
      <div style={{
        background: 'white', borderRadius: 16, padding: '20px 24px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.06)', marginBottom: 32,
      }}>
        <div style={{ fontSize: 12, color: '#888', marginBottom: 18 }}>
          % de productos con nombre correcto vs. filas rotas (scraper sin capturar el nombre)
        </div>
        {supers.map(s => {
          const total = stats.preciosPorSuper?.[s.id] || 0;
          const vacios = stats.vaciosPorSuper?.[s.id] || 0;
          const pctVacio = total ? Math.round(vacios / total * 100) : 0;
          const pctOk = 100 - pctVacio;
          return (
            <div key={s.id} style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontWeight: 800, color: OSCURO }}>{s.emoji} {s.nombre}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: pctVacio > 10 ? '#d32f2f' : '#888' }}>
                  {pctOk}% OK{pctVacio > 0 && ` · ${vacios.toLocaleString()} filas rotas (${pctVacio}%)`}
                </span>
              </div>
              <div style={{ height: 10, borderRadius: 6, background: '#f0f0f0', overflow: 'hidden', display: 'flex' }}>
                <div style={{
                  width: `${pctOk}%`, background: s.color, transition: 'width 0.6s ease',
                }} />
                {pctVacio > 0 && (
                  <div style={{
                    width: `${pctVacio}%`,
                    background: 'repeating-linear-gradient(45deg, #d32f2f, #d32f2f 4px, #ff6659 4px, #ff6659 8px)',
                    transition: 'width 0.6s ease',
                  }} />
                )}
              </div>
            </div>
          );
        })}
      </div>

      <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 900, color: OSCURO }}>🏷️ Calidad de categorización</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
        <StatCard emoji="✅" label="Categorizados" value={stats.categorizados?.toLocaleString()}
          sub={`${pct(stats.categorizados)}% del catálogo`} color={VERDE} />
        <StatCard emoji="📥" label="Bazar y Varios (sin categoría clara)" value={stats.bazarVarios?.toLocaleString()}
          sub={`${pct(stats.bazarVarios)}% del catálogo`} color="#888" />
      </div>
    </div>
  );
};

const Usuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [editando, setEditando] = useState(null);
  const [nuevoPlan, setNuevoPlan] = useState('');

  useEffect(() => {
    cargar();
  }, []);

  const cargar = async () => {
    setCargando(true);
    // Cargar desde profiles
    const { data: profiles } = await supabase
      .from('profiles')
      .select('id, plan, stripe_id, plan_desde, plan_hasta, rol, created_at')
      .order('created_at', { ascending: false })
      .limit(200);
    setUsuarios(profiles || []);
    setCargando(false);
  };

  const cambiarPlan = async (userId, plan) => {
    await supabase.from('profiles').update({ plan }).eq('id', userId);
    setEditando(null);
    cargar();
  };

  const cambiarRol = async (userId, rol) => {
    await supabase.from('profiles').update({ rol }).eq('id', userId);
    cargar();
  };

  const filtrados = usuarios.filter(u =>
    !busqueda || u.id?.includes(busqueda) || u.plan?.includes(busqueda)
  );

  const planColor = { free: '#888', basic: '#0288d1', premium: '#6200ea' };
  const rolColor = { admin: '#d32f2f', user: '#888' };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 900, color: OSCURO }}>👥 Usuarios</h2>
        <input
          placeholder="Buscar por ID o plan..."
          value={busqueda}
          onChange={e => setBusqueda(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid #ddd', fontSize: 13, width: 220 }}
        />
      </div>

      {cargando ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>Cargando usuarios...</div>
      ) : (
        <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: OSCURO, color: 'white' }}>
                {['ID (UUID)', 'Plan', 'Rol', 'Stripe ID', 'Registrado', 'Acciones'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11, letterSpacing: 0.5 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtrados.map((u, i) => (
                <tr key={u.id} style={{ background: i % 2 === 0 ? 'white' : GRIS, borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#666' }}>
                    {u.id?.slice(0, 8)}...
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    {editando === u.id ? (
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <select value={nuevoPlan} onChange={e => setNuevoPlan(e.target.value)}
                          style={{ padding: '4px 8px', borderRadius: 8, border: '1.5px solid #ddd', fontSize: 12 }}>
                          <option value="free">free</option>
                          <option value="basic">basic</option>
                          <option value="premium">premium</option>
                        </select>
                        <Btn size="sm" onClick={() => cambiarPlan(u.id, nuevoPlan)}>✓</Btn>
                        <Btn size="sm" variant="ghost" onClick={() => setEditando(null)}>✗</Btn>
                      </div>
                    ) : (
                      <Badge text={u.plan || 'free'} color={planColor[u.plan] || '#888'} />
                    )}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <Badge text={u.rol || 'user'} color={rolColor[u.rol] || '#888'} />
                  </td>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 10, color: '#aaa' }}>
                    {u.stripe_id ? u.stripe_id.slice(0, 14) + '...' : '—'}
                  </td>
                  <td style={{ padding: '10px 16px', color: '#666', fontSize: 11 }}>
                    {u.created_at ? new Date(u.created_at).toLocaleDateString('es-ES') : '—'}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Btn size="sm" variant="secondary" onClick={() => { setEditando(u.id); setNuevoPlan(u.plan || 'free'); }}>
                        Cambiar plan
                      </Btn>
                      {u.rol !== 'admin' && (
                        <Btn size="sm" variant="danger" onClick={() => cambiarRol(u.id, 'admin')}>
                          Hacer admin
                        </Btn>
                      )}
                      {u.rol === 'admin' && (
                        <Btn size="sm" variant="ghost" onClick={() => cambiarRol(u.id, 'user')}>
                          Quitar admin
                        </Btn>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtrados.length === 0 && (
            <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>No hay usuarios</div>
          )}
          <div style={{ padding: '12px 16px', background: GRIS, fontSize: 12, color: '#888', fontWeight: 700 }}>
            {filtrados.length} usuarios
          </div>
        </div>
      )}
    </div>
  );
};

const Catalogo = () => {
  const [productos, setProductos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [catFiltro, setCatFiltro] = useState('');
  const [pagina, setPagina] = useState(1);
  const [editando, setEditando] = useState(null);
  const [edit, setEdit] = useState({});
  const POR_PAGINA = 50;

  const cargarCategorias = async () => {
    const { data } = await supabase.from('categorias_maestras').select('id, categoria, subcategoria').order('categoria');
    setCategorias(data || []);
  };

  const cargar = async () => {
    setCargando(true);
    try {
      let q = supabase.from('productos_catalogo')
        .select('id, nombre_generico, tipo, id_categoria', { count: 'exact' });
      if (busqueda) q = q.ilike('nombre_generico', `%${busqueda}%`);
      if (catFiltro) q = q.eq('id_categoria', parseInt(catFiltro));
      const { data, error } = await q.range((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA - 1).order('id');
      if (error) console.error('Error catálogo:', error);
      setProductos(data || []);
    } catch(e) {
      console.error('Catch catálogo:', e);
    }
    setCargando(false);
  };

  useEffect(() => {
    cargarCategorias();
  }, []); // eslint-disable-line

  useEffect(() => {
    cargar();
  }, [busqueda, catFiltro, pagina]); // eslint-disable-line

  const guardar = async (id) => {
    await supabase.from('productos_catalogo').update({
      nombre_generico: edit.nombre_generico,
      id_categoria: parseInt(edit.id_categoria),
    }).eq('id', id);
    setEditando(null);
    cargar();
  };

  const tipoColor = { marca_blanca: '#0288d1', marca_fabricante: '#6200ea' };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 900, color: OSCURO }}>📦 Catálogo</h2>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            placeholder="Buscar producto..."
            value={busqueda}
            onChange={e => { setBusqueda(e.target.value); setPagina(1); }}
            style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid #ddd', fontSize: 13, width: 200 }}
          />
          <select value={catFiltro} onChange={e => { setCatFiltro(e.target.value); setPagina(1); }}
            style={{ padding: '8px 14px', borderRadius: 10, border: '1.5px solid #ddd', fontSize: 12 }}>
            <option value="">Todas las categorías</option>
            {categorias.map(c => (
              <option key={c.id} value={c.id}>{c.categoria} › {c.subcategoria}</option>
            ))}
          </select>
        </div>
      </div>

      {cargando ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>Cargando catálogo...</div>
      ) : (
        <>
          <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: OSCURO, color: 'white' }}>
                  {['ID', 'Nombre genérico', 'Categoría', 'Tipo', 'Acciones'].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {productos.map((p, i) => (
                  <tr key={p.id} style={{ background: i % 2 === 0 ? 'white' : GRIS, borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#888' }}>{p.id}</td>
                    <td style={{ padding: '10px 16px', fontWeight: 600, color: OSCURO }}>
                      {editando === p.id ? (
                        <input value={edit.nombre_generico} onChange={e => setEdit({ ...edit, nombre_generico: e.target.value })}
                          style={{ width: '100%', padding: '4px 8px', borderRadius: 8, border: '1.5px solid ' + VERDE, fontSize: 13 }} />
                      ) : p.nombre_generico}
                    </td>
                    <td style={{ padding: '10px 16px', fontSize: 12, color: '#666' }}>
                      {editando === p.id ? (
                        <select value={edit.id_categoria} onChange={e => setEdit({ ...edit, id_categoria: e.target.value })}
                          style={{ padding: '4px 8px', borderRadius: 8, border: '1.5px solid #ddd', fontSize: 11 }}>
                          {categorias.map(c => (
                            <option key={c.id} value={c.id}>{c.categoria} › {c.subcategoria}</option>
                          ))}
                        </select>
                      ) : (categorias.find(c => c.id === p.id_categoria)?.subcategoria || p.id_categoria)}
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      <Badge text={p.tipo || '?'} color={tipoColor[p.tipo] || '#888'} />
                    </td>
                    <td style={{ padding: '10px 16px' }}>
                      {editando === p.id ? (
                        <div style={{ display: 'flex', gap: 6 }}>
                          <Btn size="sm" onClick={() => guardar(p.id)}>✓ Guardar</Btn>
                          <Btn size="sm" variant="ghost" onClick={() => setEditando(null)}>✗</Btn>
                        </div>
                      ) : (
                        <Btn size="sm" variant="secondary" onClick={() => {
                          setEditando(p.id);
                          setEdit({ nombre_generico: p.nombre_generico, id_categoria: p.id_categoria });
                        }}>Editar</Btn>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ padding: '12px 16px', background: GRIS, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: '#888', fontWeight: 700 }}>Página {pagina}</span>
              <div style={{ display: 'flex', gap: 8 }}>
                <Btn size="sm" variant="ghost" disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>← Anterior</Btn>
                <Btn size="sm" variant="ghost" disabled={productos.length < POR_PAGINA} onClick={() => setPagina(p => p + 1)}>Siguiente →</Btn>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const Matches = ({ supers }) => {
  const [matches, setMatches] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [filtro, setFiltro] = useState('todos');
  const [pagina, setPagina] = useState(1);
  const POR_PAGINA = 40;

  const columnas = supers.map(s => s.columna_match);

  const cargar = async () => {
    if (!supers.length) return;
    setCargando(true);
    let q = supabase.from('productos_match')
      .select(`id_catalogo, ${columnas.join(', ')}, productos_catalogo(nombre_generico, id_categoria)`, { count: 'exact' });
    if (filtro !== 'todos') {
      const col = filtro.replace('sin_', '');
      const superObj = supers.find(s => s.id === col);
      if (superObj) q = q.is(superObj.columna_match, null);
    }
    const { data } = await q.range((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA - 1);
    setMatches(data || []);
    setCargando(false);
  };

  useEffect(() => { cargar(); }, [filtro, pagina, supers]); // eslint-disable-line

  const limpiarMatch = async (idCatalogo, campo) => {
    await supabase.from('productos_match').update({ [campo]: null }).eq('id_catalogo', idCatalogo);
    cargar();
  };

  const check = (val) => val ? '✅' : '❌';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 900, color: OSCURO }}>🔗 Matches</h2>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button onClick={() => { setFiltro('todos'); setPagina(1); }}
            style={{
              padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700, cursor: 'pointer',
              background: filtro === 'todos' ? OSCURO : 'white', color: filtro === 'todos' ? 'white' : OSCURO,
              border: `1.5px solid ${filtro === 'todos' ? OSCURO : '#ddd'}`,
            }}>Todos</button>
          {supers.filter(s => s.id !== 'mercadona').map(s => (
            <button key={s.id} onClick={() => { setFiltro(`sin_${s.id}`); setPagina(1); }}
              style={{
                padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                background: filtro === `sin_${s.id}` ? OSCURO : 'white', color: filtro === `sin_${s.id}` ? 'white' : OSCURO,
                border: `1.5px solid ${filtro === `sin_${s.id}` ? OSCURO : '#ddd'}`,
              }}>Sin {s.nombre}</button>
          ))}
        </div>
      </div>

      {cargando ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>Cargando matches...</div>
      ) : (
        <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: OSCURO, color: 'white' }}>
                {['CAT', 'Producto', ...supers.map(s => s.nombre), 'Acciones'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matches.map((m, i) => (
                <tr key={m.id_catalogo} style={{ background: i % 2 === 0 ? 'white' : GRIS, borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#888' }}>{m.id_catalogo}</td>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: OSCURO, maxWidth: 200 }}>
                    <div style={{ fontSize: 13 }}>{m.productos_catalogo?.nombre_generico}</div>
                    <div style={{ fontSize: 10, color: '#aaa' }}>CAT {m.id_catalogo}</div>
                  </td>
                  {supers.map(s => (
                    <td key={s.id} style={{ padding: '10px 16px', textAlign: 'center' }}>{check(m[s.columna_match])}</td>
                  ))}
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {supers.filter(s => s.id !== 'mercadona').map(s => (
                        m[s.columna_match] &&
                        <Btn key={s.id} size="sm" variant="danger" onClick={() => limpiarMatch(m.id_catalogo, s.columna_match)}>
                          ✗ {s.nombre.slice(0, 3).toUpperCase()}
                        </Btn>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '12px 16px', background: GRIS, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#888', fontWeight: 700 }}>Página {pagina}</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <Btn size="sm" variant="ghost" disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>← Anterior</Btn>
              <Btn size="sm" variant="ghost" disabled={matches.length < POR_PAGINA} onClick={() => setPagina(p => p + 1)}>Siguiente →</Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const Precios = ({ supers }) => {
  const [super_, setSuper] = useState(supers[0]?.id || '');
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [soloVacios, setSoloVacios] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [editando, setEditando] = useState(null);
  const [edit, setEdit] = useState({});
  const [guardando, setGuardando] = useState(false);
  const POR_PAGINA = 50;

  useEffect(() => {
    if (!super_ && supers[0]) setSuper(supers[0].id);
  }, [supers]); // eslint-disable-line

  const cargar = async () => {
    if (!super_) return;
    setCargando(true);
    const config = supers.find(s => s.id === super_);
    if (!config) { setCargando(false); return; }
    let q = supabase.from(config.tabla_precios).select('id, nombre_comercial, precio, precio_unidad, marca, disponible');
    if (busqueda) q = q.ilike('nombre_comercial', `%${busqueda}%`);
    if (soloVacios) q = q.or('nombre_comercial.is.null,nombre_comercial.eq.');
    const { data } = await q.range((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA - 1).order('id');
    setProductos(data || []);
    setCargando(false);
  };

  useEffect(() => { cargar(); }, [super_, busqueda, soloVacios, pagina]); // eslint-disable-line

  const empezarEdicion = (p) => {
    setEditando(p.id);
    setEdit({
      nombre_comercial: p.nombre_comercial || '',
      precio: p.precio ?? '',
      marca: p.marca || '',
      disponible: !!p.disponible,
    });
  };

  const guardar = async (id) => {
    setGuardando(true);
    const config = supers.find(s => s.id === super_);
    await supabase.from(config.tabla_precios).update({
      nombre_comercial: edit.nombre_comercial,
      precio: edit.precio === '' ? null : parseFloat(edit.precio),
      marca: edit.marca,
      disponible: edit.disponible,
    }).eq('id', id);
    setEditando(null);
    setGuardando(false);
    cargar();
  };

  const superActual = supers.find(s => s.id === super_);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 900, color: OSCURO }}>💰 Precios</h2>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 6 }}>
            {supers.map(s => (
              <button key={s.id} onClick={() => { setSuper(s.id); setPagina(1); setSoloVacios(false); }}
                style={{
                  padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                  background: super_ === s.id ? VERDE : 'white', color: super_ === s.id ? 'white' : OSCURO,
                  border: `1.5px solid ${super_ === s.id ? VERDE : '#ddd'}`,
                }}>{s.nombre}</button>
            ))}
          </div>
          <input placeholder="Buscar..." value={busqueda}
            onChange={e => { setBusqueda(e.target.value); setPagina(1); }}
            style={{ padding: '6px 14px', borderRadius: 10, border: '1.5px solid #ddd', fontSize: 12, width: 180 }} />
        </div>
      </div>

      <label style={{
        display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 16, cursor: 'pointer',
        fontSize: 12, fontWeight: 700, color: soloVacios ? '#d32f2f' : '#888',
        background: soloVacios ? '#fdecea' : 'transparent', padding: '6px 12px', borderRadius: 10,
        border: `1.5px solid ${soloVacios ? '#d32f2f' : '#ddd'}`,
      }}>
        <input type="checkbox" checked={soloVacios}
          onChange={e => { setSoloVacios(e.target.checked); setPagina(1); }} />
        ⚠️ Ver solo filas con nombre vacío (datos rotos del scraper)
      </label>

      {cargando ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>Cargando precios...</div>
      ) : (
        <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: OSCURO, color: 'white' }}>
                {['ID', 'Nombre comercial', 'Precio', '€/unidad', 'Marca', 'Disp.', 'Acciones'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {productos.map((p, i) => (
                <tr key={p.id} style={{
                  background: !p.nombre_comercial ? '#fff8f0' : (i % 2 === 0 ? 'white' : GRIS),
                  borderBottom: '1px solid #f0f0f0',
                }}>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 10, color: '#888' }}>{p.id}</td>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: OSCURO, minWidth: 200 }}>
                    {editando === p.id ? (
                      <input value={edit.nombre_comercial} onChange={e => setEdit({ ...edit, nombre_comercial: e.target.value })}
                        style={{ width: '100%', padding: '4px 8px', borderRadius: 8, border: '1.5px solid ' + VERDE, fontSize: 13 }} />
                    ) : (p.nombre_comercial || <span style={{ color: '#d32f2f', fontWeight: 700 }}>— sin nombre —</span>)}
                  </td>
                  <td style={{ padding: '10px 16px', fontWeight: 800, color: VERDE, minWidth: 90 }}>
                    {editando === p.id ? (
                      <input type="number" step="0.01" value={edit.precio} onChange={e => setEdit({ ...edit, precio: e.target.value })}
                        style={{ width: 80, padding: '4px 8px', borderRadius: 8, border: '1.5px solid ' + VERDE, fontSize: 13 }} />
                    ) : (p.precio ? `${parseFloat(p.precio).toFixed(2)}€` : '—')}
                  </td>
                  <td style={{ padding: '10px 16px', fontSize: 11, color: '#888' }}>{p.precio_unidad || '—'}</td>
                  <td style={{ padding: '10px 16px', fontSize: 11, color: '#666', minWidth: 120 }}>
                    {editando === p.id ? (
                      <input value={edit.marca} onChange={e => setEdit({ ...edit, marca: e.target.value })}
                        style={{ width: '100%', padding: '4px 8px', borderRadius: 8, border: '1.5px solid #ddd', fontSize: 12 }} />
                    ) : (p.marca || '—')}
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>
                    {editando === p.id ? (
                      <input type="checkbox" checked={edit.disponible}
                        onChange={e => setEdit({ ...edit, disponible: e.target.checked })} />
                    ) : (p.disponible ? '✅' : '❌')}
                  </td>
                  <td style={{ padding: '10px 16px' }}>
                    {editando === p.id ? (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <Btn size="sm" onClick={() => guardar(p.id)} disabled={guardando}>✓</Btn>
                        <Btn size="sm" variant="ghost" onClick={() => setEditando(null)}>✗</Btn>
                      </div>
                    ) : (
                      <Btn size="sm" variant="secondary" onClick={() => empezarEdicion(p)}>Editar</Btn>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '12px 16px', background: GRIS, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#888', fontWeight: 700 }}>
              {superActual?.nombre} · Página {pagina} · {productos.length} productos
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <Btn size="sm" variant="ghost" disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>← Anterior</Btn>
              <Btn size="sm" variant="ghost" disabled={productos.length < POR_PAGINA} onClick={() => setPagina(p => p + 1)}>Siguiente →</Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const Estadisticas = () => {
  const [datos, setDatos] = useState(null);

  useEffect(() => {
    const cargar = async () => {
      const [compras, planes] = await Promise.all([
        supabase.from('compras').select('created_at, total').order('created_at', { ascending: false }).limit(100),
        supabase.from('profiles').select('plan').neq('plan', 'free'),
      ]);

      // Agrupar compras por fecha
      const porFecha = {};
      (compras.data || []).forEach(c => {
        const fecha = new Date(c.created_at).toLocaleDateString('es-ES');
        if (!porFecha[fecha]) porFecha[fecha] = { compras: 0, total: 0 };
        porFecha[fecha].compras++;
        porFecha[fecha].total += parseFloat(c.total || 0);
      });

      const porPlan = { basic: 0, premium: 0 };
      (planes.data || []).forEach(p => { if (porPlan[p.plan] !== undefined) porPlan[p.plan]++; });

      setDatos({ porFecha, porPlan, comprasTotales: compras.data?.length || 0 });
    };
    cargar();
  }, []);

  if (!datos) return <div style={{ padding: 40, textAlign: 'center', color: '#aaa' }}>Cargando estadísticas...</div>;

  return (
    <div>
      <h2 style={{ margin: '0 0 24px', fontSize: 22, fontWeight: 900, color: OSCURO }}>📈 Estadísticas</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 32 }}>
        <StatCard emoji="📋" label="Compras guardadas (últimas 100)" value={datos.comprasTotales} color={VERDE} />
        <StatCard emoji="💳" label="Suscriptores activos" value={datos.porPlan.basic + datos.porPlan.premium}
          sub={`${datos.porPlan.basic} basic · ${datos.porPlan.premium} premium`} color="#6200ea" />
      </div>

      <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 900, color: OSCURO }}>Compras por día (últimas 100)</h3>
      <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: OSCURO, color: 'white' }}>
              {['Fecha', 'Compras', 'Total acumulado'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Object.entries(datos.porFecha).slice(0, 20).map(([fecha, d], i) => (
              <tr key={fecha} style={{ background: i % 2 === 0 ? 'white' : GRIS }}>
                <td style={{ padding: '10px 16px', fontWeight: 600 }}>{fecha}</td>
                <td style={{ padding: '10px 16px' }}>{d.compras}</td>
                <td style={{ padding: '10px 16px', color: VERDE, fontWeight: 700 }}>{d.total.toFixed(2)}€</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const Supermercados = ({ supers, onCambio }) => {
  const [editando, setEditando] = useState(null);
  const [edit, setEdit] = useState({});
  const [guardando, setGuardando] = useState(false);

  const empezarEdicion = (s) => {
    setEditando(s.id);
    setEdit({ nombre: s.nombre, color: s.color, orden: s.orden });
  };

  const guardar = async (id) => {
    setGuardando(true);
    await supabase.from('supermercados').update({
      nombre: edit.nombre,
      color: edit.color,
      orden: parseInt(edit.orden) || 0,
    }).eq('id', id);
    setEditando(null);
    setGuardando(false);
    onCambio();
  };

  const toggleActivo = async (s) => {
    await supabase.from('supermercados').update({ activo: !s.activo }).eq('id', s.id);
    onCambio();
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 900, color: OSCURO }}>🏪 Supermercados</h2>
        <p style={{ margin: 0, fontSize: 13, color: '#888', maxWidth: 640 }}>
          Aquí puedes renombrar, cambiar de color, reordenar o activar/desactivar
          (ocultar del comparador) los supermercados ya integrados, sin tocar código.
          <br />
          <strong>Añadir un supermercado nuevo de verdad (ej. Lidl) sigue necesitando un
          scraper y una columna nueva en <code>productos_match</code></strong> — eso
          requiere desarrollo, pídeselo a Claude cuando llegue el momento.
        </p>
      </div>

      <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: OSCURO, color: 'white' }}>
              {['', 'Nombre', 'Tabla precios', 'Columna match', 'Color', 'Orden', 'Activo', 'Acciones'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {supers.map((s, i) => (
              <tr key={s.id} style={{ background: i % 2 === 0 ? 'white' : GRIS, borderBottom: '1px solid #f0f0f0', opacity: s.activo ? 1 : 0.5 }}>
                <td style={{ padding: '10px 16px', fontSize: 20 }}>{s.emoji}</td>
                <td style={{ padding: '10px 16px', fontWeight: 700, color: OSCURO }}>
                  {editando === s.id ? (
                    <input value={edit.nombre} onChange={e => setEdit({ ...edit, nombre: e.target.value })}
                      style={{ width: 140, padding: '4px 8px', borderRadius: 8, border: '1.5px solid ' + VERDE, fontSize: 13 }} />
                  ) : s.nombre}
                </td>
                <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#888' }}>{s.tabla_precios}</td>
                <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#888' }}>{s.columna_match}</td>
                <td style={{ padding: '10px 16px' }}>
                  {editando === s.id ? (
                    <input type="color" value={edit.color} onChange={e => setEdit({ ...edit, color: e.target.value })}
                      style={{ width: 40, height: 28, border: 'none', borderRadius: 6, cursor: 'pointer' }} />
                  ) : (
                    <span style={{ display: 'inline-block', width: 20, height: 20, borderRadius: 6, background: s.color }} />
                  )}
                </td>
                <td style={{ padding: '10px 16px' }}>
                  {editando === s.id ? (
                    <input type="number" value={edit.orden} onChange={e => setEdit({ ...edit, orden: e.target.value })}
                      style={{ width: 50, padding: '4px 8px', borderRadius: 8, border: '1.5px solid #ddd', fontSize: 13 }} />
                  ) : s.orden}
                </td>
                <td style={{ padding: '10px 16px' }}>
                  <button onClick={() => toggleActivo(s)} style={{
                    border: 'none', background: 'none', cursor: 'pointer', fontSize: 22,
                  }} title={s.activo ? 'Desactivar (ocultar del comparador)' : 'Activar'}>
                    {s.activo ? '✅' : '⬜'}
                  </button>
                </td>
                <td style={{ padding: '10px 16px' }}>
                  {editando === s.id ? (
                    <div style={{ display: 'flex', gap: 6 }}>
                      <Btn size="sm" onClick={() => guardar(s.id)} disabled={guardando}>✓ Guardar</Btn>
                      <Btn size="sm" variant="ghost" onClick={() => setEditando(null)}>✗</Btn>
                    </div>
                  ) : (
                    <Btn size="sm" variant="secondary" onClick={() => empezarEdicion(s)}>Editar</Btn>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ── Panel principal ───────────────────────────────────────────────────────────

const AdminPanel = ({ session, onSalir }) => {
  const [seccion, setSeccion] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [esAdmin, setEsAdmin] = useState(null);
  const [supers, setSupers] = useState([]);

  useEffect(() => {
    verificarAdmin();
    cargarSupersYStats();
  }, []); // eslint-disable-line

  const verificarAdmin = async () => {
    if (!session) { setEsAdmin(false); return; }
    const { data } = await supabase.from('profiles').select('rol').eq('id', session.user.id).single();
    setEsAdmin(data?.rol === 'admin');
  };

  const cargarSupersYStats = async () => {
    const { data: supersData } = await supabase.from('supermercados').select('*').order('orden');
    const listaSupers = supersData || [];
    setSupers(listaSupers);
    await cargarStats(listaSupers);
  };

  const cargarStats = async (listaSupers) => {
    if (!listaSupers.length) return;

    const columnasMatch = listaSupers.map(s => s.columna_match);
    const [cat, comprasRes, perfilesRes, bazarRes, matchRes, ...restoRes] = await Promise.all([
      supabase.from('productos_catalogo').select('id', { count: 'exact' }).limit(1),
      supabase.from('compras').select('id', { count: 'exact' }).limit(1),
      supabase.from('profiles').select('plan'),
      // "Bazar y Varios" = id_categoria 89 en categorias_maestras (ver docs/CONTEXTO.md sección 6)
      supabase.from('productos_catalogo').select('id', { count: 'exact' }).eq('id_categoria', 89).limit(1),
      supabase.from('productos_match').select(`id_catalogo, ${columnasMatch.join(', ')}`),
      ...listaSupers.map(s => supabase.from(s.tabla_precios).select('id', { count: 'exact' }).limit(1)),
      // Filas con nombre_comercial vacío/nulo por super — calidad de datos real,
      // detectado con Alcampo (ver docs/CONTEXTO.md) pero se comprueba en todos
      ...listaSupers.map(s => supabase.from(s.tabla_precios).select('id', { count: 'exact' })
        .or('nombre_comercial.is.null,nombre_comercial.eq.').limit(1)),
    ]);

    const preciosRes = restoRes.slice(0, listaSupers.length);
    const vaciosRes = restoRes.slice(listaSupers.length);

    const matches = matchRes.data || [];
    const perfiles = perfilesRes.data || [];
    const pagos = perfiles.filter(p => p.plan !== 'free').length;
    const basic = perfiles.filter(p => p.plan === 'basic').length;
    const premium = perfiles.filter(p => p.plan === 'premium').length;

    // Cuántos supers distintos tiene cada match (el núcleo real de la app:
    // solo si hay >=2 se puede comparar precio de verdad)
    const contarSupers = (m) => columnasMatch.filter(col => m[col]).length;
    const comparando = matches.filter(m => contarSupers(m) >= 2).length;
    const comparando3mas = matches.filter(m => contarSupers(m) >= 3).length;

    // Desglose exacto: cuántos productos tienen 1, 2, 3, 4 o 5 supers
    const distribucionSupers = {};
    matches.forEach(m => {
      const n = contarSupers(m);
      distribucionSupers[n] = (distribucionSupers[n] || 0) + 1;
    });

    const matchesPorSuper = {};
    const preciosPorSuper = {};
    const vaciosPorSuper = {};
    listaSupers.forEach((s, i) => {
      matchesPorSuper[s.id] = matches.filter(m => m[s.columna_match]).length;
      preciosPorSuper[s.id] = preciosRes[i]?.count || 0;
      vaciosPorSuper[s.id] = vaciosRes[i]?.count || 0;
    });

    const catalogoTotal = cat.count || 0;
    const bazar = bazarRes.count || 0;

    setStats({
      catalogo: catalogoTotal,
      matchesPorSuper,
      preciosPorSuper,
      vaciosPorSuper,
      comparando,
      comparando3mas,
      distribucionSupers,
      bazarVarios: bazar,
      categorizados: catalogoTotal - bazar,
      compras: comprasRes.count,
      usuarios: perfiles.length,
      pagos, basic, premium,
    });
  };

  if (esAdmin === null) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: GRIS }}>
      <div style={{ fontSize: 16, color: '#aaa' }}>Verificando acceso...</div>
    </div>
  );

  if (!esAdmin) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: GRIS, flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 40 }}>🔒</div>
      <div style={{ fontSize: 20, fontWeight: 900, color: OSCURO }}>Acceso denegado</div>
      <div style={{ fontSize: 14, color: '#888' }}>No tienes permisos de administrador.</div>
      <Btn onClick={onSalir} variant="secondary">← Volver a la app</Btn>
    </div>
  );

  const MENU = [
    { id: 'dashboard', emoji: '📊', label: 'Dashboard' },
    { id: 'usuarios', emoji: '👥', label: 'Usuarios' },
    { id: 'catalogo', emoji: '📦', label: 'Catálogo' },
    { id: 'matches', emoji: '🔗', label: 'Matches' },
    { id: 'precios', emoji: '💰', label: 'Precios' },
    { id: 'supermercados', emoji: '🏪', label: 'Supermercados' },
    { id: 'estadisticas', emoji: '📈', label: 'Estadísticas' },
  ];

  const isMobile = window.innerWidth < 768;

  return (
    <div style={{ minHeight: '100vh', background: GRIS, fontFamily: 'system-ui, sans-serif' }}>
      {/* Topbar */}
      <div style={{
        background: OSCURO, padding: '0 16px', height: 52,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: VERDE, fontWeight: 900, fontSize: 14 }}>MI MEJOR CESTA</span>
          <span style={{ color: '#ffffff40' }}>|</span>
          <span style={{ color: '#aaa', fontSize: 12, fontWeight: 700 }}>ADMIN</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {!isMobile && <span style={{ color: '#aaa', fontSize: 11 }}>{session?.user?.email}</span>}
          <Btn size="sm" variant="ghost" onClick={onSalir}>← App</Btn>
        </div>
      </div>

      {/* Nav móvil — barra horizontal */}
      {isMobile && (
        <div style={{
          background: 'white', borderBottom: '1px solid #eee',
          display: 'flex', overflowX: 'auto', padding: '6px 8px', gap: 4,
          position: 'sticky', top: 52, zIndex: 99,
        }}>
          {MENU.map(item => (
            <button key={item.id} onClick={() => setSeccion(item.id)}
              style={{
                padding: '7px 12px', borderRadius: 20, border: 'none', whiteSpace: 'nowrap',
                background: seccion === item.id ? VERDE : GRIS,
                color: seccion === item.id ? 'white' : OSCURO,
                fontSize: 12, fontWeight: 700, cursor: 'pointer', flexShrink: 0,
              }}>
              {item.emoji} {item.label}
            </button>
          ))}
        </div>
      )}

      <div style={{ display: 'flex' }}>
        {/* Sidebar — solo desktop */}
        {!isMobile && (
          <div style={{
            width: 200, background: 'white', minHeight: 'calc(100vh - 52px)',
            padding: '20px 10px', boxShadow: '2px 0 12px rgba(0,0,0,0.04)',
            position: 'sticky', top: 52, alignSelf: 'flex-start', flexShrink: 0,
          }}>
            {MENU.map(item => (
              <button key={item.id} onClick={() => setSeccion(item.id)}
                style={{
                  width: '100%', padding: '9px 12px', borderRadius: 10, border: 'none',
                  background: seccion === item.id ? VERDE : 'transparent',
                  color: seccion === item.id ? 'white' : OSCURO,
                  fontSize: 13, fontWeight: 700, cursor: 'pointer', textAlign: 'left',
                  marginBottom: 3, display: 'flex', alignItems: 'center', gap: 8,
                  transition: 'all 0.15s',
                }}>
                <span>{item.emoji}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* Contenido */}
        <div style={{ flex: 1, padding: isMobile ? 16 : 28, maxWidth: 1200, minWidth: 0, overflowX: 'hidden' }}>
          {seccion === 'dashboard' && <Dashboard stats={stats} supers={supers} />}
          {seccion === 'usuarios' && <Usuarios />}
          {seccion === 'catalogo' && <Catalogo />}
          {seccion === 'matches' && <Matches supers={supers} />}
          {seccion === 'precios' && <Precios supers={supers} />}
          {seccion === 'supermercados' && <Supermercados supers={supers} onCambio={cargarSupersYStats} />}
          {seccion === 'estadisticas' && <Estadisticas />}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
