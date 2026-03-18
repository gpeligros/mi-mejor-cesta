import React from 'react';

const Terminos = () => {
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
        TÉRMINOS Y CONDICIONES DE USO
      </h1>
      
      <p><strong>Última actualización:</strong> 16 de febrero de 2026</p>
      
      <h2>1. ACEPTACIÓN</h2>
      <p>
        Al usar <strong>Mi Mejor Cesta</strong>, aceptas estos Términos y Condiciones.
      </p>
      
      <h2>2. DESCRIPCIÓN DEL SERVICIO</h2>
      <p>Mi Mejor Cesta es un comparador de precios que te permite:</p>
      <ul>
        <li>✅ Comparar precios entre supermercados</li>
        <li>✅ Crear listas de la compra</li>
        <li>✅ Calcular ahorro potencial</li>
      </ul>
      
      <h2>3. USO PERMITIDO</h2>
      <ul>
        <li>✅ Uso personal y doméstico</li>
        <li>✅ Comparar precios para tu compra</li>
        <li>✅ Guardar y compartir listas</li>
      </ul>
      
      <h2>4. USO NO PERMITIDO</h2>
      <ul>
        <li>❌ Uso comercial sin autorización</li>
        <li>❌ Scraping o extracción masiva de datos</li>
        <li>❌ Intentar hackear la seguridad</li>
      </ul>
      
      <h2>5. PRECIOS Y DISPONIBILIDAD</h2>
      <p>
        Los precios mostrados son <strong>orientativos</strong> y se actualizan periódicamente.
        Pueden existir diferencias con los precios reales en tienda.
      </p>
      
      <h2>6. PROPIEDAD INTELECTUAL</h2>
      <p>
        El diseño, código y logos son propiedad de Mi Mejor Cesta.
        No puedes copiar sin autorización.
      </p>
      
      <h2>7. CONTACTO</h2>
      <p>
        <strong>Email:</strong> [info@mimejorcesta.com]<br/>
        <strong>Web:</strong> [https://mimejorcesta.com]
      </p>
    </div>
  );
};

export default Terminos;