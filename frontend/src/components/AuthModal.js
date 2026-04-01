import React, { useState } from 'react';
import { supabase } from '../supabaseClient';

const AuthModal = ({ onClose }) => {
  const [modo, setModo] = useState('login'); // 'login' | 'registro' | 'magic'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState(null);

  const limpiar = () => { setError(null); setMensaje(null); };

  const handleLogin = async () => {
    if (!email || !password) return setError('Introduce email y contraseña.');
    setCargando(true); limpiar();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setCargando(false);
    if (error) setError('Email o contraseña incorrectos.');
    else onClose();
  };

  const handleRegistro = async () => {
    if (!email || !password) return setError('Introduce email y contraseña.');
    if (password.length < 6) return setError('La contraseña debe tener al menos 6 caracteres.');
    setCargando(true); limpiar();
    const { error } = await supabase.auth.signUp({ email, password });
    setCargando(false);
    if (error) setError(error.message);
    else setMensaje('¡Cuenta creada! Revisa tu email para confirmarla.');
  };

  const handleMagicLink = async () => {
    if (!email) return setError('Introduce tu email.');
    setCargando(true); limpiar();
    const { error } = await supabase.auth.signInWithOtp({ email });
    setCargando(false);
    if (error) setError(error.message);
    else setMensaje('¡Enlace enviado! Revisa tu email.');
  };

  const handleGoogle = async () => {
  await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: window.location.origin }
  });
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 14px',
    borderRadius: '10px',
    border: '1px solid #ddd',
    fontSize: '14px',
    boxSizing: 'border-box',
    outline: 'none',
    marginBottom: '10px',
    fontFamily: 'inherit',
  };

  const btnPrimario = {
    width: '100%',
    background: '#037623',
    color: 'white',
    border: 'none',
    padding: '13px',
    borderRadius: '10px',
    fontWeight: '900',
    fontSize: '14px',
    cursor: cargando ? 'not-allowed' : 'pointer',
    opacity: cargando ? 0.7 : 1,
    marginBottom: '10px',
    fontFamily: 'inherit',
  };

  const btnSecundario = {
    width: '100%',
    background: 'white',
    color: '#037623',
    border: '1px solid #037623',
    padding: '12px',
    borderRadius: '10px',
    fontWeight: '700',
    fontSize: '13px',
    cursor: 'pointer',
    marginBottom: '10px',
    fontFamily: 'inherit',
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '20px', boxSizing: 'border-box',
    }} onClick={onClose}>
      <div style={{
        background: 'white', borderRadius: '20px',
        padding: '32px 28px', width: '100%', maxWidth: '380px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
        position: 'relative',
      }} onClick={e => e.stopPropagation()}>

        {/* Cerrar */}
        <button onClick={onClose} style={{
          position: 'absolute', top: '16px', right: '16px',
          background: 'none', border: 'none', fontSize: '20px',
          cursor: 'pointer', color: '#999', lineHeight: 1,
        }}>✕</button>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{ fontSize: '32px' }}>🛒</div>
          <h2 style={{ color: '#037623', fontWeight: '900', fontSize: '20px', margin: '8px 0 4px' }}>
            Mi Mejor Cesta
          </h2>
          <p style={{ color: '#888', fontSize: '13px', margin: 0 }}>
            {modo === 'login' ? 'Inicia sesión para guardar tu cesta' :
             modo === 'registro' ? 'Crea tu cuenta gratuita' :
             'Recibe un enlace mágico en tu email'}
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', borderRadius: '10px', border: '1px solid #eee', marginBottom: '20px', overflow: 'hidden' }}>
          {[['login', 'Entrar'], ['registro', 'Registrarse']].map(([m, label]) => (
            <button key={m} onClick={() => { setModo(m); limpiar(); }} style={{
              flex: 1, padding: '10px', border: 'none', cursor: 'pointer',
              fontWeight: '700', fontSize: '13px', fontFamily: 'inherit',
              background: modo === m ? '#037623' : 'white',
              color: modo === m ? 'white' : '#666',
            }}>{label}</button>
          ))}
        </div>

        {/* Formulario */}
        {modo !== 'magic' && (
          <>
            <input
              type="email" placeholder="Tu email" value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (modo === 'login' ? handleLogin() : handleRegistro())}
              style={inputStyle}
            />
            <input
              type="password" placeholder="Contraseña (mín. 6 caracteres)" value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (modo === 'login' ? handleLogin() : handleRegistro())}
              style={inputStyle}
            />
            <button
              onClick={modo === 'login' ? handleLogin : handleRegistro}
              disabled={cargando} style={btnPrimario}
            >
              {cargando ? 'Cargando...' : modo === 'login' ? 'Entrar' : 'Crear cuenta gratis'}
            </button>
          </>
        )}

        {/* Magic link */}
        {modo === 'magic' && (
          <>
            <input
              type="email" placeholder="Tu email" value={email}
              onChange={e => setEmail(e.target.value)}
              style={inputStyle}
            />
            <button onClick={handleMagicLink} disabled={cargando} style={btnPrimario}>
              {cargando ? 'Enviando...' : 'Enviar enlace mágico'}
            </button>
          </>
        )}

        {/* Separador */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: '4px 0 10px' }}>
          <div style={{ flex: 1, height: '1px', background: '#eee' }}/>
          <span style={{ fontSize: '12px', color: '#aaa' }}>o</span>
          <div style={{ flex: 1, height: '1px', background: '#eee' }}/>
        </div>

        {/* Google */}
        <button onClick={handleGoogle} style={{ ...btnSecundario, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Entrar con Google
        </button>

        {/* Magic link toggle */}
        <button onClick={() => { setModo(modo === 'magic' ? 'login' : 'magic'); limpiar(); }} style={{
          background: 'none', border: 'none', color: '#037623', fontSize: '12px',
          cursor: 'pointer', width: '100%', textAlign: 'center', fontWeight: '700', padding: '4px',
        }}>
          {modo === 'magic' ? '← Volver' : '✉️ Entrar con enlace mágico'}
        </button>

        {/* Mensajes */}
        {error && (
          <div style={{ marginTop: '12px', background: '#fff0f0', color: '#d32f2f', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', fontWeight: '600' }}>
            {error}
          </div>
        )}
        {mensaje && (
          <div style={{ marginTop: '12px', background: '#f0fdf4', color: '#037623', padding: '10px 12px', borderRadius: '8px', fontSize: '13px', fontWeight: '600' }}>
            {mensaje}
          </div>
        )}

        {/* RGPD */}
        {modo === 'registro' && (
          <p style={{ fontSize: '11px', color: '#aaa', textAlign: 'center', marginTop: '16px', lineHeight: 1.4 }}>
            Al registrarte aceptas nuestra política de privacidad. Solo guardamos tu email y tu lista de compra.
          </p>
        )}
      </div>
    </div>
  );
};

export default AuthModal;
