import React, { useState } from 'react';
import { supabase } from '../supabaseClient';
import AuthModal from './AuthModal';

const SyncHeader = ({ session, syncActiva, setSyncActiva }) => {
  const [modalAbierto, setModalAbierto] = useState(false);

  return (
    <>
      {modalAbierto && <AuthModal onClose={() => setModalAbierto(false)} />}

      <div className="no-print" style={{ 
        background: '#102215', 
        color: 'white', 
        padding: '8px 16px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        fontSize: '11px',
        width: '100%',
        boxSizing: 'border-box',
        flexWrap: 'wrap',
        gap: '8px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: '800', display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
            <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: (session && syncActiva) ? '#13ec49' : '#ff4b4b', flexShrink: 0 }}></div>
            {session ? (syncActiva ? `ONLINE: ${session.user.email}` : 'MODO LOCAL (PAUSA)') : 'MODO LOCAL'}
          </span>
          {session && (
            <button onClick={() => setSyncActiva(!syncActiva)} style={{ background: syncActiva ? '#333' : '#13ec49', color: syncActiva ? '#ccc' : '#102215', border: 'none', padding: '3px 8px', borderRadius: '4px', fontWeight: '900', cursor: 'pointer', fontSize: '9px', whiteSpace: 'nowrap' }}>
              {syncActiva ? '🔌 DESACTIVAR SYNC' : '🔄 ACTIVAR SYNC'}
            </button>
          )}
        </div>

        {session ? (
          <button onClick={() => supabase.auth.signOut()} style={{ background: 'none', border: '1px solid #ff4b4b', color: '#ff4b4b', padding: '3px 8px', borderRadius: '4px', cursor: 'pointer', fontWeight: '700', whiteSpace: 'nowrap' }}>
            SALIR
          </button>
        ) : (
          <button onClick={() => setModalAbierto(true)} style={{ background: '#13ec49', color: '#102215', border: 'none', padding: '5px 12px', borderRadius: '4px', fontWeight: '800', cursor: 'pointer', whiteSpace: 'nowrap' }}>
            LOGIN / REGISTRO
          </button>
        )}
      </div>
    </>
  );
};

export default SyncHeader;
