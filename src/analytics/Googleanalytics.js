// src/analytics/GoogleAnalytics.js
// Componente para Google Analytics 4 - VERSION CORREGIDA

import { useEffect } from 'react';

// ==========================================
// CONFIGURACION
// ==========================================

// IMPORTANTE: Reemplaza con tu ID de medición de Google Analytics
const GA_MEASUREMENT_ID = 'G-XXXXXXXXXX'; // Ej: G-ABC123XYZ

// ==========================================
// FUNCIONES DE TRACKING
// ==========================================

// Inicializar Google Analytics
export const initGA = () => {
  // Cargar script de Google Analytics
  const script1 = document.createElement('script');
  script1.async = true;
  script1.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script1);

  // Configurar gtag
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;

  gtag('js', new Date());
  gtag('config', GA_MEASUREMENT_ID, {
    send_page_view: true
  });

  console.log('✅ Google Analytics inicializado');
};

// Trackear evento personalizado
export const trackEvent = (eventName, eventParams = {}) => {
  if (window.gtag) {
    window.gtag('event', eventName, eventParams);
    console.log('📊 Event:', eventName, eventParams);
  }
};

// ==========================================
// EVENTOS ESPECÍFICOS DE LA APP
// ==========================================

// Trackear búsqueda de producto
export const trackSearch = (searchTerm) => {
  trackEvent('search', {
    search_term: searchTerm,
  });
};

// Trackear producto añadido a la cesta
export const trackAddToCart = (productId, productName, quantity) => {
  trackEvent('add_to_cart', {
    product_id: productId,
    product_name: productName,
    quantity: quantity,
  });
};

// Trackear selección de supermercado
export const trackSuperSelection = (supermarkets) => {
  trackEvent('select_supermarket', {
    supermarkets: supermarkets.join(', '),
    count: supermarkets.length,
  });
};

// Trackear creación de lista
export const trackCreateList = (itemCount, totalPrice) => {
  trackEvent('create_list', {
    items: itemCount,
    value: totalPrice,
    currency: 'EUR',
  });
};

// Trackear comparación de precios
export const trackPriceComparison = (productId, cheapestSuper, savings) => {
  trackEvent('compare_prices', {
    product_id: productId,
    cheapest_supermarket: cheapestSuper,
    savings: savings,
    currency: 'EUR',
  });
};

// Trackear guardado de lista
export const trackSaveList = (listName, itemCount) => {
  trackEvent('save_list', {
    list_name: listName,
    items: itemCount,
  });
};

// Trackear cambio de categoría
export const trackCategoryChange = (category) => {
  trackEvent('select_category', {
    category: category,
  });
};

// ==========================================
// COMPONENTE DE AUTO-TRACKING
// ==========================================

const GoogleAnalytics = () => {
  useEffect(() => {
    // Inicializar GA la primera vez
    initGA();
  }, []);

  return null; // Este componente no renderiza nada
};

export default GoogleAnalytics;