import React, { useState, useEffect, useRef } from 'react';
import { supabase } from './supabaseClient';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import SyncHeader from './components/SyncHeader';
import StoreSelector from './components/StoreSelector';
import SuperCard from './components/SuperCard';
import Sidebar from './components/Sidebar';
import listaSupers from './components/LogosSuper';

const App = () => {
  // --- 1. ESTADOS ---
  const [session, setSession] = useState(null);
  const [syncActiva, setSyncActiva] = useState(() => JSON.parse(localStorage.getItem('sync_pref')) ?? true);
  const [db, setDb] = useState({});
  const [precios, setPrecios] = useState({});
  const [seleccionados, setSeleccionados] = useState(() => {
    const saved = localStorage.getItem('miCesta_v7');
    if (!saved) return [];
    try {
      const parsed = JSON.parse(saved);
      return Array.isArray(parsed) ? parsed.filter(id => id && typeof id === 'string' && id.trim() !== '') : [];
    } catch (e) {
      console.error('Error parseando localStorage:', e);
      return [];
    }
  });
  const [comprados, setComprados] = useState([]);
  const [cestasGuardadas, setCestasGuardadas] = useState(() => JSON.parse(localStorage.getItem('misCestas_v7')) || {});
  const [supersActivos, setSupersActivos] = useState(["Lidl", "Mercadona", "Carrefour"]);
  const [acordeon, setAcordeon] = useState(null);
  const [busqueda, setBusqueda] = useState("");
  const [modoTienda, setModoTienda] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [estadoSync, setEstadoSync] = useState('idle');
  const [seccionActual, setSeccionActual] = useState('comparador');
  const [mostrarCookies, setMostrarCookies] = useState(() => !localStorage.getItem('cookies_aceptadas'));
  const [escaneando, setEscaneando] = useState(false);
  const fileInputRef = useRef(null);

  // --- 2. EFECTOS Y FUNCIONES ---
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    
    const cargarDatos = async () => {
      try {
        const { data: prods, error: errorProds } = await supabase.from('productos').select('*');
        const { data: precs, error: errorPrecs } = await supabase.from('precios_mercado').select('*');
        
        if (errorProds) {
          console.error('❌ Error cargando productos:', errorProds);
        }
        if (errorPrecs) {
          console.error('❌ Error cargando precios:', errorPrecs);
        }
        
        if (prods) {
          // ✅ CORRECCIÓN: Usar id_producto en vez de id
          const dbMap = prods.reduce((acc, p) => {
            if (!p.id_producto) {
              console.warn('⚠️ Producto sin id_producto:', p);
              return acc;
            }
            if (!acc[p.categoria]) acc[p.categoria] = {};
            if (!acc[p.categoria][p.subcategoria]) acc[p.categoria][p.subcategoria] = [];
            acc[p.categoria][p.subcategoria].push(p);
            return acc;
          }, {});
          
          setDb(dbMap);
          console.log('✅ Productos cargados:', prods.length);
        }
        
        if (precs) {
          const mapa = {};
          precs.forEach(p => {
            if (!p.id_producto || !p.supermercado || p.precio == null) {
              console.warn('⚠️ Registro de precio inválido:', p);
              return;
            }
            
            if (!mapa[p.id_producto]) mapa[p.id_producto] = {};
            
            // Normalizar nombre del supermercado
            const superNormalizado = p.supermercado.charAt(0).toUpperCase() + p.supermercado.slice(1).toLowerCase();
            
            mapa[p.id_producto][superNormalizado] = p.precio;
          });
          
          setPrecios(mapa);
          console.log('✅ Precios cargados:', Object.keys(mapa).length, 'productos');
          console.log('Ejemplo:', Object.keys(mapa)[0], '→', mapa[Object.keys(mapa)[0]]);
        }
      } catch (err) {
        console.error('❌ Error general cargando datos:', err);
      } finally {
        setCargando(false);
      }
    };
    
    cargarDatos();
  }, []);

  useEffect(() => {
    localStorage.setItem('miCesta_v7', JSON.stringify(seleccionados));
    localStorage.setItem('misCestas_v7', JSON.stringify(cestasGuardadas));
    localStorage.setItem('sync_pref', JSON.stringify(syncActiva));
  }, [seleccionados, cestasGuardadas, syncActiva]);

  const sincronizarNube = async (prods, comps) => {
    if (!session || !syncActiva) return;
    setEstadoSync('sincronizando');
    try {
      await supabase.from('cestas_online').upsert({
        user_id: session.user.id,
        productos: prods,
        comprados: comps,
        updated_at: new Date()
      }, { onConflict: 'user_id' });
      setEstadoSync('ok');
      setTimeout(() => setEstadoSync('idle'), 3000);
    } catch (err) {
      console.error('❌ Error sincronizando:', err);
      setEstadoSync('error');
    }
  };

  const toggleProd = (id) => {
    const nvas = seleccionados.includes(id) ? seleccionados.filter(x => x !== id) : [...seleccionados, id];
    setSeleccionados(nvas);
    sincronizarNube(nvas, comprados);
  };

  const handleCheckTienda = (id) => {
    const nva = comprados.includes(id) ? comprados.filter(x => x !== id) : [...comprados, id];
    setComprados(nva);
    sincronizarNube(seleccionados, nva);
  };

  const vaciarCesta = () => {
    setSeleccionados([]);
    setComprados([]);
    sincronizarNube([], []);
  };

  const getProdFull = (id) => {
    // ✅ CORRECCIÓN: Buscar por id_producto
    for (const cat in db) {
      for (const sub in db[cat]) {
        const found = db[cat][sub].find(p => p.id_producto === id);
        if (found) return found;
      }
    }
    return null;
  };

  const handleFoto = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setEscaneando(true);
    
    try {
      console.log('Procesando imagen:', file.name);
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('Función de escaneo OCR pendiente de implementar.\n\nOpciones recomendadas:\n- Tesseract.js (gratis, en navegador)\n- Google Cloud Vision API\n- OpenAI Vision API');
    } catch (err) {
      console.error('Error escaneando imagen:', err);
      alert('Error al procesar la imagen. Intenta de nuevo.');
    } finally {
      setEscaneando(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // --- 3. CÁLCULOS (Stats) ---
  const stats = (() => {
    const totalesPorSuper = supersActivos.map(s => {
      const total = seleccionados.reduce((acc, id) => {
        const precio = precios[id]?.[s];
        return acc + (precio && precio > 0 ? precio : 0);
      }, 0);
      
      const productosDisponibles = seleccionados.filter(id => 
        precios[id]?.[s] && precios[id][s] > 0
      ).length;
      
      return {
        id: s,
        t: total,
        productosDisponibles
      };
    }).sort((a, b) => a.t - b.t);
    
    let multiTotal = 0;
    let productosSinPrecio = 0;
    
    seleccionados.forEach(id => {
      const preciosValidos = supersActivos
        .map(s => precios[id]?.[s])
        .filter(p => p && p > 0);
      
      if (preciosValidos.length > 0) {
        multiTotal += Math.min(...preciosValidos);
      } else {
        productosSinPrecio++;
      }
    });
    
    return {
      ahorro: totalesPorSuper.length > 1 ? 
        totalesPorSuper[totalesPorSuper.length - 1].t - totalesPorSuper[0].t : 0,
      mejor: totalesPorSuper[0]?.id || "-",
      multi: multiTotal,
      total: totalesPorSuper[0]?.t || 0,
      productosSinPrecio,
      detallePorSuper: totalesPorSuper
    };
  })();

  if (cargando) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #102215 0%, #037623 100%)',
        color: '#13ec49',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ fontSize: '3em', marginBottom: '20px' }}>🛒</div>
        <div style={{ fontSize: '1.5em', fontWeight: '800' }}>CARGANDO MI MEJOR CESTA...</div>
        <div style={{ marginTop: '10px', opacity: 0.7 }}>Conectando con base de datos</div>
      </div>
    );
  }

  // --- 4. RENDERIZADO ---
  const RenderModoTienda = () => (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto', gridColumn: '1/-1' }}>
      <button 
        onClick={() => setModoTienda(null)} 
        style={{ 
          width:'100%', 
          padding:'15px', 
          borderRadius:'15px', 
          background:'#102215', 
          color:'white', 
          fontWeight:'800', 
          marginBottom:'20px', 
          border:'none', 
          cursor:'pointer' 
        }}
      >
        ← VOLVER AL COMPARADOR
      </button>
      <h2 style={{fontWeight:'900', color:'#037623', marginBottom:'20px'}}>🛒 Comprando en {modoTienda}</h2>
      {seleccionados
        .map(id => ({ id, comprado: comprados.includes(id) }))
        .sort((a, b) => a.comprado - b.comprado)
        .map(({ id, comprado }) => {
          const p = getProdFull(id);
          return p && (
            <div 
              key={id} 
              onClick={() => handleCheckTienda(id)} 
              style={{ 
                padding: '20px', 
                backgroundColor: comprado ? '#f9f9f9' : 'white', 
                borderRadius: '15px', 
                border: comprado ? '1px solid #eee' : '1px solid #037623', 
                marginBottom: '10px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '15px', 
                cursor: 'pointer', 
                opacity: comprado ? 0.6 : 1,
                transition: 'all 0.3s ease'
              }}
            >
              <div style={{ 
                width: '30px', 
                height: '30px', 
                border: '3px solid #037623', 
                borderRadius: '10px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                background: comprado ? '#037623' : 'white' 
              }}>
                {comprado && <span style={{color:'white', fontWeight:'900'}}>✓</span>}
              </div>
              <span style={{ 
                fontWeight: '800', 
                fontSize: '18px', 
                textDecoration: comprado ? 'line-through' : 'none' 
              }}>
                {p.nombre}
              </span>
            </div>
          );
        })
      }
    </div>
  );

  return (
    <div style={{ backgroundColor: '#f4f7f5', minHeight: '100vh' }}>
      <SyncHeader 
        session={session} 
        syncActiva={syncActiva} 
        setSyncActiva={setSyncActiva} 
        estadoSync={estadoSync} 
      />
      <Navbar />

      <div style={{ padding: '30px' }}>
        {seccionActual === 'comparador' && !modoTienda && (
          <StoreSelector 
            listaSupers={listaSupers} 
            supersActivos={supersActivos} 
            setSupersActivos={setSupersActivos} 
          />
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '30px' }}>
          <Sidebar
            stats={stats}
            cestasGuardadas={cestasGuardadas}
            setCestasGuardadas={setCestasGuardadas}
            seleccionados={seleccionados}
            setSeleccionados={setSeleccionados}
            setComprados={setComprados}
            db={db}
            acordeon={acordeon}
            setAcordeon={setAcordeon}
            toggleProd={toggleProd}
            vaciarCesta={vaciarCesta}
            busqueda={busqueda}
            setBusqueda={setBusqueda}
            escaneando={escaneando}
            fileInputRef={fileInputRef}
            handleFoto={handleFoto}
          />

          <main style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '25px', alignItems: 'start' }}>
            {modoTienda ? <RenderModoTienda /> : (
              <>
                {seccionActual === 'comparador' && supersActivos.map(sId => (
                  <SuperCard 
                    key={sId} 
                    sId={sId} 
                    logo={listaSupers.find(x => x.id === sId).logo} 
                    seleccionados={seleccionados} 
                    precios={precios} 
                    supersActivos={supersActivos} 
                    getProdFull={getProdFull} 
                    setModoTienda={setModoTienda} 
                  />
                ))}
                {seccionActual === 'favoritos' && (
                  <div style={{gridColumn:'1/-1', textAlign:'center', padding:'50px'}}>
                    <h2>⭐ MIS LISTAS GUARDADAS</h2>
                  </div>
                )}
                {seccionActual === 'ahorro' && (
                  <div style={{gridColumn:'1/-1', textAlign:'center', padding:'50px'}}>
                    <h2>📊 MI AHORRO TOTAL: {stats.ahorro.toFixed(2)}€</h2>
                    {stats.productosSinPrecio > 0 && (
                      <p style={{color: '#666', marginTop: '10px'}}>
                        ⚠️ {stats.productosSinPrecio} producto(s) sin precio en ningún supermercado
                      </p>
                    )}
                  </div>
                )}
              </>
            )}
            
            {seccionActual === 'privacidad' && (
              <div style={{ gridColumn: '1/-1', background: 'white', padding: '40px', borderRadius: '20px', lineHeight: '1.6' }}>
                <h2 style={{color: '#037623', fontWeight: '900', marginBottom: '20px'}}>POLÍTICA DE PRIVACIDAD</h2>
                <p>En <strong>Mi Mejor Cesta</strong>, la privacidad de nuestros usuarios es una prioridad.</p>
              </div>
            )}

            {seccionActual === 'terminos' && (
              <div style={{ gridColumn: '1/-1', background: 'white', padding: '40px', borderRadius: '20px', lineHeight: '1.6' }}>
                <h2 style={{color: '#037623', fontWeight: '900', marginBottom: '20px'}}>TÉRMINOS Y CONDICIONES</h2>
                <p>Al utilizar esta plataforma, usted acepta los siguientes términos...</p>
              </div>
            )}

            {seccionActual === 'cookies' && (
              <div style={{ gridColumn: '1/-1', background: 'white', padding: '40px', borderRadius: '20px', lineHeight: '1.6' }}>
                <h2 style={{color: '#037623', fontWeight: '900', marginBottom: '20px'}}>POLÍTICA DE COOKIES</h2>
                <p>Utilizamos tecnologías de almacenamiento local (localStorage) para mejorar su experiencia...</p>
              </div>
            )}
          </main>
        </div>
      </div>
      
      <Footer setSeccionActual={setSeccionActual} />
      
      {mostrarCookies && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '90%',
          maxWidth: '500px',
          backgroundColor: '#102215',
          color: 'white',
          padding: '20px',
          borderRadius: '20px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          gap: '15px',
          border: '1px solid #037623'
        }}>
          <div style={{ fontSize: '14px', lineHeight: '1.4' }}>
            <strong>🍪 ¿Unas cookies para ahorrar?</strong><br/>
            Utilizamos cookies propias para guardar tu cesta y tus preferencias de supermercado.
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => {
                localStorage.setItem('cookies_aceptadas', 'true');
                setMostrarCookies(false);
              }}
              style={{
                flex: 1,
                padding: '10px',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: '#037623',
                color: 'white',
                fontWeight: '800',
                cursor: 'pointer'
              }}
            >
              ACEPTAR TODO
            </button>
            <button
              onClick={() => setSeccionActual('cookies')}
              style={{
                padding: '10px',
                borderRadius: '10px',
                border: '1px solid #555',
                backgroundColor: 'transparent',
                color: 'white',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              INFO
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;