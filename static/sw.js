const C = 'flux-v2';
self.addEventListener('install', e => e.waitUntil(
  caches.open(C).then(c => c.addAll(['/', '/style.css', '/scripts.js', '/index.html', '/logo.jpg', '/manifest.json']))
));
self.addEventListener('fetch', e => e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))));

