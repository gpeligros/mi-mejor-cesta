# 🛒 Mi Mejor Cesta — Gestión Inteligente de la Compra con IA

[![Vercel](https://img.shields.io/badge/Deploy-Vercel-black?logo=vercel)](https://mimejorcesta.vercel.app)
[![LLM Powered](https://img.shields.io/badge/Powered%20by-LLMs-blue?logo=openai)](https://mimejorcesta.vercel.app)
[![Status](https://img.shields.io/badge/Status-En%20Producción-brightgreen)]()

> Aplicación web de gestión inteligente de la compra que utiliza **Large Language Models** en producción para optimizar listas de la compra, comparar precios y asistir al usuario en decisiones de consumo cotidiano.

🔗 **Demo en vivo:** [mimejorcesta.vercel.app](https://mimejorcesta.vercel.app)

---

## 🎯 ¿Qué problema resuelve?

Gestionar la compra semanal de forma eficiente es un reto que afecta a millones de hogares. **Mi Mejor Cesta** aplica inteligencia artificial para:

- **Automatizar** la creación y organización de listas de la compra
- **Asistir** al usuario con recomendaciones basadas en IA generativa
- **Optimizar** la experiencia de compra con procesamiento de lenguaje natural

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│              Next.js / React / Vercel                │
│         Responsive · PWA-ready · SSR                 │
├─────────────────────────────────────────────────────┤
│                   API LAYER                          │
│           Vercel Serverless Functions                │
│              API Routes (Next.js)                    │
├─────────────────────────────────────────────────────┤
│                  LLM INTEGRATION                     │
│        Procesamiento de Lenguaje Natural             │
│     Generación · Clasificación · Asistencia          │
├─────────────────────────────────────────────────────┤
│                  DATA LAYER                          │
│            Persistencia · Estado · Cache             │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Rol |
|------|-----------|-----|
| **Frontend** | Next.js, React, Tailwind CSS | UI responsive, SSR, componentes reutilizables |
| **Backend** | Vercel Serverless Functions | API endpoints, lógica de negocio |
| **IA / LLMs** | API de modelos de lenguaje | NLP, generación de contenido, asistencia inteligente |
| **Deploy** | Vercel | CI/CD automático, edge network global |
| **Estilo** | Tailwind CSS | Diseño mobile-first, sistema de diseño consistente |

---

## ✨ Funcionalidades Principales

### Gestión Inteligente de Listas
- Creación y organización automática de listas de la compra
- Categorización inteligente de productos mediante NLP
- Interfaz intuitiva optimizada para uso móvil

### Asistencia con IA Generativa
- Procesamiento de lenguaje natural para interpretar intenciones del usuario
- Sugerencias contextuales basadas en patrones de compra
- Interacción conversacional con el sistema

### Experiencia de Usuario
- Diseño responsive (mobile-first)
- Rendimiento optimizado con SSR (Server-Side Rendering)
- Interfaz limpia y accesible

---

## 🧠 ¿Por qué es relevante como caso de estudio?

Este proyecto demuestra la **aplicación real de LLMs en producción**, no como prueba de concepto sino como herramienta funcional que usuarios reales utilizan. Los aspectos técnicos relevantes incluyen:

1. **Integración LLM en producción:** Gestión de prompts, control de costes por llamada, manejo de errores y latencia en entorno real.
2. **Arquitectura serverless:** Diseño escalable sin infraestructura dedicada, con costes proporcionales al uso.
3. **UX + IA:** Cómo diseñar interfaces donde la IA sea un facilitador invisible, no una barrera de complejidad.
4. **Full-stack individual:** Desde el diseño UI hasta el deploy en producción, desarrollado como proyecto personal end-to-end.

---

## 🚀 Desarrollo Local

```bash
# Clonar el repositorio
git clone https://github.com/gpeligros/mi-mejor-cesta.git
cd mi-mejor-cesta

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local con tus API keys

# Ejecutar en desarrollo
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`.

---

## 📁 Estructura del Proyecto

```
mi-mejor-cesta/
├── app/                    # App Router (Next.js 14+)
│   ├── api/               # API Routes (serverless)
│   ├── components/        # Componentes React
│   ├── layout.tsx         # Layout principal
│   └── page.tsx           # Página principal
├── lib/                   # Utilidades y helpers
│   ├── llm/              # Integración con LLMs
│   └── utils/            # Funciones auxiliares
├── public/               # Assets estáticos
├── styles/               # Estilos globales
├── .env.example          # Variables de entorno (plantilla)
├── next.config.js        # Configuración Next.js
├── tailwind.config.js    # Configuración Tailwind
└── package.json
```

---

## 📊 Otros Proyectos del Portfolio

| Proyecto | Descripción | Tecnologías |
|----------|------------|-------------|
| [ETL Datos Bancarios](./notebooks/01_ETL_Limpieza_Datos_Bancarios.ipynb) | Pipeline de limpieza de 50K transacciones bancarias | Python, pandas |
| [Dashboard KPIs Bancarios](./notebooks/02_Dashboard_KPIs_Bancarios_Plotly.ipynb) | Visualización interactiva de métricas operativas | Python, Plotly |
| [Segmentación Clientes RFM](./notebooks/03_Segmentacion_Clientes_RFM.ipynb) | Clustering de clientes con K-Means + RFM | Python, scikit-learn, Plotly |

---

## 👤 Sobre el Autor

**David González Peligros**  
Senior BI & AI Strategy | +15 años en banca (Banco Santander, CGI/Redsys)

Especializado en Business Intelligence, sistemas transaccionales a escala y aplicación de Large Language Models en entornos productivos.

- 📧 gpeligros@gmail.com
- 🔗 [LinkedIn](https://linkedin.com/in/gpeligros)
- 📱 667 674 127

---

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](./LICENSE) para más detalles.

---

*Desarrollado con ☕ y 🤖 en Madrid — 2025-2026*
