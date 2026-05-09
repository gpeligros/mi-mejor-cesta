import React from 'react';

// ──────────────────────────────────────────────────────────────────────
// Aviso Legal — Mi Mejor Cesta
// Cumple Ley 34/2002 (LSSI-CE), art. 10: información obligatoria del
// prestador de servicios de la sociedad de la información.
// Placeholders: [TITULAR], [NIF], [DIRECCION], [EMAIL], [TELEFONO]
//   Si tienes SL: añadir [REGISTRO_MERCANTIL] y [DATOS_INSCRIPCION].
// ──────────────────────────────────────────────────────────────────────

const AvisoLegal = () => {
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
        Aviso Legal
      </h1>

      <p style={{ color: '#6b7280', marginBottom: '24px' }}>
        Última actualización: 8 de mayo de 2026
      </p>

      <p>
        Este aviso recoge la información obligatoria sobre quién está detrás de Mi Mejor
        Cesta, en cumplimiento del artículo 10 de la Ley 34/2002 de Servicios de la Sociedad
        de la Información y Comercio Electrónico (LSSI-CE).
      </p>

      <h2>1. Titularidad</h2>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '20px', fontSize: '14px' }}>
        <tbody>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700', width: '180px' }}>Titular</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[TITULAR]</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>NIF / CIF</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[NIF]</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>Domicilio</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[DIRECCION]</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>Email de contacto</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[EMAIL]</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>Teléfono (opcional)</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[TELEFONO]</td>
          </tr>
          {/*
            Si operas como Sociedad Limitada, descomenta y rellena:
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>Registro Mercantil</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[REGISTRO_MERCANTIL]</td>
          </tr>
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>Datos de inscripción</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>[DATOS_INSCRIPCION]</td>
          </tr>
          */}
          <tr>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb', fontWeight: '700' }}>Web</td>
            <td style={{ padding: '10px', border: '1px solid #e5e7eb' }}>https://mi-mejor-cesta.vercel.app</td>
          </tr>
        </tbody>
      </table>

      <h2>2. Objeto</h2>
      <p>
        Mi Mejor Cesta es un servicio digital de comparación de precios entre supermercados
        españoles, con funciones gratuitas y planes de suscripción que añaden funcionalidades
        adicionales (asistente IA, menús, estadísticas).
      </p>

      <h2>3. Condiciones de uso</h2>
      <p>
        El uso del servicio se rige por nuestros <a href="/?seccion=terminos">Términos y
        Condiciones</a>. El tratamiento de datos personales se rige por nuestra
        <a href="/?seccion=privacidad"> Política de Privacidad</a>.
      </p>

      <h2>4. Propiedad intelectual e industrial</h2>
      <p>
        El diseño, código fuente, marca, logotipos y contenido original de Mi Mejor Cesta son
        propiedad de [TITULAR]. Las marcas, logos e información de los supermercados que se
        comparan son propiedad de sus respectivos titulares y se usan únicamente con fines
        informativos y comparativos, sin que ello implique afiliación, patrocinio o
        respaldo.
      </p>

      <h2>5. Responsabilidad</h2>
      <p>
        Hacemos esfuerzos razonables por mantener la información actualizada y la app
        disponible, pero no garantizamos la exactitud absoluta de los precios mostrados ni la
        ausencia total de incidencias técnicas. La fuente oficial de cada precio sigue siendo
        siempre el supermercado correspondiente.
      </p>

      <h2>6. Enlaces externos</h2>
      <p>
        Mi Mejor Cesta puede contener enlaces a webs de terceros (supermercados, recetas,
        proveedores). No nos hacemos responsables del contenido de esas webs ni de las
        prácticas de privacidad de terceros.
      </p>

      <h2>7. Legislación aplicable</h2>
      <p>
        El presente aviso se rige por la legislación española. Para cualquier conflicto, las
        partes se someten, con renuncia expresa a otro fuero, a los juzgados y tribunales que
        correspondan según la normativa de defensa de consumidores y usuarios.
      </p>

      <h2>8. Contacto</h2>
      <p>
        Para cualquier consulta legal o reclamación: <strong>[EMAIL]</strong>.
      </p>

      <p style={{ marginTop: '32px', fontSize: '12px', color: '#6b7280' }}>
        Mi Mejor Cesta · [TITULAR] · NIF [NIF]
      </p>
    </div>
  );
};

export default AvisoLegal;
