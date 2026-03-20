import React, { useState, useEffect } from 'react';

const SUPERS = ['Mercadona', 'DIA', 'Carrefour', 'Lidl', 'Aldi', 'Alcampo'];

const BENEFICIOS = [
  { icono: '💰', titulo: 'Ahorra hasta 100€/mes', texto: 'Compara precios en tiempo real y elige siempre el más barato.' },
  { icono: '🛒', titulo: 'Tu cesta inteligente', texto: 'Añade productos y ve al instante dónde te sale más barato todo.' },
  { icono: '📸', titulo: 'Escanea tu lista', texto: 'Fotografía tu lista de papel y la importamos automáticamente.' },
];

const Landing = ({ onEntrar }) => {
  const [superIdx, setSuperIdx] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
    const timer = setInterval(() => {
      setSuperIdx(i => (i + 1) % SUPERS.length);
    }, 1800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      background: '#f4f7f5',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      overflowX: 'hidden',
    }}>

      {/* NAVBAR */}
      <nav style={{
        background: '#102215',
        padding: '0 24px',
        height: '56px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <span style={{ color: 'white', fontWeight: '900', fontSize: '16px' }}>🛒 MI MEJOR CESTA</span>
        <button
          onClick={onEntrar}
          style={{
            background: '#13ec49',
            color: '#102215',
            border: 'none',
            padding: '8px 18px',
            borderRadius: '20px',
            fontWeight: '900',
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          Entrar gratis →
        </button>
      </nav>

      {/* HERO */}
      <section style={{
        background: 'linear-gradient(160deg, #102215 0%, #037623 100%)',
        color: 'white',
        padding: '64px 24px 80px',
        textAlign: 'center',
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(20px)',
        transition: 'opacity 0.6s ease, transform 0.6s ease',
      }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <div style={{ fontSize: '52px', marginBottom: '16px' }}>🛒</div>
          <h1 style={{
            fontSize: 'clamp(28px, 6vw, 48px)',
            fontWeight: '900',
            margin: '0 0 16px',
            lineHeight: 1.1,
          }}>
            Compara precios en{' '}
            <span style={{
              color: '#13ec49',
              display: 'inline-block',
              minWidth: '140px',
              transition: 'opacity 0.3s',
            }}>
              {SUPERS[superIdx]}
            </span>
            {' '}y ahorra
          </h1>
          <p style={{
            fontSize: 'clamp(15px, 3vw, 18px)',
            opacity: 0.85,
            margin: '0 0 36px',
            lineHeight: 1.5,
          }}>
            Descubre dónde te sale más barato cada producto.<br />
            Crea tu cesta ideal y ahorra hasta <strong>100€ al mes</strong>.
          </p>

          <button
            onClick={onEntrar}
            style={{
              background: '#13ec49',
              color: '#102215',
              border: 'none',
              padding: '18px 40px',
              borderRadius: '50px',
              fontWeight: '900',
              fontSize: '16px',
              cursor: 'pointer',
              boxShadow: '0 8px 32px rgba(19,236,73,0.3)',
              transition: 'transform 0.15s, box-shadow 0.15s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'scale(1.04)';
              e.currentTarget.style.boxShadow = '0 12px 40px rgba(19,236,73,0.4)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'scale(1)';
              e.currentTarget.style.boxShadow = '0 8px 32px rgba(19,236,73,0.3)';
            }}
          >
            Empezar gratis — sin registro
          </button>

          <p style={{ fontSize: '12px', opacity: 0.6, marginTop: '12px' }}>
            Gratis para siempre · Sin tarjeta · Sin registro
          </p>
        </div>
      </section>

      {/* STATS */}
      <section style={{
        background: 'white',
        padding: '32px 24px',
        display: 'flex',
        justifyContent: 'center',
        gap: '0',
        flexWrap: 'wrap',
        borderBottom: '1px solid #eee',
      }}>
        {[
          { num: '+4.000', label: 'productos comparados' },
          { num: '6', label: 'supermercados' },
          { num: '100€', label: 'ahorro medio/mes' },
        ].map((s, i) => (
          <div key={i} style={{
            textAlign: 'center',
            padding: '16px 32px',
            borderRight: i < 2 ? '1px solid #eee' : 'none',
            minWidth: '120px',
          }}>
            <div style={{ fontSize: 'clamp(22px, 5vw, 32px)', fontWeight: '900', color: '#037623' }}>{s.num}</div>
            <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>{s.label}</div>
          </div>
        ))}
      </section>

      {/* BENEFICIOS */}
      <section style={{ padding: '64px 24px', maxWidth: '900px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontWeight: '900', fontSize: 'clamp(20px, 4vw, 28px)', marginBottom: '48px', color: '#102215' }}>
          ¿Por qué usar Mi Mejor Cesta?
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '24px',
        }}>
          {BENEFICIOS.map((b, i) => (
            <div key={i} style={{
              background: 'white',
              borderRadius: '20px',
              padding: '32px 24px',
              border: '1px solid #e8f0e9',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '36px', marginBottom: '16px' }}>{b.icono}</div>
              <h3 style={{ fontWeight: '900', fontSize: '16px', color: '#102215', marginBottom: '8px' }}>{b.titulo}</h3>
              <p style={{ fontSize: '14px', color: '#666', lineHeight: 1.5, margin: 0 }}>{b.texto}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SUPERMERCADOS */}
      <section style={{ background: '#102215', padding: '48px 24px', textAlign: 'center' }}>
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '12px', fontWeight: '700', letterSpacing: '2px', marginBottom: '24px' }}>
          SUPERMERCADOS DISPONIBLES
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '12px' }}>
          {SUPERS.map(s => (
            <span key={s} style={{
              background: 'rgba(255,255,255,0.1)',
              color: 'white',
              padding: '8px 20px',
              borderRadius: '50px',
              fontSize: '14px',
              fontWeight: '700',
              border: '1px solid rgba(255,255,255,0.15)',
            }}>{s}</span>
          ))}
        </div>
      </section>

      {/* CTA FINAL */}
      <section style={{ padding: '80px 24px', textAlign: 'center', background: '#f4f7f5' }}>
        <h2 style={{ fontWeight: '900', fontSize: 'clamp(22px, 4vw, 32px)', color: '#102215', marginBottom: '16px' }}>
          Empieza a ahorrar hoy
        </h2>
        <p style={{ color: '#666', fontSize: '16px', marginBottom: '32px' }}>
          Gratis, sin registro, sin tarjeta. Listo en segundos.
        </p>
        <button
          onClick={onEntrar}
          style={{
            background: '#037623',
            color: 'white',
            border: 'none',
            padding: '18px 48px',
            borderRadius: '50px',
            fontWeight: '900',
            fontSize: '16px',
            cursor: 'pointer',
          }}
        >
          Ir a la app →
        </button>
      </section>

      {/* FOOTER */}
      <footer style={{
        background: '#102215',
        color: 'rgba(255,255,255,0.4)',
        textAlign: 'center',
        padding: '24px',
        fontSize: '12px',
      }}>
        © 2026 Mi Mejor Cesta · Comparador de precios de supermercados en España
      </footer>
    </div>
  );
};

export default Landing;
