// v4 - 이전 캐시 전부 삭제, 캐시 사용 안 함
self.addEventListener('install', () => self.skipWaiting())

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => caches.delete(k))))
  )
  self.clients.claim()
})

// 네트워크만 사용, 캐시 안 함
self.addEventListener('fetch', () => {})
