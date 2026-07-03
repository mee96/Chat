export const AI_ROOM = 'Yuki, la teva IA';
export const YUKI_NAME = 'Yuki';
export const PDF_CHAT = '📚 Gramàtica';

export interface AiUsage {
  prompt: number;
  completion: number;
  total: number;
}

export interface AiPayload {
  text: string;
  usage: AiUsage | null;
}

// Parses the JSON body of an incoming "AI:" websocket message.
export function parseAiPayload(json: string): AiPayload {
  const data = JSON.parse(json) as {
    text?: string;
    usage?: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    } | null;
  };

  const usage = data.usage
    ? {
        prompt: data.usage.prompt_tokens,
        completion: data.usage.completion_tokens,
        total: data.usage.total_tokens,
      }
    : null;

  return { text: data.text ?? '', usage };
}
