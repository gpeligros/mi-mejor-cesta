import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// 🆕 REGISTRO DE SERVICE WORKER (PWA)
// Cambia a false para desactivar
const ENABLE_SERVICE_WORKER = true;

if (ENABLE_SERVICE_WORKER && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('✅ Service Worker registrado:', registration.scope);
        
        // Detectar actualizaciones
        registration.onupdatefound = () => {
          const installingWorker = registration.installing;
          
          if (installingWorker) {
            installingWorker.onstatechange = () => {
              if (installingWorker.state === 'installed') {
                if (navigator.serviceWorker.controller) {
                  // Nueva versión disponible
                  console.log('🆕 Nueva versión disponible');
                  
                  // Opcional: Auto-actualizar
                  if (window.confirm('Nueva versión disponible. ¿Recargar ahora?')) {
                    window.location.reload();
                  }
                } else {
                  // Primera instalación
                  console.log('✅ App lista para funcionar offline');
                }
              }
            };
          }
        };
      })
      .catch((error) => {
        console.log('❌ Error registrando Service Worker:', error);
      });
  });
}

reportWebVitals();
