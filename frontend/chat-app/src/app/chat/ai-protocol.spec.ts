import { describe, it, expect } from 'vitest';
import { parseAiPayload } from './ai-protocol';

describe('parseAiPayload', () => {
  it('parses text and usage breakdown', () => {
    const json = JSON.stringify({
      text: 'Hola! soc la Yuki',
      usage: { prompt_tokens: 5, completion_tokens: 7, total_tokens: 12 },
    });
    const result = parseAiPayload(json);
    expect(result.text).toBe('Hola! soc la Yuki');
    expect(result.usage).toEqual({ prompt: 5, completion: 7, total: 12 });
  });

  it('returns null usage on error payloads', () => {
    const json = JSON.stringify({ text: '⚠️ error', usage: null });
    const result = parseAiPayload(json);
    expect(result.usage).toBeNull();
    expect(result.text).toBe('⚠️ error');
  });
});
