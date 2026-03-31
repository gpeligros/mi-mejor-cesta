import React, { useState } from 'react';

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
        padding: '10px 15px',
        borderRadius: '15px',
        border: '1px solid #e0e6e1',
        marginBottom: '25px',
      }}
    >
      {/* DESKTOP: fila compacta */}
      {!isMobile && (
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontWeight: '800', fontSize: '12px', color: '#555', whiteSpace: 'nowrap' }}>
            MIS TIENDAS:
          </span>
          {supersVisibles.map(s => (
            <label
              key={s.id}
              style={{
                padding: '4px 8px',
                borderRadius: '8px',
                border: '1px solid ' + (supersActivos.includes(s.id) ? '#037623' : '#eee'),
                cursor: 'pointer',
                backgroundColor: supersActivos.includes(s.id) ? '#e8fdf0' : 'white',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                transition: 'all 0.15s ease',
              }}
            >
              <input
                type="checkbox"
                checked={supersActivos.includes(s.id)}
                onChange={() => {
                  if (supersActivos.includes(s.id)) {
                    setSupersActivos(prev => prev.filter(x => x !== s.id));
                  } else {
                    setSupersActivos([...supersActivos, s.id]);
                  }
                }}
                style={{ width: '12px', height: '12px', cursor: 'pointer' }}
              />
              <img
                src={s.logo}
                alt={s.id}
                title={s.id}
                style={{ height: "26px", maxWidth: '80px', objectFit: 'contain' }}
              />
            </label>
          ))}
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
              padding: '4px 0',
            }}
          >
            <span style={{ fontWeight: '800', fontSize: '13px' }}>
              MIS TIENDAS ({supersActivos.length} seleccionadas)
            </span>
            <span style={{ fontSize: '18px', color: '#037623', fontWeight: '900' }}>
              {abierto ? '−' : '+'}
            </span>
          </div>

          {abierto && (
            <div style={{ marginTop: '10px', display: 'grid', gap: '8px' }}>
              {supersVisibles.map(s => (
                <label
                  key={s.id}
                  style={{
                    padding: '10px',
                    borderRadius: '10px',
                    border: '2px solid ' + (supersActivos.includes(s.id) ? '#037623' : '#eee'),
                    cursor: 'pointer',
                    backgroundColor: supersActivos.includes(s.id) ? '#e8fdf0' : 'white',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    fontSize: '14px',
                    fontWeight: '700',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={supersActivos.includes(s.id)}
                    onChange={() => {
                      if (supersActivos.includes(s.id)) {
                        setSupersActivos(prev => prev.filter(x => x !== s.id));
                      } else {
                        setSupersActivos([...supersActivos, s.id]);
                      }
                    }}
                    style={{ width: '20px', height: '20px', cursor: 'pointer' }}
                  />
                  <img src={s.logo} alt={s.id} style={{ width: '28px', height: '28px', objectFit: 'contain' }} />
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
