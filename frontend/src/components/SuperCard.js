import React from 'react';

const SuperCard = ({ sId, logo, seleccionados, precios, referencias, supersActivos, getProdFull, setModoTienda, getNombreReal, toggleProd }) => {
  const totalS = seleccionados.reduce((acc, id) => {
    const precio = precios[id]?.[sId];
    return acc + (precio && precio > 0 ? precio : 0);
  }, 0);

  return (
    <div style={{ 
      backgroundColor: 'white', 
      padding: '20px', 
      borderRadius: '30px', 
      borderTop: '8px solid #037623', 
      boxShadow: '0 10px 20px rgba(0,0,0,0.02)',
      width: '100%',
      boxSizing: 'border-box',
      minWidth: 0,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', gap: '8px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
          <img src={logo} alt={sId} style={{ height: '30px', flexShrink: 0 }} />
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '900', whiteSpace: 'nowrap' }}>{sId}</h3>
        </div>
        <button 
          onClick={() => setModoTienda(sId)} 
          style={{ background: '#e8fdf0', color: '#037623', border: 'none', padding: '6px 10px', borderRadius: '10px', fontSize: '10px', fontWeight: '900', cursor: 'pointer', whiteSpace: 'nowrap', flexShrink: 0 }}
        >
          CONTROL LISTA →
        </button>
      </div>

      {/* Lista de productos */}
      {seleccionados.map(id => {
        const producto = getProdFull(id);
        if (!producto) return null;

        const precioActual = precios[id]?.[sId];
        const precioValido = precioActual && precioActual > 0 ? precioActual : 0;

        // Precio de referencia por unidad (€/L, €/kg...) — solo Mercadona por ahora
        const refPrecio = referencias?.[id]?.[sId] || null;

        const preciosDisponibles = supersActivos
          .map(s => precios[id]?.[s])
          .filter(p => p && p > 0);

        const esPrecioMinimo = precioValido > 0 && 
                               preciosDisponibles.length > 0 && 
                               precioValido === Math.min(...preciosDisponibles);

        return (
          <div 
            key={`${sId}-${id}`}
            style={{ padding: '10px 0', borderBottom: '1px solid #f8faf9', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}
          >
            {/* Botón × para quitar producto */}
            <button
              onClick={() => toggleProd(id)}
              title="Quitar de la cesta"
              style={{
                background: 'none',
                border: 'none',
                color: '#ccc',
                fontSize: '16px',
                cursor: 'pointer',
                padding: '0 4px',
                lineHeight: 1,
                flexShrink: 0,
                transition: 'color 0.2s'
              }}
              onMouseEnter={e => e.target.style.color = '#ff4b4b'}
              onMouseLeave={e => e.target.style.color = '#ccc'}
            >
              ×
            </button>

            {/* Nombre */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#102215' }}>
                {(getNombreReal && getNombreReal(id, sId)) || producto.nombre}
              </div>
              <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                {producto.formato}
              </div>
            </div>

            {/* Precio + referencia */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0 }}>
              <span style={{ 
                fontWeight: '900', 
                color: esPrecioMinimo ? '#037623' : '#102215', 
                background: esPrecioMinimo ? '#e8fdf0' : 'transparent', 
                padding: '4px 8px', borderRadius: '6px', fontSize: '14px',
                minWidth: '60px', textAlign: 'right',
              }}>
                {precioValido > 0 ? `${precioValido.toFixed(2)}€` : '--'}
              </span>
              {/* Precio por unidad de medida */}
              {refPrecio && precioValido > 0 && (
                <span style={{ fontSize: '9px', color: '#aaa', marginTop: '2px', paddingRight: '8px' }}>
                  {refPrecio}
                </span>
              )}
            </div>
          </div>
        );
      })}

      {/* Total */}
      <div style={{ marginTop: '20px', textAlign: 'right' }}>
        <div style={{ fontSize: '10px', color: '#bbb', fontWeight: '900', letterSpacing: '1px' }}>TOTAL EN TIENDA</div>
        <div style={{ fontSize: '38px', fontWeight: '900', color: '#102215', marginTop: '5px' }}>{totalS.toFixed(2)}€</div>
      </div>
    </div>
  );
};

export default SuperCard;
