import React, { useState } from 'react';

const VERDE = '#037623';
const OSCURO = '#102215';

// ── Parsea el texto del menú en estructura de días ─────────────
const parsearMenu = (texto) => {
  const dias = ['lunes', 'martes', 'miércoles', 'miercoles', 'jueves', 'viernes', 'sábado', 'sabado', 'domingo'];
  const resultado = [];

  const lineas = texto.split('\n').map(l => l.trim()).filter(Boolean);
  let diaActual = null;
  let comidas = {};

  lineas.forEach(linea => {
    const lineaLower = linea.toLowerCase();
    const diaEncontrado = dias.find(d => lineaLower.includes(d));

    if (diaEncontrado) {
      if (diaActual) resultado.push({ dia: diaActual, comidas });
      diaActual = linea.replace(/[*#]/g, '').trim();
      comidas = {};
      return;
    }

    if (lineaLower.includes('desayuno') || lineaLower.includes('breakfast')) {
      comidas.desayuno = linea.replace(/[*#•\-]/g, '').replace(/desayuno:/i, '').trim();
    } else if (lineaLower.includes('comida') || lineaLower.includes('almuerzo') || lineaLower.includes('lunch')) {
      comidas.comida = linea.replace(/[*#•\-]/g, '').replace(/(comida|almuerzo):/i, '').trim();
    } else if (lineaLower.includes('cena') || lineaLower.includes('dinner')) {
      comidas.cena = linea.replace(/[*#•\-]/g, '').replace(/cena:/i, '').trim();
    }
  });

  if (diaActual) resultado.push({ dia: diaActual, comidas });
  return resultado;
};

// ── Parsea la lista de la compra ───────────────────────────────
const parsearListaCompra = (texto) => {
  const lineas = texto.split('\n').map(l => l.trim()).filter(Boolean);
  const inicio = lineas.findIndex(l =>
    l.toLowerCase().includes('lista') && l.toLowerCase().includes('compra')
  );
  if (inicio === -1) return [];

  return lineas.slice(inicio + 1)
    .filter(l => /^[-•*]/.test(l) || /^\d+\./.test(l))
    .map(l => l.replace(/^[-•*\d.]+\s*/, '').trim())
    .filter(Boolean)
    .slice(0, 30);
};

// ── Componente tarjeta de día ──────────────────────────────────
const TarjetaDia = ({ dia, comidas }) => (
  <div style={{
    background: 'white',
    border: '1px solid #e8f0e9',
    borderRadius: '14px',
    padding: '14px',
    minWidth: '200px',
    flex: '0 0 auto',
  }}>
    <div style={{
      fontWeight: '900',
      fontSize: '12px',
      color: VERDE,
      marginBottom: '10px',
      textTransform: 'uppercase',
      borderBottom: `2px solid ${VERDE}`,
      paddingBottom: '6px',
    }}>
      {dia}
    </div>
    {[
      { key: 'desayuno', emoji: '☀️', label: 'Desayuno' },
      { key: 'comida',   emoji: '🍽️', label: 'Comida' },
      { key: 'cena',     emoji: '🌙', label: 'Cena' },
    ].map(({ key, emoji, label }) => (
      <div key={key} style={{ marginBottom: '8px' }}>
        <div style={{ fontSize: '10px', fontWeight: '800', color: '#999' }}>{emoji} {label}</div>
        <div style={{ fontSize: '12px', color: OSCURO, marginTop: '2px', lineHeight: 1.3 }}>
          {comidas?.[key] || '—'}
        </div>
      </div>
    ))}
  </div>
);

const MenuSemanal = ({ onClose, supersActivos, precios, seleccionados, getProdFull }) => {
  const [paso, setPaso]           = useState('form');   // form | generando | resultado | recetas
  const [respuestaIA, setRespuestaIA] = useState('');
  const [error, setError]         = useState(null);
  const [modoVista, setModoVista] = useState('menu');   // menu | lista

  // Formulario
  const [personas,    setPersonas]    = useState('2');
  const [dias,        setDias]        = useState('7');
  const [restriccion, setRestriccion] = useState('ninguna');
  const [presupuesto, setPresupuesto] = useState('');
  const [preferencia, setPreferencia] = useState('');

  const diasMenu   = parsearMenu(respuestaIA);
  const listaCompra = parsearListaCompra(respuestaIA);

  // ── Generar menú semanal ─────────────────────────────────────
  const generarMenu = async () => {
    setPaso('generando');
    setError(null);

    const restriccionTexto = restriccion === 'ninguna' ? 'sin restricciones especiales' : restriccion;
    const presupuestoTexto = presupuesto ? `con un presupuesto aproximado de ${presupuesto}€ a la semana` : '';
    const preferenciaTexto = preferencia ? `Preferencias adicionales: ${preferencia}.` : '';

    const prompt = `Genera un menú semanal completo para ${personas} persona${personas !== '1' ? 's' : ''} durante ${dias} días.
Restricciones dietéticas: ${restriccionTexto}.
${presupuestoTexto}
${preferenciaTexto}

El menú debe incluir desayuno, comida y cena para cada día.
Usa ingredientes típicos de supermercados españoles (Mercadona, DIA, Alcampo).
Al final incluye una lista de la compra organizada con las cantidades necesarias.

Formato de respuesta:
**LUNES**
- Desayuno: [plato]
- Comida: [plato]
- Cena: [plato]

[repetir para cada día]

**LISTA DE LA COMPRA**
- [ingrediente y cantidad]
...`;

    try {
      const res = await fetch('/api/cestita', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system: `Eres un nutricionista y chef experto en cocina española. Generas menús semanales equilibrados, variados y económicos adaptados a supermercados españoles. Siempre incluyes desayuno, comida y cena para cada día, y una lista de la compra detallada al final.`,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 2048,
        }),
      });

      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      const texto = data.content?.[0]?.text || '';
      setRespuestaIA(texto);
      setPaso('resultado');
    } catch (e) {
      setError('No se pudo generar el menú. Inténtalo de nuevo.');
      setPaso('form');
    }
  };

  // ── Generar sugerencias de recetas con la cesta ──────────────
  const generarRecetas = async () => {
    if (!seleccionados || seleccionados.length === 0) {
      setError('Añade productos a tu cesta antes de pedir sugerencias de recetas.');
      return;
    }
    setPaso('generando');
    setError(null);

    const productosEnCesta = (seleccionados || []).map(id => {
      const p = getProdFull(id);
      return p ? p.nombre : null;
    }).filter(Boolean);

    const listaProductos = productosEnCesta.length > 0
      ? productosEnCesta.join(', ')
      : 'productos básicos de supermercado español';

    const prompt = `Tengo estos productos en mi cesta de la compra: ${listaProductos}.

Sugiere 5 recetas que pueda preparar con estos ingredientes. Para cada receta indica:
- Nombre del plato
- Tiempo de preparación aproximado
- Ingredientes necesarios (marcando cuáles ya tengo)
- Pasos breves de preparación

Adapta las recetas a la cocina española.`;

    try {
      const res = await fetch('/api/cestita', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system: `Eres un chef experto en cocina española. Sugieres recetas prácticas, ricas y fáciles de preparar basándote en los ingredientes disponibles. Siempre adaptas las recetas al contexto español.`,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 2048,
        }),
      });

      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      const texto = data.content?.[0]?.text || '';
      setRespuestaIA(texto);
      setPaso('recetas');
    } catch (e) {
      setError('No se pudo generar las recetas. Inténtalo de nuevo.');
      setPaso('form');
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 3000,
      background: 'rgba(0,0,0,0.55)',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'center',
      padding: '20px',
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      <div style={{
        background: 'white',
        borderRadius: '24px',
        width: '100%',
        maxWidth: '720px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        overflow: 'hidden',
        marginTop: '20px',
        marginBottom: '20px',
      }}>
        {/* Header */}
        <div style={{
          background: VERDE,
          padding: '18px 22px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ color: 'white', fontWeight: '900', fontSize: '17px' }}>
              {paso === 'recetas' ? '💡 Sugerencias de recetas' : '🍽️ Menú semanal con IA'}
            </div>
            <div style={{ color: '#a8f0be', fontSize: '12px', marginTop: '2px' }}>
              {paso === 'form' && 'Cuéntame tus preferencias'}
              {paso === 'generando' && 'Generando con inteligencia artificial...'}
              {paso === 'resultado' && 'Tu menú está listo'}
              {paso === 'recetas' && 'Basado en tu cesta actual'}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', borderRadius: '10px', padding: '6px 12px', cursor: 'pointer', fontWeight: '700', fontSize: '13px' }}
          >
            ✕ Cerrar
          </button>
        </div>

        <div style={{ padding: '24px' }}>

          {/* ── FORMULARIO ────────────────────────────────────── */}
          {paso === 'form' && (
            <div>
              {error && (
                <div style={{ background: '#fff0f0', color: '#d32f2f', padding: '10px 14px', borderRadius: '10px', marginBottom: '16px', fontSize: '13px', fontWeight: '600' }}>
                  {error}
                </div>
              )}

              <div style={{ display: 'grid', gap: '16px' }}>
                {/* Personas y días */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                      👥 Número de personas
                    </label>
                    <select value={personas} onChange={e => setPersonas(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '10px', border: '1.5px solid #ddd', fontSize: '14px', fontFamily: 'inherit' }}>
                      {['1','2','3','4','5','6'].map(n => <option key={n} value={n}>{n} persona{n !== '1' ? 's' : ''}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                      📅 Días del menú
                    </label>
                    <select value={dias} onChange={e => setDias(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '10px', border: '1.5px solid #ddd', fontSize: '14px', fontFamily: 'inherit' }}>
                      {['3','5','7'].map(n => <option key={n} value={n}>{n} días</option>)}
                    </select>
                  </div>
                </div>

                {/* Restricciones */}
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                    🥗 Restricción dietética
                  </label>
                  <select value={restriccion} onChange={e => setRestriccion(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '10px', border: '1.5px solid #ddd', fontSize: '14px', fontFamily: 'inherit' }}>
                    <option value="ninguna">Sin restricciones</option>
                    <option value="vegetariano">Vegetariano</option>
                    <option value="vegano">Vegano</option>
                    <option value="sin gluten">Sin gluten</option>
                    <option value="sin lactosa">Sin lactosa</option>
                    <option value="bajo en carbohidratos">Bajo en carbohidratos</option>
                    <option value="mediterráneo">Dieta mediterránea</option>
                  </select>
                </div>

                {/* Presupuesto */}
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                    💶 Presupuesto semanal (opcional)
                  </label>
                  <input
                    type="number"
                    placeholder="Ej: 80"
                    value={presupuesto}
                    onChange={e => setPresupuesto(e.target.value)}
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', border: '1.5px solid #ddd', fontSize: '14px', fontFamily: 'inherit', boxSizing: 'border-box' }}
                  />
                </div>

                {/* Preferencias */}
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                    ✨ Preferencias adicionales (opcional)
                  </label>
                  <textarea
                    placeholder="Ej: me gusta la cocina italiana, poco picante, fácil de preparar..."
                    value={preferencia}
                    onChange={e => setPreferencia(e.target.value)}
                    rows={2}
                    style={{ width: '100%', padding: '10px', borderRadius: '10px', border: '1.5px solid #ddd', fontSize: '13px', fontFamily: 'inherit', resize: 'none', boxSizing: 'border-box' }}
                  />
                </div>

                {/* Botones */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <button
                    onClick={generarMenu}
                    style={{ background: VERDE, color: 'white', border: 'none', padding: '14px', borderRadius: '12px', fontWeight: '900', fontSize: '14px', cursor: 'pointer' }}
                  >
                    🍽️ Generar menú semanal
                  </button>
                  <button
                    onClick={generarRecetas}
                    style={{ background: '#f0fdf4', color: VERDE, border: `1.5px solid ${VERDE}`, padding: '14px', borderRadius: '12px', fontWeight: '900', fontSize: '14px', cursor: 'pointer' }}
                  >
                    💡 Recetas con mi cesta
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── GENERANDO ─────────────────────────────────────── */}
          {paso === 'generando' && (
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <div style={{ fontSize: '40px', marginBottom: '16px' }}>🍳</div>
              <div style={{ fontWeight: '900', fontSize: '16px', color: OSCURO, marginBottom: '8px' }}>
                Generando tu menú...
              </div>
              <div style={{ fontSize: '13px', color: '#888' }}>
                La IA está preparando un menú personalizado para ti.<br />
                Puede tardar unos segundos.
              </div>
              <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'center', gap: '6px' }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: '8px', height: '8px', borderRadius: '50%', background: VERDE,
                    animation: `bounce 1s infinite ${i * 0.2}s`,
                  }} />
                ))}
              </div>
              <style>{`@keyframes bounce { 0%,100%{transform:translateY(0);opacity:0.4} 50%{transform:translateY(-6px);opacity:1} }`}</style>
            </div>
          )}

          {/* ── RESULTADO MENÚ ────────────────────────────────── */}
          {paso === 'resultado' && (
            <div>
              {/* Tabs */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
                {[
                  { id: 'menu', label: '🍽️ Menú semanal' },
                  { id: 'lista', label: '🛒 Lista de la compra' },
                  { id: 'texto', label: '📄 Ver completo' },
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setModoVista(tab.id)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '10px',
                      border: `1.5px solid ${modoVista === tab.id ? VERDE : '#eee'}`,
                      background: modoVista === tab.id ? '#f0fdf4' : 'white',
                      color: modoVista === tab.id ? VERDE : '#888',
                      fontWeight: '800',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Vista menú por días */}
              {modoVista === 'menu' && (
                <div style={{ overflowX: 'auto', paddingBottom: '8px' }}>
                  {diasMenu.length > 0 ? (
                    <div style={{ display: 'flex', gap: '12px', width: 'max-content' }}>
                      {diasMenu.map((d, i) => (
                        <TarjetaDia key={i} dia={d.dia} comidas={d.comidas} />
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '13px', color: '#888', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                      {respuestaIA}
                    </div>
                  )}
                </div>
              )}

              {/* Vista lista de la compra */}
              {modoVista === 'lista' && (
                <div>
                  {listaCompra.length > 0 ? (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                      {listaCompra.map((item, i) => (
                        <div key={i} style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          padding: '8px 10px',
                          background: '#f8faf9',
                          borderRadius: '8px',
                          fontSize: '12px',
                          fontWeight: '600',
                          color: OSCURO,
                        }}>
                          <span style={{ color: VERDE, fontWeight: '900' }}>✓</span>
                          {item}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '13px', color: '#888' }}>
                      No se encontró lista de la compra. Mira la vista completa.
                    </div>
                  )}
                </div>
              )}

              {/* Vista texto completo */}
              {modoVista === 'texto' && (
                <div style={{
                  background: '#f8faf9',
                  borderRadius: '12px',
                  padding: '16px',
                  fontSize: '13px',
                  lineHeight: '1.7',
                  color: OSCURO,
                  whiteSpace: 'pre-wrap',
                  maxHeight: '400px',
                  overflowY: 'auto',
                }}>
                  {respuestaIA}
                </div>
              )}

              {/* Botones acción */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '20px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => { setPaso('form'); setRespuestaIA(''); setModoVista('menu'); }}
                  style={{ background: '#f0fdf4', color: VERDE, border: `1.5px solid ${VERDE}`, padding: '10px 16px', borderRadius: '10px', fontWeight: '800', fontSize: '12px', cursor: 'pointer' }}
                >
                  🔄 Generar otro
                </button>
                <button
                  onClick={() => {
                    const blob = new Blob([respuestaIA], { type: 'text/plain;charset=utf-8' });
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = 'menu-semanal-mi-mejor-cesta.txt';
                    a.click();
                  }}
                  style={{ background: OSCURO, color: 'white', border: 'none', padding: '10px 16px', borderRadius: '10px', fontWeight: '800', fontSize: '12px', cursor: 'pointer' }}
                >
                  📥 Descargar menú
                </button>
              </div>
            </div>
          )}

          {/* ── RESULTADO RECETAS ─────────────────────────────── */}
          {paso === 'recetas' && (
            <div>
              <div style={{
                background: '#f8faf9',
                borderRadius: '12px',
                padding: '16px',
                fontSize: '13px',
                lineHeight: '1.7',
                color: OSCURO,
                whiteSpace: 'pre-wrap',
                maxHeight: '450px',
                overflowY: 'auto',
              }}>
                {respuestaIA}
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button
                  onClick={() => { setPaso('form'); setRespuestaIA(''); }}
                  style={{ background: '#f0fdf4', color: VERDE, border: `1.5px solid ${VERDE}`, padding: '10px 16px', borderRadius: '10px', fontWeight: '800', fontSize: '12px', cursor: 'pointer' }}
                >
                  🔄 Volver
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default MenuSemanal;
