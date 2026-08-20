import React, { useState } from 'react';

const VERDE = '#037623';
const VERDE_OSCURO = '#025c1c';

const StoreSelector = ({ listaSupers, supersActivos, setSupersActivos }) => {
  const [abierto, setAbierto] = useState(false);
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  const supersVisibles = listaSupers.filter(s => s.visible !== false);

  const toggle = (id) => {
    if (supersActivos.includes(id)) {
      setSupersActivos(prev => prev.filter(x => x !== id));
    } else {
      setSupersActivos([...supersActivos, id]);
    }
  };

  return (
    <section
      className="no-print"
      style={{
        backgroundColor: 'white',
        padding: isMobile ? '16px' : '18px 20px',
        borderRadius: '20px',
        border: '1px solid #e8ede9',
        marginBottom: '25px',
        boxShadow: '0 6px 24px rgba(3, 118, 35, 0.07)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div style={{
        position: 'absolute', top: 0, left: 0, bottom: 0, width: '4px',
        background: `repeating-linear-gradient(180deg, ${VERDE} 0, ${VERDE} 6px, transparent 6px, transparent 12px)`,
      }} />

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: isMobile ? 0 : '14px', cursor: isMobile ? 'pointer' : 'default',
      }} onClick={isMobile ? () => setAbierto(!abierto) : undefined}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
          <span style={{
            fontSize: '11px', fontWeight: '900', color: VERDE, letterSpacing: '1.5px',
            textTransform: 'uppercase',
          }}>
            Mis tiendas
          </span>
          <span style={{ fontSize: '11px', fontWeight: '700', color: '#aaa' }}>
            {supersActivos.length} de {supersVisibles.length} activas
          </span>
        </div>
        {isMobile && (
          <span style={{
            fontSize: '14px', color: VERDE, fontWeight: '900',
            width: '28px', height: '28px', borderRadius: '50%',
            background: '#eefaf1', display: 'flex', alignItems: 'center', justifyContent: 'center',
            transform: abierto ? 'rotate(180deg)' : 'none', transition: 'transform 0.25s ease',
          }}>
            ▾
          </span>
        )}
      </div>

      {/* Tarjetas de ANCHO FLEXIBLE — cada logo ocupa lo que necesita a una
          altura fija de 40px. Los logos reales tienen proporciones muy
          distintas (Mercadona 5.87:1, DIA 1.8:1) y forzarlos a una tarjeta
          cuadrada aplastaba los más anchos. Así cada uno se ve a tamaño
          consistente, como hacen los comparadores reales (Idealo, Google
          Shopping) cuando mezclan logos de marcas con formatos distintos. */}
      {(!isMobile || abierto) && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: isMobile ? '10px' : '12px',
          marginTop: isMobile ? '14px' : 0,
        }}>
          {supersVisibles.map(s => {
            const activo = supersActivos.includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => toggle(s.id)}
                aria-pressed={activo}
                style={{
                  position: 'relative',
                  height: isMobile ? '52px' : '56px',
                  borderRadius: '14px',
                  border: activo ? `2px solid ${VERDE}` : '2px solid #ecefec',
                  background: activo ? 'white' : '#fafbfa',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '0 20px',
                  transition: 'all 0.22s cubic-bezier(0.34, 1.3, 0.64, 1)',
                  boxShadow: activo
                    ? '0 6px 16px rgba(3, 118, 35, 0.16)'
                    : '0 1px 3px rgba(0,0,0,0.03)',
                  transform: activo ? 'translateY(-2px) scale(1.02)' : 'none',
                }}
                onMouseEnter={e => {
                  if (!activo) {
                    e.currentTarget.style.borderColor = '#cfd6d0';
                    e.currentTarget.style.background = 'white';
                  }
                }}
                onMouseLeave={e => {
                  if (!activo) {
                    e.currentTarget.style.borderColor = '#ecefec';
                    e.currentTarget.style.background = '#fafbfa';
                  }
                }}
              >
                <img
                  src={s.logo}
                  alt={s.id}
                  title={s.id}
                  style={{
                    height: isMobile ? '30px' : '32px',
                    width: 'auto',
                    objectFit: 'contain',
                    filter: activo ? 'none' : 'grayscale(85%) opacity(0.55)',
                    transition: 'filter 0.22s ease',
                  }}
                />
                <div style={{
                  position: 'absolute',
                  top: '-8px',
                  right: '-8px',
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  background: activo ? `linear-gradient(135deg, ${VERDE}, ${VERDE_OSCURO})` : 'white',
                  border: activo ? 'none' : '2px solid #e0e0e0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: 'white',
                  fontWeight: '900',
                  boxShadow: activo ? '0 2px 6px rgba(3,118,35,0.4)' : 'none',
                  transform: activo ? 'scale(1)' : 'scale(0.85)',
                  transition: 'all 0.22s cubic-bezier(0.34, 1.3, 0.64, 1)',
                }}>
                  {activo ? '✓' : ''}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
};

export default StoreSelector;
