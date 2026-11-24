// Trakerz Service Worker - Milestone 3
// Provides offline shell caching for mobile browsers.
// NOTE: Dynamic expense data requires network connection to backend.

const CACHE_NAME = 'trakerz-shell-v5';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/vendor/chart.umd.min.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Trakerz SW] Pre-caching offline shell assets...');
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('[Trakerz SW] Shell cache warning (will fetch on demand):', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Trakerz SW] Removing old cache version:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // For API endpoints, always go to network (never serve stale financial data)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch((err) => {
        return new Response(
          JSON.stringify({
            error: 'Offline',
            detail: 'Unable to reach Trakerz backend server. Please check your network connection.'
          }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
          }
        );
      })
    );
    return;
  }

  // For static assets, try cache first, fallback to network
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).catch(() => {
        // Fallback for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      });
    })
  );
});
