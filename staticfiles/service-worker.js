 const CACHE_NAME = "movie-stream-v1";
const urlsToCache = [
    "/",
    "/home.html", // Thêm trang HTML chính
    "/static/css/style.css",
    "/static/js/main.js",
    "/static/manifest.json", // Thêm manifest.json
    "/static/icons/icon-192.png", // Thêm biểu tượng
    "/static/icons/icon-512.png"  // Thêm biểu tượng
];

// Sự kiện "install" - Lưu trữ các tài nguyên cơ bản vào cache
self.addEventListener("install", event => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log("Caching files");
            return cache.addAll(urlsToCache);
        }).catch(err => console.error("Cache open failed:", err))
    );
});


// Sự kiện "fetch" - Phục vụ tài nguyên từ cache hoặc tải từ mạng
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            // Nếu tài nguyên có trong cache, trả về từ cache
            if (response) {
                return response;
            }

            // Nếu không có trong cache, tải từ mạng và lưu vào cache
            return fetch(event.request).then(networkResponse => {
                // Chỉ lưu trữ các phản hồi hợp lệ (status 200 và type basic)
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== "basic") {
                    return networkResponse;
                }

                // Clone phản hồi để lưu vào cache
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseToCache);
                });

                return networkResponse;
            }).catch(err => {
                // Nếu không thể tải từ mạng (offline), trả về trang mặc định từ cache
                console.error("Fetch failed:", err);
                return caches.match("/home.html");
            });
        })
    );
});

// Sự kiện "activate" - Xóa các cache cũ không còn dùng
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});
