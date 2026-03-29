import React, { useState, useRef, useEffect } from 'react';

const CESTITA_VERDE = '#037623';
const CESTITA_OSCURO = '#102215';

const Cestita = ({ seleccionados, precios, supersActivos, getProdFull, session }) => {
  const [abierto, setAbierto]       = useState(false);
  const [mensajes, setMensajes]     = useState([
    {
      rol: 'assistant',
      texto: '¡Hola! Soy CESTITA 🛒\n\nTu asistente de compra inteligente. Puedo ayudarte a:\n• Comparar precios entre supermercados\n• Encontrar los mejores productos\n• Calcular tu ahorro\n• Resolver dudas sobre tu cesta\n\n¿En qué te ayudo hoy?'
    }
  ]);
  const [input, setInput]           = useState('');
  const [cargando, setCargando]     = useState(false);
  const [, setError]                = useState(null);
  const mensajesRef                 = useRef(null);
  const inputRef                    = useRef(null);

  // Scroll al último mensaje
  useEffect(() => {
    if (mensajesRef.current) {
      mensajesRef.current.scrollTop = mensajesRef.current.scrollHeight;
    }
  }, [mensajes, abierto]);

  // Focus al abrir
  useEffect(() => {
    if (abierto && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [abierto]);

  // Construir contexto de la cesta actual
  const buildContextoCesta = () => {
    if (!seleccionados || seleccionados.length === 0) {
      return 'El usuario no tiene productos en la cesta actualmente.';
    }

    const lineas = seleccionados.map(id => {
      const prod = getProdFull(id);
      if (!prod) return null;
      const preciosProd = (supersActivos || []).map(s => {
        const p = precios[id]?.[s];
        return p ? `${s}: ${p.toFixed(2)}€` : null;
      }).filter(Boolean);
      return `• ${prod.nombre} — ${preciosProd.join(' | ') || 'sin precio'}`;
    }).filter(Boolean);

    const totales = (supersActivos || []).map(s => {
      const t = seleccionados.reduce((acc, id) => acc + (precios[id]?.[s] || 0), 0);
      return t > 0 ? `${s}: ${t.toFixed(2)}€` : null;
    }).filter(Boolean);

    return `Cesta actual (${seleccionados.length} productos):\n${lineas.join('\n')}\n\nTotales por supermercado:\n${totales.map(t => `• ${t}`).join('\n')}`;
  };

  const enviar = async () => {
    const texto = input.trim();
    if (!texto || cargando) return;

    const nuevoMensaje = { rol: 'user', texto };
    const nuevosMensajes = [...mensajes, nuevoMensaje];
    setMensajes(nuevosMensajes);
    setInput('');
    setCargando(true);
    setError(null);

    try {
      const apiKey = process.env.REACT_APP_ANTHROPIC_API_KEY;
      if (!apiKey) throw new Error('Falta REACT_APP_ANTHROPIC_API_KEY en el .env');

      const contextoCesta = buildContextoCesta();
      const systemPrompt = `Eres CESTITA, la asistente de inteligencia artificial de Mi Mejor Cesta. 
Eres simpática, cercana y experta en compras de supermercado en España.
Tu objetivo es ayudar al usuario a ahorrar en su cesta de la compra.

CONTEXTO ACTUAL DEL USUARIO:
${contextoCesta}

Supermercados activos en la app: ${(supersActivos || []).join(', ')}
Usuario autenticado: ${session ? 'Sí' : 'No (plan gratuito)'}

INSTRUCCIONES:
- Responde siempre en español, con tono amigable y cercano
- Sé concisa y directa — respuestas cortas y útiles
- Si el usuario pregunta por precios, usa los datos de la cesta que tienes
- Si pregunta algo que no puedes saber (ubicación exacta de tiendas, stock en tiempo real), díselo con honestidad
- Usa emojis con moderación para hacer la conversación más amigable
- Nunca inventes precios o datos que no tengas`;

      // Construir historial para la API (sin el mensaje de bienvenida inicial)
      const historial = nuevosMensajes
        .filter(m => !(m.rol === 'assistant' && m === mensajes[0]))
        .map(m => ({ role: m.rol === 'user' ? 'user' : 'assistant', content: m.texto }));

      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true'
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1024,
          system: systemPrompt,
          messages: historial
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error?.message || `Error ${res.status}`);
      }

      const data = await res.json();
      const respuesta = data.content?.[0]?.text || 'No he podido procesar tu mensaje.';

      setMensajes(prev => [...prev, { rol: 'assistant', texto: respuesta }]);
    } catch (_error) {
      setError(e.message);
      setMensajes(prev => [...prev, {
        rol: 'assistant',
        texto: '😔 Ha ocurrido un error. Por favor, inténtalo de nuevo.',
        esError: true
      }]);
    } finally {
      setCargando(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviar();
    }
  };

  const limpiarChat = () => {
    setMensajes([{
      rol: 'assistant',
      texto: '¡Hola de nuevo! Soy CESTITA 🛒\n¿En qué te ayudo?'
    }]);
    setError(null);
  };

  // Sugerencias rápidas según el estado de la cesta
  const sugerencias = seleccionados?.length > 0
    ? ['¿Dónde me sale más barato?', '¿Cuánto ahorro?', 'Analiza mi cesta']
    : ['¿Cómo funciona la app?', '¿Qué supermercados tienes?', 'Ayúdame a empezar'];

  return (
    <>
      {/* Botón flotante */}
      <button
        onClick={() => setAbierto(!abierto)}
        className="no-print"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: abierto ? CESTITA_OSCURO : CESTITA_VERDE,
          color: 'white',
          border: 'none',
          cursor: 'pointer',
          fontSize: '26px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          zIndex: 2000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s ease',
          transform: abierto ? 'rotate(0deg)' : 'rotate(0deg)',
        }}
        title={abierto ? 'Cerrar CESTITA' : 'Abrir CESTITA'}
      >
        {abierto ? '✕' : '🛒'}
      </button>

      {/* Panel de chat */}
      {abierto && (
        <div
          className="no-print"
          style={{
            position: 'fixed',
            bottom: '96px',
            right: '24px',
            width: '360px',
            maxWidth: 'calc(100vw - 48px)',
            height: '520px',
            maxHeight: 'calc(100vh - 120px)',
            background: 'white',
            borderRadius: '20px',
            boxShadow: '0 10px 40px rgba(0,0,0,0.18)',
            zIndex: 1999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            border: `2px solid ${CESTITA_VERDE}`,
          }}
        >
          {/* Header */}
          <div style={{
            background: CESTITA_VERDE,
            padding: '14px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '22px' }}>🛒</span>
              <div>
                <div style={{ color: 'white', fontWeight: '900', fontSize: '16px', lineHeight: 1 }}>
                  CESTITA
                </div>
                <div style={{ color: '#a8f0be', fontSize: '11px', marginTop: '2px' }}>
                  Tu asistente de compra IA
                </div>
              </div>
            </div>
            <button
              onClick={limpiarChat}
              style={{
                background: 'rgba(255,255,255,0.15)',
                border: 'none',
                color: 'white',
                borderRadius: '8px',
                padding: '5px 10px',
                fontSize: '11px',
                cursor: 'pointer',
                fontWeight: '700',
              }}
              title="Limpiar conversación"
            >
              LIMPIAR
            </button>
          </div>

          {/* Mensajes */}
          <div
            ref={mensajesRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
              background: '#f8faf9',
            }}
          >
            {mensajes.map((m, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: m.rol === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  style={{
                    maxWidth: '82%',
                    padding: '10px 14px',
                    borderRadius: m.rol === 'user'
                      ? '18px 18px 4px 18px'
                      : '18px 18px 18px 4px',
                    background: m.rol === 'user'
                      ? CESTITA_VERDE
                      : m.esError ? '#fff0f0' : 'white',
                    color: m.rol === 'user' ? 'white' : CESTITA_OSCURO,
                    fontSize: '13px',
                    lineHeight: '1.5',
                    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                    border: m.esError ? '1px solid #ffcccc' : 'none',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {m.texto}
                </div>
              </div>
            ))}

            {cargando && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  background: 'white',
                  borderRadius: '18px 18px 18px 4px',
                  padding: '12px 16px',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                  display: 'flex',
                  gap: '5px',
                  alignItems: 'center',
                }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: '7px', height: '7px',
                      borderRadius: '50%',
                      background: CESTITA_VERDE,
                      animation: `bounce 1s infinite ${i * 0.15}s`,
                    }} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sugerencias rápidas */}
          {mensajes.length <= 2 && !cargando && (
            <div style={{
              padding: '8px 12px',
              display: 'flex',
              gap: '6px',
              flexWrap: 'wrap',
              borderTop: '1px solid #eee',
              background: 'white',
              flexShrink: 0,
            }}>
              {sugerencias.map((s, i) => (
                <button
                  key={i}
                  onClick={() => { setInput(s); inputRef.current?.focus(); }}
                  style={{
                    background: '#e8fdf0',
                    color: CESTITA_VERDE,
                    border: `1px solid #b7f0cc`,
                    borderRadius: '20px',
                    padding: '5px 10px',
                    fontSize: '11px',
                    fontWeight: '700',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{
            padding: '12px',
            borderTop: '1px solid #eee',
            display: 'flex',
            gap: '8px',
            background: 'white',
            flexShrink: 0,
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Escribe tu pregunta..."
              disabled={cargando}
              rows={1}
              style={{
                flex: 1,
                border: '1.5px solid #ddd',
                borderRadius: '12px',
                padding: '10px 12px',
                fontSize: '13px',
                resize: 'none',
                outline: 'none',
                fontFamily: 'inherit',
                lineHeight: '1.4',
                maxHeight: '80px',
                overflowY: 'auto',
              }}
            />
            <button
              onClick={enviar}
              disabled={!input.trim() || cargando}
              style={{
                background: input.trim() && !cargando ? CESTITA_VERDE : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                width: '42px',
                flexShrink: 0,
                cursor: input.trim() && !cargando ? 'pointer' : 'not-allowed',
                fontSize: '18px',
                transition: 'background 0.2s',
              }}
            >
              ↑
            </button>
          </div>
        </div>
      )}

      {/* Animación de los puntos */}
      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); opacity: 0.4; }
          50% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </>
  );
};

export default Cestita;
