import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import reportWebVitals from './reportWebVitals';

// ----------------------------------------------------------------------
// Sentry: monitorizacion de errores en produccion (DESACTIVADO)
// ----------------------------------------------------------------------
// Para activarlo cuando quieras:
//   1) cd frontend && npm install --save @sentry/react
//   2) En Vercel, anadir env var REACT_APP_SENTRY_DSN con el DSN de sentry.io
//   3) Descomentar el bloque de abajo y hacer push
//
// const SENTRY_DSN = process.env.REACT_APP_SENTRY_DSN;
// if (SENTRY_DSN) {
//   import('@sentry/react').then((Sentry) => {
//     Sentry.init({
//       dsn: SENTRY_DSN,
//       environment: process.env.NODE_ENV || 'production',
//       tracesSampleRate: 0.1,
//       replaysSessionSampleRate: 0,
//       replaysOnErrorSampleRate: 0,
//       ignoreErrors: [
//         'ResizeObserver loop limit exceeded',
//         'ResizeObserver loop completed with undelivered notifications',
//         'Non-Error promise rejection captured',
//       ],
//       beforeSend(event) {
//         if (window.location.hostname === 'localhost') return null;
//         return event;
//       },
//     });
//     window.Sentry = Sentry;
//   }).catch(() => {});
// }
// ----------------------------------------------------------------------

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// ----------------------------------------------------------------------
// Service Worker (PWA)
// ----------------------------------------------------------------------
const ENABLE_SERVICE_WORKER = true;

if (ENABLE_SERVICE_WORKER && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('Service Worker registrado:', registration.scope);

        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          if (installingWorker) {
            installingWorker.onstatechange = () => {
              if (installingWorker.state === 'installed') {
                if (navigator.serviceWorker.controller) {
                  console.log('Nueva version disponible');
                  if (window.confirm('Nueva version disponible. Recargar ahora?')) {
                    window.location.reload();
                  }
                } else {
                  console.log('App lista para funcionar offline');
                }
              }
            };
          }
        };
      })
      .catch((error) => {
        console.log('Error registrando Service Worker:', error);
      });
  });
}

reportWebVitals();
