import React from 'react';

const SuperCard = ({ sId, logo, seleccionados, precios, supersActivos, getProdFull, setModoTienda }) => {
  // Calcular total del supermercado
  const totalS = seleccionados.reduce((acc, id) => {
    const precio = precios[id]?.[sId];
    return acc + (precio && precio > 0 ? precio : 0);
  }, 0);

  return (
    <div style={{ 
      backgroundColor: 'white', 
      padding: '25px', 
      borderRadius: '30px', 
      borderTop: '8px solid #037623', 
      boxShadow: '0 10px 20px rgba(0,0,0,0.02)' 
    }}>
      {/* Header con logo y botón */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px' 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src={logo} alt={sId} style={{ height: '35px' }} />
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '900' }}>{sId}</h3>
        </div>
        <button 
          onClick={() => setModoTienda(sId)} 
          style={{ 
            background: '#e8fdf0', 
            color: '#037623', 
            border: 'none', 
            padding: '8px 12px', 
            borderRadius: '10px', 
            fontSize: '11px', 
            fontWeight: '900', 
            cursor: 'pointer' 
          }}
        >
          CONTROL LISTA →
        </button>
      </div>

      {/* Lista de productos */}
      {seleccionados.map(id => {
        // Obtener datos del producto
        const producto = getProdFull(id);
        
        // Si el producto no existe, no renderizar nada (pero mantener la key para React)
        if (!producto) {
          console.warn(`⚠️ Producto no encontrado: ${id}`);
          return null;
        }
        
        // Obtener precio de este supermercado
        const precioActual = precios[id]?.[sId];
        const precioValido = precioActual && precioActual > 0 ? precioActual : 0;
        
        // Calcular si es el precio mínimo
        // ✅ FIX: Solo comparar precios válidos (mayores a 0)
        const preciosDisponibles = supersActivos
          .map(nombreSuper => precios[id]?.[nombreSuper])
          .filter(precio => precio && precio > 0);
        
        const esPrecioMinimo = precioValido > 0 && 
                               preciosDisponibles.length > 0 && 
                               precioValido === Math.min(...preciosDisponibles);
        
        return (
          <div 
            key={`${sId}-${id}`}
            style={{ 
              padding: '10px 0', 
              borderBottom: '1px solid #f8faf9', 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            {/* Información del producto */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#102215' }}>
                {producto.nombre}
              </div>
              <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                {producto.formato}
              </div>
            </div>
            
            {/* Precio */}
            <span style={{ 
              fontWeight: '900', 
              color: esPrecioMinimo ? '#037623' : '#102215', 
              background: esPrecioMinimo ? '#e8fdf0' : 'transparent', 
              padding: '4px 8px', 
              borderRadius: '6px',
              fontSize: '14px',
              minWidth: '60px',
              textAlign: 'right'
            }}>
              {precioValido > 0 ? `${precioValido.toFixed(2)}€` : '--'}
            </span>
          </div>
        );
      })}

      {/* Total del supermercado */}
      <div style={{ marginTop: '20px', textAlign: 'right' }}>
        <div style={{ fontSize: '10px', color: '#bbb', fontWeight: '900', letterSpacing: '1px' }}>
          TOTAL EN TIENDA
        </div>
        <div style={{ fontSize: '38px', fontWeight: '900', color: '#102215', marginTop: '5px' }}>
          {totalS.toFixed(2)}€
        </div>
      </div>
    </div>
  );
};

export default SuperCard;