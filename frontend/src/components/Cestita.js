import React, { useState } from 'react';

const Cestita = ({ seleccionados, precios, supersActivos, getProdFull, session }) => {
  const [abierto, setAbierto] = useState(false);

  return (
    <div style={{ position: 'fixed', bottom: 0, right: 0, zIndex: 99999 }}>
      <button
        onClick={() => setAbierto(!abierto)}
        style={{
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: '#037623',
          color: 'white',
          border: '3px solid red',
          cursor: 'pointer',
          fontSize: '26px',
          margin: '24px',
          display: 'block',
        }}
      >
        🛒
      </button>
      {abierto && (
        <div style={{
          position: 'fixed',
          bottom: '100px',
          right: '24px',
          width: '300px',
          height: '400px',
          background: 'white',
          border: '3px solid #037623',
          borderRadius: '20px',
          zIndex: 99999,
          padding: '20px',
          boxSizing: 'border-box',
        }}>
          <h3 style={{ color: '#037623', margin: 0 }}>🛒 CESTITA</h3>
          <p style={{ fontSize: '13px', color: '#666' }}>
            Productos en cesta: {seleccionados?.length || 0}
          </p>
          <p style={{ fontSize: '12px', color: '#999' }}>
            (versión debug — IA pendiente de créditos)
          </p>
        </div>
      )}
    </div>
  );
};

export default Cestita;
