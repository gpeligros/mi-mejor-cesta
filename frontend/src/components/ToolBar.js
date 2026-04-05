import React from 'react';

const VERDE = '#037623';
const OSCURO = '#102215';

const ToolBar = ({ plan, onUpgrade, session, onMenuSemanal, onSugerirRecetas, onNutricional, seleccionados }) => {
  const esPremium = plan === 'premium';

  const handleMenuSemanal = () => {
    if (!session) { onUpgrade('menuSemanal', 'premium'); return; }
    if (!esPremium) { onUpgrade('menuSemanal', 'premium'); return; }
    onMenuSemanal();
  };

  const handleSugerirRecetas = () => {
    if (!session) { onUpgrade('recetas', 'premium'); return; }
    if (!esPremium) { onUpgrade('recetas', 'premium'); return; }
    if (!seleccionados || seleccionados.length === 0) {
      alert('Añade productos a tu cesta para recibir sugerencias de recetas.');
      return;
    }
    onSugerirRecetas();
  };

  const handleNutricional = () => {
    if (!session) { onUpgrade('nutricional', 'premium'); return; }
    if (!esPremium) { onUpgrade('nutricional', 'premium'); return; }
    if (!seleccionados || seleccionados.length === 0) {
      alert('Añade productos a tu cesta para ver el análisis nutricional.');
      return;
    }
    onNutricional();
  };

  const botones = [
    {
      id: 'menu',
      emoji: '🍽️',
      label: 'Menú semanal',
      sublabel: 'IA genera tu semana',
      onClick: handleMenuSemanal,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
    },
    {
      id: 'recetas',
      emoji: '💡',
      label: 'Sugerir recetas',
      sublabel: seleccionados?.length > 0 ? `Con tus ${seleccionados.length} productos` : 'Basado en tu cesta',
      onClick: handleSugerirRecetas,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
    },
    {
      id: 'nutricional',
      emoji: '🥗',
      label: 'Nutricional',
      sublabel: seleccionados?.length > 0 ? `${seleccionados.length} productos` : 'Análisis de tu cesta',
      onClick: handleNutricional,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
    },
  ];

  return (
    <div
      className="no-print"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '10px',
        marginBottom: '20px',
        paddingTop: '14px',
      }}
    >
      {botones.map(b => (
        <button
          key={b.id}
          onClick={b.onClick || undefined}
          style={{
            flex: '1',
            minWidth: '100px',
            background: 'white',
            border: `1.5px solid ${b.activo ? VERDE : '#ccc'}`,
            borderRadius: '14px',
            padding: '10px 12px',
            cursor: 'pointer',
            textAlign: 'center',
            transition: 'all 0.15s ease',
            position: 'relative',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = '#f0fdf4'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'white'; }}
        >
          {b.badge && (
            <span style={{
              position: 'absolute',
              top: '-10px',
              right: '8px',
              background: VERDE,
              color: 'white',
              fontSize: '8px',
              fontWeight: '900',
              padding: '2px 5px',
              borderRadius: '4px',
            }}>
              {b.badge}
            </span>
          )}
          <div style={{ fontSize: '20px', marginBottom: '4px' }}>{b.emoji}</div>
          <div style={{
            fontSize: '11px',
            fontWeight: '900',
            color: b.activo ? OSCURO : '#999',
            lineHeight: 1.2,
          }}>
            {b.label}
          </div>
          <div style={{
            fontSize: '9px',
            color: '#aaa',
            marginTop: '2px',
            fontWeight: '600',
          }}>
            {b.sublabel}
          </div>
        </button>
      ))}
    </div>
  );
};

export default ToolBar;
