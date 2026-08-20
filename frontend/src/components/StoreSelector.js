import React, { useState } from 'react';

const VERDE = '#037623';
const OSCURO = '#102215';

const StoreSelector = ({ listaSupers, supersActivos, setSupersActivos }) => {
  const [abierto, setAbierto] = useState(false);
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  // Solo mostramos los supers marcados como visible
  const supersVisibles = listaSupers.filter(s => s.visible !== false);

  return (
    <section
      className="no-print"
      style={{
        backgroundColor: 'white',
        padding: '14px 18px',
        borderRadius: '16px',
        border: '1px solid #e0e6e1',
        borderTop: `3px solid ${VERDE}`,
        marginBottom: '25px',
        boxShadow: '0 4px 16px rgba(3, 118, 35, 0.06)',
      }}
    >
      {/* DESKTOP: fila compacta */}
      {!isMobile && (
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
            <span style={{ fontSize: '14px' }}>🛍️</span>
            <span style={{ fontWeight: '900', fontSize: '12px', color: OSCURO, letterSpacing: '0.3px' }}>
              MIS TIENDAS
            </span>
            <span style={{
              background: VERDE,
              color: 'white',
              fontSize: '10px',
              fontWeight: '900',
              padding: '2px 7px',
              borderRadius: '10px',
              marginLeft: '2px',
            }}>
              {supersActivos.length}
            </span>
          </div>
          {supersVisibles.map(s => {
            const activo = supersActivos.includes(s.id);
            return (
              <label
                key={s.id}
                style={{
                  padding: '6px 12px',
                  borderRadius: '12px',
                  border: activo ? `1.5px solid ${VERDE}` : '1.5px solid #e8e8e8',
                  cursor: 'pointer',
                  background: activo
                    ? `linear-gradient(135deg, #e8fdf0, #d4f7e0)`
                    : 'white',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  boxShadow: activo ? '0 2px 8px rgba(3, 118, 35, 0.15)' : 'none',
                  transform: activo ? 'translateY(-1px)' : 'none',
                }}
                onMouseEnter={e => { if (!activo) e.currentTarget.style.borderColor = '#bbb'; }}
                onMouseLeave={e => { if (!activo) e.currentTarget.style.borderColor = '#e8e8e8'; }}
              >
                <input
                  type="checkbox"
                  checked={activo}
                  onChange={() => {
                    if (activo) {
                      setSupersActivos(prev => prev.filter(x => x !== s.id));
                    } else {
                      setSupersActivos([...supersActivos, s.id]);
                    }
                  }}
                  style={{ width: '13px', height: '13px', cursor: 'pointer', accentColor: VERDE }}
                />
                <img
                  src={s.logo}
                  alt={s.id}
                  title={s.id}
                  style={{
                    height: '24px',
                    maxWidth: '76px',
                    objectFit: 'contain',
                    filter: activo ? 'none' : 'grayscale(35%) opacity(0.75)',
                    transition: 'filter 0.2s ease',
                  }}
                />
              </label>
            );
          })}
        </div>
      )}

      {/* MÓVIL: acordeón */}
      {isMobile && (
        <>
          <div
            onClick={() => setAbierto(!abierto)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              padding: '2px 0',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '15px' }}>🛍️</span>
              <span style={{ fontWeight: '900', fontSize: '13px', color: OSCURO }}>
                MIS TIENDAS
              </span>
              <span style={{
                background: VERDE, color: 'white', fontSize: '10px', fontWeight: '900',
                padding: '2px 8px', borderRadius: '10px',
              }}>
                {supersActivos.length}
              </span>
            </div>
            <span style={{
              fontSize: '16px', color: VERDE, fontWeight: '900',
              width: '26px', height: '26px', borderRadius: '50%',
              background: '#e8fdf0', display: 'flex', alignItems: 'center', justifyContent: 'center',
              transform: abierto ? 'rotate(180deg)' : 'none', transition: 'transform 0.25s ease',
            }}>
              ▾
            </span>
          </div>

          {abierto && (
            <div style={{ marginTop: '12px', display: 'grid', gap: '8px' }}>
              {supersVisibles.map(s => {
                const activo = supersActivos.includes(s.id);
                return (
                  <label
                    key={s.id}
                    style={{
                      padding: '11px 14px',
                      borderRadius: '12px',
                      border: activo ? `2px solid ${VERDE}` : '2px solid #eee',
                      cursor: 'pointer',
                      background: activo ? 'linear-gradient(135deg, #e8fdf0, #d4f7e0)' : 'white',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      fontSize: '14px',
                      fontWeight: '700',
                      transition: 'all 0.2s ease',
                      boxShadow: activo ? '0 2px 8px rgba(3, 118, 35, 0.15)' : 'none',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={activo}
                      onChange={() => {
                        if (activo) {
                          setSupersActivos(prev => prev.filter(x => x !== s.id));
                        } else {
                          setSupersActivos([...supersActivos, s.id]);
                        }
                      }}
                      style={{ width: '20px', height: '20px', cursor: 'pointer', accentColor: VERDE }}
                    />
                    <img src={s.logo} alt={s.id} style={{ width: '28px', height: '28px', objectFit: 'contain' }} />
                    <span>{s.id}</span>
                    {activo && <span style={{ marginLeft: 'auto', color: VERDE, fontSize: '16px' }}>✓</span>}
                  </label>
                );
              })}
            </div>
          )}
        </>
      )}
    </section>
  );
};

export default StoreSelector;
