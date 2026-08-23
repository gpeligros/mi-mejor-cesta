import React from 'react';
import { supabase } from '../supabaseClient';

// Alertas de precio (P0 #1, plan Básico — 23/08/2026), versión 1: solo
// dentro de la app (sin email ni notificaciones push todavía — eso es una
// decisión de infraestructura aparte, ver CONTEXTO.md sección 12).
//
// Compara, para cada producto de la cesta actual, los dos precios más
// recientes en `historico_precios` (por supermercado) y avisa si alguno
// ha subido o bajado desde la última vez que se detectó un cambio.
//
// ⚠️ Sin probar contra datos reales: `historico_precios` se creó hoy mismo
// y no tiene filas en producción todavía (falta ejecutar el SQL y que los
// scrapers vuelvan a correr). Hasta entonces este panel mostrará "Sin
// cambios de precio detectados todavía" para cualquier cesta.

const AlertasPrecio = ({ seleccionados, getProdFull, plan, onUpgrade, session }) => {
  const [abierto, setAbierto] = React.useState(false);
  const [cargando, setCargando] = React.useState(false);
  const [cambios, setCambios] = React.useState(null); // null = no cargado todavía

  const esPlanBasic = plan === 'basic' || plan === 'premium';

  const cargarCambios = async () => {
    if (!seleccionados || seleccionados.length === 0) {
      setCambios([]);
      return;
    }
    setCargando(true);
    try {
      const { data: matches, error: errMatch } = await supabase
        .from('productos_match')
        .select('id_catalogo, id_mercadona, id_dia, id_alcampo, id_ahorramas, id_carrefour')
        .in('id_catalogo', seleccionados);
      if (errMatch) throw errMatch;

      const idASuper = {}; // id_producto_super -> id_catalogo
      (matches || []).forEach(m => {
        ['id_mercadona', 'id_dia', 'id_alcampo', 'id_ahorramas', 'id_carrefour'].forEach(campo => {
          if (m[campo]) idASuper[m[campo]] = m.id_catalogo;
        });
      });
      const todosLosIds = Object.keys(idASuper);
      if (todosLosIds.length === 0) {
        setCambios([]);
        return;
      }

      const { data: historico, error: errHist } = await supabase
        .from('historico_precios')
        .select('id_producto_super, super, precio, fecha')
        .in('id_producto_super', todosLosIds)
        .order('fecha', { ascending: false });
      if (errHist) throw errHist;

      // Para cada (id_producto_super), los dos registros más recientes ya
      // vienen ordenados por fecha descendente — comparamos el 1º con el 2º.
      const porId = {};
      (historico || []).forEach(row => {
        if (!porId[row.id_producto_super]) porId[row.id_producto_super] = [];
        if (porId[row.id_producto_super].length < 2) porId[row.id_producto_super].push(row);
      });

      const detectados = [];
      Object.entries(porId).forEach(([idProdSuper, filas]) => {
        if (filas.length < 2) return; // solo un precio registrado = nada que comparar
        const [reciente, anterior] = filas;
        if (reciente.precio === anterior.precio) return;
        const idCatalogo = idASuper[idProdSuper];
        const producto = getProdFull ? getProdFull(idCatalogo) : null;
        detectados.push({
          idCatalogo,
          nombre: producto?.nombre || idProdSuper,
          super: reciente.super,
          precioAnterior: anterior.precio,
          precioNuevo: reciente.precio,
          bajada: reciente.precio < anterior.precio,
          fecha: reciente.fecha,
        });
      });

      setCambios(detectados);
    } catch (e) {
      console.error('Error cargando alertas de precio:', e);
      setCambios([]);
    } finally {
      setCargando(false);
    }
  };

  const alAbrir = () => {
    if (!esPlanBasic) {
      if (onUpgrade) onUpgrade('alertasPrecio', 'basic');
      return;
    }
    const nuevoEstado = !abierto;
    setAbierto(nuevoEstado);
    if (nuevoEstado && cambios === null) cargarCambios();
  };

  if (!session) return null; // alertas solo tiene sentido con sesión iniciada

  const bajadas = (cambios || []).filter(c => c.bajada).length;
  const subidas = (cambios || []).filter(c => !c.bajada).length;

  return (
    <div style={{ marginBottom: '20px' }}>
      <button
        onClick={alAbrir}
        style={{
          width: '100%',
          background: 'white',
          border: '1px solid #e0e6e1',
          borderRadius: '16px',
          padding: '12px 16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          fontSize: '13px',
          fontWeight: '900',
          color: '#102215',
        }}
      >
        <span>🔔 Alertas de precio{cambios && cambios.length > 0 ? ` (${cambios.length})` : ''}</span>
        <span style={{ fontSize: '11px', color: '#999' }}>{abierto ? '▲' : '▼'}</span>
      </button>

      {abierto && esPlanBasic && (
        <div style={{ background: 'white', border: '1px solid #e0e6e1', borderTop: 'none', borderRadius: '0 0 16px 16px', padding: '12px 16px' }}>
          {cargando && <div style={{ fontSize: '12px', color: '#999' }}>Comprobando cambios de precio...</div>}
          {!cargando && cambios && cambios.length === 0 && (
            <div style={{ fontSize: '12px', color: '#999' }}>Sin cambios de precio detectados todavía.</div>
          )}
          {!cargando && cambios && cambios.length > 0 && (
            <>
              <div style={{ fontSize: '11px', color: '#666', marginBottom: '8px' }}>
                {bajadas > 0 && <span style={{ color: '#037623', fontWeight: '700' }}>↓ {bajadas} bajada(s)</span>}
                {bajadas > 0 && subidas > 0 && '  ·  '}
                {subidas > 0 && <span style={{ color: '#b8321d', fontWeight: '700' }}>↑ {subidas} subida(s)</span>}
              </div>
              {cambios.map((c, i) => (
                <div key={i} style={{ fontSize: '12px', padding: '6px 0', borderTop: i > 0 ? '1px solid #f4f4f4' : 'none' }}>
                  <div style={{ fontWeight: '700', color: '#102215' }}>{c.nombre}</div>
                  <div style={{ color: c.bajada ? '#037623' : '#b8321d' }}>
                    {c.bajada ? '↓' : '↑'} {c.precioAnterior.toFixed(2)}€ → {c.precioNuevo.toFixed(2)}€ en {c.super}
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default AlertasPrecio;
