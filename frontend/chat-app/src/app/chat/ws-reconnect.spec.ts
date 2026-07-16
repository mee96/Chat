import { describe, it, expect } from 'vitest';
import { reconnectDelay } from './ws-reconnect';

describe('reconnectDelay', () => {
  it('starts at the base delay on the first attempt', () => {
    expect(reconnectDelay(0, 1000, 15000)).toBe(1000);
  });

  it('doubles with each attempt (exponential backoff)', () => {
    expect(reconnectDelay(1, 1000, 15000)).toBe(2000);
    expect(reconnectDelay(2, 1000, 15000)).toBe(4000);
    expect(reconnectDelay(3, 1000, 15000)).toBe(8000);
  });

  it('caps at the maximum delay', () => {
    expect(reconnectDelay(10, 1000, 15000)).toBe(15000);
  });

  it('treats negative attempts as the base delay', () => {
    expect(reconnectDelay(-3, 1000, 15000)).toBe(1000);
  });
});
