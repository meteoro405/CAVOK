/* CAVOK Service Worker v10
   Cachea el shell (HTML + pistas.js + íconos) para carga offline.
   Las llamadas a CheckWX van siempre a la red (no se cachean). */

const CACHE = 'cavok-v11';
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
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Dejar pasar siempre las llamadas a la API
  if (e.request.url.includes('checkwx.com') || e.request.url.includes('fonts.googleapis')) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
