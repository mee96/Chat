# Chat amb IA (Groq) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afegir una conversa especial "Chat amb IA" (la Yuki), sempre disponible per a cada usuari, que crida Groq via WebSocket i mostra els tokens gastats sota cada resposta.

**Architecture:** Es reaprofita el WebSocket existent amb un prefix nou `AI:`. La resposta de la IA viatja com a JSON (`{text, usage}`) perquè el text pot contenir `:` i salts de línia. El backend manté un historial per usuari (context multi-torn) i crida `AsyncGroq`. El frontend tracta la IA com una conversa especial separada de les rooms, amb indicador "escrivint…" i una línia de tokens (total visible, desglossat al tooltip).

**Tech Stack:** Backend FastAPI + `groq` (AsyncGroq), Python venv, pytest per als tests. Frontend Angular 21 (signals) + Vitest per als tests de la funció de parseig.

## Global Constraints

- Model Groq: `llama-3.1-8b-instant` (exacte).
- Variable d'entorn de la clau: `GROQ_API_KEY`.
- `requirements.txt` del backend ha d'incloure **totes** les dependències: `fastapi`, `uvicorn`, `websockets`, `groq`.
- Versions instal·lades a fixar: `fastapi==0.136.3`, `uvicorn==0.49.0`, `websockets==16.0` (la de `groq` es captura en instal·lar).
- Prefix de protocol: client→servidor `AI:<text>`; servidor→client `AI:` + JSON `{"text": str, "usage": {"prompt_tokens", "completion_tokens", "total_tokens"} | null}`.
- Payload d'error: `{"text": "⚠️ no s'ha pogut contactar amb la IA", "usage": null}`.
- System prompt: la IA es diu **Yuki**, dolça/amable/una mica kawaii (alguna expressió tendra ocasional sense exagerar), respon SEMPRE en català, i si li pregunten qui és es presenta com la Yuki, l'assistent del xat.
- Angular: no posar `standalone: true`; usar signals, `@if`/`@for`, `class`/`style` bindings (no `ngClass`/`ngStyle`).
- Comandes des de `backend/`: usar l'intèrpret del venv `./venv/Scripts/python.exe`.

---

### Task 1: Backend dependencies (`requirements.txt` + instal·lar groq)

**Files:**
- Create: `backend/requirements.txt`

**Interfaces:**
- Produces: el paquet `groq` importable (`from groq import AsyncGroq`) al venv del backend.

- [ ] **Step 1: Crear `backend/requirements.txt`**

```
fastapi==0.136.3
uvicorn==0.49.0
websockets==16.0
groq
```

- [ ] **Step 2: Instal·lar les dependències al venv**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pip install -r requirements.txt`
Expected: instal·la `groq` i confirma que fastapi/uvicorn/websockets ja hi són.

- [ ] **Step 3: Fixar la versió de groq instal·lada**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pip show groq` per veure la versió (p. ex. `0.x.y`), i editar `requirements.txt` canviant la línia `groq` per `groq==0.x.y` amb el número real.

- [ ] **Step 4: Verificar la importació**

Run (des de `backend/`): `./venv/Scripts/python.exe -c "from groq import AsyncGroq; print('ok')"`
Expected: imprimeix `ok`.

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt
git commit -m "build: requirements.txt del backend amb groq"
```

---

### Task 2: Backend — historial IA, system prompt i handler de Groq

**Files:**
- Modify: `backend/main.py`
- Test: `backend/test_ai.py`

**Interfaces:**
- Consumes: `from groq import AsyncGroq` (Task 1).
- Produces:
  - `main.AI_SYSTEM_PROMPT: str`
  - `main.GROQ_MODEL = "llama-3.1-8b-instant"`
  - `async def main.call_groq(messages: list[dict]) -> tuple[str, dict]` (retorna `(text, usage_dict)` on `usage_dict` té claus `prompt_tokens`, `completion_tokens`, `total_tokens`).
  - `ConnectionManager.ai_histories: dict[str, list[dict]]`
  - `ConnectionManager._ensure_ai_history(username: str) -> list[dict]`
  - `async ConnectionManager.handle_ai_message(username: str, text: str) -> None` (envia `AI:`+JSON via `send_text`).
  - Branca de routing al `websocket_endpoint`: `data.startswith("AI:")`.

- [ ] **Step 1: Instal·lar pytest al venv (dev)**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pip install pytest`
Expected: pytest instal·lat (no s'afegeix a requirements.txt; és només per a dev).

- [ ] **Step 2: Escriure els tests que fallen** — crear `backend/test_ai.py`

```python
import asyncio
import json

import main


def test_history_seeded_with_system_prompt():
    m = main.ConnectionManager()
    history = m._ensure_ai_history("alice")
    assert history[0]["role"] == "system"
    assert "Yuki" in history[0]["content"]
    # Cridar-ho dos cops no duplica el system prompt.
    again = m._ensure_ai_history("alice")
    assert again is history
    assert len([msg for msg in again if msg["role"] == "system"]) == 1


def test_handle_ai_message_appends_and_sends(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    async def fake_call(messages):
        return "Hola! soc la Yuki", {
            "prompt_tokens": 5,
            "completion_tokens": 7,
            "total_tokens": 12,
        }

    monkeypatch.setattr(m, "send_text", fake_send)
    monkeypatch.setattr(main, "call_groq", fake_call)

    asyncio.run(m.handle_ai_message("alice", "qui ets?"))

    history = m.ai_histories["alice"]
    assert [msg["role"] for msg in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "qui ets?"
    assert history[2]["content"] == "Hola! soc la Yuki"

    assert len(sent) == 1
    username, message = sent[0]
    assert username == "alice"
    assert message.startswith("AI:")
    payload = json.loads(message[len("AI:"):])
    assert payload["text"] == "Hola! soc la Yuki"
    assert payload["usage"]["total_tokens"] == 12


def test_handle_ai_message_error_path(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    async def fake_call(messages):
        raise RuntimeError("groq down")

    monkeypatch.setattr(m, "send_text", fake_send)
    monkeypatch.setattr(main, "call_groq", fake_call)

    asyncio.run(m.handle_ai_message("bob", "hola"))

    history = m.ai_histories["bob"]
    # L'usuari hi és, però NO s'afegeix cap resposta d'assistant fallida.
    assert [msg["role"] for msg in history] == ["system", "user"]
    payload = json.loads(sent[0][1][len("AI:"):])
    assert payload["usage"] is None
    assert "no s'ha pogut" in payload["text"]
```

- [ ] **Step 3: Executar els tests per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_ai.py -v`
Expected: FAIL (p. ex. `AttributeError: module 'main' has no attribute 'AI_SYSTEM_PROMPT'` o `ConnectionManager` sense `_ensure_ai_history`).

- [ ] **Step 4: Implementar — capçalera de `main.py`**

A `backend/main.py`, després de les importacions existents (`from fastapi ...`, `from fastapi.middleware.cors ...`), afegir:

```python
import json
import os

from groq import AsyncGroq
```

I després de `MAX_ROOMS_PER_USER = 3`, afegir:

```python
GROQ_MODEL = "llama-3.1-8b-instant"

AI_SYSTEM_PROMPT = (
    "Et dius Yuki i ets l'assistent d'aquest xat. Ets dolça, amable i una mica "
    "kawaii en el to: pots fer servir alguna expressió tendra de tant en tant, "
    "sense exagerar. Respon SEMPRE en català. Si et pregunten qui ets, presenta't "
    "com la Yuki, l'assistent del xat."
)

_groq_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))
    return _groq_client


async def call_groq(messages: list[dict]) -> tuple[str, dict]:
    response = await get_groq_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
    )
    text = response.choices[0].message.content
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
    return text, usage
```

- [ ] **Step 5: Implementar — `ConnectionManager`**

A `ConnectionManager.__init__`, afegir el diccionari d'historials sota `self.rooms`:

```python
        self.ai_histories: dict[str, list[dict]] = {}
```

I afegir aquests dos mètodes a `ConnectionManager` (p. ex. just abans del comentari `# ---- Rooms ----`):

```python
    def _ensure_ai_history(self, username: str) -> list[dict]:
        history = self.ai_histories.get(username)
        if history is None:
            history = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
            self.ai_histories[username] = history
        return history

    async def handle_ai_message(self, username: str, text: str):
        history = self._ensure_ai_history(username)
        history.append({"role": "user", "content": text})
        try:
            reply, usage = await call_groq(history)
        except Exception:
            await self.send_text(
                username,
                "AI:" + json.dumps(
                    {"text": "⚠️ no s'ha pogut contactar amb la IA", "usage": None}
                ),
            )
            return
        history.append({"role": "assistant", "content": reply})
        await self.send_text(
            username,
            "AI:" + json.dumps({"text": reply, "usage": usage}),
        )
```

- [ ] **Step 6: Executar els tests per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_ai.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Afegir la branca de routing al `websocket_endpoint`**

A `backend/main.py`, dins el `while True` del `websocket_endpoint`, afegir una branca `elif` **abans** del `else:` final (el que fa `receiver, message = data.split(":", 1)`):

```python
            elif data.startswith("AI:"):
                await manager.handle_ai_message(username, data[len("AI:"):])
```

- [ ] **Step 8: Verificar que el mòdul carrega i els tests segueixen verds**

Run (des de `backend/`): `./venv/Scripts/python.exe -c "import main; print('import ok')"` → Expected: `import ok`.
Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_ai.py -v` → Expected: PASS (3 tests).

- [ ] **Step 9: Commit**

```bash
git add backend/main.py backend/test_ai.py
git commit -m "feat(backend): handler de Chat amb IA (Groq) amb historial i tokens"
```

---

### Task 3: Frontend — funció de parseig `AI:` + setup de Vitest

**Files:**
- Create: `frontend/chat-app/src/app/chat/ai-protocol.ts`
- Create: `frontend/chat-app/src/app/chat/ai-protocol.spec.ts`
- Create: `frontend/chat-app/vitest.config.ts`
- Modify: `frontend/chat-app/package.json` (script `test:unit` + devDep `vitest`)

**Interfaces:**
- Produces:
  - `export const AI_ROOM = 'Chat amb IA'`
  - `export interface AiUsage { prompt: number; completion: number; total: number }`
  - `export interface AiPayload { text: string; usage: AiUsage | null }`
  - `export function parseAiPayload(json: string): AiPayload`

- [ ] **Step 1: Instal·lar Vitest com a devDependency**

Run (des de `frontend/chat-app/`): `npm install -D vitest`
Expected: `vitest` afegit a `devDependencies` de `package.json`.

- [ ] **Step 2: Crear la config de Vitest** — `frontend/chat-app/vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    include: ['src/**/*.spec.ts'],
  },
});
```

- [ ] **Step 3: Afegir el script de test** — a `frontend/chat-app/package.json`, dins `"scripts"`, afegir:

```json
    "test:unit": "vitest run"
```

(Deixar intacte el `"test": "ng test"` existent.)

- [ ] **Step 4: Escriure el test que falla** — crear `frontend/chat-app/src/app/chat/ai-protocol.spec.ts`

```typescript
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
```

- [ ] **Step 5: Executar el test per veure'l fallar**

Run (des de `frontend/chat-app/`): `npm run test:unit`
Expected: FAIL (no es pot resoldre `./ai-protocol`).

- [ ] **Step 6: Implementar** — crear `frontend/chat-app/src/app/chat/ai-protocol.ts`

```typescript
export const AI_ROOM = 'Chat amb IA';

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
```

- [ ] **Step 7: Executar el test per veure'l passar**

Run (des de `frontend/chat-app/`): `npm run test:unit`
Expected: PASS (2 tests).

- [ ] **Step 8: Commit**

```bash
git add frontend/chat-app/src/app/chat/ai-protocol.ts frontend/chat-app/src/app/chat/ai-protocol.spec.ts frontend/chat-app/vitest.config.ts frontend/chat-app/package.json frontend/chat-app/package-lock.json
git commit -m "feat(frontend): parseig del protocol AI i setup de vitest"
```

---

### Task 4: Frontend — integrar la conversa IA al `ChatComponent`

**Files:**
- Modify: `frontend/chat-app/src/app/chat/chat.ts`

**Interfaces:**
- Consumes: `AI_ROOM`, `AiUsage`, `parseAiPayload` de `./ai-protocol` (Task 3).
- Produces (usat per la plantilla a Task 5):
  - `aiChat: { name: string; messages: WritableSignal<Message[]>; lastMessage: WritableSignal<string> }`
  - `activeAi: Signal<boolean>`, `aiTyping: Signal<boolean>`
  - `selectAi(): void`
  - `active()` retorna un objecte amb el camp addicional `isAi: boolean`.
  - `Message` amb camp opcional `usage?: AiUsage`.

- [ ] **Step 1: Importar el protocol IA** — a dalt de `chat.ts`, afegir sota la importació de `FormsModule`:

```typescript
import { AI_ROOM, AiUsage, parseAiPayload } from './ai-protocol';
```

- [ ] **Step 2: Afegir `usage` a la interfície `Message`**

```typescript
interface Message {
  text: string;
  sender: string;
  time: string;
  isMe: boolean;
  usage?: AiUsage;
}
```

- [ ] **Step 3: Declarar l'estat de la IA** — després de `readonly activeRoom = signal<Room | null>(null);`, afegir:

```typescript
  readonly aiChat = {
    name: AI_ROOM,
    messages: signal<Message[]>([]),
    lastMessage: signal('')
  };
  readonly activeAi = signal(false);
  readonly aiTyping = signal(false);
```

- [ ] **Step 4: Afegir la branca IA al computed `active`** — al principi del cos del `computed`, abans de `const c = this.activeContact();`, afegir:

```typescript
    if (this.activeAi()) {
      return {
        title: this.aiChat.name,
        subtitle: this.aiTyping() ? 'escrivint…' : 'sempre disponible ✦',
        initials: '🤖',
        online: true,
        isRoom: false,
        isAi: true,
        messages: this.aiChat.messages,
      };
    }
```

I afegir `isAi: false,` als dos `return` existents (el del contacte i el de la room), perquè el tipus retornat sigui consistent. Concretament, dins l'objecte del contacte i dins l'objecte de la room, afegir la línia `isAi: false,` (per exemple just abans de `messages:`).

- [ ] **Step 5: Gestionar el missatge `AI:` entrant** — dins `this.socket.onmessage`, afegir aquest bloc just abans del bloc `if (data.startsWith('SYSTEM:users:'))`:

```typescript
      if (data.startsWith('AI:')) {
        this.handleAiMessage(data.slice('AI:'.length));
        return;
      }
```

- [ ] **Step 6: Afegir el mètode `handleAiMessage`** — afegir-lo com a mètode privat (p. ex. després de `handleRoomMessage`):

```typescript
  private handleAiMessage(json: string) {
    this.aiTyping.set(false);

    let payload;
    try {
      payload = parseAiPayload(json);
    } catch {
      console.warn('Invalid AI payload', json);
      return;
    }

    this.aiChat.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: AI_ROOM,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
    this.aiChat.lastMessage.set(payload.text);
  }
```

- [ ] **Step 7: Afegir `selectAi` i netejar `activeAi` als altres selectors**

Afegir el mètode:

```typescript
  selectAi() {
    this.activeContact.set(null);
    this.activeRoom.set(null);
    this.activeAi.set(true);
  }
```

I a `selectContact` afegir `this.activeAi.set(false);` com a primera línia; a `selectRoom` afegir també `this.activeAi.set(false);` com a primera línia. Resultat:

```typescript
  selectContact(contact: Contact) {
    this.activeAi.set(false);
    this.activeRoom.set(null);
    this.activeContact.set(contact);
  }

  selectRoom(room: Room) {
    this.activeAi.set(false);
    this.activeContact.set(null);
    this.activeRoom.set(room);
  }
```

- [ ] **Step 8: Enviar a la IA des de `sendMessage`** — dins `sendMessage`, just després del bloc de comprovació `if (this.socket?.readyState !== WebSocket.OPEN) {...}` i abans de `const room = this.activeRoom();`, afegir:

```typescript
    if (this.activeAi()) {
      this.socket.send('AI:' + text);
      this.aiChat.messages.update(msgs => [...msgs, {
        text,
        sender: this.myName(),
        time: this.getTime(),
        isMe: true
      }]);
      this.aiChat.lastMessage.set(text);
      this.aiTyping.set(true);
      this.newMessage = '';
      return;
    }
```

- [ ] **Step 9: Verificar que compila (build)**

Run (des de `frontend/chat-app/`): `npm run build`
Expected: build OK sense errors de TypeScript. (La plantilla encara no usa `selectAi`/`isAi`; això és normal i no trenca el build.)

- [ ] **Step 10: Commit**

```bash
git add frontend/chat-app/src/app/chat/chat.ts
git commit -m "feat(frontend): integrar la conversa IA al ChatComponent"
```

---

### Task 5: Frontend — UI (entrada de la IA, indicador i línia de tokens)

**Files:**
- Modify: `frontend/chat-app/src/app/chat/chat.html`
- Modify: `frontend/chat-app/src/app/chat/chat.scss`

**Interfaces:**
- Consumes: `aiChat`, `activeAi()`, `aiTyping()`, `selectAi()`, `active().isAi`, `msg.usage` (Task 4).

- [ ] **Step 1: Afegir l'entrada "Chat amb IA" al sidebar** — a `chat.html`, dins `<div class="chats-section">`, just després de `<div class="section-title">💬 chats</div>` i abans del `@for (contact of contacts(); ...)`, afegir:

```html
      <div class="contact ai" [class.active]="activeAi()" (click)="selectAi()">
        <div class="avatar ai">🤖</div>
        <div class="contact-info">
          <div class="contact-name">Chat amb IA</div>
          <div class="contact-last">{{ aiChat.lastMessage() || 'parla amb la Yuki ✦' }}</div>
        </div>
      </div>
```

- [ ] **Step 2: Afegir la línia de tokens sota cada missatge** — a `chat.html`, dins el `@for (msg of a.messages(); ...)`, just després del `<div class="bubble" ...>...</div>`, afegir:

```html
            @if (msg.usage; as u) {
              <span
                class="tokens"
                [title]="'prompt: ' + u.prompt + ' · resposta: ' + u.completion + ' · total: ' + u.total">
                {{ u.total }} tokens
              </span>
            }
```

- [ ] **Step 3: Afegir l'indicador "escrivint…"** — a `chat.html`, dins `<div class="messages" #messagesContainer>`, just després del bloc `@for (msg of a.messages(); ...)`, afegir:

```html
        @if (a.isAi && aiTyping()) {
          <div class="msg-row">
            <span class="msg-meta">Chat amb IA</span>
            <div class="bubble typing">escrivint…</div>
          </div>
        }
```

- [ ] **Step 4: Afegir els estils** — al final de `frontend/chat-app/src/app/chat/chat.scss`, afegir:

```scss
.avatar.ai {
  background: #f7a8c4;
  border-color: #e06a98;
  color: #6b1f3d;
}

.contact.ai {
  &.active {
    background: #fbdce8;
    border-color: #e06a98;
  }
}

.tokens {
  font-size: 9px;
  color: #b3578a;
  padding: 0 4px;
  cursor: help;
}

.bubble.typing {
  background: #fbdce8;
  border: 1.5px solid #f7a8c4;
  color: #b3578a;
  font-style: italic;
}
```

- [ ] **Step 5: Verificar el build**

Run (des de `frontend/chat-app/`): `npm run build`
Expected: build OK sense errors.

- [ ] **Step 6: Verificació manual (extrem a extrem)**

Requereix `GROQ_API_KEY` definida a l'entorn del backend.
1. Backend (des de `backend/`): `./venv/Scripts/uvicorn.exe main:app --reload` (o `./venv/Scripts/python.exe -m uvicorn main:app --reload`).
2. Frontend (des de `frontend/chat-app/`): `npm start`. **Nota:** el `chat.ts` apunta a `wss://chat-backend-6g1r.onrender.com`; per provar contra el backend local, canviar temporalment la URL del WebSocket a `ws://localhost:8000/ws/${this.myName()}` (no commitejar aquest canvi tret que sigui el desitjat).
3. Entrar amb un nom, obrir "Chat amb IA", enviar "qui ets?".
4. Comprovar: apareix "escrivint…", després la resposta de la Yuki en català, i sota la resposta `N tokens`; en passar el ratolí per sobre, el tooltip mostra el desglossat.

- [ ] **Step 7: Commit**

```bash
git add frontend/chat-app/src/app/chat/chat.html frontend/chat-app/src/app/chat/chat.scss
git commit -m "feat(frontend): UI del Chat amb IA (entrada, escrivint, tokens)"
```

---

## Notes de desplegament (Render)

- Definir `GROQ_API_KEY` a les variables d'entorn del servei backend a Render.
- Assegurar que el comandament de build del backend instal·la `backend/requirements.txt` i el d'inici és `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- El frontend en producció ja apunta a `wss://chat-backend-6g1r.onrender.com`; revertir qualsevol canvi local de la URL del WebSocket abans de desplegar.
