// Bump when shell HTML or critical assets change — activate() evicts older caches.
const CACHE = 'animus-v57';

self.addEventListener('install', e => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // API calls always go to network (default fetch handler)
  if (e.request.url.includes('/api/')) return;

  const url = new URL(e.request.url);

  // Never cache the SW script itself via Cache Storage (avoids “stuck” SW updates).
  if (url.pathname === '/sw.js') {
    e.respondWith(fetch(e.request, { cache: 'no-store' }));
    return;
  }

  // HTML shell: network-first so UI updates (cron builder, etc.) always ship.
  if (e.request.mode === 'navigate' || url.pathname === '/' || url.pathname === '/index.html') {
    e.respondWith(
      fetch(e.request, { cache: 'no-store' })
        .then((nr) => {
          if (nr && nr.ok && nr.status === 200) {
            const copy = nr.clone();
            caches.open(CACHE).then((c) => c.put(new Request(url.origin + '/'), copy));
          }
          return nr;
        })
        .catch(() => caches.match('/'))
    );
    return;
  }

  // Other static assets: cache-first, refresh in background
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(nr => {
      const clone = nr.clone();
      caches.open(CACHE).then(c => c.put(e.request, clone));
      return nr;
    }))
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil((async () => {
    const allClients = await clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of allClients) {
      if ('focus' in client) {
        await client.focus();
        return;
      }
    }
    if (clients.openWindow) await clients.openWindow('/');
  })());
});
