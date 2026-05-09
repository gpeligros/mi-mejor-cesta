import React from 'react';

// ----------------------------------------------------------------------
// Politica de Cookies - Mi Mejor Cesta
// Cumple Guia AEPD sobre cookies (noviembre 2023):
//  - Informacion clara antes del consentimiento.
//  - Aceptar / Rechazar igual de faciles.
//  - No carga cookies analiticas hasta que el usuario consiente.
//  - Posibilidad de retirar el consentimiento en cualquier momento.
// Placeholders: [TITULAR], [EMAIL]
// ----------------------------------------------------------------------

const Cookies = () => {
  const restablecerConsentimiento = () => {
    try {
      localStorage.removeItem('cookies_consent_v2');
      localStorage.removeItem('cookies_aceptadas');
    } catch (e) {}
    try {
      window.dispatchEvent(new CustomEvent('cookies:open-banner'));
    } catch (e) {}
  };

  return (
    <div style={{
      maxWidth: '800px',
      margin: '40px auto',
      padding: '24px',
      backgroundColor: 'white',
      borderRadius: '15px',
      fontFamily: 'system-ui, sans-serif',
      lineHeight: 1.55,
      color: '#1f2937',
    }}>
      <h1 style={{ color: '#037623', fontWeight: '900', marginTop: 0 }}>
        Politica de Cookies
      </h1>

      <p style={{ color: '#6b7280', marginBottom: '24px' }}>
        Ultima actualizacion: 8 de mayo de 2026 - Version 2.0
      </p>

      <p>
        Las cookies son archivitos que tu navegador guarda mientras navegas. Algunas son
        imprescindibles (sin ellas la app no funciona) y otras nos ayudan a entender que se
        usa y que no. Aqui te contamos que usamos y, sobre todo, te damos el control para
        decirnos que no si asi lo prefieres.
      </p>

      <h2>1. Categorias de cookies que usamos</h2>

      <h3>Imprescindibles (siempre activas)</h3>
      <p>
        Sin estas la app simplemente no funciona. No se pueden desactivar y no requieren
        consentimiento porque solo guardamos lo que tu nos has pedido (tu cesta, tus
        preferencias).
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px', fontSize: '13px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0fdf4' }}>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Nombre</th>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Para que sirve</th>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Duracion</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>miCesta_v7</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Guarda tu cesta actual en este dispositivo</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Permanente hasta que la borres</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>misCestas_v7</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Guarda tus listas favoritas</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Permanente hasta que la borres</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>supersActivos_v1</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Recuerda que supermercados tienes seleccionados</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Permanente</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>sync_pref</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Recuerda si has activado la sincronizacion en la nube</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Permanente</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>cookies_consent_v2</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Guarda tu decision sobre las cookies de esta politica</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>12 meses</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>landing_vista</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Para no ensenarte la pantalla de bienvenida cada vez</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Permanente</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Cookies de Supabase</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Mantener tu sesion iniciada de forma segura</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Sesion / 7 dias</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Cookies de Stripe</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Procesar pagos con seguridad y prevenir fraude</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Variable (Stripe)</td>
          </tr>
        </tbody>
      </table>

      <h3>Analiticas (opcionales, requieren tu consentimiento)</h3>
      <p>
        Si las aceptas, usamos Google Analytics 4 para entender que partes de la app se usan
        mas y donde se atascan los usuarios. Los datos viajan agregados y anonimizados - no
        sabemos que eres tu concretamente.
      </p>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px', fontSize: '13px' }}>
        <thead>
          <tr style={{ backgroundColor: '#fef3c7' }}>
            <th style={{ padding: '10px', border: '1px solid #fde68a', textAlign: 'left' }}>Nombre</th>
            <th style={{ padding: '10px', border: '1px solid #fde68a', textAlign: 'left' }}>Propietario</th>
            <th style={{ padding: '10px', border: '1px solid #fde68a', textAlign: 'left' }}>Duracion</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>_ga</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Google Ireland Ltd.</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>24 meses</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}><code>_ga_*</code></td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Google Ireland Ltd.</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>24 meses</td>
          </tr>
        </tbody>
      </table>

      <h2>2. Como gestionar tu decision</h2>
      <p>
        Cuando entras por primera vez te aparece un panel de cookies con tres opciones:
        aceptar todas, solo las imprescindibles o configurarlas en detalle. Tu decision queda
        guardada durante 12 meses, despues te volvemos a preguntar.
      </p>
      <p>
        Has cambiado de opinion? Pulsa el boton siguiente para volver a abrir el panel:
      </p>
      <button
        onClick={restablecerConsentimiento}
        style={{
          background: '#037623',
          color: 'white',
          border: 'none',
          borderRadius: '12px',
          padding: '12px 20px',
          fontWeight: '800',
          cursor: 'pointer',
          marginBottom: '20px',
        }}
      >
        Cambiar mis preferencias de cookies
      </button>

      <h2>3. Como desactivarlas desde el navegador</h2>
      <p>Como alternativa, puedes desactivar las cookies en cualquier navegador:</p>
      <ul>
        <li><strong>Chrome:</strong> Configuracion -> Privacidad y seguridad -> Cookies</li>
        <li><strong>Firefox:</strong> Ajustes -> Privacidad y seguridad -> Cookies</li>
        <li><strong>Safari:</strong> Preferencias -> Privacidad</li>
        <li><strong>Edge:</strong> Configuracion -> Cookies y permisos del sitio</li>
      </ul>

      <h2>4. Contacto</h2>
      <p>
        Para cualquier duda sobre esta politica puedes escribirnos a <strong>[EMAIL]</strong>.
      </p>

      <p style={{ marginTop: '32px', fontSize: '12px', color: '#6b7280' }}>
        Mi Mejor Cesta - [TITULAR] - [EMAIL]
      </p>
    </div>
  );
};

export default Cookies;
