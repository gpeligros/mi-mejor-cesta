import logoMercadona from '../assets/mercadona.svg';
import logoCarrefour from '../assets/carrefour.svg';
import logoLidl from '../assets/lidl.svg';
import logoAldi from '../assets/aldi.svg';
import logoAlcampo from '../assets/alcampo.svg';
import logoHipercor from '../assets/hipercor.svg';
import logoDIA from '../assets/DIA.svg';
import logoLadespensa from '../assets/LaDespensa.jpeg';
import logoAhorraMas from '../assets/AhorraMas.png';
import logoBM from '../assets/BMSupermercados.png';

// visible: true  → aparece en el selector
// visible: false → oculto (próximamente) — cambiar a true cuando tenga datos
const listaSupers = [
  { id: "Mercadona",        logo: logoMercadona,   visible: true  },
  { id: "DIA",              logo: logoDIA,          visible: true  },
  { id: "Alcampo",          logo: logoAlcampo,      visible: true  },
  { id: "Carrefour",        logo: logoCarrefour,    visible: true  },
  { id: "Lidl",             logo: logoLidl,         visible: true  },
  { id: "Hipercor",         logo: logoHipercor,     visible: true  },
  { id: "Aldi",             logo: logoAldi,         visible: true  },
  { id: "La Despensa",      logo: logoLadespensa,   visible: true  },
  { id: "AhorraMas",        logo: logoAhorraMas,    visible: true  },
  { id: "BM Supermercados", logo: logoBM,           visible: false }, // sin datos aún
];

export default listaSupers;
