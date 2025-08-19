const CACHE_NAME = 'myzone-v1';
const STATIC_CACHE_NAME = 'myzone-static-v1';
const DYNAMIC_CACHE_NAME = 'myzone-dynamic-v1';

// 캐시할 정적 자원들
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico'
];

// 캐시할 API 엔드포인트 패턴
const API_CACHE_PATTERNS = [
  /\/api\/v1\/plans/,
  /\/api\/v1\/devices/,
  /\/api\/v1\/numbers/
];

// 캐시하지 않을 패턴
const NO_CACHE_PATTERNS = [
  /\/api\/v1\/auth/,
  /\/api\/v1\/orders/,
  /\/api\/v1\/payments/
];

// 서비스 워커 설치
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Installed');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// 서비스 워커 활성화
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// 네트워크 요청 가로채기
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 캐시하지 않을 요청들
  if (shouldNotCache(request)) {
    return;
  }

  // GET 요청만 캐시
  if (request.method !== 'GET') {
    return;
  }

  // 정적 자원 요청
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE_NAME));
    return;
  }

  // API 요청
  if (isApiRequest(request)) {
    event.respondWith(networkFirst(request, DYNAMIC_CACHE_NAME));
    return;
  }

  // 기타 요청 (HTML 페이지 등)
  event.respondWith(networkFirst(request, DYNAMIC_CACHE_NAME));
});

// 캐시 우선 전략 (정적 자원용)
async function cacheFirst(request, cacheName) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('Cache first strategy failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// 네트워크 우선 전략 (동적 콘텐츠용)
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 오프라인 페이지 반환
    if (request.destination === 'document') {
      return caches.match('/offline.html') || new Response('Offline', { status: 503 });
    }
    
    return new Response('Offline', { status: 503 });
  }
}

// 정적 자원 확인
function isStaticAsset(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/static/') || 
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.jpeg') ||
         url.pathname.endsWith('.webp') ||
         url.pathname.endsWith('.svg');
}

// API 요청 확인
function isApiRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/');
}

// 캐시하지 않을 요청 확인
function shouldNotCache(request) {
  const url = new URL(request.url);
  
  // 인증, 주문, 결제 관련 요청은 캐시하지 않음
  return NO_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

// 백그라운드 동기화 (향후 확장용)
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

async function doBackgroundSync() {
  // 오프라인 상태에서 저장된 데이터를 서버로 전송
  console.log('Background sync triggered');
}

// 푸시 알림 (향후 확장용)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/icon-192x192.png',
      badge: '/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: data.primaryKey
      }
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// 알림 클릭 처리
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});