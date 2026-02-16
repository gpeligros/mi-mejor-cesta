import React from 'react';

const Cookies = () => {
  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '40px auto', 
      padding: '20px',
      backgroundColor: 'white',
      borderRadius: '15px',
      fontFamily: 'system-ui, sans-serif'
    }}>
      <h1 style={{ color: '#037623', fontWeight: '900' }}>
        POLÍTICA DE COOKIES
      </h1>
      
      <p><strong>Última actualización:</strong> 16 de febrero de 2026</p>
      
      <h2>¿QUÉ SON LAS COOKIES?</h2>
      <p>
        Las cookies son pequeños archivos que se almacenan en tu dispositivo 
        para recordar tus preferencias.
      </p>
      
      <h2>¿QUÉ COOKIES USAMOS?</h2>
      
      <h3>1. COOKIES ESENCIALES (Siempre activas)</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={{ padding: '10px', border: '1px solid #ddd' }}>Cookie</th>
            <th style={{ padding: '10px', border: '1px solid #ddd' }}>Propósito</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #ddd' }}><code>miCesta_v7</code></td>
            <td style={{ padding: '10px', border: '1px solid #ddd' }}>Guarda tu lista de productos</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #ddd' }}><code>misCestas_v7</code></td>
            <td style={{ padding: '10px', border: '1px solid #ddd' }}>Guarda tus listas favoritas</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #ddd' }}><code>cookies_aceptadas</code></td>
            <td style={{ padding: '10px', border: '1px solid #ddd' }}>Registra aceptación de cookies</td>
          </tr>
        </tbody>
      </table>
      
      <h3>2. COOKIES ANALÍTICAS (Opcionales)</h3>
      <p>Si aceptas, usamos Google Analytics para mejorar la app.</p>
      
      <h2>CÓMO GESTIONAR COOKIES</h2>
      <p>Puedes desactivar las cookies en tu navegador:</p>
      <ul>
        <li><strong>Chrome:</strong> Configuración → Privacidad → Cookies</li>
        <li><strong>Firefox:</strong> Opciones → Privacidad → Cookies</li>
        <li><strong>Safari:</strong> Preferencias → Privacidad</li>
      </ul>
      
      <h2>CONTACTO</h2>
      <p>
        <strong>Email:</strong> [info@mimejorcesta.com]
      </p>
    </div>
  );
};

export default Cookies;