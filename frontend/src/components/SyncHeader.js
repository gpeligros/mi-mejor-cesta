import React from 'react';
import { supabase } from '../supabaseClient';

const SyncHeader = ({ session, syncActiva, setSyncActiva }) => {
  const handleLogin = async () => {
    const email = window.prompt("Introduce tu email para el enlace mágico:");
    if (email) await supabase.auth.signInWithOtp({ email });
  };

  return (
    <div className="no-print" style={{ background: '#102215', color: 'white', padding: '10px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
        <span style={{ fontWeight: '800', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: (session && syncActiva) ? '#13ec49' : '#ff4b4b' }}></div>
          {session ? (syncActiva ? `ONLINE: ${session.user.email}` : "MODO LOCAL (PAUSA)") : "MODO LOCAL"}
        </span>
        {session && (
          <button onClick={() => setSyncActiva(!syncActiva)} style={{ background: syncActiva ? '#333' : '#13ec49', color: syncActiva ? '#ccc' : '#102215', border: 'none', padding: '3px 8px', borderRadius: '4px', fontWeight: '900', cursor: 'pointer', fontSize: '9px' }}>
            {syncActiva ? "🔌 DESACTIVAR SYNC" : "🔄 ACTIVAR SYNC"}
          </button>
        )}
      </div>
      {session ? (
        <button onClick={() => supabase.auth.signOut()} style={{ background: 'none', border: '1px solid #ff4b4b', color: '#ff4b4b', padding: '3px 8px', borderRadius: '4px', cursor: 'pointer', fontWeight: '700' }}>SALIR</button>
      ) : (
        <button onClick={handleLogin} style={{ background: '#13ec49', color: '#102215', border: 'none', padding: '5px 10px', borderRadius: '4px', fontWeight: '800', cursor: 'pointer' }}>LOGIN</button>
      )}
    </div>
  );
};

export default SyncHeader;