import React from 'react';

const Navbar = () => (
  <nav style={{ 
    padding: '15px 20px', 
    backgroundColor: 'white', 
    borderBottom: '1px solid #eee', 
    fontFamily: 'system-ui, sans-serif',
    width: '100%',
    boxSizing: 'border-box',
  }}>
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '10px',
      justifyContent: 'center'
    }}>
      <svg 
        width="36" 
        height="36" 
        viewBox="0 0 24 24" 
        fill="none"
        style={{ flexShrink: 0 }}
      >
        <path d="M3 9h18l-1.5 11h-15L3 9z" stroke="#102215" strokeWidth="1.5" fill="white"/>
        <path d="M8 9V6c0-2 1.5-3.5 4-3.5s4 1.5 4 3.5v3" stroke="#102215" strokeWidth="1.5"/>
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="#ff0000" transform="translate(6.5, 11) scale(0.45)"/>
      </svg>
      <h1 style={{ 
        color: '#037623', 
        fontWeight: '900', 
        fontSize: 'clamp(18px, 5vw, 36px)', 
        margin: 0,
        whiteSpace: 'nowrap',
      }}>
        MI MEJOR CESTA
      </h1>
    </div>
    <p style={{ 
      color: '#666', 
      fontSize: 'clamp(11px, 3vw, 14px)', 
      margin: '6px 0 0 0', 
      fontWeight: '500',
      textAlign: 'center',
      padding: '0 10px',
    }}>
      Ahorra en tu compra diaria comparando todos los supermercados
    </p>
  </nav>
);

export default Navbar;
