// frontend/api/cestita.js
// Vercel Serverless Function — proxy seguro para la API de Anthropic
// La ANTHROPIC_API_KEY vive aquí en el servidor, nunca en el frontend

import { setCorsHeaders, handlePreflight } from './cors_helper.js';

export default async function handler(req, res) {
  // Preflight CORS (OPTIONS) — el navegador lo envía antes del POST real
  if (handlePreflight(req, res)) return;

  // Aplicar cabeceras CORS al POST
  setCorsHeaders(req, res);

  // Solo POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'API key no configurada en el servidor' });
  }

  try {
    const { messages, system, max_tokens = 1024 } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Formato de mensajes inválido' });
    }

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens,
        system,
        messages,
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      return res.status(response.status).json({ error: err.error?.message || 'Error de API' });
    }

    const data = await response.json();
    return res.status(200).json(data);

  } catch (err) {
    console.error('Error en /api/cestita:', err);
    return res.status(500).json({ error: 'Error interno del servidor' });
  }
}
