# Disseny: Chat amb IA (Groq)

**Data:** 2026-06-29
**Projecte:** Chat (Angular 21 + FastAPI + WebSocket, desplegat a Render)

## Objectiu

Afegir una conversa especial "Chat amb IA", sempre disponible per a cada usuari, on
el backend crida Groq (`llama-3.1-8b-instant`) quan l'usuari envia un missatge i
retorna la resposta de la IA juntament amb els tokens gastats (`usage`). El frontend
mostra el total de tokens sota cada resposta de la IA, amb el desglossat al tooltip.

## Decisions preses

- **Memòria:** la IA recorda la sessió (context multi-torn). El backend manté un
  historial per usuari i l'envia sencer a Groq cada vegada.
- **Tokens:** es mostra `total_tokens` visible sota cada resposta; el tooltip (atribut
  `title`) mostra el desglossat `prompt_tokens` / `completion_tokens` / `total_tokens`.
- **Lliurament:** resposta completa (no streaming). Indicador "escrivint…" mentre
  s'espera Groq.
- **Model:** `llama-3.1-8b-instant`.
- **Personalitat (system prompt):** la IA es diu **Yuki**, és dolça, amable i una mica
  kawaii en el to (pot usar alguna expressió tendra ocasionalment, sense exagerar),
  respon **sempre en català**, i si li pregunten qui és es presenta com la Yuki,
  l'assistent del xat.

## Arquitectura general

Es reaprofita el WebSocket existent amb un **prefix nou `AI:`**, en paral·lel als
prefixos actuals (`JOIN:` / `ROOM:` / missatge directe `receiver:message`).

La "Chat amb IA" **no és una room real** amb membres: és una conversa especial sempre
present per cada usuari, que no passa pel sistema de rooms ni pel límit de 3.

- SDK: `groq` (Python). Client `AsyncGroq` per fer `await` dins el handler sense
  bloquejar la resta d'usuaris.
- Clau: variable d'entorn `GROQ_API_KEY` (configurada a Render i en local).

## Protocol

A diferència de la resta de missatges (text delimitat per `:`), la resposta de la IA
viatja com a **JSON** darrere el prefix, perquè el text pot contenir `:` i salts de
línia.

- **Client → servidor:** `AI:<text de l'usuari>`
- **Servidor → client:** `AI:` + JSON

```json
{
  "text": "resposta de la IA...",
  "usage": { "prompt_tokens": 12, "completion_tokens": 34, "total_tokens": 46 }
}
```

- **Error de Groq / sense clau:** `AI:` + `{ "text": "⚠️ no s'ha pogut contactar amb la IA", "usage": null }`

## Backend (`backend/main.py`)

- `ConnectionManager` guanya `ai_histories: dict[str, list[dict]]` — historial per
  usuari en format `messages` de Groq (`{"role": ..., "content": ...}`). Persisteix
  mentre el servidor viu, igual que `rooms`. El system prompt de la Yuki s'afegeix com
  a primer missatge quan es crea l'historial d'un usuari.
- Constant `SYSTEM_PROMPT` amb la personalitat de la Yuki.
- Nou mètode `handle_ai_message(username, text)`:
  1. Afegeix `{"role": "user", "content": text}` a l'historial de l'usuari.
  2. Crida `AsyncGroq().chat.completions.create(model="llama-3.1-8b-instant", messages=historial)`.
  3. Afegeix `{"role": "assistant", "content": resposta}` a l'historial.
  4. Envia `AI:` + JSON amb `text` i `usage` (de `response.usage`).
  5. En cas d'excepció, envia el payload d'error (`usage: null`) i no contamina
     l'historial amb una resposta fallida.
- A `websocket_endpoint`, branca nova: `elif data.startswith("AI:")` →
  `handle_ai_message(username, data[len("AI:"):])`.
- Actualment el backend no té cap `requirements.txt`. Cal crear-lo (amb `fastapi`,
  `uvicorn`, `groq`, etc.) perquè Render instal·li la dependència `groq` al desplegar.

## Frontend (`chat.ts` / `chat.html` / `chat.scss`)

- Constant `AI_ROOM = 'Chat amb IA'` i un objecte especial `aiChat` (amb signal
  `messages`), **separat** de `rooms` perquè la sincronització del servidor
  (`handleJoin` / `send_user_rooms`) no l'afecti. Es fixa a dalt de la llista de
  converses i sempre està disponible.
- La interfície `Message` guanya un camp opcional
  `usage?: { prompt: number; completion: number; total: number }`.
- Signal `activeAi` (o reaprofitar un patró equivalent). El `computed` `active`
  inclou la conversa de la IA amb un flag `isAi: true`.
- Signal `aiTyping` per a l'indicador "escrivint…".
- En enviar amb la IA activa: `socket.send('AI:' + text)`, pinta el missatge propi i
  activa `aiTyping`.
- En rebre un missatge `AI:`: parseja el JSON, afegeix el missatge de la IA amb
  `usage`, i apaga `aiTyping`.
- A la plantilla, sota cada missatge de la IA que tingui `usage`: línia amb
  `total_tokens` visible i atribut `title` amb el desglossat.

## Gestió d'errors

- Si Groq falla o falta `GROQ_API_KEY`, el backend respon amb el payload d'error
  (`usage: null`); el frontend mostra el text d'avís sense línia de tokens i apaga
  l'indicador "escrivint…".
- Si el JSON entrant no es pot parsejar al frontend, es registra l'error i s'apaga
  l'indicador sense trencar la conversa.

## Testing

- **Backend:** amb un mock de Groq, comprovar que el prefix `AI:` s'encamina al
  handler, que l'historial de l'usuari creix (user + assistant), i que el payload
  enviat inclou `text` i `usage`. Comprovar també el camí d'error (excepció de Groq →
  payload amb `usage: null`, historial sense resposta fallida).
- **Frontend:** comprovar el parseig d'un missatge `AI:` entrant i el renderitzat de la
  línia de tokens (total visible, desglossat al `title`).

## Fora d'abast (YAGNI)

- Streaming token a token.
- Persistència de l'historial en base de dades (es manté en memòria del procés).
- Configuració de model/temperatura des del frontend.
