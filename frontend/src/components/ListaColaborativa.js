import React, { useState, useEffect, useRef } from 'react';
import { supabase } from '../supabaseClient';

// Genera código de 6 caracteres alfanumérico
const generarCodigo = () => Math.random().toString(36).substring(2, 8).toUpperCase();

const ListaColaborativa = ({ session, seleccionados, setSeleccionados, comprados, setComprados, onClose }) => {
  const [modo, setModo] = useState('menu'); // 'menu' | 'crear' | 'unirse' | 'activa'
  const [codigo, setCodigo] = useState('');
  const [codigoInput, setCodigoInput] = useState('');
  const [nombreLista, setNombreLista] = useState('Mi lista compartida');
  const [listaId, setListaId] = useState(null);
  const [miembros, setMiembros] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [copiado, setCopiado] = useState(false);
  const canalRef = useRef(null);

  // Suscribirse a cambios en tiempo real
  useEffect(() => {
    if (!listaId) return;

    const canal = supabase
      .channel(`lista_${listaId}`)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'listas_colaborativas',
        filter: `id=eq.${listaId}`,
      }, (payload) => {
        const datos = payload.new;
        if (datos.productos) setSeleccionados(datos.productos);
        if (datos.comprados) setComprados(datos.comprados);
        if (datos.miembros) setMiembros(datos.miembros);
      })
      .subscribe();

    canalRef.current = canal;
    return () => supabase.removeChannel(canal);
  }, [listaId, setSeleccionados, setComprados]);
  const crearLista = async () => {
    if (!session) return setError('Debes iniciar sesión para crear una lista colaborativa.');
    setCargando(true); setError(null);
    const nuevoCodigo = generarCodigo();
    const { data, error } = await supabase.from('listas_colaborativas').insert({
      codigo: nuevoCodigo,
      nombre: nombreLista,
      productos: seleccionados,
      comprados: comprados,
      creador_id: session.user.id,
      miembros: [session.user.email],
    }).select().single();

    setCargando(false);
    if (error) return setError('Error creando la lista.');
    setListaId(data.id);
    setCodigo(nuevoCodigo);
    setMiembros([session.user.email]);
    setModo('activa');
  };

  const unirseALista = async () => {
    if (!session) return setError('Debes iniciar sesión para unirte a una lista.');
    if (codigoInput.length < 6) return setError('Introduce el código de 6 caracteres.');
    setCargando(true); setError(null);

    const { data, error } = await supabase
      .from('listas_colaborativas')
      .select()
      .eq('codigo', codigoInput.toUpperCase())
      .single();

    if (error || !data) {
      setCargando(false);
      return setError('Código no encontrado. Verifica que sea correcto.');
    }

    // Añadir email a miembros si no está
    const nuevosMiembros = data.miembros.includes(session.user.email)
      ? data.miembros
      : [...data.miembros, session.user.email];

    await supabase.from('listas_colaborativas').update({
      miembros: nuevosMiembros
    }).eq('id', data.id);

    setListaId(data.id);
    setCodigo(data.codigo);
    setNombreLista(data.nombre);
    setSeleccionados(data.productos || []);
    setComprados(data.comprados || []);
    setMiembros(nuevosMiembros);
    setCargando(false);
    setModo('activa');
  };

  const copiarCodigo = () => {
    navigator.clipboard.writeText(codigo);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  const compartirWhatsApp = () => {
    const url = window.location.origin;
    const texto = `🛒 Únete a mi lista de compra "${nombreLista}" en Mi Mejor Cesta.\n\nCódigo: *${codigo}*\n\nEntra en: ${url}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(texto)}`, '_blank');
  };

  const compartirEmail = () => {
    const url = window.location.origin;
    const asunto = `Lista de compra compartida: ${nombreLista}`;
    const cuerpo = `Hola!\n\nTe comparto mi lista de compra "${nombreLista}" en Mi Mejor Cesta.\n\nCódigo de acceso: ${codigo}\n\nEntra en: ${url} y usa el código para unirte.\n\n¡Hasta luego!`;
    window.open(`mailto:?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(cuerpo)}`);
  };

  const salirDeLista = async () => {
    if (canalRef.current) supabase.removeChannel(canalRef.current);
    setListaId(null);
    setCodigo('');
    setMiembros([]);
    setModo('menu');
  };

  const s = {
    overlay: { position: 'fixed', inset: 0, zIndex: 9998, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', boxSizing: 'border-box' },
    modal: { background: 'white', borderRadius: '20px', padding: '28px 24px', width: '100%', maxWidth: '400px', position: 'relative', maxHeight: '90vh', overflowY: 'auto' },
    titulo: { fontWeight: '900', fontSize: '18px', color: '#102215', margin: '0 0 6px' },
    subtitulo: { fontSize: '13px', color: '#888', margin: '0 0 20px' },
    btn: (bg, color) => ({ width: '100%', background: bg, color, border: 'none', padding: '13px', borderRadius: '10px', fontWeight: '900', fontSize: '14px', cursor: 'pointer', marginBottom: '10px', fontFamily: 'inherit' }),
    input: { width: '100%', padding: '12px 14px', borderRadius: '10px', border: '1px solid #ddd', fontSize: '14px', boxSizing: 'border-box', marginBottom: '10px', fontFamily: 'inherit' },
    codigo: { background: '#f4faf6', border: '2px dashed #037623', borderRadius: '12px', padding: '16px', textAlign: 'center', marginBottom: '16px' },
  };

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.modal} onClick={e => e.stopPropagation()}>
        <button onClick={onClose} style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', color: '#999' }}>✕</button>

        {/* MENÚ INICIAL */}
        {modo === 'menu' && (
          <>
            <h2 style={s.titulo}>👥 Lista colaborativa</h2>
            <p style={s.subtitulo}>Comparte tu lista en tiempo real con otra persona</p>
            {!session && (
              <div style={{ background: '#fff8e1', border: '1px solid #ffc107', borderRadius: '10px', padding: '12px', fontSize: '13px', color: '#856404', marginBottom: '16px' }}>
                ⚠️ Necesitas iniciar sesión para usar listas colaborativas.
              </div>
            )}
            <button onClick={() => setModo('crear')} style={s.btn('#037623', 'white')}>
              ✨ Crear nueva lista compartida
            </button>
            <button onClick={() => setModo('unirse')} style={s.btn('white', '#037623')} onMouseEnter={e => e.currentTarget.style.background = '#f0fdf4'} onMouseLeave={e => e.currentTarget.style.background = 'white'}>
              🔗 Unirme con un código
            </button>
          </>
        )}

        {/* CREAR LISTA */}
        {modo === 'crear' && (
          <>
            <h2 style={s.titulo}>✨ Nueva lista compartida</h2>
            <p style={s.subtitulo}>Se compartirán tus {seleccionados.length} productos actuales</p>
            <input style={s.input} placeholder="Nombre de la lista" value={nombreLista} onChange={e => setNombreLista(e.target.value)} />
            <button onClick={crearLista} disabled={cargando} style={s.btn('#037623', 'white')}>
              {cargando ? 'Creando...' : 'Crear y obtener código'}
            </button>
            <button onClick={() => setModo('menu')} style={s.btn('#f5f5f5', '#666')}>← Volver</button>
          </>
        )}

        {/* UNIRSE */}
        {modo === 'unirse' && (
          <>
            <h2 style={s.titulo}>🔗 Unirse a una lista</h2>
            <p style={s.subtitulo}>Introduce el código que te han compartido</p>
            <input
              style={{ ...s.input, textTransform: 'uppercase', fontSize: '20px', textAlign: 'center', letterSpacing: '4px', fontWeight: '900' }}
              placeholder="ABC123"
              maxLength={6}
              value={codigoInput}
              onChange={e => setCodigoInput(e.target.value.toUpperCase())}
            />
            <button onClick={unirseALista} disabled={cargando} style={s.btn('#037623', 'white')}>
              {cargando ? 'Buscando...' : 'Unirme a la lista'}
            </button>
            <button onClick={() => setModo('menu')} style={s.btn('#f5f5f5', '#666')}>← Volver</button>
          </>
        )}

        {/* LISTA ACTIVA */}
        {modo === 'activa' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h2 style={{ ...s.titulo, margin: 0 }}>🟢 {nombreLista}</h2>
                <p style={{ fontSize: '11px', color: '#13ec49', fontWeight: '700', margin: '4px 0 0' }}>EN TIEMPO REAL</p>
              </div>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#13ec49', boxShadow: '0 0 8px #13ec49' }}></div>
            </div>

            {/* Código */}
            <div style={s.codigo}>
              <p style={{ fontSize: '11px', color: '#888', margin: '0 0 6px', fontWeight: '700' }}>CÓDIGO DE ACCESO</p>
              <p style={{ fontSize: '32px', fontWeight: '900', color: '#037623', margin: '0 0 8px', letterSpacing: '4px' }}>{codigo}</p>
              <button onClick={copiarCodigo} style={{ background: copiado ? '#037623' : '#e8fdf0', color: copiado ? 'white' : '#037623', border: 'none', padding: '6px 14px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer', fontSize: '12px' }}>
                {copiado ? '✅ Copiado' : '📋 Copiar código'}
              </button>
            </div>

            {/* Miembros */}
            {miembros.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <p style={{ fontSize: '11px', fontWeight: '700', color: '#888', margin: '0 0 8px' }}>MIEMBROS ({miembros.length})</p>
                {miembros.map((m, i) => (
                  <div key={i} style={{ fontSize: '13px', padding: '6px 10px', background: '#f4faf6', borderRadius: '8px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#13ec49', flexShrink: 0 }}></span>
                    {m}
                  </div>
                ))}
              </div>
            )}

            {/* Compartir */}
            <p style={{ fontSize: '11px', fontWeight: '700', color: '#888', margin: '0 0 8px' }}>COMPARTIR POR</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' }}>
              <button onClick={compartirWhatsApp} style={{ background: '#25D366', color: 'white', border: 'none', padding: '10px', borderRadius: '10px', fontWeight: '700', cursor: 'pointer', fontSize: '13px' }}>
                📱 WhatsApp
              </button>
              <button onClick={compartirEmail} style={{ background: '#f5f5f5', color: '#333', border: 'none', padding: '10px', borderRadius: '10px', fontWeight: '700', cursor: 'pointer', fontSize: '13px' }}>
                ✉️ Email
              </button>
            </div>

            <button onClick={salirDeLista} style={s.btn('#fff0f0', '#d32f2f')}>
              🚪 Salir de la lista
            </button>
          </>
        )}

        {error && (
          <div style={{ marginTop: '12px', background: '#fff0f0', color: '#d32f2f', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', fontWeight: '600' }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default ListaColaborativa;
