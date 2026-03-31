import { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';

// Límites por plan
export const PLANES = {
  free:     { nombre: 'Gratuito',          maxSupers: 2,  maxProductos: 20, precio: 0    },
  free_reg: { nombre: 'Gratuito',          maxSupers: 2,  maxProductos: 20, precio: 0    },
  basic:    { nombre: 'Básico',            maxSupers: 999, maxProductos: 999, precio: 2.99 },
  premium:  { nombre: 'Premium',           maxSupers: 999, maxProductos: 999, precio: 6.99 },
};

export const FUNCIONALIDADES = {
  guardarListas:      { free: false, free_reg: true,  basic: true,  premium: true  },
  listasFavoritas:    { free: false, free_reg: 1,     basic: 999,   premium: 999   },
  exportarPDF:        { free: false, free_reg: true,  basic: true,  premium: true  },
  compartirLista:     { free: false, free_reg: true,  basic: true,  premium: true  },
  escanearLista:      { free: false, free_reg: false, basic: true,  premium: true  },
  alertasPrecio:      { free: false, free_reg: false, basic: true,  premium: true  },
  guardarCompra:      { free: false, free_reg: false, basic: true,  premium: true  },
  historialCompras:   { free: false, free_reg: false, basic: '3m',  premium: true  },
  planificacionMes:   { free: false, free_reg: false, basic: false, premium: true  },
  menuSemanal:        { free: false, free_reg: false, basic: false, premium: true  },
  recetasIA:          { free: false, free_reg: false, basic: false, premium: true  },
  estadisticasBasic:  { free: false, free_reg: false, basic: true,  premium: true  },
  estadisticasFull:   { free: false, free_reg: false, basic: false, premium: true  },
  nutricional:        { free: false, free_reg: false, basic: false, premium: true  },
  cestivaBasic:       { free: true,  free_reg: true,  basic: true,  premium: true  },
  cestivaFull:        { free: false, free_reg: false, basic: true,  premium: true  },
};

export function usePlan(session) {
  const [plan, setPlan] = useState('free');
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    if (!session) {
      setPlan('free');
      setCargando(false);
      return;
    }

    const cargar = async () => {
      const { data } = await supabase
        .from('profiles')
        .select('plan')
        .eq('id', session.user.id)
        .single();

      if (data?.plan) setPlan(data.plan);
      else setPlan('free_reg'); // usuario registrado sin perfil aún
      setCargando(false);
    };

    cargar();
  }, [session]);

  const puedeUsar = (funcionalidad) => {
    return !!FUNCIONALIDADES[funcionalidad]?.[plan];
  };

  const limiteSupers = () => PLANES[plan]?.maxSupers || 2;
  const limiteProductos = () => PLANES[plan]?.maxProductos || 20;
  const esPago = () => plan === 'basic' || plan === 'premium';
  const esPremium = () => plan === 'premium';

  return { plan, cargando, puedeUsar, limiteSupers, limiteProductos, esPago, esPremium };
}
