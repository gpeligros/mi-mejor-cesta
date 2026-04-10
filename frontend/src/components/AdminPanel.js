import React, { useState, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL,
  process.env.REACT_APP_SUPABASE_ANON_KEY
);

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

const Dashboard = ({ stats }) => {
  if (!stats) return <div style={{ padding: 40, textAlign: 'center', color: '#aaa' }}>Cargando...</div>;
  return (
    <div>
      <h2 style={{ margin: '0 0 24px', fontSize: 22, fontWeight: 900, color: OSCURO }}>📊 Dashboard</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        <StatCard emoji="👥" label="Usuarios registrados" value={stats.usuarios} color={VERDE} />
        <StatCard emoji="💳" label="Suscriptores de pago" value={stats.pagos} sub={`${stats.basic} basic · ${stats.premium} premium`} color="#6200ea" />
        <StatCard emoji="🛒" label="Productos catálogo" value={stats.catalogo?.toLocaleString()} color="#0288d1" />
        <StatCard emoji="🔗" label="Matches Mercadona" value={stats.con_mercadona?.toLocaleString()} sub="100% del catálogo" color={VERDE} />
        <StatCard emoji="🔗" label="Matches DIA" value={stats.con_dia?.toLocaleString()} sub={`${stats.con_dia && stats.catalogo ? Math.round(stats.con_dia/stats.catalogo*100) : 0}% del catálogo`} color="#e53935" />
        <StatCard emoji="🔗" label="Matches Alcampo" value={stats.con_alcampo?.toLocaleString()} sub={`${stats.con_alcampo && stats.catalogo ? Math.round(stats.con_alcampo/stats.catalogo*100) : 0}% del catálogo`} color="#f57c00" />
        <StatCard emoji="🔗" label="Matches Ahorramas" value={stats.con_ahorramas?.toLocaleString()} sub={`${stats.con_ahorramas && stats.catalogo ? Math.round(stats.con_ahorramas/stats.catalogo*100) : 0}% del catálogo`} color="#c62828" />
        <StatCard emoji="📦" label="Compras guardadas" value={stats.compras?.toLocaleString()} color="#00796b" />
      </div>

      <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 900, color: OSCURO }}>📦 Precios en BBDD</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16 }}>
        <StatCard emoji="🟢" label="Mercadona" value={stats.mercadona?.toLocaleString()} color={VERDE} />
        <StatCard emoji="🔴" label="DIA" value={stats.dia?.toLocaleString()} color="#e53935" />
        <StatCard emoji="🟠" label="Alcampo" value={stats.alcampo?.toLocaleString()} color="#f57c00" />
        <StatCard emoji="🟥" label="Ahorramas" value={stats.ahorramas?.toLocaleString()} color="#c62828" />
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
    const { data } = await supabase.rpc('admin_get_usuarios').maybeSingle();
    // Fallback: cargar desde profiles + auth.users
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
        <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
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

  useEffect(() => {
    cargarCategorias();
  }, []);

  useEffect(() => {
    cargar();
  }, [busqueda, catFiltro, pagina]); // eslint-disable-line

  const cargarCategorias = async () => {
    const { data } = await supabase.from('categorias_maestras').select('id, categoria, subcategoria').order('categoria');
    setCategorias(data || []);
  };

  const cargar = async () => {
    setCargando(true);
    let q = supabase.from('vista_productos')
      .select('id, nombre_generico, categoria, subcategoria, tipo, id_categoria', { count: 'exact' });
    if (busqueda) q = q.ilike('nombre_generico', `%${busqueda}%`);
    if (catFiltro) q = q.eq('id_categoria', catFiltro);
    const { data } = await q.range((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA - 1).order('id');
    setProductos(data || []);
    setCargando(false);
  };

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
          <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
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
                      ) : `${p.categoria} › ${p.subcategoria}`}
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

const Matches = () => {
  const [matches, setMatches] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [filtro, setFiltro] = useState('todos');
  const [pagina, setPagina] = useState(1);
  const POR_PAGINA = 40;

  useEffect(() => { cargar(); }, [filtro, pagina]); // eslint-disable-line

  const cargar = async () => {
    setCargando(true);
    let q = supabase.from('productos_match')
      .select('id_catalogo, id_mercadona, id_dia, id_alcampo, id_ahorramas, vista_productos(nombre_generico, categoria)', { count: 'exact' });
    if (filtro === 'sin_dia') q = q.is('id_dia', null);
    else if (filtro === 'sin_alcampo') q = q.is('id_alcampo', null);
    else if (filtro === 'sin_ahorramas') q = q.is('id_ahorramas', null);
    const { data } = await q.range((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA - 1);
    setMatches(data || []);
    setCargando(false);
  };

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
          {['todos', 'sin_dia', 'sin_alcampo', 'sin_ahorramas'].map(f => (
            <button key={f} onClick={() => { setFiltro(f); setPagina(1); }}
              style={{
                padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                background: filtro === f ? OSCURO : 'white',
                color: filtro === f ? 'white' : OSCURO,
                border: `1.5px solid ${filtro === f ? OSCURO : '#ddd'}`,
              }}>
              {f === 'todos' ? 'Todos' : f === 'sin_dia' ? 'Sin DIA' : f === 'sin_alcampo' ? 'Sin Alcampo' : 'Sin Ahorramas'}
            </button>
          ))}
        </div>
      </div>

      {cargando ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>Cargando matches...</div>
      ) : (
        <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: OSCURO, color: 'white' }}>
                {['CAT', 'Producto', 'Mercadona', 'DIA', 'Alcampo', 'Ahorramas', 'Acciones'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matches.map((m, i) => (
                <tr key={m.id_catalogo} style={{ background: i % 2 === 0 ? 'white' : GRIS, borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 11, color: '#888' }}>{m.id_catalogo}</td>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: OSCURO, maxWidth: 200 }}>
                    <div style={{ fontSize: 13 }}>{m.vista_productos?.nombre_generico}</div>
                    <div style={{ fontSize: 10, color: '#aaa' }}>{m.vista_productos?.categoria}</div>
                  </td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>{check(m.id_mercadona)}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>{check(m.id_dia)}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>{check(m.id_alcampo)}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>{check(m.id_ahorramas)}</td>
                  <td style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {m.id_dia && <Btn size="sm" variant="danger" onClick={() => limpiarMatch(m.id_catalogo, 'id_dia')}>✗ DIA</Btn>}
                      {m.id_alcampo && <Btn size="sm" variant="danger" onClick={() => limpiarMatch(m.id_catalogo, 'id_alcampo')}>✗ ALC</Btn>}
                      {m.id_ahorramas && <Btn size="sm" variant="danger" onClick={() => limpiarMatch(m.id_catalogo, 'id_ahorramas')}>✗ AHO</Btn>}
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

const Precios = () => {
  const [super_, setSuper] = useState('mercadona');
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [pagina, setPagina] = useState(1);
  const POR_PAGINA = 50;

  const SUPERS = [
    { id: 'mercadona', tabla: 'precios_mercadona', label: 'Mercadona' },
    { id: 'dia', tabla: 'precios_dia', label: 'DIA' },
    { id: 'alcampo', tabla: 'precios_alcampo', label: 'Alcampo' },
    { id: 'ahorramas', tabla: 'precios_ahorramas', label: 'Ahorramas' },
  ];

  useEffect(() => { cargar(); }, [super_, busqueda, pagina]); // eslint-disable-line

  const cargar = async () => {
    setCargando(true);
    const config = SUPERS.find(s => s.id === super_);
    let q = supabase.from(config.tabla).select('id, nombre_comercial, precio, precio_unidad, marca, disponible');
    if (busqueda) q = q.ilike('nombre_comercial', `%${busqueda}%`);
    const { data } = await q.range((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA - 1).order('id');
    setProductos(data || []);
    setCargando(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 900, color: OSCURO }}>💰 Precios</h2>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', gap: 6 }}>
            {SUPERS.map(s => (
              <button key={s.id} onClick={() => { setSuper(s.id); setPagina(1); }}
                style={{
                  padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                  background: super_ === s.id ? VERDE : 'white', color: super_ === s.id ? 'white' : OSCURO,
                  border: `1.5px solid ${super_ === s.id ? VERDE : '#ddd'}`,
                }}>{s.label}</button>
            ))}
          </div>
          <input placeholder="Buscar..." value={busqueda}
            onChange={e => { setBusqueda(e.target.value); setPagina(1); }}
            style={{ padding: '6px 14px', borderRadius: 10, border: '1.5px solid #ddd', fontSize: 12, width: 180 }} />
        </div>
      </div>

      {cargando ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#aaa' }}>Cargando precios...</div>
      ) : (
        <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: OSCURO, color: 'white' }}>
                {['ID', 'Nombre comercial', 'Precio', '€/unidad', 'Marca', 'Disp.'].map(h => (
                  <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 800, fontSize: 11 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {productos.map((p, i) => (
                <tr key={p.id} style={{ background: i % 2 === 0 ? 'white' : GRIS, borderBottom: '1px solid #f0f0f0' }}>
                  <td style={{ padding: '10px 16px', fontFamily: 'monospace', fontSize: 10, color: '#888' }}>{p.id}</td>
                  <td style={{ padding: '10px 16px', fontWeight: 600, color: OSCURO }}>{p.nombre_comercial}</td>
                  <td style={{ padding: '10px 16px', fontWeight: 800, color: VERDE }}>{p.precio ? `${parseFloat(p.precio).toFixed(2)}€` : '—'}</td>
                  <td style={{ padding: '10px 16px', fontSize: 11, color: '#888' }}>{p.precio_unidad || '—'}</td>
                  <td style={{ padding: '10px 16px', fontSize: 11, color: '#666' }}>{p.marca || '—'}</td>
                  <td style={{ padding: '10px 16px', textAlign: 'center' }}>{p.disponible ? '✅' : '❌'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: '12px 16px', background: GRIS, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: '#888', fontWeight: 700 }}>Página {pagina} · {productos.length} productos</span>
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
      <div style={{ background: 'white', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
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

// ── Panel principal ───────────────────────────────────────────────────────────

const AdminPanel = ({ session, onSalir }) => {
  const [seccion, setSeccion] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [esAdmin, setEsAdmin] = useState(null);

  useEffect(() => {
    verificarAdmin();
    cargarStats();
  }, []); // eslint-disable-line

  const verificarAdmin = async () => {
    if (!session) { setEsAdmin(false); return; }
    const { data } = await supabase.from('profiles').select('rol').eq('id', session.user.id).single();
    setEsAdmin(data?.rol === 'admin');
  };

  const cargarStats = async () => {
    const [cat, merc, dia, alc, ah, matchRes, comprasRes, perfilesRes] = await Promise.all([
      supabase.from('productos_catalogo').select('id', { count: 'exact' }).limit(1),
      supabase.from('precios_mercadona').select('id', { count: 'exact' }).limit(1),
      supabase.from('precios_dia').select('id', { count: 'exact' }).limit(1),
      supabase.from('precios_alcampo').select('id', { count: 'exact' }).limit(1),
      supabase.from('precios_ahorramas').select('id', { count: 'exact' }).limit(1),
      supabase.from('productos_match').select('id_catalogo, id_mercadona, id_dia, id_alcampo, id_ahorramas'),
      supabase.from('compras').select('id', { count: 'exact' }).limit(1),
      supabase.from('profiles').select('plan'),
    ]);

    const matches = matchRes.data || [];
    const perfiles = perfilesRes.data || [];
    const pagos = perfiles.filter(p => p.plan !== 'free').length;
    const basic = perfiles.filter(p => p.plan === 'basic').length;
    const premium = perfiles.filter(p => p.plan === 'premium').length;

    setStats({
      catalogo: cat.count,
      mercadona: merc.count,
      dia: dia.count,
      alcampo: alc.count,
      ahorramas: ah.count,
      con_mercadona: matches.filter(m => m.id_mercadona).length,
      con_dia: matches.filter(m => m.id_dia).length,
      con_alcampo: matches.filter(m => m.id_alcampo).length,
      con_ahorramas: matches.filter(m => m.id_ahorramas).length,
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
    { id: 'estadisticas', emoji: '📈', label: 'Estadísticas' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: GRIS, fontFamily: 'system-ui, sans-serif' }}>
      {/* Topbar */}
      <div style={{
        background: OSCURO, padding: '0 24px', height: 56,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: VERDE, fontWeight: 900, fontSize: 16 }}>MI MEJOR CESTA</span>
          <span style={{ color: '#ffffff40', fontSize: 14 }}>|</span>
          <span style={{ color: '#aaa', fontSize: 13, fontWeight: 700 }}>ADMIN</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: '#aaa', fontSize: 12 }}>{session?.user?.email}</span>
          <Btn size="sm" variant="ghost" onClick={onSalir}>← App</Btn>
        </div>
      </div>

      <div style={{ display: 'flex' }}>
        {/* Sidebar */}
        <div style={{
          width: 220, background: 'white', minHeight: 'calc(100vh - 56px)',
          padding: '24px 12px', boxShadow: '2px 0 12px rgba(0,0,0,0.04)',
          position: 'sticky', top: 56, alignSelf: 'flex-start',
        }}>
          {MENU.map(item => (
            <button key={item.id} onClick={() => setSeccion(item.id)}
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 12, border: 'none',
                background: seccion === item.id ? VERDE : 'transparent',
                color: seccion === item.id ? 'white' : OSCURO,
                fontSize: 14, fontWeight: 700, cursor: 'pointer', textAlign: 'left',
                marginBottom: 4, display: 'flex', alignItems: 'center', gap: 10,
                transition: 'all 0.15s',
              }}>
              <span>{item.emoji}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        {/* Contenido */}
        <div style={{ flex: 1, padding: 32, maxWidth: 1200, minWidth: 0 }}>
          {seccion === 'dashboard' && <Dashboard stats={stats} />}
          {seccion === 'usuarios' && <Usuarios />}
          {seccion === 'catalogo' && <Catalogo />}
          {seccion === 'matches' && <Matches />}
          {seccion === 'precios' && <Precios />}
          {seccion === 'estadisticas' && <Estadisticas />}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
