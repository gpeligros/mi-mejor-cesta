import React from 'react';

const VERDE = '#037623';
const OSCURO = '#102215';

const BENEFICIOS = {
  basic: [
    'Todos los supermercados sin límite',
    'Lista de productos ilimitada',
    'Alertas de subida y bajada de precio',
    'Guardar compras realizadas',
    'Historial de 3 meses',
    'Escanear lista con la cámara',
    'CESTITA con contexto completo',
    'Dictado de lista por voz',
  ],
  premium: [
    'Todo lo del plan Básico',
    'Historial ilimitado de compras',
    'Planificación mensual de menús',
    'Generador de menú semanal con IA',
    'Lista de ingredientes desde receta',
    'Estadísticas completas de gasto',
    'Evolución histórica de precios',
    'Datos nutricionales de tu cesta*',
    'CESTITA con recetas y nutrición',
  ],
};

const ModalUpgrade = ({ onCerrar, funcionalidad = '', planRequerido = 'basic', session }) => {
  const [cargando, setCargando] = React.useState(false);
  const [error, setError] = React.useState(null);

  const handlePago = async (plan) => {
    if (!session) {
      setError('Necesitas iniciar sesión antes de suscribirte.');
      return;
    }
    setCargando(true);
    setError(null);
    try {
      const res = await fetch('/api/stripe-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planRequerido: plan,
          userEmail: session.user.email,
          userId: session.user.id,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.url) throw new Error(data.error || 'Error al crear sesión de pago');
      window.location.href = data.url;
    } catch (e) {
      setError(e.message);
      setCargando(false);
    }
  };
  const mensajes = {
    guardarListas:    'Guardar listas requiere registrarte',
    listasFavoritas:  'Más listas favoritas disponibles en plan Básico',
    exportarPDF:      'Exportar PDF requiere registro',
    compartirLista:   'Compartir listas requiere registro',
    escanearLista:    'Escanear listas requiere plan Básico',
    alertasPrecio:    'Las alertas de precio son del plan Básico',
    guardarCompra:    'Guardar compras realizadas requiere plan Básico',
    menuSemanal:      'Los menús semanales son del plan Premium',
    recetasIA:        'Las recetas con IA son del plan Premium',
    nutricional:      'Los datos nutricionales son del plan Premium',
    estadisticasFull: 'Las estadísticas completas son del plan Premium',
    maxSupers:        'Compara más supermercados con plan Básico',
    maxProductos:     'Lista ilimitada disponible en plan Básico',
  };

  const mensaje = mensajes[funcionalidad] || 'Esta funcionalidad requiere un plan superior';
  const esPremium = planRequerido === 'premium';

  return (
    <div
      onClick={onCerrar}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: 'white',
          borderRadius: '24px',
          padding: '32px',
          maxWidth: '480px',
          width: '100%',
          boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>🔒</div>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '900', color: OSCURO }}>
            {mensaje}
          </h2>
          <p style={{ color: '#666', fontSize: '14px', marginTop: '8px' }}>
            Desbloquea esta funcionalidad con el plan {esPremium ? 'Premium' : 'Básico'}
          </p>
        </div>

        {/* Planes */}
        <div style={{ display: 'grid', gridTemplateColumns: esPremium ? '1fr' : '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          {!esPremium && (
            <div style={{
              border: `2px solid ${VERDE}`,
              borderRadius: '16px',
              padding: '16px',
            }}>
              <div style={{ fontWeight: '900', fontSize: '16px', color: VERDE, marginBottom: '4px' }}>
                Básico
              </div>
              <div style={{ fontSize: '22px', fontWeight: '900', color: OSCURO, marginBottom: '12px' }}>
                2,99€<span style={{ fontSize: '12px', fontWeight: '400', color: '#999' }}>/mes</span>
              </div>
              {BENEFICIOS.basic.slice(0, 5).map((b, i) => (
                <div key={i} style={{ fontSize: '12px', color: '#444', marginBottom: '4px' }}>
                  ✅ {b}
                </div>
              ))}
            </div>
          )}
          <div style={{
            border: `2px solid ${OSCURO}`,
            borderRadius: '16px',
            padding: '16px',
            background: esPremium ? '#f8fdf9' : 'white',
          }}>
            <div style={{ fontWeight: '900', fontSize: '16px', color: OSCURO, marginBottom: '4px' }}>
              Premium
            </div>
            <div style={{ fontSize: '22px', fontWeight: '900', color: OSCURO, marginBottom: '12px' }}>
              6,99€<span style={{ fontSize: '12px', fontWeight: '400', color: '#999' }}>/mes</span>
            </div>
            {BENEFICIOS.premium.slice(0, esPremium ? 9 : 5).map((b, i) => (
              <div key={i} style={{ fontSize: '12px', color: '#444', marginBottom: '4px' }}>
                ✅ {b}
              </div>
            ))}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: '#fff0f0', color: '#d32f2f', padding: '10px 14px', borderRadius: '10px', fontSize: '13px', fontWeight: '600', marginBottom: '12px' }}>
            {error}
          </div>
        )}

        {/* CTA */}
        {!esPremium && (
          <button
            onClick={() => handlePago('basic')}
            disabled={cargando}
            style={{
              width: '100%',
              background: VERDE,
              color: 'white',
              border: 'none',
              borderRadius: '14px',
              padding: '16px',
              fontSize: '16px',
              fontWeight: '900',
              cursor: cargando ? 'not-allowed' : 'pointer',
              opacity: cargando ? 0.7 : 1,
              marginBottom: '10px',
            }}
          >
            {cargando ? 'Redirigiendo...' : 'Activar plan Básico — 2,99€/mes →'}
          </button>
        )}
        <button
          onClick={() => handlePago('premium')}
          disabled={cargando}
          style={{
            width: '100%',
            background: esPremium ? VERDE : OSCURO,
            color: 'white',
            border: 'none',
            borderRadius: '14px',
            padding: '16px',
            fontSize: '16px',
            fontWeight: '900',
            cursor: cargando ? 'not-allowed' : 'pointer',
            opacity: cargando ? 0.7 : 1,
            marginBottom: '10px',
          }}
        >
          {cargando ? 'Redirigiendo...' : 'Activar plan Premium — 6,99€/mes →'}
        </button>
        <button
          onClick={onCerrar}
          style={{
            width: '100%',
            background: 'none',
            border: 'none',
            color: '#999',
            fontSize: '13px',
            cursor: 'pointer',
            padding: '8px',
          }}
        >
          Ahora no
        </button>

        {esPremium && (
          <p style={{ fontSize: '10px', color: '#bbb', textAlign: 'center', marginTop: '8px' }}>
            * Los datos nutricionales son orientativos. No somos médicos ni nutricionistas.
          </p>
        )}
      </div>
    </div>
  );
};

export default ModalUpgrade;
