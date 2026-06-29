const PROD_WS_BASE = 'wss://chat-backend-6g1r.onrender.com';
const LOCAL_WS_BASE = 'ws://localhost:8000';

// When the page is served from localhost we talk to the local backend
// (so local dev/testing hits the backend you're running), otherwise the
// deployed Render backend.
export function resolveWsBase(hostname: string): string {
  return hostname === 'localhost' || hostname === '127.0.0.1'
    ? LOCAL_WS_BASE
    : PROD_WS_BASE;
}
