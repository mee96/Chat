// Exponential backoff (in ms) for WebSocket reconnection attempts.
// attempt 0 -> base, doubling each attempt, never exceeding max. Negative
// attempts are clamped to the base delay.
export function reconnectDelay(
  attempt: number,
  base = 1000,
  max = 15000,
): number {
  const exp = base * 2 ** Math.max(0, attempt);
  return Math.min(exp, max);
}
