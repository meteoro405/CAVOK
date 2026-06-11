/* CAVOK Service Worker v20
   Cachea el shell para carga offline.
   Las llamadas a CheckWX y Google Fonts van siempre a la red. */

const CACHE = 'cavok-v20';
const SHELL = [
  './index.html',
  './aeropuertos_mundo.js',
  './pistas.js',
  './icon-192.png',
  './icon-512.png',
  './manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(SHELL))
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
      .then(() => {
        return self.clients.matchAll({ type: 'window' }).then(clients => {
          clients.forEach(c => c.postMessage({ type: 'SW_UPDATED', version: 'v20' }));
        });
      })
  );
});

// Recibir SKIP_WAITING desde el cliente (botón Actualizar)
self.addEventListener('message', e => {
  if (e.data?.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', e => {
  if (e.request.url.includes('checkwx.com') ||
      e.request.url.includes('fonts.googleapis') ||
      e.request.url.includes('fonts.gstatic')) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
