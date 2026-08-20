import React from 'react';

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
      color: '#037623',
      tinte: '#e8fdf0',
    },
    {
      id: 'recetas',
      emoji: '💡',
      label: 'Sugerir recetas',
      sublabel: seleccionados?.length > 0 ? `Con tus ${seleccionados.length} productos` : 'Basado en tu cesta',
      onClick: handleSugerirRecetas,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
      color: '#c26a00',
      tinte: '#fff4e5',
    },
    {
      id: 'nutricional',
      emoji: '🥗',
      label: 'Nutricional',
      sublabel: seleccionados?.length > 0 ? `${seleccionados.length} productos` : 'Análisis de tu cesta',
      onClick: handleNutricional,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
      color: '#1565c0',
      tinte: '#e8f2fd',
    },
  ];

  return (
    <div
      className="no-print"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '12px',
        marginBottom: '20px',
        paddingTop: '14px',
      }}
    >
      {botones.map(b => (
        <button
          key={b.id}
          onClick={b.onClick || undefined}
          style={{
            minWidth: '100px',
            background: b.activo ? b.tinte : '#fafafa',
            border: `1.5px solid ${b.activo ? 'transparent' : '#eee'}`,
            borderRadius: '16px',
            padding: '14px 12px',
            cursor: 'pointer',
            textAlign: 'center',
            transition: 'all 0.2s ease',
            position: 'relative',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.08)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          {b.badge && (
            <span style={{
              position: 'absolute', top: '-8px', right: '10px',
              background: OSCURO, color: 'white', fontSize: '8px', fontWeight: '900',
              padding: '3px 7px', borderRadius: '6px', letterSpacing: '0.4px',
            }}>
              {b.badge}
            </span>
          )}
          <div style={{
            width: '38px', height: '38px', borderRadius: '50%',
            background: b.activo ? 'white' : '#eee',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 8px', fontSize: '18px',
            boxShadow: b.activo ? '0 2px 6px rgba(0,0,0,0.08)' : 'none',
          }}>
            {b.emoji}
          </div>
          <div style={{
            fontSize: '11px', fontWeight: '900',
            color: b.activo ? OSCURO : '#999', lineHeight: 1.2,
          }}>
            {b.label}
          </div>
          <div style={{ fontSize: '9px', color: '#999', marginTop: '2px', fontWeight: '600' }}>
            {b.sublabel}
          </div>
        </button>
      ))}
    </div>
  );
};

export default ToolBar;
