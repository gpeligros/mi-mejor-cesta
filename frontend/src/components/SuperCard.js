import React from 'react';

const SuperCard = ({ sId, logo, seleccionados, precios, referencias, supersActivos, getProdFull, setModoTienda, getNombreReal, toggleProd, getCantidad, setCantidadProducto }) => {
  // getCantidad es opcional (por si algún consumidor viejo no lo pasa) — sin
  // él, todo se comporta como cantidad 1 siempre, igual que antes.
  const cantidadDe = (id) => (getCantidad ? getCantidad(id) : 1);

  const totalS = seleccionados.reduce((acc, id) => {
    const precio = precios[id]?.[sId];
    return acc + (precio && precio > 0 ? precio * cantidadDe(id) : 0);
  }, 0);

  // Cobertura: cuántos de los productos de la cesta tiene precio este super
  // (petición de la auditoría: "18/20 productos encontrados", ver PLAN_PRIORIZADO.md)
  const totalProductos = seleccionados.length;
  const productosDisponibles = seleccionados.filter(id => {
    const precio = precios[id]?.[sId];
    return precio && precio > 0;
  }).length;
  const coberturaCompleta = totalProductos > 0 && productosDisponibles === totalProductos;

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
          {totalProductos > 0 && (
            <span
              title="Cuántos productos de tu cesta tienen precio en este supermercado"
              style={{
                fontSize: '10px',
                fontWeight: '900',
                padding: '2px 7px',
                borderRadius: '20px',
                whiteSpace: 'nowrap',
                flexShrink: 0,
                color: coberturaCompleta ? '#037623' : '#b8860b',
                background: coberturaCompleta ? '#e8fdf0' : '#fff8e6',
              }}
            >
              {productosDisponibles}/{totalProductos}
            </span>
          )}
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
        const cantidad = cantidadDe(id);
        const subtotal = precioValido * cantidad;

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
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#102215', display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                <span>{(getNombreReal && getNombreReal(id, sId)) || producto.nombre}</span>
                {/* Marca blanca: el pipeline lo compara por tipo de producto,
                    no es literalmente la misma marca en cada supermercado
                    (ver agrupar_productos.py / PLAN_PRIORIZADO.md PRODUCT-06) */}
                {producto.tipo === 'marca_blanca' && (
                  <span
                    title="Comparamos este producto por tipo, no es la misma marca en cada supermercado (ej. marca propia de cada cadena)"
                    style={{
                      fontSize: '9px',
                      fontWeight: '900',
                      color: '#946200',
                      background: '#fff4de',
                      border: '1px solid #f0dcae',
                      borderRadius: '6px',
                      padding: '1px 6px',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    ≈ alternativa equivalente
                  </span>
                )}
              </div>
              {producto.subcategoria && (
                <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                  {producto.subcategoria}
                </div>
              )}
            </div>

            {/* Cantidad — solo si hay forma de cambiarla */}
            {setCantidadProducto && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', flexShrink: 0 }}>
                <button
                  onClick={() => setCantidadProducto(id, cantidad - 1)}
                  disabled={cantidad <= 1}
                  title="Quitar una unidad"
                  style={{ width: '20px', height: '20px', borderRadius: '6px', border: '1px solid #eee', background: 'white', color: cantidad <= 1 ? '#ddd' : '#102215', fontWeight: '900', fontSize: '11px', cursor: cantidad <= 1 ? 'not-allowed' : 'pointer', lineHeight: 1 }}
                >
                  −
                </button>
                <span style={{ minWidth: '14px', textAlign: 'center', fontWeight: '800', fontSize: '11px' }}>{cantidad}</span>
                <button
                  onClick={() => setCantidadProducto(id, cantidad + 1)}
                  title="Añadir una unidad"
                  style={{ width: '20px', height: '20px', borderRadius: '6px', border: '1px solid #eee', background: 'white', color: '#102215', fontWeight: '900', fontSize: '11px', cursor: 'pointer', lineHeight: 1 }}
                >
                  +
                </button>
              </div>
            )}

            {/* Precio + referencia */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', flexShrink: 0 }}>
              <span style={{
                fontWeight: '900',
                color: esPrecioMinimo ? '#037623' : '#102215',
                background: esPrecioMinimo ? '#e8fdf0' : 'transparent',
                padding: '4px 8px', borderRadius: '6px', fontSize: '14px',
                minWidth: '60px', textAlign: 'right',
              }}>
                {subtotal > 0 ? `${subtotal.toFixed(2)}€` : '--'}
              </span>
              {/* Precio por unidad de medida, o precio unitario si hay más de 1 */}
              {precioValido > 0 && (
                cantidad > 1
                  ? <span style={{ fontSize: '9px', color: '#aaa', marginTop: '2px', paddingRight: '8px' }}>{precioValido.toFixed(2)}€/ud</span>
                  : refPrecio && (
                    <span style={{ fontSize: '9px', color: '#aaa', marginTop: '2px', paddingRight: '8px' }}>
                      {refPrecio}
                    </span>
                  )
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
