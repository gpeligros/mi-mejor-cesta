import React from 'react';

// ----------------------------------------------------------------------
// ErrorBoundary global de Mi Mejor Cesta
// Captura errores de renderizado de cualquier componente hijo y muestra
// una pantalla amable con boton de recargar. Si Sentry esta cargado,
// envia el error automaticamente.
// ----------------------------------------------------------------------

const VERDE = '#037623';
const OSCURO = '#102215';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || String(error) };
  }

  componentDidCatch(error, info) {
    // Reportar a Sentry si esta cargado
    try {
      if (typeof window !== 'undefined' && window.Sentry && window.Sentry.captureException) {
        window.Sentry.captureException(error, { extra: info });
      }
    } catch (e) {}
    // Log local siempre (visible en Sentry o en consola)
    if (typeof console !== 'undefined' && console.error) {
      console.error('ErrorBoundary capturo:', error, info);
    }
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div style={{
        minHeight: '100vh',
        background: '#f4f7f5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{
          background: 'white',
          maxWidth: '480px',
          width: '100%',
          padding: '32px',
          borderRadius: '20px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.08)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '52px', marginBottom: '16px' }}>🛒💥</div>
          <h1 style={{ color: OSCURO, fontWeight: '900', fontSize: '22px', marginTop: 0 }}>
            Algo se ha roto en la cesta
          </h1>
          <p style={{ color: '#555', fontSize: '14px', lineHeight: 1.5, marginBottom: '24px' }}>
            Ha pasado un error inesperado. Hemos avisado al equipo automaticamente.
            Prueba a recargar la pagina; si sigue fallando, escribenos y lo miramos.
          </p>
          {this.state.message && (
            <pre style={{
              fontSize: '11px',
              color: '#999',
              background: '#f6faf7',
              padding: '12px',
              borderRadius: '10px',
              textAlign: 'left',
              overflow: 'auto',
              maxHeight: '120px',
              marginBottom: '24px',
            }}>{this.state.message}</pre>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              background: VERDE,
              color: 'white',
              border: 'none',
              borderRadius: '14px',
              padding: '14px 28px',
              fontWeight: '900',
              fontSize: '15px',
              cursor: 'pointer',
            }}
          >
            Recargar la app
          </button>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
