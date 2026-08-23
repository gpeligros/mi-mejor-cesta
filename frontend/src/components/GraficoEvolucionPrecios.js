import React from 'react';

// Gráfico de evolución de precios (P0 #1, plan Premium — 23/08/2026).
// Componente autocontenido: dibuja un SVG a mano, sin librería de
// gráficos nueva (no había ninguna instalada y esta sesión no puede
// verificar un `npm install`). Recibe los datos ya calculados — no
// consulta Supabase él mismo, eso lo hace quien lo usa (ver
// cargarEvolucionPrecio() en SuperCard.js).
//
// ⚠️ Sin probar contra datos reales: la tabla `historico_precios` se creó
// hoy mismo y todavía no tiene filas en producción (falta ejecutar
// historico_precios.sql y que los scrapers vuelvan a correr). Probar en
// cuanto haya un producto con varios días de histórico real.

const COLOR_SUPER = {
  mercadona: '#00A650',
  dia:       '#E30613',
  alcampo:   '#004B93',
  ahorramas: '#EE7203',
  carrefour: '#004E9E',
};
const COLOR_DEFECTO = '#666';
const NOMBRE_SUPER = {
  mercadona: 'Mercadona',
  dia:       'DIA',
  alcampo:   'Alcampo',
  ahorramas: 'AhorraMas',
  carrefour: 'Carrefour',
};

const ANCHO = 560;
const ALTO = 260;
const MARGEN = { top: 20, right: 16, bottom: 32, left: 48 };

const formatoFecha = (iso) => {
  const [, mes, dia] = (iso || '').split('-');
  return mes && dia ? `${dia}/${mes}` : iso;
};

const GraficoEvolucionPrecios = ({ datos, nombreProducto, onCerrar }) => {
  // datos: [{ fecha: 'YYYY-MM-DD', precio: number, super: 'mercadona'|... }, ...]
  const porSuper = {};
  (datos || []).forEach(d => {
    if (!d || !d.fecha || d.precio == null) return;
    if (!porSuper[d.super]) porSuper[d.super] = [];
    porSuper[d.super].push(d);
  });
  Object.values(porSuper).forEach(arr => arr.sort((a, b) => a.fecha.localeCompare(b.fecha)));

  const supers = Object.keys(porSuper);
  const todosPuntos = supers.flatMap(s => porSuper[s]);
  const hayDatos = todosPuntos.length > 0;

  let contenidoGrafico;
  if (!hayDatos) {
    contenidoGrafico = (
      <div style={{ padding: '40px 20px', textAlign: 'center', color: '#999', fontSize: '13px' }}>
        Todavía no hay histórico de precios para este producto.
        <br />Vuelve a mirar en unos días.
      </div>
    );
  } else {
    const fechas = [...new Set(todosPuntos.map(d => d.fecha))].sort();
    const precios = todosPuntos.map(d => d.precio);
    const precioMin = Math.min(...precios);
    const precioMax = Math.max(...precios);
    // Margen visual para que las líneas no toquen los bordes
    const rango = precioMax - precioMin || 1;
    const yMin = Math.max(0, precioMin - rango * 0.1);
    const yMax = precioMax + rango * 0.1;

    const anchoUtil = ANCHO - MARGEN.left - MARGEN.right;
    const altoUtil = ALTO - MARGEN.top - MARGEN.bottom;

    const x = (fecha) => {
      const idx = fechas.indexOf(fecha);
      const total = Math.max(fechas.length - 1, 1);
      return MARGEN.left + (idx / total) * anchoUtil;
    };
    const y = (precio) => MARGEN.top + altoUtil - ((precio - yMin) / (yMax - yMin)) * altoUtil;

    // Mostrar como mucho ~6 etiquetas de fecha en el eje X para no amontonarlas
    const paso = Math.max(1, Math.ceil(fechas.length / 6));
    const fechasEtiquetadas = fechas.filter((_, i) => i % paso === 0 || i === fechas.length - 1);

    contenidoGrafico = (
      <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} style={{ width: '100%', height: 'auto' }}>
        {/* líneas guía horizontales */}
        {[0, 0.5, 1].map(frac => {
          const yy = MARGEN.top + altoUtil * frac;
          const precioEtiqueta = yMax - (yMax - yMin) * frac;
          return (
            <g key={frac}>
              <line x1={MARGEN.left} x2={ANCHO - MARGEN.right} y1={yy} y2={yy} stroke="#eee" strokeWidth="1" />
              <text x={MARGEN.left - 6} y={yy + 4} fontSize="10" fill="#999" textAnchor="end">
                {precioEtiqueta.toFixed(2)}€
              </text>
            </g>
          );
        })}

        {/* eje X: fechas */}
        {fechasEtiquetadas.map(f => (
          <text key={f} x={x(f)} y={ALTO - 10} fontSize="10" fill="#999" textAnchor="middle">
            {formatoFecha(f)}
          </text>
        ))}

        {/* una línea + puntos por supermercado */}
        {supers.map(s => {
          const puntos = porSuper[s];
          if (puntos.length === 0) return null;
          const color = COLOR_SUPER[s] || COLOR_DEFECTO;
          const puntosStr = puntos.map(p => `${x(p.fecha)},${y(p.precio)}`).join(' ');
          return (
            <g key={s}>
              {puntos.length > 1 && (
                <polyline points={puntosStr} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" />
              )}
              {puntos.map((p, i) => (
                <circle key={i} cx={x(p.fecha)} cy={y(p.precio)} r="3.5" fill={color} />
              ))}
            </g>
          );
        })}
      </svg>
    );
  }

  return (
    <div
      onClick={onCerrar}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'white',
          borderRadius: '20px',
          padding: '24px',
          maxWidth: '600px',
          width: '100%',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: '900', color: '#102215' }}>📈 Evolución de precio</h3>
            {nombreProducto && (
              <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#666' }}>{nombreProducto}</p>
            )}
          </div>
          <button onClick={onCerrar} style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: '#999', lineHeight: 1 }}>×</button>
        </div>

        {contenidoGrafico}

        {supers.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '12px', justifyContent: 'center' }}>
            {supers.map(s => (
              <div key={s} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#444' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: COLOR_SUPER[s] || COLOR_DEFECTO, display: 'inline-block' }} />
                {NOMBRE_SUPER[s] || s}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default GraficoEvolucionPrecios;
