import React, { useState } from 'react';

const StoreSelector = ({ listaSupers, supersActivos, setSupersActivos }) => {
  const [abierto, setAbierto] = useState(false);
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  return (
    <section 
      className="no-print" 
      style={{ 
        backgroundColor: 'white', 
        padding: '15px', 
        borderRadius: '15px', 
        border: '1px solid #e0e6e1', 
        marginBottom: '25px' 
      }}
    >
      {/* DESKTOP: Todo visible */}
      {!isMobile && (
        <div style={{ 
          display: 'flex', 
          gap: '12px', 
          flexWrap: 'wrap', 
          alignItems: 'center' 
        }}>
          <span style={{ fontWeight: '800', fontSize: '13px' }}>MIS TIENDAS:</span>
          {listaSupers.map(s => (
            <label 
              key={s.id} 
              style={{ 
                padding: '6px 10px', 
                borderRadius: '8px', 
                border: '1px solid #eee', 
                cursor: 'pointer', 
                backgroundColor: supersActivos.includes(s.id) ? '#e8fdf0' : 'white', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px', 
                fontSize: '12px', 
                fontWeight: '700' 
              }}
            >
              <input 
                type="checkbox" 
                checked={supersActivos.includes(s.id)} 
                onChange={() => setSupersActivos(prev => 
                  prev.includes(s.id) ? prev.filter(x => x !== s.id) : [...prev, s.id]
                )} 
              />
              <img 
                src={s.logo} 
                alt={s.id} 
                style={{ width: '20px', height: '20px', objectFit: 'contain' }} 
              />
              {s.id}
            </label>
          ))}
        </div>
      )}

      {/* MÓVIL: Acordeón */}
      {isMobile && (
        <>
          {/* Header del acordeón */}
          <div 
            onClick={() => setAbierto(!abierto)}
            style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              cursor: 'pointer',
              padding: '8px 0'
            }}
          >
            <span style={{ fontWeight: '800', fontSize: '14px' }}>
              MIS TIENDAS ({supersActivos.length} seleccionadas)
            </span>
            <span style={{ fontSize: '18px', color: '#037623', fontWeight: '900' }}>
              {abierto ? '−' : '+'}
            </span>
          </div>

          {/* Contenido del acordeón */}
          {abierto && (
            <div style={{ 
              marginTop: '12px',
              display: 'grid',
              gap: '10px'
            }}>
              {listaSupers.map(s => (
                <label 
                  key={s.id} 
                  style={{ 
                    padding: '12px', 
                    borderRadius: '10px', 
                    border: '2px solid ' + (supersActivos.includes(s.id) ? '#037623' : '#eee'), 
                    cursor: 'pointer', 
                    backgroundColor: supersActivos.includes(s.id) ? '#e8fdf0' : 'white', 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '12px', 
                    fontSize: '14px', 
                    fontWeight: '700',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <input 
                    type="checkbox" 
                    checked={supersActivos.includes(s.id)} 
                    onChange={() => setSupersActivos(prev => 
                      prev.includes(s.id) ? prev.filter(x => x !== s.id) : [...prev, s.id]
                    )}
                    style={{
                      width: '20px',
                      height: '20px',
                      cursor: 'pointer'
                    }}
                  />
                  <img 
                    src={s.logo} 
                    alt={s.id} 
                    style={{ width: '28px', height: '28px', objectFit: 'contain' }} 
                  />
                  <span>{s.id}</span>
                </label>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
};

export default StoreSelector;