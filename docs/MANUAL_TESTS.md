# MANUAL_TESTS.md - Mi Mejor Cesta

Casos de prueba manuales antes de cada despliegue importante.

Marca cada caso como pasa / falla / no aplica conforme avances. Si algo
falla, abre un issue con captura, navegador y pasos para reproducirlo.
Documento vivo: amplialo cada vez que detectes un caso nuevo.

> Entornos: probar siempre en al menos Chrome desktop + Safari iOS
> (con su modo privado). Para temas de cookies probar tambien Firefox.

---

## 1. Onboarding y landing

| # | Caso | Esperado |
|---|------|----------|
| 1.1 | Primera visita en navegador limpio | Aparece pantalla de bienvenida (Landing) |
| 1.2 | Pulsar "Entrar" en landing | Desaparece y queda guardado landing_vista en localStorage |
| 1.3 | Recargar pagina tras entrar | Va directo al comparador, no vuelve a salir el landing |
| 1.4 | Banner de cookies en primera visita | Sale automaticamente con 3 botones: ACEPTAR TODO, SOLO NECESARIAS y "Configurar en detalle" |
| 1.5 | Pulsar SOLO NECESARIAS | El banner se cierra. localStorage cookies_consent_v2 contiene analiticas:false. GA4 no se carga (verificar Network) |
| 1.6 | Pulsar ACEPTAR TODO | localStorage cookies_consent_v2 contiene analiticas:true. GA4 se carga (Network: googletagmanager.com) |
| 1.7 | Pulsar Configurar -> desmarcar analiticas -> guardar | Mismo efecto que SOLO NECESARIAS |
| 1.8 | Ir a /Cookies (footer) y pulsar "Cambiar mis preferencias" | Se reabre el banner |

---

## 2. Comparador (sin login)

| # | Caso | Esperado |
|---|------|----------|
| 2.1 | Catalogo se carga al entrar | Se ven categorias en sidebar y tarjetas de supermercados a la derecha |
| 2.2 | Anadir un producto a la cesta (toggle) | Aparece en las tarjetas de supermercado con su precio |
| 2.3 | Anadir el producto numero 21 | Aparece ModalUpgrade con mensaje "Lista ilimitada disponible en plan Basico" (limite plan free=20) |
| 2.4 | Activar/desactivar supermercados (StoreSelector) | El boton aplica solo si hay <=2 supers (limite free) |
| 2.5 | Intentar activar 3 supers en plan free | ModalUpgrade aparece |
| 2.6 | Recargar la pagina | La cesta y los supers seleccionados se mantienen (localStorage) |
| 2.7 | Buscador en sidebar | Filtra productos en tiempo real |

---

## 3. Login y registro

| # | Caso | Esperado |
|---|------|----------|
| 3.1 | Registro con email + contrasena | Se crea entrada en auth.users + profiles (plan=free_reg) |
| 3.2 | Login con email | Sesion activa, sidebar muestra "MIS LISTAS" y demas |
| 3.3 | Login con Google OAuth | Idem 3.2 |
| 3.4 | Logout | Vuelve a comportamiento anonimo |

---

## 4. Sincronizacion en la nube

| # | Caso | Esperado |
|---|------|----------|
| 4.1 | Estando logueado, anadir producto | Aparece estadoSync = "sincronizando" -> "ok" |
| 4.2 | Logueado en Chrome, abrir Firefox y loguear | La cesta se ve igual en ambos |
| 4.3 | Desactivar sincronizacion en SyncHeader | No se sincroniza con la nube pero si se mantiene en localStorage |

---

## 5. CESTITA (asistente IA)

| # | Caso | Esperado |
|---|------|----------|
| 5.1 | Boton de CESTITA en esquina inferior | Abre el chat |
| 5.2 | Mensaje "Cuanto vale la cesta?" | Responde con el total y el supermercado mas barato |
| 5.3 | "Anade leche a la cesta" | Anade leche al carrito real (toggleProd) |
| 5.4 | "Vacia la cesta" | Confirma y vacia |
| 5.5 | Sin login: pregunta tecnica | Responde pero sin acceder a contexto premium |
| 5.6 | Inspeccionar Network al pedir a CESTITA | La llamada va a /api/cestita y NO expone la API key de Anthropic en frontend |

---

## 6. Funciones premium (requieren plan basic/premium)

NOTA: en TEST puedes simular plan cambiando manualmente profiles.plan en Supabase
(`UPDATE profiles SET plan='premium' WHERE id = 'TU_UUID';`).

| # | Caso | Esperado |
|---|------|----------|
| 6.1 | ToolBar visible solo si es premium | En free aparecen pero al pulsar sale ModalUpgrade |
| 6.2 | Generar menu semanal (premium) | Se genera correctamente, se guarda y se ve en pestaña "guardados" |
| 6.3 | Sugerir recetas (premium) | Devuelve recetas basadas en cesta actual |
| 6.4 | Analisis nutricional (premium) | Devuelve estimacion |
| 6.5 | Modal de upgrade desde funcion premium | Boton "Activar Premium" lleva a Stripe checkout TEST |
| 6.6 | Pago en Stripe TEST con tarjeta 4242 4242 4242 4242 | Webhook actualiza profiles.plan a 'premium' en menos de 30s |
| 6.7 | Cancelar suscripcion (Stripe) -> webhook subscription.deleted | profiles.plan vuelve a 'free' |

---

## 7. Exportar PDF

| # | Caso | Esperado |
|---|------|----------|
| 7.1 | Cesta vacia, pulsar "Exportar PDF" | Alert "Anade productos primero" |
| 7.2 | Cesta con productos | Abre ventana con tablas por supermercado, totales y resaltado del minimo |
| 7.3 | Imprimir desde el dialogo de print del navegador | Sale limpio sin elementos UI |

---

## 8. Lista colaborativa

| # | Caso | Esperado |
|---|------|----------|
| 8.1 | Compartir lista | Genera URL con codigo |
| 8.2 | Abrir URL en otro navegador | Pide login (o accede como invitado segun config) |
| 8.3 | Anadir producto desde un dispositivo | Se ve en otro en tiempo real |

---

## 9. Compras realizadas

| # | Caso | Esperado |
|---|------|----------|
| 9.1 | Modo tienda con productos | Permite marcar comprados |
| 9.2 | Finalizar compra | Inserta en compras y compras_detalle |
| 9.3 | Sidebar "MIS COMPRAS" | Muestra historial |
| 9.4 | Sidebar "MIS ESTADISTICAS" (basic+) | Muestra grafico de gasto |

---

## 10. PWA

| # | Caso | Esperado |
|---|------|----------|
| 10.1 | Lighthouse en Chrome | PWA instalable, sin warnings rojos |
| 10.2 | Instalar como app en movil | Aparece icono y abre standalone |
| 10.3 | Modo offline (despues de la primera carga) | La app sigue funcionando con datos en cache (al menos sidebar) |

---

## 11. Legal y privacidad

| # | Caso | Esperado |
|---|------|----------|
| 11.1 | Footer -> Privacidad | Renderiza Privacidad.js completo, sin emojis |
| 11.2 | Footer -> Terminos | Renderiza Terminos.js, IVA incluido visible, plazo desistimiento explicado |
| 11.3 | Footer -> Cookies | Renderiza tabla de cookies con duraciones |
| 11.4 | Footer -> Aviso Legal | Renderiza AvisoLegal.js |
| 11.5 | Verificar que no quedan placeholders [TITULAR] / [NIF] visibles antes de Stripe live | Buscar por "[TITULAR]" en cada pagina |
| 11.6 | GA4 NO carga sin consentimiento | Network tab confirma googletagmanager.com solo aparece tras ACEPTAR TODO |

---

## 12. Errores y robustez

| # | Caso | Esperado |
|---|------|----------|
| 12.1 | Bloquear *.supabase.co en DevTools | App muestra mensaje de error o cesta vacia, no se rompe |
| 12.2 | localStorage lleno (DevTools -> Application -> simular) | App sigue funcionando, no peta |
| 12.3 | Safari en modo privado | App carga y permite usar el comparador |
| 12.4 | Token de sesion caducado | Auto-refresh transparente |

---

## 13. Performance basica

| # | Caso | Esperado |
|---|------|----------|
| 13.1 | Lighthouse mobile | Performance >= 70, Best Practices >= 90 |
| 13.2 | First Contentful Paint en 3G simulado | < 5 s |
| 13.3 | Bundle size de produccion | < 1 MB gzipped |

---

## Checklist de release (resumen rapido)

- [ ] Todos los matches a dia ejecutados (verificar_estado.py limpio)
- [ ] Sentry instalado y enviando errores reales
- [ ] GA4 con eventos custom basicos: cart_added, cestita_used, upgrade_open
- [ ] Cookie banner probado en Chrome, Safari iOS, Firefox
- [ ] Placeholders legales rellenos (si vamos a cobrar)
- [ ] Webhook Stripe en LIVE configurado (si vamos a cobrar)
- [ ] Backup de Supabase activado
- [ ] DNS y dominio personalizado (si aplica)
- [ ] Lighthouse mobile >= 70
- [ ] Tests manuales del 1 al 13 ejecutados al menos una vez
