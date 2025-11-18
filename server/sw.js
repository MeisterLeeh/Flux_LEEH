const C = 'flux-v1';
self.addEventListener('install', e => e.waitUntil(caches.open(C).then(c => c.addAll(['/', '/style.css', '/script.js']))));
self.addEventListener('fetch', e => e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))));