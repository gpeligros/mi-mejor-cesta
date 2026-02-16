// service-worker.js
// PWA Service Worker para Mi Mejor Cesta

const CACHE_NAME = 'mi-mejor-cesta-v1';
const RUNTIME_CACHE = 'mi-mejor-cesta-runtime-v1';

// Archivos a cachear en la instalacion
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/bundle.js',
  '/manifest.json',
  '/logo192.png',
  '/logo512.png'
];

// Instalacion del service worker
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Instalando...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Pre-cacheando archivos estaticos');
        // Cachear solo los archivos que existen
        return cache.addAll(PRECACHE_URLS.filter(url => {
          // Filtrar URLs que sabemos que existen
          return url === '/' || url === '/index.html' || url === '/manifest.json';
        }));
      })
      .then(() => self.skipWaiting())
  );
});

// Activacion del service worker
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activando...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Eliminar caches antiguos
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('[ServiceWorker] Eliminando cache antigua:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estrategia de cache: Network First, falling back to Cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar requests que no son HTTP/HTTPS
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Ignorar requests a APIs externas (Supabase)
  if (url.hostname.includes('supabase.co')) {
    return; // Dejar que pase directo, no cachear
  }

  // Para archivos estaticos: Cache First
  if (
    request.destination === 'image' ||
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'font'
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }

        return fetch(request).then((response) => {
          // Si la respuesta es valida, cachearla
          if (response && response.status === 200) {
            const responseToCache = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return response;
        });
      })
    );
    return;
  }

  // Para navegacion (HTML): Network First, falling back to Cache
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cachear la respuesta
          const responseToCache = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseToCache);
          });
          return response;
        })
        .catch(() => {
          // Si falla la red, intentar cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Si tampoco hay cache, mostrar pagina offline
            return caches.match('/');
          });
        })
    );
    return;
  }

  // Para todo lo demas: Network First
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response && response.status === 200) {
          const responseToCache = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(request);
      })
  );
});

// Manejar mensajes del cliente
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

// Sincronizacion en segundo plano (opcional)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-cesta') {
    event.waitUntil(syncCesta());
  }
});

async function syncCesta() {
  // Aqui podrias sincronizar la cesta con Supabase cuando vuelva la conexion
  console.log('[ServiceWorker] Sincronizando cesta...');
}

console.log('[ServiceWorker] Cargado y listo');
