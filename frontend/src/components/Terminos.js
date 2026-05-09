import React from 'react';

// ----------------------------------------------------------------------
// Terminos y Condiciones - Mi Mejor Cesta
// Tono cercano + cumplimiento Ley 3/2014 (consumidores), Ley 34/2002 (LSSI-CE)
// y Real Decreto-ley 7/2021 (suscripciones digitales).
// Placeholders: [TITULAR], [NIF], [DIRECCION], [EMAIL], [PROVINCIA]
// ----------------------------------------------------------------------

const Terminos = () => {
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
        Terminos y Condiciones de Uso
      </h1>

      <p style={{ color: '#6b7280', marginBottom: '24px' }}>
        Ultima actualizacion: 8 de mayo de 2026 - Version 2.0
      </p>

      <p>
        Bienvenida o bienvenido a Mi Mejor Cesta. Estos terminos son nuestro acuerdo. Hemos
        intentado escribirlos como nos gusta hablar - claros, sin letra pequena tramposa.
        Si algo no se entiende, escribenos a <strong>[EMAIL]</strong> y lo aclaramos.
      </p>

      <h2>1. Quienes somos</h2>
      <p>
        Mi Mejor Cesta es un servicio prestado por <strong>[TITULAR]</strong> (NIF
        <strong> [NIF]</strong>), con domicilio en <strong>[DIRECCION]</strong>. Email de
        contacto: <strong>[EMAIL]</strong>. Web: <a href="https://mi-mejor-cesta.vercel.app">mi-mejor-cesta.vercel.app</a>.
      </p>

      <h2>2. Que te ofrecemos</h2>
      <p>
        Una herramienta para comparar precios entre supermercados, ahorrar en tu compra y
        organizar tus listas. Algunas funciones (como la asistente CESTITA, los menus
        semanales o las estadisticas) requieren un plan de pago.
      </p>

      <h2>3. Tu cuenta</h2>
      <ul>
        <li>Para guardar listas en la nube necesitas crear una cuenta.</li>
        <li>Usa un email real y una contrasena segura. Eres responsable de lo que se haga desde tu cuenta.</li>
        <li>Si detectas un acceso no autorizado, avisanos cuanto antes a <strong>[EMAIL]</strong>.</li>
      </ul>

      <h2>4. Planes y precios</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px', fontSize: '14px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0fdf4' }}>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Plan</th>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Precio</th>
            <th style={{ padding: '10px', border: '1px solid #d1fae5', textAlign: 'left' }}>Renovacion</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Gratuito</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>0 EUR</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>-</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Basico</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>2,99 EUR/mes (IVA incluido)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Mensual automatica</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Premium</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>6,99 EUR/mes (IVA incluido)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>Mensual automatica</td>
          </tr>
        </tbody>
      </table>

      <p>
        El cobro lo procesa <strong>Stripe Payments Europe Ltd.</strong> Tu nos das tu tarjeta
        directamente a Stripe - nosotros no la vemos.
      </p>

      <h2>5. Renovacion, cancelacion y reembolsos</h2>
      <p>
        Las suscripciones se <strong>renuevan automaticamente</strong> cada mes hasta que las
        canceles. Cancelar es facil:
      </p>
      <ol>
        <li>Entra en tu cuenta -> Mi plan -> "Cancelar suscripcion".</li>
        <li>O escribenos a <strong>[EMAIL]</strong> y la cancelamos en menos de 24 horas.</li>
      </ol>
      <p>
        Si cancelas, mantienes el plan activo hasta el final del periodo ya pagado. No te
        cobramos un mes prorrateado al cancelar.
      </p>
      <p>
        <strong>Politica de reembolsos:</strong> si en los primeros 14 dias no estas contento,
        te devolvemos el dinero integro escribiendo a <strong>[EMAIL]</strong> sin mas
        preguntas. Pasado ese plazo, no hay reembolsos por meses ya consumidos, pero puedes
        cancelar cuando quieras.
      </p>

      <h2>6. Derecho de desistimiento (suscripciones digitales)</h2>
      <p>
        Como consumidor tienes 14 dias naturales desde la contratacion para desistir sin
        explicar el motivo (Real Decreto Legislativo 1/2007, art. 102 y ss.).
      </p>
      <p>
        <strong>Importante:</strong> al activar la suscripcion aceptas que prestemos el
        servicio inmediatamente y que <strong>renuncias al desistimiento</strong> respecto a
        las funcionalidades digitales ya consumidas (ese es el equilibrio que la ley pide para
        contenidos digitales). Aun asi, mantenemos los 14 dias de reembolso del punto anterior
        como garantia adicional voluntaria por nuestra parte.
      </p>

      <h2>7. Subidas y bajadas de plan</h2>
      <p>
        Puedes cambiar de plan cuando quieras. Si subes, el cobro se prorratea desde ese dia.
        Si bajas, el cambio aplica al inicio del siguiente ciclo.
      </p>

      <h2>8. Lo que puedes y lo que no puedes hacer</h2>
      <p>Puedes:</p>
      <ul>
        <li>Usar la app para tu uso personal y domestico.</li>
        <li>Compartir listas con tu familia o conocidos.</li>
        <li>Exportar tu cesta a PDF.</li>
      </ul>
      <p>Por favor no:</p>
      <ul>
        <li>Hagas scraping ni extraccion masiva de nuestros datos.</li>
        <li>Compartas tu cuenta con muchas personas (es para uso personal).</li>
        <li>Intentes saltarte limites del plan, hackear o atacar la plataforma.</li>
        <li>Uses la app para fines comerciales sin acuerdo previo con nosotros.</li>
      </ul>

      <h2>9. Sobre los precios mostrados</h2>
      <p>
        Los precios de los supermercados se actualizan periodicamente desde fuentes publicas y
        son orientativos. Pueden no coincidir con los del dia y la tienda exactos. No nos
        hacemos responsables de discrepancias en caja: la fuente oficial siempre es el
        supermercado.
      </p>
      <p>
        Mi Mejor Cesta no esta afiliado, patrocinado ni respaldado por las cadenas de
        supermercados que se comparan. Las marcas y logos pertenecen a sus respectivos
        propietarios y se usan con fines informativos.
      </p>

      <h2>10. CESTITA y otras funciones con IA</h2>
      <p>
        CESTITA, los menus semanales, las recetas y los datos nutricionales se generan
        mediante modelos de inteligencia artificial. Son una guia orientativa: pueden contener
        errores. <strong>No sustituyen consejo medico, nutricional ni profesional.</strong>
        Si tienes alergias, dieta especial o cualquier condicion medica, consulta siempre a
        tu profesional de referencia.
      </p>

      <h2>11. Disponibilidad del servicio</h2>
      <p>
        Hacemos todo lo posible por mantener la app disponible 24/7, pero a veces toca hacer
        mantenimiento, los proveedores fallan o pasa lo inesperado. Si el servicio se cae
        durante un periodo prolongado, te lo compensamos extendiendo tu plan los dias
        afectados.
      </p>

      <h2>12. Limitacion de responsabilidad</h2>
      <p>
        En la medida maxima permitida por la ley, nuestra responsabilidad por danos se limita
        al importe que hayas pagado en los ultimos 12 meses. No respondemos de perdidas
        indirectas, lucro cesante o danos imposibles de prever.
      </p>
      <p>
        Esto no afecta a los derechos que la legislacion de consumo te reconoce como
        consumidor.
      </p>

      <h2>13. Modificaciones</h2>
      <p>
        Si actualizamos estos terminos te avisamos por email con al menos 30 dias de
        antelacion si el cambio afecta a tu suscripcion. Si no estas de acuerdo, puedes
        cancelar antes de que entren en vigor.
      </p>

      <h2>14. Ley aplicable y juzgados</h2>
      <p>
        Este contrato se rige por la legislacion espanola. Para cualquier conflicto, las
        partes se someten a los juzgados y tribunales del domicilio del consumidor (si eres
        consumidor), o a los de <strong>[PROVINCIA]</strong> en caso contrario.
      </p>

      <h2>15. Resolucion de conflictos</h2>
      <p>
        Antes de ir a juicio escribenos a <strong>[EMAIL]</strong>. Si en 30 dias no llegamos
        a acuerdo, puedes acudir a la plataforma europea de resolucion de litigios:
        <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer"> ec.europa.eu/consumers/odr</a>.
      </p>

      <p style={{ marginTop: '32px', fontSize: '12px', color: '#6b7280' }}>
        Mi Mejor Cesta - [TITULAR] - NIF [NIF] - [DIRECCION] - [EMAIL]
      </p>
    </div>
  );
};

export default Terminos;
