import React from 'react';

const Privacidad = () => {
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
        POLÍTICA DE PRIVACIDAD
      </h1>
      
      <p><strong>Última actualización:</strong> 16 de febrero de 2026</p>
      
      <h2>1. INFORMACIÓN GENERAL</h2>
      <p>
        <strong>Mi Mejor Cesta</strong> es un comparador de precios de supermercados. 
        Esta Política de Privacidad describe cómo recopilamos, usamos y protegemos tu información personal.
      </p>
      
      <h2>2. DATOS QUE RECOPILAMOS</h2>
      <h3>2.1 Datos que proporcionas:</h3>
      <ul>
        <li><strong>Email y contraseña</strong> (si creas una cuenta)</li>
        <li><strong>Listas de la compra</strong> (productos que seleccionas)</li>
        <li><strong>Preferencias</strong> (supermercados favoritos)</li>
      </ul>
      
      <h3>2.2 Datos que recopilamos automáticamente:</h3>
      <ul>
        <li><strong>Datos de uso</strong> (páginas visitadas, funciones usadas)</li>
        <li><strong>Datos técnicos</strong> (tipo de dispositivo, navegador)</li>
        <li><strong>Cookies</strong> (para mejorar tu experiencia)</li>
      </ul>
      
      <h2>3. CÓMO USAMOS TUS DATOS</h2>
      <ul>
        <li>✅ Proporcionar el servicio de comparación de precios</li>
        <li>✅ Guardar tus listas de la compra</li>
        <li>✅ Sincronizar tus datos entre dispositivos</li>
        <li>✅ Mejorar la aplicación</li>
      </ul>
      
      <p><strong>NO vendemos ni compartimos tus datos con terceros.</strong></p>
      
      <h2>4. DÓNDE ALMACENAMOS TUS DATOS</h2>
      <ul>
        <li><strong>localStorage:</strong> Tus listas se guardan en tu dispositivo</li>
        <li><strong>Supabase (EU):</strong> Si creas cuenta, datos en servidores europeos cifrados</li>
      </ul>
      
      <h2>5. TUS DERECHOS (RGPD)</h2>
      <ul>
        <li>✅ Acceder a tus datos</li>
        <li>✅ Rectificar datos incorrectos</li>
        <li>✅ Eliminar tu cuenta y datos</li>
        <li>✅ Descargar tus datos</li>
      </ul>
      
      <p>Para ejercer estos derechos, contacta: <strong>[TU_EMAIL]</strong></p>
      
      <h2>6. SEGURIDAD</h2>
      <ul>
        <li>🔒 Conexiones HTTPS cifradas</li>
        <li>🔒 Autenticación segura</li>
        <li>🔒 Contraseñas hasheadas</li>
      </ul>
      
      <h2>7. CONTACTO</h2>
      <p>
        Para cualquier duda sobre esta Política:<br/>
        <strong>Email:</strong> [info@mimejorcesta.com]<br/>
        <strong>Web:</strong> [https://mimejorcesta.com]
      </p>
      
      <p style={{ marginTop: '40px', fontSize: '12px', color: '#666' }}>
        <strong>Última actualización:</strong> 16 de febrero de 2026
      </p>
    </div>
  );
};

export default Privacidad;