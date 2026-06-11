/* CAVOK Service Worker v26
   Estrategia: Network-first para index.html (siempre actualizado),
   Cache-first para assets pesados (pistas.js, aeropuertos_mundo.js, íconos).
   Las llamadas a CheckWX y Google Fonts van siempre a la red. */

const CACHE = 'cavok-v27';

// Assets pesados — raramente cambian, se sirven desde caché
const ASSETS = [
  './aeropuertos_mundo.js',
  './pistas.js',
  './icon-192.png',
  './icon-512.png',
  './manifest.json'
];

// Shell — siempre se intenta la red primero
const SHELL = ['./index.html', './sw.js'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))   // solo assets, NO index.html
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = e.request.url;

  // Nunca interceptar: API, fonts
  if (url.includes('checkwx.com') ||
      url.includes('fonts.googleapis') ||
      url.includes('fonts.gstatic')) {
    return;
  }

  // index.html y sw.js: Network-first, fallback a caché
  if (url.endsWith('/') || url.includes('index.html') || url.includes('sw.js')) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          // Guardar copia fresca en caché
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Assets pesados: Cache-first
  e.respondWith(
    caches.match(e.request)
      .then(cached => cached || fetch(e.request).then(res => {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return res;
      }))
  );
});

// Recibir SKIP_WAITING desde el cliente
self.addEventListener('message', e => {
  if (e.data?.type === 'SKIP_WAITING') self.skipWaiting();
});
