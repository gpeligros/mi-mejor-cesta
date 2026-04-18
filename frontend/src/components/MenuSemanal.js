import React, { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';

const VERDE = '#037623';
const OSCURO = '#102215';
const VERDE_CLARO = '#f0fdf4';

// ══════════════════════════════════════════════════════════════════
// HELPERS DE PARSEO
// ══════════════════════════════════════════════════════════════════

// Extrae el JSON de la respuesta de la IA (puede venir rodeado de texto)
const extraerJSON = (texto) => {
  if (!texto) return null;
  // Intento 1: ¿es JSON puro?
  try { return JSON.parse(texto); } catch {}
  // Intento 2: buscar el primer { ... } balanceado
  const match = texto.match(/\{[\s\S]*\}/);
  if (match) {
    try { return JSON.parse(match[0]); } catch {}
  }
  return null;
};

// Genera un nombre automático para el menú según sus características
const generarNombreMenu = (menuData, restriccion, personas) => {
  const fecha = new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
  const restTexto = restriccion && restriccion !== 'ninguna' ? ` (${restriccion})` : '';
  return `Menú ${personas}p${restTexto} — ${fecha}`;
};

// ══════════════════════════════════════════════════════════════════
// COMPONENTE: TARJETA DE UNA COMIDA
// ══════════════════════════════════════════════════════════════════

const TarjetaComida = ({ tipo, emoji, label, comida }) => {
  if (!comida || !comida.plato) {
    return (
      <div style={{ marginBottom: '10px', opacity: 0.4 }}>
        <div style={{ fontSize: '10px', fontWeight: '800', color: '#999' }}>{emoji} {label}</div>
        <div style={{ fontSize: '12px', color: '#bbb', marginTop: '2px' }}>—</div>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ fontSize: '10px', fontWeight: '800', color: '#999', marginBottom: '3px' }}>
        {emoji} {label}
      </div>
      <div style={{ fontSize: '12px', color: OSCURO, fontWeight: '700', lineHeight: 1.3 }}>
        {comida.plato}
      </div>
      {(comida.tiempo || comida.dificultad) && (
        <div style={{ fontSize: '10px', color: '#888', marginTop: '3px', display: 'flex', gap: '8px' }}>
          {comida.tiempo && <span>⏱ {comida.tiempo} min</span>}
          {comida.dificultad && <span>· {comida.dificultad}</span>}
        </div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════
// COMPONENTE: TARJETA DE UN DÍA
// ══════════════════════════════════════════════════════════════════

const TarjetaDia = ({ dia }) => (
  <div style={{
    background: 'white',
    border: '1px solid #e8f0e9',
    borderRadius: '14px',
    padding: '14px',
    minWidth: '220px',
    flex: '0 0 auto',
  }}>
    <div style={{
      fontWeight: '900',
      fontSize: '12px',
      color: VERDE,
      marginBottom: '12px',
      textTransform: 'uppercase',
      borderBottom: `2px solid ${VERDE}`,
      paddingBottom: '6px',
    }}>
      {dia.dia}
    </div>
    <TarjetaComida tipo="desayuno" emoji="☀️" label="Desayuno" comida={dia.desayuno} />
    <TarjetaComida tipo="comida"   emoji="🍽️" label="Comida"   comida={dia.comida} />
    <TarjetaComida tipo="cena"     emoji="🌙" label="Cena"     comida={dia.cena} />
  </div>
);

// ══════════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════════

const MenuSemanal = ({
  onClose,
  supersActivos,
  precios,
  seleccionados,
  getProdFull,
  session,
  plan,
  limiteMenusGuardados,
  modoInicial = 'menu',
}) => {
  // Pestaña activa: 'menu' | 'recetas' | 'nutricional' | 'guardados'
  const [pestana, setPestana] = useState(modoInicial);

  // Estado del formulario (solo aplica a 'menu')
  const [personas,    setPersonas]    = useState('2');
  const [dias,        setDias]        = useState('7');
  const [restriccion, setRestriccion] = useState('ninguna');
  const [presupuesto, setPresupuesto] = useState('');
  const [preferencia, setPreferencia] = useState('');

  // Estados de flujo
  const [generando, setGenerando]       = useState(false);
  const [error, setError]               = useState(null);
  const [menuData, setMenuData]         = useState(null);     // objeto parseado del menú
  const [respuestaCruda, setRespuestaCruda] = useState('');   // texto de recetas/nutricional
  const [vistaResultado, setVistaResultado] = useState('menu'); // 'menu' | 'lista'

  // Biblioteca
  const [menusGuardados, setMenusGuardados] = useState([]);
  const [cargandoGuardados, setCargandoGuardados] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [mensajeGuardado, setMensajeGuardado] = useState(null);

  const limiteGuardados = limiteMenusGuardados ? limiteMenusGuardados() : 0;

  // ──────────────────────────────────────────────────────────────
  // CARGAR MENÚS GUARDADOS (al abrir pestaña guardados)
  // ──────────────────────────────────────────────────────────────
  const cargarMenusGuardados = useCallback(async () => {
    if (!session) return;
    setCargandoGuardados(true);
    try {
      const { data, error: errSup } = await supabase
        .from('menus_guardados')
        .select('*')
        .eq('user_id', session.user.id)
        .order('created_at', { ascending: false });

      if (errSup) throw errSup;
      setMenusGuardados(data || []);
    } catch (e) {
      console.error('Error cargando menús:', e);
      setMenusGuardados([]);
    } finally {
      setCargandoGuardados(false);
    }
  }, [session]);

  useEffect(() => {
    if (pestana === 'guardados') cargarMenusGuardados();
  }, [pestana, cargarMenusGuardados]);

  // ──────────────────────────────────────────────────────────────
  // GENERAR MENÚ SEMANAL (JSON estructurado)
  // ──────────────────────────────────────────────────────────────
  const generarMenu = async () => {
    setGenerando(true);
    setError(null);
    setMenuData(null);

    const restriccionTexto = restriccion === 'ninguna' ? 'sin restricciones especiales' : restriccion;
    const presupuestoTexto = presupuesto ? `con un presupuesto aproximado de ${presupuesto}€ a la semana` : '';
    const preferenciaTexto = preferencia ? `Preferencias adicionales: ${preferencia}.` : '';

    const prompt = `Genera un menú semanal de cocina española para ${personas} persona${personas !== '1' ? 's' : ''} durante ${dias} días.
Restricciones dietéticas: ${restriccionTexto}.
${presupuestoTexto}
${preferenciaTexto}

REGLAS ESTRICTAS:
- Cada comida (desayuno, comida, cena) DEBE ser un plato real y cocinable, no una lista de ingredientes ni productos sueltos.
- NUNCA pongas cosas como "Huevos (docena)", "1 cartón de leche" o "2 kg de tomates" como plato. Eso son ingredientes, no comidas.
- Usa platos típicos españoles y variados: lentejas, tortilla, ensaladas, pasta, arroces, pescados, carnes, etc.
- Desayunos sencillos y realistas (tostadas, yogur con fruta, café con leche y galletas, etc.).
- Cenas ligeras y realistas (ensaladas, tortillas, cremas, pescado a la plancha, etc.).
- Incluye el tiempo de preparación aproximado en minutos y la dificultad (muy fácil / fácil / media / difícil).
- La lista de la compra debe agrupar ingredientes por categoría (Frutas y verduras, Carnes y pescados, Lácteos, Despensa, Otros).

Responde ÚNICAMENTE con un objeto JSON válido, sin texto antes ni después, con esta estructura exacta:

{
  "comensales": ${personas},
  "dias_total": ${dias},
  "restriccion": "${restriccionTexto}",
  "dias": [
    {
      "dia": "Lunes",
      "desayuno": { "plato": "Tostadas con tomate y aceite", "tiempo": 5, "dificultad": "muy fácil" },
      "comida":   { "plato": "Lentejas guisadas con verduras", "tiempo": 45, "dificultad": "fácil" },
      "cena":     { "plato": "Tortilla francesa con ensalada", "tiempo": 10, "dificultad": "muy fácil" }
    }
  ],
  "lista_compra": {
    "Frutas y verduras": ["2 kg tomates", "1 lechuga"],
    "Carnes y pescados": ["500g pechuga de pollo"],
    "Lácteos": ["1 L leche"],
    "Despensa": ["1 paquete arroz"],
    "Otros": []
  }
}`;

    try {
      const res = await fetch('/api/cestita', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system: `Eres un nutricionista y chef experto en cocina española. Generas menús semanales equilibrados, variados y realistas. SIEMPRE respondes con JSON válido siguiendo la estructura pedida, sin texto adicional.`,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 2500,
        }),
      });

      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      const texto = data.content?.[0]?.text || '';

      const parsed = extraerJSON(texto);
      if (!parsed || !parsed.dias || !Array.isArray(parsed.dias)) {
        throw new Error('La IA no devolvió un formato válido. Inténtalo de nuevo.');
      }

      setMenuData(parsed);
      setVistaResultado('menu');
    } catch (e) {
      console.error('Error generando menú:', e);
      setError(e.message || 'No se pudo generar el menú. Inténtalo de nuevo.');
    } finally {
      setGenerando(false);
    }
  };

  // ──────────────────────────────────────────────────────────────
  // GENERAR RECETAS CON LA CESTA
  // ──────────────────────────────────────────────────────────────
  const generarRecetas = useCallback(async () => {
    if (!seleccionados || seleccionados.length === 0) {
      setError('Añade productos a tu cesta antes de pedir sugerencias de recetas.');
      return;
    }
    setGenerando(true);
    setError(null);
    setRespuestaCruda('');

    const productosEnCesta = (seleccionados || []).map(id => {
      const p = getProdFull(id);
      return p ? p.nombre : null;
    }).filter(Boolean);

    const prompt = `Tengo estos productos en mi cesta de la compra: ${productosEnCesta.join(', ')}.

Sugiere 5 recetas de cocina española que pueda preparar con estos ingredientes. Para cada receta indica:
- 🍴 Nombre del plato
- ⏱ Tiempo de preparación aproximado
- 📋 Ingredientes necesarios (marca con ✅ los que ya tengo en la cesta)
- 👨‍🍳 Pasos breves de preparación (máximo 5 pasos)

Separa cada receta con una línea de guiones. Sé claro y práctico.`;

    try {
      const res = await fetch('/api/cestita', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system: `Eres un chef experto en cocina española. Sugieres recetas prácticas, ricas y fáciles.`,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 2048,
        }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      setRespuestaCruda(data.content?.[0]?.text || '');
    } catch (e) {
      setError('No se pudo generar las recetas. Inténtalo de nuevo.');
    } finally {
      setGenerando(false);
    }
  }, [seleccionados, getProdFull]);

  // ──────────────────────────────────────────────────────────────
  // GENERAR ANÁLISIS NUTRICIONAL
  // ──────────────────────────────────────────────────────────────
  const generarNutricional = useCallback(async () => {
    if (!seleccionados || seleccionados.length === 0) {
      setError('Añade productos a tu cesta antes de ver el análisis nutricional.');
      return;
    }
    setGenerando(true);
    setError(null);
    setRespuestaCruda('');

    const productosEnCesta = (seleccionados || []).map(id => {
      const p = getProdFull(id);
      return p ? p.nombre : null;
    }).filter(Boolean);

    const prompt = `Analiza nutricionalmente estos productos de supermercado español:
${productosEnCesta.map((p, i) => `${i + 1}. ${p}`).join('\n')}

Para cada producto proporciona una estimación de calorías, proteínas, carbohidratos, grasas y valoración (SALUDABLE / MODERADO / OCASIONAL).

Al final incluye un RESUMEN NUTRICIONAL de la cesta y 2-3 recomendaciones concretas.

Formato para cada producto:
📦 [Nombre]
- Calorías: X kcal | Proteínas: X g | Carbohidratos: X g | Grasas: X g
- Valoración: [SALUDABLE / MODERADO / OCASIONAL]`;

    try {
      const res = await fetch('/api/cestita', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system: `Eres un nutricionista experto. Proporcionas estimaciones orientativas claras. Aclaras siempre que son estimaciones y no consejo médico.`,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: 2048,
        }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      setRespuestaCruda(data.content?.[0]?.text || '');
    } catch (e) {
      setError('No se pudo generar el análisis. Inténtalo de nuevo.');
    } finally {
      setGenerando(false);
    }
  }, [seleccionados, getProdFull]);

  // Autogenerar al entrar en recetas o nutricional si hay productos
  useEffect(() => {
    if (pestana === 'recetas' && !respuestaCruda && !generando && seleccionados?.length > 0) {
      generarRecetas();
    }
    if (pestana === 'nutricional' && !respuestaCruda && !generando && seleccionados?.length > 0) {
      generarNutricional();
    }
  }, [pestana]); // eslint-disable-line react-hooks/exhaustive-deps

  // ──────────────────────────────────────────────────────────────
  // GUARDAR MENÚ EN BIBLIOTECA
  // ──────────────────────────────────────────────────────────────
  const guardarMenu = async () => {
    if (!session || !menuData) return;
    if (menusGuardados.length >= limiteGuardados) {
      setError(`Has alcanzado el límite de ${limiteGuardados} menús guardados. Borra alguno para guardar otro.`);
      return;
    }
    setGuardando(true);
    setMensajeGuardado(null);

    try {
      const nombre = generarNombreMenu(menuData, restriccion, personas);
      const { error: errSup } = await supabase
        .from('menus_guardados')
        .insert({
          user_id: session.user.id,
          nombre,
          menu_json: menuData,
          comensales: parseInt(personas) || 2,
          dias: parseInt(dias) || 7,
        });
      if (errSup) throw errSup;
      setMensajeGuardado('✅ Menú guardado en tu biblioteca');
      setTimeout(() => setMensajeGuardado(null), 3000);
    } catch (e) {
      console.error('Error guardando:', e);
      setError('No se pudo guardar el menú.');
    } finally {
      setGuardando(false);
    }
  };

  // ──────────────────────────────────────────────────────────────
  // BORRAR MENÚ GUARDADO
  // ──────────────────────────────────────────────────────────────
  const borrarMenuGuardado = async (id) => {
    if (!window.confirm('¿Borrar este menú de tu biblioteca?')) return;
    try {
      const { error: errSup } = await supabase
        .from('menus_guardados')
        .delete()
        .eq('id', id);
      if (errSup) throw errSup;
      setMenusGuardados(prev => prev.filter(m => m.id !== id));
    } catch (e) {
      console.error('Error borrando:', e);
      alert('No se pudo borrar el menú.');
    }
  };

  // ──────────────────────────────────────────────────────────────
  // CARGAR UN MENÚ GUARDADO PARA VISUALIZAR
  // ──────────────────────────────────────────────────────────────
  const abrirMenuGuardado = (menuGuardado) => {
    setMenuData(menuGuardado.menu_json);
    setPestana('menu');
    setVistaResultado('menu');
    setError(null);
  };

  // ──────────────────────────────────────────────────────────────
  // DESCARGAR MENÚ COMO TXT
  // ──────────────────────────────────────────────────────────────
  const descargarMenuTxt = () => {
    if (!menuData) return;
    let txt = `MENÚ SEMANAL — Mi Mejor Cesta\n`;
    txt += `Comensales: ${menuData.comensales} · Días: ${menuData.dias?.length || 0}\n`;
    if (menuData.restriccion) txt += `Dieta: ${menuData.restriccion}\n`;
    txt += `\n${'='.repeat(50)}\n\n`;

    menuData.dias?.forEach(d => {
      txt += `${d.dia.toUpperCase()}\n`;
      txt += `  ☀️ Desayuno: ${d.desayuno?.plato || '—'}\n`;
      txt += `  🍽️ Comida:   ${d.comida?.plato || '—'}\n`;
      txt += `  🌙 Cena:     ${d.cena?.plato || '—'}\n\n`;
    });

    if (menuData.lista_compra) {
      txt += `\n${'='.repeat(50)}\nLISTA DE LA COMPRA\n${'='.repeat(50)}\n\n`;
      Object.entries(menuData.lista_compra).forEach(([cat, items]) => {
        if (items && items.length > 0) {
          txt += `${cat}:\n`;
          items.forEach(i => { txt += `  · ${i}\n`; });
          txt += `\n`;
        }
      });
    }

    const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'menu-semanal-mi-mejor-cesta.txt';
    a.click();
  };

  // ══════════════════════════════════════════════════════════════
  // RENDER
  // ══════════════════════════════════════════════════════════════

  const tabs = [
    { id: 'menu',        label: '🍽️ Menú semanal' },
    { id: 'recetas',     label: '💡 Recetas' },
    { id: 'nutricional', label: '🥗 Nutricional' },
    { id: 'guardados',   label: `📚 Guardados${menusGuardados.length > 0 ? ` (${menusGuardados.length})` : ''}` },
  ];

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
        maxWidth: '820px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        overflow: 'hidden',
        marginTop: '20px',
        marginBottom: '20px',
      }}>
        {/* ── HEADER ── */}
        <div style={{
          background: VERDE,
          padding: '18px 22px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ color: 'white', fontWeight: '900', fontSize: '17px' }}>
              🍽️ Menú semanal con IA
            </div>
            <div style={{ color: '#a8f0be', fontSize: '12px', marginTop: '2px' }}>
              Planifica, guarda y reutiliza tus menús favoritos
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', borderRadius: '10px', padding: '6px 12px', cursor: 'pointer', fontWeight: '700', fontSize: '13px' }}
          >
            ✕ Cerrar
          </button>
        </div>

        {/* ── TABS ── */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid #e8f0e9',
          background: '#fafbfa',
          overflowX: 'auto',
        }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => { setPestana(t.id); setError(null); }}
              style={{
                flex: '1 0 auto',
                minWidth: '110px',
                padding: '12px 14px',
                background: pestana === t.id ? 'white' : 'transparent',
                border: 'none',
                borderBottom: pestana === t.id ? `3px solid ${VERDE}` : '3px solid transparent',
                color: pestana === t.id ? VERDE : '#888',
                fontWeight: '800',
                fontSize: '12px',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div style={{ padding: '24px' }}>

          {/* ── ERROR GLOBAL ── */}
          {error && (
            <div style={{ background: '#fff0f0', color: '#d32f2f', padding: '10px 14px', borderRadius: '10px', marginBottom: '16px', fontSize: '13px', fontWeight: '600' }}>
              ⚠️ {error}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════ */}
          {/* PESTAÑA: MENÚ SEMANAL                                   */}
          {/* ══════════════════════════════════════════════════════ */}
          {pestana === 'menu' && !generando && !menuData && (
            <div style={{ display: 'grid', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                    👥 Personas
                  </label>
                  <select value={personas} onChange={e => setPersonas(e.target.value)} style={selectStyle}>
                    {['1','2','3','4','5','6'].map(n => <option key={n} value={n}>{n} persona{n !== '1' ? 's' : ''}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                    📅 Días
                  </label>
                  <select value={dias} onChange={e => setDias(e.target.value)} style={selectStyle}>
                    {['3','5','7'].map(n => <option key={n} value={n}>{n} días</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                  🥗 Restricción dietética
                </label>
                <select value={restriccion} onChange={e => setRestriccion(e.target.value)} style={selectStyle}>
                  <option value="ninguna">Sin restricciones</option>
                  <option value="vegetariano">Vegetariano</option>
                  <option value="vegano">Vegano</option>
                  <option value="sin gluten">Sin gluten</option>
                  <option value="sin lactosa">Sin lactosa</option>
                  <option value="bajo en carbohidratos">Bajo en carbohidratos</option>
                  <option value="mediterráneo">Dieta mediterránea</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                  💶 Presupuesto semanal (opcional)
                </label>
                <input
                  type="number"
                  placeholder="Ej: 80"
                  value={presupuesto}
                  onChange={e => setPresupuesto(e.target.value)}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '800', color: '#555', display: 'block', marginBottom: '6px' }}>
                  ✨ Preferencias adicionales (opcional)
                </label>
                <textarea
                  placeholder="Ej: me gusta la cocina italiana, poco picante, fácil de preparar..."
                  value={preferencia}
                  onChange={e => setPreferencia(e.target.value)}
                  rows={2}
                  style={{ ...inputStyle, resize: 'none' }}
                />
              </div>

              <button
                onClick={generarMenu}
                style={{ background: VERDE, color: 'white', border: 'none', padding: '14px', borderRadius: '12px', fontWeight: '900', fontSize: '14px', cursor: 'pointer', marginTop: '8px' }}
              >
                🍽️ Generar menú semanal
              </button>
            </div>
          )}

          {/* Cargando menú */}
          {pestana === 'menu' && generando && <Cargando texto="Generando tu menú..." subtexto="La IA está planificando tu semana. Tardará unos segundos." emoji="🍳" />}

          {/* Resultado del menú */}
          {pestana === 'menu' && !generando && menuData && (
            <div>
              {/* Sub-tabs menú / lista */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '18px' }}>
                {[
                  { id: 'menu',  label: '📅 Semana' },
                  { id: 'lista', label: '🛒 Lista de la compra' },
                ].map(v => (
                  <button
                    key={v.id}
                    onClick={() => setVistaResultado(v.id)}
                    style={{
                      padding: '8px 14px',
                      borderRadius: '10px',
                      border: `1.5px solid ${vistaResultado === v.id ? VERDE : '#eee'}`,
                      background: vistaResultado === v.id ? VERDE_CLARO : 'white',
                      color: vistaResultado === v.id ? VERDE : '#888',
                      fontWeight: '800',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    {v.label}
                  </button>
                ))}
              </div>

              {/* Vista semana */}
              {vistaResultado === 'menu' && (
                <div style={{ overflowX: 'auto', paddingBottom: '8px' }}>
                  <div style={{ display: 'flex', gap: '12px', width: 'max-content' }}>
                    {menuData.dias?.map((d, i) => <TarjetaDia key={i} dia={d} />)}
                  </div>
                </div>
              )}

              {/* Vista lista compra */}
              {vistaResultado === 'lista' && (
                <div style={{ display: 'grid', gap: '14px' }}>
                  {menuData.lista_compra && Object.entries(menuData.lista_compra).map(([categoria, items]) => {
                    if (!items || items.length === 0) return null;
                    return (
                      <div key={categoria} style={{ background: '#fafbfa', borderRadius: '12px', padding: '12px 14px' }}>
                        <div style={{ fontSize: '11px', fontWeight: '900', color: VERDE, textTransform: 'uppercase', marginBottom: '8px' }}>
                          {categoria}
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '6px' }}>
                          {items.map((item, i) => (
                            <div key={i} style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '6px',
                              padding: '6px 10px',
                              background: 'white',
                              borderRadius: '8px',
                              fontSize: '12px',
                              color: OSCURO,
                            }}>
                              <span style={{ color: VERDE, fontWeight: '900' }}>✓</span>
                              {item}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Mensaje guardado */}
              {mensajeGuardado && (
                <div style={{ marginTop: '16px', padding: '10px 14px', background: VERDE_CLARO, color: VERDE, borderRadius: '10px', fontSize: '13px', fontWeight: '700' }}>
                  {mensajeGuardado}
                </div>
              )}

              {/* Botones de acción */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '20px', flexWrap: 'wrap' }}>
                <button
                  onClick={() => { setMenuData(null); setError(null); }}
                  style={btnSecundario}
                >
                  🔄 Generar otro
                </button>
                <button
                  onClick={guardarMenu}
                  disabled={guardando || menusGuardados.length >= limiteGuardados}
                  style={{
                    ...btnPrimario,
                    opacity: (guardando || menusGuardados.length >= limiteGuardados) ? 0.5 : 1,
                    cursor: (guardando || menusGuardados.length >= limiteGuardados) ? 'not-allowed' : 'pointer',
                  }}
                >
                  {guardando ? '⏳ Guardando...' : '💾 Guardar en mi biblioteca'}
                </button>
                <button onClick={descargarMenuTxt} style={btnOscuro}>
                  📥 Descargar TXT
                </button>
              </div>

              {menusGuardados.length >= limiteGuardados && (
                <div style={{ marginTop: '10px', fontSize: '11px', color: '#888' }}>
                  Límite de {limiteGuardados} menús guardados alcanzado. Borra alguno para guardar otro.
                </div>
              )}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════ */}
          {/* PESTAÑA: RECETAS                                        */}
          {/* ══════════════════════════════════════════════════════ */}
          {pestana === 'recetas' && (
            <div>
              {(!seleccionados || seleccionados.length === 0) ? (
                <AvisoVacio
                  emoji="🛒"
                  titulo="Tu cesta está vacía"
                  texto="Añade productos a tu cesta desde el catálogo para que la IA pueda sugerirte recetas."
                />
              ) : generando ? (
                <Cargando texto="Buscando recetas..." subtexto="Analizando los productos de tu cesta." emoji="💡" />
              ) : respuestaCruda ? (
                <>
                  <BloqueTexto texto={respuestaCruda} />
                  <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                    <button onClick={generarRecetas} style={btnSecundario}>🔄 Generar otras</button>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '30px' }}>
                  <button onClick={generarRecetas} style={btnPrimario}>
                    💡 Sugerir recetas con mi cesta
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════ */}
          {/* PESTAÑA: NUTRICIONAL                                    */}
          {/* ══════════════════════════════════════════════════════ */}
          {pestana === 'nutricional' && (
            <div>
              {(!seleccionados || seleccionados.length === 0) ? (
                <AvisoVacio
                  emoji="🥗"
                  titulo="Tu cesta está vacía"
                  texto="Añade productos a tu cesta para ver su análisis nutricional."
                />
              ) : generando ? (
                <Cargando texto="Analizando tu cesta..." subtexto="Calculando valores nutricionales orientativos." emoji="🥗" />
              ) : respuestaCruda ? (
                <>
                  <BloqueTexto texto={respuestaCruda} />
                  <div style={{ marginTop: '12px', padding: '10px 14px', background: '#fff8e1', borderRadius: '10px', fontSize: '11px', color: '#856404', fontWeight: '600' }}>
                    ⚠️ Datos orientativos generados por IA. No constituyen consejo médico ni nutricional profesional.
                  </div>
                  <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
                    <button onClick={generarNutricional} style={btnSecundario}>🔄 Regenerar</button>
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: '30px' }}>
                  <button onClick={generarNutricional} style={btnPrimario}>
                    🥗 Analizar mi cesta
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ══════════════════════════════════════════════════════ */}
          {/* PESTAÑA: GUARDADOS                                      */}
          {/* ══════════════════════════════════════════════════════ */}
          {pestana === 'guardados' && (
            <div>
              {cargandoGuardados ? (
                <Cargando texto="Cargando tus menús..." emoji="📚" />
              ) : menusGuardados.length === 0 ? (
                <AvisoVacio
                  emoji="📚"
                  titulo="Sin menús guardados aún"
                  texto="Genera un menú y pulsa 'Guardar en mi biblioteca' para reutilizarlo cuando quieras."
                />
              ) : (
                <div>
                  <div style={{ fontSize: '12px', color: '#888', marginBottom: '14px' }}>
                    {menusGuardados.length} de {limiteGuardados} menús guardados
                  </div>
                  <div style={{ display: 'grid', gap: '10px' }}>
                    {menusGuardados.map(m => (
                      <div key={m.id} style={{
                        background: 'white',
                        border: '1.5px solid #e8f0e9',
                        borderRadius: '12px',
                        padding: '14px 16px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: '10px',
                      }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontWeight: '800', fontSize: '14px', color: OSCURO, marginBottom: '2px' }}>
                            {m.nombre}
                          </div>
                          <div style={{ fontSize: '11px', color: '#888' }}>
                            👥 {m.comensales} · 📅 {m.dias} días · {new Date(m.created_at).toLocaleDateString('es-ES')}
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            onClick={() => abrirMenuGuardado(m)}
                            style={{ background: VERDE, color: 'white', border: 'none', padding: '8px 12px', borderRadius: '8px', fontWeight: '700', fontSize: '11px', cursor: 'pointer' }}
                          >
                            Abrir
                          </button>
                          <button
                            onClick={() => borrarMenuGuardado(m.id)}
                            style={{ background: '#fff0f0', color: '#d32f2f', border: 'none', padding: '8px 10px', borderRadius: '8px', fontWeight: '700', fontSize: '11px', cursor: 'pointer' }}
                          >
                            🗑
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════
// SUB-COMPONENTES Y ESTILOS
// ══════════════════════════════════════════════════════════════════

const Cargando = ({ texto, subtexto, emoji = '🍳' }) => (
  <div style={{ textAlign: 'center', padding: '40px 20px' }}>
    <div style={{ fontSize: '40px', marginBottom: '16px' }}>{emoji}</div>
    <div style={{ fontWeight: '900', fontSize: '16px', color: OSCURO, marginBottom: '8px' }}>{texto}</div>
    {subtexto && <div style={{ fontSize: '13px', color: '#888' }}>{subtexto}</div>}
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
);

const AvisoVacio = ({ emoji, titulo, texto }) => (
  <div style={{ textAlign: 'center', padding: '40px 20px' }}>
    <div style={{ fontSize: '44px', marginBottom: '12px' }}>{emoji}</div>
    <div style={{ fontWeight: '900', fontSize: '15px', color: OSCURO, marginBottom: '6px' }}>{titulo}</div>
    <div style={{ fontSize: '13px', color: '#888', maxWidth: '380px', margin: '0 auto' }}>{texto}</div>
  </div>
);

const BloqueTexto = ({ texto }) => (
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
    {texto}
  </div>
);

const selectStyle = {
  width: '100%',
  padding: '10px',
  borderRadius: '10px',
  border: '1.5px solid #ddd',
  fontSize: '14px',
  fontFamily: 'inherit',
};

const inputStyle = {
  width: '100%',
  padding: '10px',
  borderRadius: '10px',
  border: '1.5px solid #ddd',
  fontSize: '13px',
  fontFamily: 'inherit',
  boxSizing: 'border-box',
};

const btnPrimario = {
  background: VERDE,
  color: 'white',
  border: 'none',
  padding: '12px 18px',
  borderRadius: '12px',
  fontWeight: '900',
  fontSize: '13px',
  cursor: 'pointer',
};

const btnSecundario = {
  background: VERDE_CLARO,
  color: VERDE,
  border: `1.5px solid ${VERDE}`,
  padding: '10px 16px',
  borderRadius: '10px',
  fontWeight: '800',
  fontSize: '12px',
  cursor: 'pointer',
};

const btnOscuro = {
  background: OSCURO,
  color: 'white',
  border: 'none',
  padding: '10px 16px',
  borderRadius: '10px',
  fontWeight: '800',
  fontSize: '12px',
  cursor: 'pointer',
};

export default MenuSemanal;
