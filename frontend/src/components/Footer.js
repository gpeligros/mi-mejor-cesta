import React from 'react';

const Footer = ({ setSeccionActual }) => {
  return (
    <footer 
      className="no-print" 
      style={{ 
        background: '#102215', 
        color: 'white', 
        padding: '40px 20px', 
        textAlign: 'center', 
        marginTop: '50px' 
      }}
    >
      <h2 style={{ 
        marginBottom: '10px', 
        fontWeight: '900',
        fontSize: 'clamp(18px, 4vw, 24px)'
      }}>
        MI MEJOR CESTA
      </h2>
      
      <p style={{ 
        fontSize: 'clamp(12px, 3vw, 14px)', 
        opacity: 0.8, 
        maxWidth: '600px', 
        margin: '0 auto 30px',
        padding: '0 20px'
      }}>
        Tu comparador de confianza para el ahorro diario. Analizamos los precios de los principales 
        supermercados para que siempre pagues lo mínimo.
      </p>

      {/* Navegación Principal */}
      <div style={{ 
        display: 'flex', 
        gap: '20px', 
        justifyContent: 'center', 
        fontSize: 'clamp(11px, 2.5vw, 13px)', 
        fontWeight: '700', 
        marginBottom: '20px',
        flexWrap: 'wrap',
        padding: '0 20px'
      }}>
        <span onClick={() => setSeccionActual('comparador')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          INICIO
        </span>
        <span onClick={() => setSeccionActual('favoritos')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          MIS LISTAS
        </span>
        <span onClick={() => setSeccionActual('ahorro')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          AHORRO
        </span>
      </div>

      {/* Enlaces Legales */}
      <div style={{ 
        display: 'flex', 
        gap: '15px', 
        justifyContent: 'center', 
        fontSize: 'clamp(9px, 2vw, 11px)', 
        opacity: 0.6, 
        borderTop: '1px solid rgba(255,255,255,0.1)', 
        paddingTop: '20px',
        flexWrap: 'wrap',
        padding: '20px 20px 0 20px'
      }}>
        <span onClick={() => setSeccionActual('privacidad')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          PRIVACIDAD
        </span>
        <span onClick={() => setSeccionActual('terminos')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          TÉRMINOS
        </span>
        <span onClick={() => setSeccionActual('cookies')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          COOKIES
        </span>
        <span onClick={() => setSeccionActual('aviso-legal')} style={{ cursor: 'pointer', whiteSpace: 'nowrap' }}>
          AVISO LEGAL
        </span>
        <span style={{ whiteSpace: 'nowrap' }}>© 2026</span>
      </div>
    </footer>
  );
};

export default Footer;