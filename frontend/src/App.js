import React, { useState, useEffect, useRef } from 'react';
import { supabase } from './supabaseClient';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import SyncHeader from './components/SyncHeader';
import StoreSelector from './components/StoreSelector';
import SuperCard from './components/SuperCard';
import Sidebar from './components/Sidebar';
import listaSupers from './components/LogosSuper';
import Privacidad from './components/Privacidad';
import Landing from './components/Landing';
import Terminos from './components/Terminos';
import Cookies from './components/Cookies';
import ListaColaborativa from './components/ListaColaborativa';
import Cestita from './components/Cestita';
import ModalUpgrade from './components/ModalUpgrade';
import { usePlan } from './hooks/usePlan';

const App = () => {
  // Estados
  const [session, setSession] = useState(null);
  const [syncActiva, setSyncActiva] = useState(() => JSON.parse(localStorage.getItem('sync_pref')) ?? true);
  const [db, setDb] = useState({});
  const [precios, setPrecios] = useState({});
  const [nombresReales, setNombresReales] = useState({});
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
  const [supersActivos, setSupersActivos] = useState(["Mercadona", "DIA", "Alcampo"]);
  const [modalUpgrade, setModalUpgrade] = useState(null);
  const { plan, cargando: planCargando, puedeUsar, limiteSupers, limiteProductos } = usePlan(session);
  console.log('PLAN DEBUG:', plan, '| limProd:', limiteProductos(), '| limSup:', limiteSupers());

  // Recortar cesta si supera el límite del plan al cargar
  useEffect(() => {
    if (!planCargando && seleccionados.length > limiteProductos()) {
      const recortados = seleccionados.slice(0, limiteProductos());
      setSeleccionados(recortados);
    }
  }, [planCargando]);

  const setSupersActivosConLimite = (nuevosSups) => {
    if (nuevosSups.length > limiteSupers()) {
      setModalUpgrade({ funcionalidad: 'maxSupers', planRequerido: 'basic' });
      return;
    }
    setSupersActivos(nuevosSups);
  };
  const [referencias, setReferencias] = useState({});
  const [acordeon, setAcordeon] = useState(null);
  const [busqueda, setBusqueda] = useState("");
  const [modoTienda, setModoTienda] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [estadoSync, setEstadoSync] = useState('idle');
  const [seccionActual, setSeccionActual] = useState('comparador');
  const [mostrarCookies, setMostrarCookies] = useState(() => !localStorage.getItem('cookies_aceptadas'));
  const [mostrarLanding, setMostrarLanding] = useState(() => !localStorage.getItem('landing_vista'));
  const [mostrarColaborativa, setMostrarColaborativa] = useState(false);
  const [escaneando, setEscaneando] = useState(false);
  const fileInputRef = useRef(null);
  
  // Estados responsive
  const [sidebarAbierto, setSidebarAbierto] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1024);

  // ============================================================================
  // ✅ CAMBIO PRINCIPAL: Cargar datos de NUEVAS TABLAS
  // ============================================================================
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
    
    const cargarDatos = async () => {
      try {
        // ── Cargar catálogo para el SIDEBAR ───────────────────────────────
        const { data: catalogo, error: errCat } = await supabase
          .from('vista_productos')
          .select('id, nombre_generico, categoria, subcategoria')
          .range(0, 10000);

        if (errCat) console.error('❌ Error catálogo:', errCat);

        // ── Cargar tipo de productos_catalogo (marca_fabricante / marca_blanca) ──
        const { data: tiposCat } = await supabase
          .from('productos_catalogo')
          .select('id, tipo')
          .range(0, 10000);
        const idxTipo = {};
        (tiposCat || []).forEach(p => { if (p.tipo) idxTipo[p.id] = p.tipo; });

        // ── Cargar matches + precios Mercadona ────────────────────────────
        const { data: matches, error: errMatch } = await supabase
          .from('productos_match')
          .select('id_catalogo, id_mercadona, id_dia, id_alcampo')
          .range(0, 10000);

        if (errMatch) console.error('❌ Error matches:', errMatch);

        const { data: preciosMerc, error: errMerc } = await supabase
          .from('precios_mercadona')
          .select('id, precio, precio_unidad, nombre_comercial, reference_price, reference_format')
          .range(0, 10000);

        if (errMerc) console.error('❌ Error precios Mercadona:', errMerc);

        const { data: preciosDia, error: errDia } = await supabase
          .from('precios_dia')
          .select('id, precio, precio_unidad, nombre_comercial')
          .range(0, 10000);

        if (errDia) console.error('❌ Error precios DIA:', errDia);

        const { data: preciosAlcampo, error: errAlcampo } = await supabase
          .from('precios_alcampo')
          .select('id, precio, nombre_comercial')
          .range(0, 10000);

        if (errAlcampo) console.error('❌ Error precios Alcampo:', errAlcampo);

        if (catalogo && matches) {
          // ── Índices de precios por ID ──────────────────────────────────
          const idxMerc = {};
          const nombresMerc = {};
          const idxMercRef = {}; // reference_price por id Mercadona
          (preciosMerc || []).forEach(p => {
            if (p.precio) {
              idxMerc[p.id] = parseFloat(p.precio);
              nombresMerc[p.id] = p.nombre_comercial || null;
            }
            if (p.reference_price && p.reference_format) {
              idxMercRef[p.id] = `${parseFloat(p.reference_price).toFixed(2)}€/${p.reference_format}`;
            }
          });

          const idxDia = {};
          const nombresDia = {};
          (preciosDia || []).forEach(p => {
            if (p.precio) {
              idxDia[p.id] = parseFloat(p.precio);
              nombresDia[p.id] = p.nombre_comercial || null;
            }
          });

          const idxAlcampo = {};
          const nombresAlcampo = {};
          (preciosAlcampo || []).forEach(p => {
            if (p.precio) {
              idxAlcampo[p.id] = parseFloat(p.precio);
              nombresAlcampo[p.id] = p.nombre_comercial || null;
            }
          });

          // ── Índice match por id_catalogo ───────────────────────────────
          const idxMatch = {};
          matches.forEach(m => { idxMatch[m.id_catalogo] = m; });

          // ── Construir sidebar (db) ─────────────────────────────────────
          const dbMap = {};
          catalogo.forEach(p => {
            const cat   = p.categoria    || null;
            const subcat = p.subcategoria || 'Otros';
            // Filtrar categoría General — productos sin categoría asignada
            if (!cat || cat.toLowerCase() === 'general') return;
            if (!dbMap[cat]) dbMap[cat] = {};
            if (!dbMap[cat][subcat]) dbMap[cat][subcat] = [];
            dbMap[cat][subcat].push({
              id_producto:  String(p.id),
              nombre:       p.nombre_generico,
              categoria:    cat,
              subcategoria: subcat,
              tipo:         idxTipo[p.id] || null, // marca_fabricante | marca_blanca
            });
          });
          setDb(dbMap);

          // ── Construir mapa de precios (número simple — compatible con SuperCard) ──
          // clave: id_catalogo → { Mercadona: 0.85, DIA: 0.79 }
          const mapa = {};
          // mapa de nombres reales por super: id_catalogo → { Mercadona: "nombre", DIA: "nombre" }
          const mapaNombres = {};

          catalogo.forEach(p => {
            const m = idxMatch[p.id];
            if (!m) return;
            const precios_prod = {};
            const nombres_prod = {};
            if (m.id_mercadona && idxMerc[m.id_mercadona]) {
              precios_prod['Mercadona'] = idxMerc[m.id_mercadona];
              nombres_prod['Mercadona'] = nombresMerc[m.id_mercadona];
            }
            if (m.id_dia && idxDia[m.id_dia]) {
              precios_prod['DIA'] = idxDia[m.id_dia];
              nombres_prod['DIA'] = nombresDia[m.id_dia];
            }
            if (m.id_alcampo && idxAlcampo[m.id_alcampo]) {
              precios_prod['Alcampo'] = idxAlcampo[m.id_alcampo];
              nombres_prod['Alcampo'] = nombresAlcampo[m.id_alcampo];
            }
            if (Object.keys(precios_prod).length > 0) {
              mapa[String(p.id)] = precios_prod;
              mapaNombres[String(p.id)] = nombres_prod;
            }
          });
          setPrecios(mapa);
          // Guardar nombres reales en estado separado
          setNombresReales(mapaNombres);

          // ── Construir mapa de precios de referencia (€/L, €/kg) ────────
          const mapaRef = {};
          catalogo.forEach(p => {
            const m = idxMatch[p.id];
            if (!m) return;
            const refs = {};
            if (m.id_mercadona && idxMercRef[m.id_mercadona]) {
              refs['Mercadona'] = idxMercRef[m.id_mercadona];
            }
            if (Object.keys(refs).length > 0) {
              mapaRef[String(p.id)] = refs;
            }
          });
          setReferencias(mapaRef);

          console.log('✅ Catálogo:', catalogo.length, '| Matches:', matches.length,
            '| Con precios:', Object.keys(mapa).length);
        }
      } catch (err) {
        console.error('❌ Error general:', err);
      } finally {
        setCargando(false);
      }
    };

    cargarDatos();

    return () => subscription.unsubscribe();
  }, []);

  // Detectar cambios de tamaño
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      if (!mobile) setSidebarAbierto(false);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Guardar en localStorage
  useEffect(() => {
    localStorage.setItem('miCesta_v7', JSON.stringify(seleccionados));
    localStorage.setItem('misCestas_v7', JSON.stringify(cestasGuardadas));
    localStorage.setItem('sync_pref', JSON.stringify(syncActiva));
  }, [seleccionados, cestasGuardadas, syncActiva]);

  // Funciones
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
    const estaEnCesta = seleccionados.includes(id);
    if (!estaEnCesta && seleccionados.length >= limiteProductos()) {
      setModalUpgrade({ funcionalidad: 'maxProductos', planRequerido: 'basic' });
      return;
    }
    const nvas = estaEnCesta ? seleccionados.filter(x => x !== id) : [...seleccionados, id];
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

  // Helper: precio numérico (precios sigue siendo número directo)
  const getPrecio = (id, super_) => precios[id]?.[super_] || 0;

  // Exportar PDF limpio solo con la cesta
  const exportarPDF = () => {
    if (seleccionados.length === 0) {
      alert('Añade productos a tu cesta antes de exportar.');
      return;
    }

    const fecha = new Date().toLocaleDateString('es-ES');

    // Construir filas por supermercado
    const supersConDatos = supersActivos.filter(s =>
      seleccionados.some(id => (precios[id]?.[s] || 0) > 0)
    );

    const tablasHTML = supersConDatos.map(s => {
      const filas = seleccionados.map(id => {
        const prod = getProdFull(id);
        if (!prod) return '';
        const nombre = (getNombreReal && getNombreReal(id, s)) || prod.nombre;
        const precio = precios[id]?.[s] || 0;
        // Marca precio mínimo en verde
        const preciosValidos = supersActivos.map(x => precios[id]?.[x] || 0).filter(p => p > 0);
        const esMinimo = precio > 0 && precio === Math.min(...preciosValidos);
        return `<tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;font-size:13px;">${nombre}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:900;font-size:13px;color:${esMinimo ? '#037623' : '#102215'}">
            ${precio > 0 ? precio.toFixed(2) + '€' : '—'}
          </td>
        </tr>`;
      }).join('');

      const total = seleccionados.reduce((acc, id) => acc + (precios[id]?.[s] || 0), 0);

      return `
        <div style="margin-bottom:32px;break-inside:avoid;">
          <div style="background:#037623;color:white;padding:12px 16px;border-radius:10px 10px 0 0;font-weight:900;font-size:15px;">${s}</div>
          <table style="width:100%;border-collapse:collapse;background:white;border:1px solid #e8f0e9;border-top:none;">
            ${filas}
            <tr style="background:#f4faf6;">
              <td style="padding:10px 12px;font-weight:900;font-size:13px;">TOTAL EN ${s.toUpperCase()}</td>
              <td style="padding:10px 12px;text-align:right;font-weight:900;font-size:16px;color:#037623;">${total.toFixed(2)}€</td>
            </tr>
          </table>
        </div>`;
    }).join('');

    const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>Mi Mejor Cesta — ${fecha}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; background: #f4f7f5; color: #102215; }
    @media print { body { background: white; padding: 0; } }
  </style>
</head>
<body>
  <div style="text-align:center;margin-bottom:28px;padding-bottom:20px;border-bottom:2px solid #037623;">
    <h1 style="color:#037623;font-size:28px;font-weight:900;margin:0;">🛒 MI MEJOR CESTA</h1>
    <p style="color:#666;font-size:13px;margin:6px 0 0;">${fecha} · ${seleccionados.length} productos</p>
  </div>

  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:28px;">
    <div style="background:#037623;color:white;padding:16px 20px;border-radius:12px;">
      <div style="font-size:11px;font-weight:700;opacity:0.8;margin-bottom:4px;">MI MEJOR CESTA</div>
      <div style="font-size:26px;font-weight:900;">${stats.multi.toFixed(2)}€</div>
      <div style="font-size:11px;opacity:0.8;">comprando en el más barato</div>
    </div>
    <div style="background:#102215;color:white;padding:16px 20px;border-radius:12px;">
      <div style="font-size:11px;font-weight:700;color:#13ec49;margin-bottom:4px;">ESTÁS AHORRANDO</div>
      <div style="font-size:26px;font-weight:900;color:#13ec49;">${stats.ahorro.toFixed(2)}€</div>
      <div style="font-size:11px;opacity:0.8;">respecto al más caro</div>
    </div>
  </div>

  ${tablasHTML}

  <p style="text-align:center;font-size:11px;color:#999;margin-top:24px;">
    Generado por mimejorcesta.vercel.app · Los precios pueden variar
  </p>
</body>
</html>`;

    const ventana = window.open('', '_blank');
    ventana.document.write(html);
    ventana.document.close();
    ventana.onload = () => ventana.print();
  };

  // Helper: nombre real del super para un producto
  const getNombreReal = (id, super_) => nombresReales[id]?.[super_] || null;

  // Cálculos
  const stats = (() => {
    const totalesPorSuper = supersActivos.map(s => {
      const total = seleccionados.reduce((acc, id) => {
        const precio = precios[id]?.[s] || 0;
        return acc + (precio > 0 ? precio : 0);
      }, 0);
      const productosDisponibles = seleccionados.filter(id =>
        (precios[id]?.[s] || 0) > 0
      ).length;
      return { id: s, t: total, productosDisponibles };
    }).sort((a, b) => a.t - b.t);

    let multiTotal = 0;
    let productosSinPrecio = 0;
    seleccionados.forEach(id => {
      const preciosValidos = supersActivos
        .map(s => precios[id]?.[s] || 0)
        .filter(p => p > 0);
      if (preciosValidos.length > 0) {
        multiTotal += Math.min(...preciosValidos);
      } else {
        productosSinPrecio++;
      }
    });

    const ahorro = totalesPorSuper.length > 0 && totalesPorSuper[totalesPorSuper.length - 1].t > 0
      ? totalesPorSuper[totalesPorSuper.length - 1].t - multiTotal
      : 0;
    
    return { 
      totalesPorSuper, 
      multi: multiTotal,
      ahorro: ahorro || 0,
      productosSinPrecio
    };
  })();

  const RenderModoTienda = () => {
    const prods = seleccionados
      .map(id => {
        const p = getProdFull(id);
        if (!p) return null;
        const precioVal = precios[id]?.[modoTienda] || 0;
        const nombreReal = getNombreReal(id, modoTienda);
        if (!precioVal || precioVal <= 0) return null;
        return { ...p, precio: precioVal, nombreReal };
      })
      .filter(Boolean)
      .sort((a, b) => (b.precio || 0) - (a.precio || 0));

    return (
      <div style={{ 
        gridColumn: '1/-1', 
        maxWidth: '600px', 
        margin: '0 auto',
        background: 'white',
        borderRadius: '20px',
        padding: '30px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.08)'
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          marginBottom: '25px'
        }}>
          <h2 style={{ margin: 0, fontSize: '22px', fontWeight: '900' }}>
            🛒 Lista para {modoTienda}
          </h2>
          <button
            onClick={() => setModoTienda(null)}
            style={{
              background: '#037623',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              padding: '10px 20px',
              fontWeight: '800',
              cursor: 'pointer'
            }}
          >
            ← Volver
          </button>
        </div>
        
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '15px' 
        }}>
          {prods.map(p => (
            <div 
              key={p.id_producto}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '15px',
                padding: '15px',
                background: comprados.includes(p.id_producto) ? '#e8f5e9' : '#f9f9f9',
                borderRadius: '15px',
                border: comprados.includes(p.id_producto) ? '2px solid #037623' : '2px solid transparent',
                transition: 'all 0.2s ease'
              }}
            >
              <input
                type="checkbox"
                checked={comprados.includes(p.id_producto)}
                onChange={() => handleCheckTienda(p.id_producto)}
                style={{ width: '20px', height: '20px' }}
              />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: '700', fontSize: '16px' }}>
                  {p.nombreReal || p.nombre}
                </div>
                {p.nombreReal && p.nombreReal !== p.nombre && (
                  <div style={{ fontSize: '11px', color: '#999' }}>{p.nombre}</div>
                )}
                <div style={{ fontSize: '13px', color: '#666' }}>
                  {p.categoria} · {p.subcategoria}
                </div>
              </div>
              <div style={{ fontWeight: '900', fontSize: '18px', color: '#037623' }}>
                {(p.precio || 0).toFixed(2)}€
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const RenderPrivacidad = () => <Privacidad />;
  const RenderTerminos = () => <Terminos />;
  const RenderCookies = () => <Cookies />;

  if (cargando) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f4f7f5' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>🛒</div>
          <div style={{ fontSize: '18px', fontWeight: '800', color: '#037623' }}>Cargando productos...</div>
        </div>
      </div>
    );
  }

  if (mostrarLanding) {
    return (
      <Landing onEntrar={() => {
        localStorage.setItem('landing_vista', '1');
        setMostrarLanding(false);
      }} />
    );
  }

  return (
    <div style={{ background: '#f4f7f5', minHeight: '100vh', overflowX: 'hidden', width: '100%', boxSizing: 'border-box' }}>
      <SyncHeader 
        session={session}
        syncActiva={syncActiva}
        setSyncActiva={setSyncActiva}
        estadoSync={estadoSync}
      />
      <Navbar />

      {isMobile && (
        <button
          onClick={() => setSidebarAbierto(!sidebarAbierto)}
          style={{
            position: 'fixed',
            top: '80px',
            left: '20px',
            zIndex: 1001,
            background: '#037623',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            padding: '12px 16px',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            fontWeight: '800',
            fontSize: '16px'
          }}
        >
          {sidebarAbierto ? '✕ Cerrar' : `☰ Mi Cesta (${seleccionados.length})`}
        </button>
      )}

      {isMobile && sidebarAbierto && (
        <div
          onClick={() => setSidebarAbierto(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 999
          }}
        />
      )}

      <div style={{ padding: isMobile ? '12px' : '30px', boxSizing: 'border-box' }}>
        {seccionActual === 'comparador' && !modoTienda && (
          <StoreSelector 
            listaSupers={listaSupers} 
            supersActivos={supersActivos} 
            setSupersActivos={setSupersActivosConLimite}
            planActual={plan} 
          />
        )}

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: isMobile ? '1fr' : '400px 1fr', 
          gap: '30px',
          position: 'relative',
          alignItems: 'start'
        }}>
          <div style={{
            position: isMobile ? 'fixed' : 'sticky',
            top: isMobile ? 0 : '20px',
            left: isMobile ? (sidebarAbierto ? 0 : '-100%') : 'auto',
            width: isMobile ? '85%' : '400px',
            maxWidth: isMobile ? '400px' : 'none',
            height: isMobile ? '100vh' : 'calc(100vh - 40px)',
            maxHeight: isMobile ? '100vh' : 'calc(100vh - 40px)',
            background: '#f4f7f5',
            zIndex: 1000,
            transition: 'left 0.3s ease',
            overflowY: 'auto',
            padding: isMobile ? '20px' : '0',
            paddingTop: isMobile ? '80px' : '0'
          }}>
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
              exportarPDF={exportarPDF}
              onCompartir={() => setMostrarColaborativa(true)}
              plan={plan}
              onUpgrade={(f, p) => setModalUpgrade({ funcionalidad: f, planRequerido: p || 'basic' })}
            />
          </div>

          <main style={{ 
            display: 'grid', 
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(350px, 1fr))', 
            gap: '25px', 
            alignItems: 'start',
            minWidth: 0
          }}>
            {modoTienda ? <RenderModoTienda /> : (
              <>
                {seccionActual === 'comparador' && supersActivos.map(sId => (
                  <SuperCard 
                    key={sId} 
                    sId={sId} 
                    logo={listaSupers.find(x => x.id === sId).logo} 
                    seleccionados={seleccionados} 
                    precios={precios}
                    referencias={referencias}
                    getPrecio={getPrecio}
                    getNombreReal={getNombreReal}
                    supersActivos={supersActivos} 
                    getProdFull={getProdFull} 
                    setModoTienda={setModoTienda}
                    toggleProd={toggleProd}
                  />
                ))}
                {seccionActual === 'privacidad' && <RenderPrivacidad />}
                {seccionActual === 'terminos' && <RenderTerminos />}
                {seccionActual === 'cookies' && <RenderCookies />}
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
          </main>
        </div>
      </div>
      
      <Footer setSeccionActual={setSeccionActual} />

      {modalUpgrade && (
        <ModalUpgrade
          funcionalidad={modalUpgrade.funcionalidad}
          planRequerido={modalUpgrade.planRequerido}
          onCerrar={() => setModalUpgrade(null)}
        />
      )}

      <Cestita
        seleccionados={seleccionados}
        precios={precios}
        supersActivos={supersActivos}
        getProdFull={getProdFull}
        session={session}
      />

      {mostrarColaborativa && (
        <ListaColaborativa
          session={session}
          seleccionados={seleccionados}
          setSeleccionados={setSeleccionados}
          comprados={comprados}
          setComprados={setComprados}
          onClose={() => setMostrarColaborativa(false)}
        />
      )}

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
