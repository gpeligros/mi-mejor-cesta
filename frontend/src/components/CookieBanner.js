import React, { useState, useEffect } from 'react';

// ──────────────────────────────────────────────────────────────────────
// CookieBanner — Mi Mejor Cesta
// Cumple Guía AEPD nov-2023:
//   1. Aceptar y rechazar igual de visibles, mismo nivel.
//   2. No se cargan cookies analíticas hasta consentimiento explícito.
//   3. Permite configurar granularmente.
//   4. Caduca a los 12 meses.
//
// API:
//   - Lee/escribe localStorage 'cookies_consent_v2' = JSON
//     { necesarias: true, analiticas: bool, ts: ISOString }
//   - Dispara evento window 'cookies:consent-changed' al cambiar para que
//     index.html (o cualquier listener) cargue/destruya GA4.
// ──────────────────────────────────────────────────────────────────────

const CONSENT_KEY = 'cookies_consent_v2';
const CONSENT_TTL_MS = 1000 * 60 * 60 * 24 * 365; // 12 meses

const VERDE = '#037623';
const OSCURO = '#102215';

export const leerConsentimiento = () => {
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed.ts) return null;
    if (Date.now() - new Date(parsed.ts).getTime() > CONSENT_TTL_MS) {
      return null; // caducado
    }
    return parsed;
  } catch {
    return null;
  }
};

export const guardarConsentimiento = (analiticas) => {
  const consent = {
    necesarias: true,
    analiticas: !!analiticas,
    ts: new Date().toISOString(),
  };
  try {
    localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
    // Limpiar la cookie antigua si existe
    localStorage.removeItem('cookies_aceptadas');
  } catch {}
  // Avisar al resto de la app (loader de GA4 escucha esto)
  try {
    window.dispatchEvent(new CustomEvent('cookies:consent-changed', { detail: consent }));
  } catch {}
  return consent;
};

const CookieBanner = ({ onCambiarPreferencias, onIrAPolitica }) => {
  const [visible, setVisible] = useState(false);
  const [modoDetalle, setModoDetalle] = useState(false);
  const [analiticasMarcado, setAnaliticasMarcado] = useState(true);

  useEffect(() => {
    const consent = leerConsentimiento();
    setVisible(consent === null);
  }, []);

  // Permite reabrir el banner desde fuera (botón "cambiar preferencias")
  useEffect(() => {
    const handler = () => {
      const consent = leerConsentimiento();
      setAnaliticasMarcado(consent?.analiticas ?? true);
      setVisible(true);
      setModoDetalle(true);
    };
    window.addEventListener('cookies:open-banner', handler);
    return () => window.removeEventListener('cookies:open-banner', handler);
  }, []);

  if (!visible) return null;

  const aceptarTodo = () => {
    guardarConsentimiento(true);
    setVisible(false);
  };
  const soloNecesarias = () => {
    guardarConsentimiento(false);
    setVisible(false);
  };
  const guardarConfiguracion = () => {
    guardarConsentimiento(analiticasMarcado);
    setVisible(false);
  };

  return (
    <div
      role="dialog"
      aria-label="Aviso de cookies"
      aria-modal="true"
      style={{
        position: 'fixed',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '92%',
        maxWidth: '560px',
        backgroundColor: 'white',
        color: OSCURO,
        padding: '20px',
        borderRadius: '20px',
        boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
        zIndex: 9999,
        border: `2px solid ${VERDE}`,
      }}
    >
      <div style={{ fontSize: '15px', fontWeight: '900', marginBottom: '8px' }}>
        🍪 Cookies en Mi Mejor Cesta
      </div>
      <div style={{ fontSize: '13px', lineHeight: 1.4, marginBottom: '14px' }}>
        Usamos cookies <strong>imprescindibles</strong> para que la app funcione (guardar tu cesta,
        mantener tu sesión) y, solo si lo aceptas, cookies <strong>analíticas</strong> para entender
        cómo se usa y mejorarla. Tú eliges.{' '}
        <button
          onClick={() => onIrAPolitica && onIrAPolitica()}
          style={{
            background: 'none',
            border: 'none',
            color: VERDE,
            fontWeight: '800',
            cursor: 'pointer',
            padding: 0,
            textDecoration: 'underline',
          }}
        >
          Más información
        </button>
      </div>

      {modoDetalle && (
        <div style={{
          background: '#f6faf7',
          border: '1px solid #d1fae5',
          borderRadius: '12px',
          padding: '12px',
          marginBottom: '14px',
          fontSize: '13px',
        }}>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', marginBottom: '10px', opacity: 0.6 }}>
            <input type="checkbox" checked disabled style={{ marginTop: '3px' }} />
            <div>
              <div style={{ fontWeight: '800' }}>Imprescindibles · siempre activas</div>
              <div style={{ fontSize: '12px', color: '#555' }}>
                Cesta, sesión, preferencias de supermercado. Sin esto la app no funciona.
              </div>
            </div>
          </label>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <input
              type="checkbox"
              checked={analiticasMarcado}
              onChange={(e) => setAnaliticasMarcado(e.target.checked)}
              style={{ marginTop: '3px' }}
            />
            <div>
              <div style={{ fontWeight: '800' }}>Analíticas · Google Analytics</div>
              <div style={{ fontSize: '12px', color: '#555' }}>
                Nos ayudan a saber qué se usa y qué mejorar. Datos agregados, no identificativos.
              </div>
            </div>
          </label>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {!modoDetalle ? (
          <>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={aceptarTodo}
                style={{
                  flex: 1,
                  background: VERDE,
                  color: 'white',
                  border: 'none',
                  borderRadius: '12px',
                  padding: '12px',
                  fontWeight: '900',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                ACEPTAR TODO
              </button>
              <button
                onClick={soloNecesarias}
                style={{
                  flex: 1,
                  background: 'white',
                  color: OSCURO,
                  border: `2px solid ${OSCURO}`,
                  borderRadius: '12px',
                  padding: '12px',
                  fontWeight: '900',
                  cursor: 'pointer',
                  fontSize: '13px',
                }}
              >
                SOLO NECESARIAS
              </button>
            </div>
            <button
              onClick={() => setModoDetalle(true)}
              style={{
                background: 'none',
                color: '#555',
                border: '1px solid #ccc',
                borderRadius: '10px',
                padding: '8px',
                fontWeight: '700',
                fontSize: '12px',
                cursor: 'pointer',
              }}
            >
              Configurar en detalle
            </button>
          </>
        ) : (
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={guardarConfiguracion}
              style={{
                flex: 1,
                background: VERDE,
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                padding: '12px',
                fontWeight: '900',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              GUARDAR MI ELECCIÓN
            </button>
            <button
              onClick={aceptarTodo}
              style={{
                flex: 1,
                background: 'white',
                color: VERDE,
                border: `2px solid ${VERDE}`,
                borderRadius: '12px',
                padding: '12px',
                fontWeight: '900',
                cursor: 'pointer',
                fontSize: '13px',
              }}
            >
              ACEPTAR TODO
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CookieBanner;
