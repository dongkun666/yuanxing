'use strict';

var CACHE_NAME = 'lexprime-cache-v1';
var CACHE_NAME_RUNTIME = 'lexprime-runtime-v1';
var OFFLINE_PAGE = './offline.html';

var PRECACHE_ASSETS = [
    './index.html',
    './offline.html',
    './assets/css/tailwind.css',
    './assets/css/styles.css',
    './assets/css/marketplace.css',
    './assets/js/bootstrap.js',
    './assets/js/api.js',
    './assets/js/auth.js',
    './assets/js/app-state.js',
    './assets/js/router.js',
    './assets/js/utils.js',
    './assets/js/script.js',
    './assets/js/iconify-icon.min.js',
    './assets/icons/mdi.json',
    './assets/images/avatar.jpg',
    './assets/icons/pwa/icon-48x48.png',
    './assets/icons/pwa/icon-72x72.png',
    './assets/icons/pwa/icon-96x96.png',
    './assets/icons/pwa/icon-144x144.png',
    './assets/icons/pwa/icon-192x192.png',
    './assets/icons/pwa/icon-512x512.png',
    './templates/modals.html',
    './templates/views/workstation.html'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(PRECACHE_ASSETS);
        }).then(function() {
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate', function(event) {
    var currentCaches = [CACHE_NAME, CACHE_NAME_RUNTIME];
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (currentCaches.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(function() {
            return self.clients.claim();
        })
    );
});

self.addEventListener('fetch', function(event) {
    var request = event.request;

    if (request.method !== 'GET') {
        return;
    }

    if (request.url.indexOf('./api/') !== -1 || request.url.indexOf('/api/') !== -1) {
        event.respondWith(
            fetchAndCacheRuntime(request)
        );
        return;
    }

    event.respondWith(
        caches.match(request).then(function(cachedResponse) {
            var fetchPromise = fetch(request).then(function(networkResponse) {
                if (networkResponse && networkResponse.status === 200) {
                    var cacheCopy = networkResponse.clone();
                    caches.open(CACHE_NAME).then(function(cache) {
                        cache.put(request, cacheCopy);
                    });
                }
                return networkResponse;
            }).catch(function() {
                if (request.mode === 'navigate') {
                    return caches.match(OFFLINE_PAGE);
                }
                return cachedResponse;
            });

            return cachedResponse ? cachedResponse : fetchPromise;
        })
    );
});

function fetchAndCacheRuntime(request) {
    return caches.open(CACHE_NAME_RUNTIME).then(function(cache) {
        return fetch(request).then(function(networkResponse) {
            if (networkResponse && networkResponse.status === 200) {
                cache.put(request, networkResponse.clone());
            }
            return networkResponse;
        }).catch(function() {
            return cache.match(request);
        });
    });
}

self.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});