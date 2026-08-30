{% load static %}// cote-me service worker — cache básico de assets estáticos
const CACHE_VERSION = "cote-me-v1";

const PRECACHE_URLS = [
  "{% static 'css/glassmorphism.css' %}",
  "{% static 'js/app.js' %}",
  "{% static 'icons/icon.svg' %}",
  "{% static 'icons/icon-maskable.svg' %}",
  "{% static 'icons/favicon.svg' %}",
];

// Install: precache static assets
self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      return cache.addAll(PRECACHE_URLS);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) { return key !== CACHE_VERSION; })
          .map(function (key) { return caches.delete(key); })
      );
    })
  );
  self.clients.claim();
});

// Fetch: cache-first for static assets, network-first for pages
self.addEventListener("fetch", function (event) {
  var url = new URL(event.request.url);

  // Skip non-GET requests
  if (event.request.method !== "GET") return;

  // Skip cross-origin requests (fonts, analytics, etc.)
  if (url.origin !== location.origin) return;

  // Static assets (CSS, JS, images, fonts, icons): cache-first
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(event.request));
    return;
  }

  // HTML pages: network-first (fresh content, fallback to cache)
  if (event.request.headers.get("Accept") && event.request.headers.get("Accept").indexOf("text/html") !== -1) {
    event.respondWith(networkFirst(event.request));
    return;
  }
});

function isStaticAsset(pathname) {
  return /\.(css|js|svg|png|jpg|jpeg|gif|ico|woff2?|ttf|eot)(\?.*)?$/.test(pathname);
}

function cacheFirst(request) {
  return caches.match(request).then(function (cached) {
    if (cached) return cached;
    return fetch(request).then(function (response) {
      if (response.ok) {
        var clone = response.clone();
        caches.open(CACHE_VERSION).then(function (cache) {
          cache.put(request, clone);
        });
      }
      return response;
    });
  });
}

function networkFirst(request) {
  return fetch(request)
    .then(function (response) {
      if (response.ok) {
        var clone = response.clone();
        caches.open(CACHE_VERSION).then(function (cache) {
          cache.put(request, clone);
        });
      }
      return response;
    })
    .catch(function () {
      return caches.match(request).then(function (cached) {
        return cached || new Response("Offline", { status: 503, statusText: "Offline" });
      });
    });
}
