import React from 'react';

const VERDE = '#037623';
const VERDE_CLARO = '#13ec49';
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
      gradiente: 'linear-gradient(135deg, #037623, #059c33)',
    },
    {
      id: 'recetas',
      emoji: '💡',
      label: 'Sugerir recetas',
      sublabel: seleccionados?.length > 0 ? `Con tus ${seleccionados.length} productos` : 'Basado en tu cesta',
      onClick: handleSugerirRecetas,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
      gradiente: 'linear-gradient(135deg, #f57c00, #ffa726)',
    },
    {
      id: 'nutricional',
      emoji: '🥗',
      label: 'Nutricional',
      sublabel: seleccionados?.length > 0 ? `${seleccionados.length} productos` : 'Análisis de tu cesta',
      onClick: handleNutricional,
      activo: esPremium && !!session,
      badge: !esPremium ? 'PREMIUM' : null,
      gradiente: 'linear-gradient(135deg, #1565c0, #42a5f5)',
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
            flex: '1',
            minWidth: '100px',
            background: 'white',
            border: `1.5px solid ${b.activo ? '#e0f2e6' : '#e5e5e5'}`,
            borderRadius: '16px',
            padding: '14px 12px',
            cursor: 'pointer',
            textAlign: 'center',
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            position: 'relative',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = 'translateY(-3px)';
            e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.10)';
            e.currentTarget.style.borderColor = b.activo ? VERDE : '#ccc';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)';
            e.currentTarget.style.borderColor = b.activo ? '#e0f2e6' : '#e5e5e5';
          }}
        >
          {b.badge && (
            <span style={{
              position: 'absolute',
              top: '-9px',
              right: '10px',
              background: 'linear-gradient(135deg, #7b2ff7, #9b4dff)',
              color: 'white',
              fontSize: '8px',
              fontWeight: '900',
              padding: '3px 7px',
              borderRadius: '6px',
              letterSpacing: '0.4px',
              boxShadow: '0 2px 6px rgba(123,47,247,0.35)',
            }}>
              ✨ {b.badge}
            </span>
          )}
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '50%',
            background: b.activo ? b.gradiente : '#f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 8px',
            fontSize: '19px',
            boxShadow: b.activo ? '0 4px 10px rgba(0,0,0,0.15)' : 'none',
            transition: 'all 0.25s ease',
          }}>
            {b.emoji}
          </div>
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
