# La Yuki via @yuki arreu + zoom mòbil + igualtat de noms — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** La Yuki respon a `@yuki` a totes les converses (1-a-1 i grups), es treu el checkbox i el membre reservat, es reanomena la conversa dedicada a "Yuki, la teva IA", s'arregla el zoom mòbil dels inputs i es blinda la igualtat exacta de noms.

**Architecture:** Backend: la Yuki passa a ser ambient — `send_to_room` sempre processa `@yuki` (sense membre reservat) i `send_to` afegeix el mateix per als fils 1-a-1, amb historial per parella i una línia nova `DIRECTAI:`. Frontend: rename de constants, eliminació del checkbox, i un handler `DIRECTAI:` que reaprofita `parseAiPayload`. CSS: `font-size: 16px` als inputs en mòbil.

**Tech Stack:** Backend FastAPI + `groq` + pytest. Frontend Angular 21 (signals) + Vitest.

## Global Constraints

- Menció estricta: `"@yuki" in message.lower()` (backend); la Yuki respon només amb `@yuki`.
- Constants frontend: `AI_ROOM = 'Yuki, la teva IA'` (títol conversa dedicada), `YUKI_NAME = 'Yuki'` (etiqueta de remitent). S'**elimina** `YUKI_MEMBER` (frontend i backend).
- Protocol nou servidor→client: `DIRECTAI:<contacte>:` + JSON `{"text": str, "usage": {...}}`, on `<contacte>` és l'altra persona des del punt de vista de cada receptor (a qui escriu → el destinatari; a l'altre → qui escriu). `ROOMAI:` es manté i ara s'aplica a qualsevol sala. `AI:` (dedicada) es manté.
- Historials separats sembrats amb `AI_SYSTEM_PROMPT`: per usuari (`ai_histories`, dedicada), per sala (`room_ai_histories`), per parella (`direct_ai_histories`, clau `"|".join(sorted([a,b]))`).
- Igualtat de noms exacta a tot arreu (frontend `===`, backend `==`/pertinença a llista/`dict.get`).
- Zoom mòbil: `font-size: 16px` als inputs dins `@media (max-width: 768px)`, a cada full d'estils del component (chat.scss i login.scss). Desktop intacte.
- Angular 21: `@if`/`@for`, class bindings (no `ngClass`/`ngStyle`), signals `.set`/`.update` (no `.mutate`), sense `standalone: true`.
- Backend: comandes des de `backend/` amb `./venv/Scripts/python.exe`; tests `./venv/Scripts/python.exe -m pytest <fitxer> -v`.
- Frontend: des de `frontend/chat-app/`; build `npm run build`; tests `npm run test:unit`.

---

### Task 1: Backend — la Yuki ambient a les sales (treure YUKI_MEMBER)

**Files:**
- Modify: `backend/main.py`
- Modify (reescriure): `backend/test_rooms_ai.py`

**Interfaces:**
- Consumes: `AI_SYSTEM_PROMPT`, `MAX_ROOMS_PER_USER`, `call_groq`, `_ensure_room_history`, `_handle_room_ai` existents.
- Produces: `send_to_room` crida sempre `_handle_room_ai`; el límit de `join_room` torna a l'original; `YUKI_MEMBER` deixa d'existir.

- [ ] **Step 1: Reescriure els tests** — substituir **tot** el contingut de `backend/test_rooms_ai.py` per:

```python
import asyncio
import json

import main


def _mgr_with_capture(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    monkeypatch.setattr(m, "send_text", fake_send)
    return m, sent


def test_room_history_seeded_with_system_prompt():
    m = main.ConnectionManager()
    history = m._ensure_room_history("r1")
    assert history[0]["role"] == "system"
    assert "Yuki" in history[0]["content"]
    assert m._ensure_room_history("r1") is history  # idempotent


def test_send_to_room_mention_calls_groq_and_broadcasts(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    m.rooms = {"r1": ["anna", "bob"]}  # cap "Yuki" membre: la Yuki és ambient

    async def fake_call(messages):
        return "Hola a tothom!", {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        }

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to_room("anna", "r1", "ei @yuki què tal?"))

    history = m.room_ai_histories["r1"]
    assert [x["role"] for x in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "anna: ei @yuki què tal?"

    roomai = [(u, msg) for (u, msg) in sent if msg.startswith("ROOMAI:")]
    recipients = [u for (u, msg) in roomai]
    assert "anna" in recipients and "bob" in recipients  # inclòs el remitent
    payload = json.loads(roomai[0][1][len("ROOMAI:r1:"):])
    assert payload["text"] == "Hola a tothom!"
    assert payload["usage"]["total_tokens"] == 15


def test_send_to_room_no_mention_grows_history_without_groq(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    m.rooms = {"r1": ["anna", "bob"]}
    called = []

    async def fake_call(messages):
        called.append(1)
        return "x", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to_room("anna", "r1", "hola sense mencio"))

    assert called == []
    history = m.room_ai_histories["r1"]
    assert [x["role"] for x in history] == ["system", "user"]
    assert not any(msg.startswith("ROOMAI:") for (u, msg) in sent)
```

- [ ] **Step 2: Executar per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rooms_ai.py -v`
Expected: FAIL — `test_send_to_room_mention...` falla perquè ara `send_to_room` només crida la Yuki si `YUKI_MEMBER in members` (i la sala no té "Yuki").

- [ ] **Step 3: Eliminar la constant `YUKI_MEMBER`** — a `backend/main.py`, esborrar la línia:

```python
YUKI_MEMBER = "Yuki"
```

- [ ] **Step 4: Revertir el límit de `join_room`** — a `backend/main.py`, dins `join_room`, canviar:

```python
            if user != YUKI_MEMBER and self._room_count(user) >= MAX_ROOMS_PER_USER:
```

per:

```python
            if self._room_count(user) >= MAX_ROOMS_PER_USER:
```

- [ ] **Step 5: La Yuki sempre ambient a `send_to_room`** — a `backend/main.py`, dins `send_to_room`, substituir:

```python
        if YUKI_MEMBER in members:
            await self._handle_room_ai(room_name, sender, message)
```

per:

```python
        await self._handle_room_ai(room_name, sender, message)
```

- [ ] **Step 6: Executar per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rooms_ai.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Comprovar que el mòdul carrega (sense referències a YUKI_MEMBER)**

Run (des de `backend/`): `./venv/Scripts/python.exe -c "import main; print('ok')"`
Expected: `ok` (cap `NameError`).

- [ ] **Step 8: Commit**

```bash
git add backend/main.py backend/test_rooms_ai.py
git commit -m "feat(backend): la Yuki és ambient a totes les sales (treure YUKI_MEMBER)"
```

---

### Task 2: Backend — la Yuki als xats 1-a-1 (@yuki) + igualtat exacta de noms

**Files:**
- Modify: `backend/main.py`
- Test: `backend/test_direct_ai.py`

**Interfaces:**
- Consumes: `AI_SYSTEM_PROMPT`, `call_groq`, `logger`, `send_text` existents.
- Produces:
  - `ConnectionManager.direct_ai_histories: dict[str, list[dict]]`
  - `ConnectionManager._pair_key(a, b) -> str` (staticmethod)
  - `ConnectionManager._ensure_direct_history(key) -> list[dict]`
  - `ConnectionManager._handle_direct_ai(sender, receiver, message) -> None`
  - `send_to` crida `_handle_direct_ai` després de lliurar el missatge.

- [ ] **Step 1: Escriure els tests que fallen** — crear `backend/test_direct_ai.py`:

```python
import asyncio
import json

import main


def _mgr_with_capture(monkeypatch):
    m = main.ConnectionManager()
    sent = []

    async def fake_send(username, message):
        sent.append((username, message))

    monkeypatch.setattr(m, "send_text", fake_send)
    return m, sent


def test_pair_key_symmetric():
    assert main.ConnectionManager._pair_key("carme", "pau") == \
           main.ConnectionManager._pair_key("pau", "carme")


def test_send_text_exact_connection_no_prefix_match():
    m = main.ConnectionManager()
    received = {"carme": [], "carme-mobil": []}

    class FakeSocket:
        def __init__(self, name):
            self.name = name

        async def send_text(self, msg):
            received[self.name].append(msg)

    m.connections = {
        "carme": FakeSocket("carme"),
        "carme-mobil": FakeSocket("carme-mobil"),
    }
    asyncio.run(m.send_text("carme-mobil", "hi"))
    assert received["carme-mobil"] == ["hi"]
    assert received["carme"] == []  # cap lliurament per prefix/substring


def test_direct_mention_calls_groq_and_sends_to_both(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)

    async def fake_call(messages):
        return "Sóc la Yuki!", {
            "prompt_tokens": 8,
            "completion_tokens": 4,
            "total_tokens": 12,
        }

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to("carme", "pau", "@yuki ajuda"))

    key = main.ConnectionManager._pair_key("carme", "pau")
    history = m.direct_ai_histories[key]
    assert [x["role"] for x in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "carme: @yuki ajuda"

    directai = [(u, msg) for (u, msg) in sent if msg.startswith("DIRECTAI:")]
    by_recipient = {u: msg for (u, msg) in directai}
    assert by_recipient["carme"].startswith("DIRECTAI:pau:")
    assert by_recipient["pau"].startswith("DIRECTAI:carme:")
    payload = json.loads(by_recipient["carme"][len("DIRECTAI:pau:"):])
    assert payload["text"] == "Sóc la Yuki!"
    assert payload["usage"]["total_tokens"] == 12


def test_direct_no_mention_grows_history_without_groq(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    called = []

    async def fake_call(messages):
        called.append(1)
        return "x", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to("carme", "pau", "hola sense mencio"))

    assert called == []
    key = main.ConnectionManager._pair_key("carme", "pau")
    assert [x["role"] for x in m.direct_ai_histories[key]] == ["system", "user"]
    assert not any(msg.startswith("DIRECTAI:") for (u, msg) in sent)
```

- [ ] **Step 2: Executar per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_direct_ai.py -v`
Expected: FAIL (`AttributeError: ... _pair_key` / `direct_ai_histories`).

- [ ] **Step 3: Afegir l'estat de l'historial de parella** — a `ConnectionManager.__init__` de `backend/main.py`, sota `self.ai_histories`:

```python
        self.direct_ai_histories: dict[str, list[dict]] = {}
```

- [ ] **Step 4: Afegir els helpers i el handler 1-a-1** — a `ConnectionManager`, afegir aquests mètodes (p. ex. just abans de `broadcast`):

```python
    @staticmethod
    def _pair_key(a: str, b: str) -> str:
        return "|".join(sorted([a, b]))

    def _ensure_direct_history(self, key: str) -> list[dict]:
        history = self.direct_ai_histories.get(key)
        if history is None:
            history = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
            self.direct_ai_histories[key] = history
        return history

    async def _handle_direct_ai(self, sender: str, receiver: str, message: str):
        history = self._ensure_direct_history(self._pair_key(sender, receiver))
        history.append({"role": "user", "content": f"{sender}: {message}"})
        if "@yuki" not in message.lower():
            return
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq direct call failed for %s/%s", sender, receiver)
            return
        history.append({"role": "assistant", "content": reply})
        body = json.dumps({"text": reply, "usage": usage})
        await self.send_text(sender, f"DIRECTAI:{receiver}:{body}")
        await self.send_text(receiver, f"DIRECTAI:{sender}:{body}")
```

- [ ] **Step 5: Connectar `send_to` amb el handler** — a `backend/main.py`, substituir `send_to` per:

```python
    async def send_to(self, sender: str, receiver: str, message: str):
        await self.send_text(receiver, f"{sender}:{message}")
        await self._handle_direct_ai(sender, receiver, message)
```

- [ ] **Step 6: Executar per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_direct_ai.py -v`
Expected: PASS (4 tests).

- [ ] **Step 7: Tota la suite verda**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest -v`
Expected: PASS (test_ai.py 3 + test_rooms_ai.py 3 + test_direct_ai.py 4 = 10).

- [ ] **Step 8: Commit**

```bash
git add backend/main.py backend/test_direct_ai.py
git commit -m "feat(backend): la Yuki respon a @yuki als xats 1-a-1 (DIRECTAI) + test exactesa de noms"
```

---

### Task 3: Frontend — rename, treure checkbox, handler DIRECTAI, zoom mòbil

**Files:**
- Modify: `frontend/chat-app/src/app/chat/ai-protocol.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.html`
- Modify: `frontend/chat-app/src/app/chat/chat.scss`
- Modify: `frontend/chat-app/src/app/login/login.scss`

**Interfaces:**
- Consumes: `parseAiPayload`, `Contact`/`Message`, backend `DIRECTAI:` (Task 2).
- Produces: `YUKI_NAME` exportat; handler `handleDirectAiMessage`; sense `YUKI_MEMBER`/`addYuki`.

- [ ] **Step 1: Constants** — a `ai-protocol.ts`, substituir les dues primeres línies:

```typescript
export const AI_ROOM = 'Chat amb IA';
export const YUKI_MEMBER = 'Yuki';
```

per:

```typescript
export const AI_ROOM = 'Yuki, la teva IA';
export const YUKI_NAME = 'Yuki';
```

- [ ] **Step 2: Import al component** — a `chat.ts`, canviar la importació de `./ai-protocol`:

```typescript
import { AI_ROOM, AiUsage, parseAiPayload, YUKI_MEMBER } from './ai-protocol';
```

per:

```typescript
import { AI_ROOM, AiUsage, parseAiPayload, YUKI_NAME } from './ai-protocol';
```

- [ ] **Step 3: Treure el camp `addYuki`** — a `chat.ts`, esborrar la línia:

```typescript
  addYuki = false;
```

- [ ] **Step 4: Treure el reset d'`addYuki` a `toggleGroupMode`** — esborrar dins el bloc `if (!next) { ... }` la línia:

```typescript
      this.addYuki = false;
```

- [ ] **Step 5: Treure l'afegit de Yuki i el reset a `createGroup`** — a `createGroup`, esborrar aquest bloc:

```typescript
    if (this.addYuki) {
      members.push(YUKI_MEMBER);
    }

```

i esborrar també la línia `this.addYuki = false;` (a la part de reset al final del mètode).

- [ ] **Step 6: Etiqueta de remitent a `handleAiMessage`** — a `chat.ts`, dins `handleAiMessage`, canviar `sender: AI_ROOM` per `sender: YUKI_NAME`:

```typescript
    this.aiChat.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: YUKI_NAME,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
```

- [ ] **Step 7: Etiqueta de remitent a `handleRoomAiMessage`** — dins `handleRoomAiMessage`, canviar `sender: YUKI_MEMBER` per `sender: YUKI_NAME`:

```typescript
    room.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: YUKI_NAME,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
```

- [ ] **Step 8: Routing de `DIRECTAI:`** — a `chat.ts`, dins `this.socket.onmessage`, just després del bloc `if (data.startsWith('ROOMAI:')) { ... }`:

```typescript
      if (data.startsWith('DIRECTAI:')) {
        this.handleDirectAiMessage(data.slice('DIRECTAI:'.length));
        return;
      }
```

- [ ] **Step 9: Mètode `handleDirectAiMessage`** — a `chat.ts`, just després de `handleRoomAiMessage`:

```typescript
  // DIRECTAI:contactName:{json}  — resposta de la Yuki dins un fil 1-a-1
  private handleDirectAiMessage(rest: string) {
    const idx = rest.indexOf(':');
    if (idx === -1) return;
    const contactName = rest.slice(0, idx);
    const json = rest.slice(idx + 1);

    let payload;
    try {
      payload = parseAiPayload(json);
    } catch {
      console.warn('Invalid DIRECTAI payload', json);
      return;
    }

    let contact = this.contacts().find(c => c.name === contactName);
    if (!contact) {
      contact = {
        name: contactName,
        initials: contactName.slice(0, 2).toUpperCase(),
        online: true,
        lastMessage: signal(''),
        messages: signal<Message[]>([])
      };
      this.contacts.update(list => [...list, contact!]);
    }

    contact.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: YUKI_NAME,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
    contact.lastMessage.set(payload.text);
  }
```

- [ ] **Step 10: Rename a la plantilla i treure el checkbox** — a `chat.html`:

(a) canviar el text del sidebar de la conversa dedicada:

```html
          <div class="contact-name">Chat amb IA</div>
```

per:

```html
          <div class="contact-name">Yuki, la teva IA</div>
```

(b) esborrar el bloc del checkbox dins `.group-create`:

```html
          <label class="yuki-check">
            <input type="checkbox" [(ngModel)]="addYuki" />
            Afegir la Yuki
          </label>
```

- [ ] **Step 11: CSS — treure `.yuki-check` i afegir el font-size mòbil** — a `chat.scss`:

(a) esborrar el bloc:

```scss
.yuki-check {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #b3578a;
  cursor: pointer;
}
```

(b) dins el bloc `@media (max-width: 768px) { ... }` existent, afegir-hi:

```scss
  .chat-input {
    font-size: 16px;
  }
```

- [ ] **Step 12: CSS del login** — al final de `frontend/chat-app/src/app/login/login.scss`:

```scss
@media (max-width: 768px) {
  .login-input {
    font-size: 16px;
  }
}
```

- [ ] **Step 13: Build + tests**

Run (des de `frontend/chat-app/`): `npm run build`
Expected: build OK, sense errors de TypeScript/plantilla (l'avís de budget CSS és acceptable).
Run (des de `frontend/chat-app/`): `npm run test:unit`
Expected: PASS (4 tests).

- [ ] **Step 14: Commit**

```bash
git add frontend/chat-app/src/app/chat/ai-protocol.ts frontend/chat-app/src/app/chat/chat.ts frontend/chat-app/src/app/chat/chat.html frontend/chat-app/src/app/chat/chat.scss frontend/chat-app/src/app/login/login.scss
git commit -m "feat(frontend): Yuki via @yuki (DIRECTAI), rename, treure checkbox, font-size mòbil"
```

---

## Verificació manual (després de les tasques)

Requereix `GROQ_API_KEY` al backend i, per a producció, el backend de Render redeployat des de `main`.

1. Backend local: `./venv/Scripts/python.exe -m uvicorn main:app --reload` (des de `backend/`).
2. Frontend: `npm start`; obrir `http://localhost:4200` amb dos noms diferents (dues pestanyes).
3. **Dedicada:** la conversa "Yuki, la teva IA" respon a tot sense `@yuki`.
4. **1-a-1:** des d'una persona, obrir xat amb l'altra i escriure "@yuki hola" → la resposta de la Yuki apareix a **tots dos** amb la línia de tokens.
5. **Grup:** crear un grup (ja sense checkbox) i escriure "@yuki" → la Yuki respon a la sala.
6. **Mòbil:** a amplada <768px, en tocar un input no s'ha de fer zoom automàtic.
