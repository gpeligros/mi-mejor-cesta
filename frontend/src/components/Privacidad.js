import React from 'react';

// ----------------------------------------------------------------------
// Politica de Privacidad - Mi Mejor Cesta
// Estilo cercano + cumplimiento RGPD (UE 2016/679) y LOPDGDD 3/2018.
// Placeholders entre corchetes a rellenar antes de publicar:
//   [TITULAR]      - tu nombre o razon social
//   [NIF]          - DNI/NIE/CIF
//   [DIRECCION]    - domicilio fiscal
//   [EMAIL]        - email de contacto (minimo uno publico)
// ----------------------------------------------------------------------

const Privacidad = () => {
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
        Politica de Privacidad
      </h1>

      <p style={{ color: '#6b7280', marginBottom: '24px' }}>
        Ultima actualizacion: 8 de mayo de 2026 - Version 2.0
      </p>

      <p>
        Hola. Esta es la version sin tecnicismos: en Mi Mejor Cesta tratamos tus datos
        como nos gustaria que tratasen los nuestros - solo lo imprescindible, en servidores
        europeos, y nunca los vendemos ni compartimos con anunciantes.
      </p>

      <p>
        Si despues de leer esto te queda alguna duda, escribenos a <strong>[EMAIL]</strong> y
        te respondemos rapido y claro.
      </p>

      <h2>1. Quien es el responsable</h2>
      <p>
        El responsable del tratamiento de tus datos es <strong>[TITULAR]</strong>, con
        NIF <strong>[NIF]</strong> y domicilio en <strong>[DIRECCION]</strong>.
        Email de contacto: <strong>[EMAIL]</strong>.
      </p>

      <h2>2. Que datos recogemos y para que</h2>
      <p>Solo lo necesario para que la app funcione y para mejorarla:</p>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px', fontSize: '14px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0fdf4' }}>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Dato</th>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Para que lo usamos</th>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Base legal</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Email y contrasena</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Identificarte y permitir que entres a tu cuenta</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Ejecucion del contrato</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Cesta y listas guardadas</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Sincronizarlas entre tus dispositivos</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Ejecucion del contrato</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Historial de compras (planes de pago)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Mostrarte tus estadisticas y evolucion de gasto</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Ejecucion del contrato</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Datos de pago (Stripe)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Cobrar la suscripcion. Nosotros no vemos tu tarjeta - la gestiona Stripe</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Ejecucion del contrato</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Cookies analiticas (Google Analytics)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Saber que partes de la app se usan mas para mejorarlas</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Tu consentimiento (puedes retirarlo cuando quieras)</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Mensajes a CESTITA (asistente IA)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Procesarlos con la API de Anthropic para responderte</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Ejecucion del contrato</td>
          </tr>
        </tbody>
      </table>

      <h2>3. Quien mas toca tus datos (encargados del tratamiento)</h2>
      <p>
        Para que esto funcione confiamos en proveedores muy especificos. Todos cumplen RGPD y
        estan obligados por contrato a tratar tus datos solo para lo que les pedimos:
      </p>
      <ul>
        <li><strong>Supabase</strong> (Estados Unidos, con clausulas tipo de la UE) - base de datos y autenticacion.</li>
        <li><strong>Vercel</strong> (Estados Unidos, con clausulas tipo de la UE) - alojamiento de la web.</li>
        <li><strong>Stripe Payments Europe Ltd.</strong> (Irlanda) - cobro de las suscripciones.</li>
        <li><strong>Anthropic PBC</strong> (Estados Unidos) - solo cuando hablas con CESTITA.</li>
        <li><strong>Google Ireland Ltd.</strong> - solo si aceptas cookies analiticas.</li>
      </ul>
      <p>
        Algunos de estos proveedores estan fuera del Espacio Economico Europeo. Las
        transferencias internacionales se hacen con las clausulas contractuales tipo aprobadas
        por la Comision Europea.
      </p>

      <h2>4. Cuanto tiempo guardamos tus datos</h2>
      <ul>
        <li>Mientras tu cuenta este activa.</li>
        <li>Si la borras, eliminamos tus datos en un plazo maximo de 30 dias, salvo lo que la ley nos obligue a conservar (por ejemplo, facturacion: 6 anos para Hacienda).</li>
        <li>Las cookies analiticas tienen una duracion de hasta 24 meses.</li>
      </ul>

      <h2>5. Tus derechos (RGPD)</h2>
      <p>
        Sobre tus datos tienes el control. Puedes ejercer estos derechos cuando quieras
        escribiendonos a <strong>[EMAIL]</strong>:
      </p>
      <ul>
        <li><strong>Acceso</strong> - pedirnos copia de todo lo que tenemos sobre ti.</li>
        <li><strong>Rectificacion</strong> - corregir cualquier dato incorrecto.</li>
        <li><strong>Supresion</strong> ("derecho al olvido") - borrar tu cuenta y datos.</li>
        <li><strong>Limitacion</strong> - pausar el tratamiento mientras se resuelve una duda.</li>
        <li><strong>Portabilidad</strong> - descargar tus datos en formato exportable.</li>
        <li><strong>Oposicion</strong> - oponerte a tratamientos basados en interes legitimo.</li>
        <li><strong>Retirar el consentimiento</strong> - en cualquier momento, sin tener que justificarte.</li>
      </ul>
      <p>
        Si crees que no tratamos bien tus datos, puedes reclamar ante la Agencia Espanola de
        Proteccion de Datos (<a href="https://www.aepd.es" target="_blank" rel="noopener noreferrer">aepd.es</a>),
        aunque preferimos que primero nos lo digas a nosotros y lo arreglemos.
      </p>

      <h2>6. Seguridad</h2>
      <ul>
        <li>Conexiones cifradas (HTTPS/TLS) en toda la app.</li>
        <li>Las contrasenas viajan y se almacenan cifradas (bcrypt via Supabase Auth).</li>
        <li>No almacenamos numeros de tarjeta. Eso es responsabilidad de Stripe (PCI DSS Nivel 1).</li>
      </ul>

      <h2>7. Menores de edad</h2>
      <p>
        Mi Mejor Cesta no esta dirigida a menores de 14 anos. Si crees que tu hija o hijo nos
        ha facilitado datos sin tu permiso, escribenos y los borramos de inmediato.
      </p>

      <h2>8. Cambios en esta politica</h2>
      <p>
        Si actualizamos esta politica te avisaremos por email (si tienes cuenta) o con un aviso
        visible en la app. Mientras tanto, esta version es la que aplica.
      </p>

      <p style={{ marginTop: '32px', fontSize: '12px', color: '#6b7280' }}>
        Mi Mejor Cesta - Responsable: [TITULAR] - NIF [NIF] - [EMAIL]
      </p>
    </div>
  );
};

export default Privacidad;
