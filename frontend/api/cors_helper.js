// frontend/api/cors_helper.js
// Utilidad CORS reutilizable para todas las Serverless Functions de Vercel
// Para añadir un origen nuevo, editar SOLO este fichero.

const ALLOWED_ORIGINS = [
  'https://mi-mejor-cesta.vercel.app',
  'http://localhost:3000',
];

/**
 * Aplica las cabeceras CORS a la respuesta.
 * Solo establece Access-Control-Allow-Origin si el origen está en la lista blanca.
 */
export function setCorsHeaders(req, res) {
  const origin = req.headers.origin;
  if (ALLOWED_ORIGINS.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Max-Age', '86400'); // preflight cacheado 24h
}

/**
 * Gestiona la petición OPTIONS (preflight del navegador).
 * Devuelve true si la petición era OPTIONS y ya fue respondida.
 * Usar así al inicio del handler:
 *   if (handlePreflight(req, res)) return;
 */
export function handlePreflight(req, res) {
  if (req.method === 'OPTIONS') {
    setCorsHeaders(req, res);
    res.status(204).end();
    return true;
  }
  return false;
}
