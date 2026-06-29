import { describe, it, expect } from 'vitest';
import { resolveWsBase } from './ws-url';

describe('resolveWsBase', () => {
  it('uses the local backend when served from localhost', () => {
    expect(resolveWsBase('localhost')).toBe('ws://localhost:8000');
    expect(resolveWsBase('127.0.0.1')).toBe('ws://localhost:8000');
  });

  it('uses the deployed backend otherwise', () => {
    expect(resolveWsBase('chat-frontend.onrender.com')).toBe(
      'wss://chat-backend-6g1r.onrender.com'
    );
  });
});
