# La Yuki dins les rooms — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permetre afegir la Yuki com a membre d'una sala de grup; quan la mencionen amb `@yuki`, el backend crida Groq amb l'historial de la sala i reparteix la resposta (amb tokens) a tots els membres.

**Architecture:** La Yuki és un membre reservat (`"Yuki"`) de la sala, afegit via el `JOIN:` existent. El backend manté un historial de context per sala, afegeix cada missatge del grup, i quan detecta `@yuki` crida Groq i fa broadcast d'una línia nova `ROOMAI:<sala>:{json}`. El frontend afegeix un checkbox "Afegir la Yuki" a la creació de grup i un handler `ROOMAI:` que reaprofita `parseAiPayload` i la UI de tokens existent.

**Tech Stack:** Backend FastAPI + `groq` (AsyncGroq) + pytest. Frontend Angular 21 (signals) + Vitest.

## Global Constraints

- Nom reservat de la Yuki: `"Yuki"` — backend `YUKI_MEMBER = "Yuki"`, frontend `YUKI_MEMBER = 'Yuki'` (mateix literal exacte).
- Detecció de menció **estricta**: `"@yuki" in message.lower()` (insensible a majúscules).
- La Yuki **no compta** ni es rebutja pel límit `MAX_ROOMS_PER_USER` (= 3).
- Línia nova servidor→client: `ROOMAI:<sala>:` + JSON `{"text": str, "usage": {"prompt_tokens","completion_tokens","total_tokens"}}`, repartida a **tots** els membres de la sala (inclòs el remitent).
- Historial per sala (`room_ai_histories`), sembrat amb `AI_SYSTEM_PROMPT`; cada missatge del grup s'hi afegeix com `{"role":"user","content":"<remitent>: <missatge>"}` **només** si la sala té la Yuki; la resposta s'afegeix com `{"role":"assistant","content":<resposta>}`.
- Es reaprofiten `call_groq` i `AI_SYSTEM_PROMPT`; **cap canvi** al xat 1-a-1 de la Yuki.
- En error de Groq: log de l'excepció, **no** s'envia `ROOMAI:` i **no** s'afegeix resposta fallida a l'historial.
- Angular: no `standalone: true`; signals; `@if`/`@for`; class bindings (no `ngClass`/`ngStyle`); `.update`/`.set` (no `.mutate`).
- Backend: comandes des de `backend/` amb `./venv/Scripts/python.exe`; tests `./venv/Scripts/python.exe -m pytest <fitxer> -v`.
- Frontend: comandes des de `frontend/chat-app/`; build `npm run build`; tests `npm run test:unit`.

---

### Task 1: Backend — membre reservat Yuki, historial per sala i bypass del límit

**Files:**
- Modify: `backend/main.py`
- Test: `backend/test_rooms_ai.py`

**Interfaces:**
- Consumes: `AI_SYSTEM_PROMPT`, `MAX_ROOMS_PER_USER`, `ConnectionManager` existents.
- Produces:
  - `main.YUKI_MEMBER = "Yuki"`
  - `ConnectionManager.room_ai_histories: dict[str, list[dict]]`
  - `ConnectionManager._ensure_room_history(room_name: str) -> list[dict]`
  - `join_room` accepta `"Yuki"` com a membre saltant-se el límit.

- [ ] **Step 1: Escriure els tests que fallen** — crear `backend/test_rooms_ai.py`

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


def test_join_room_adds_yuki_without_limit(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    Y = main.YUKI_MEMBER
    # Yuki ja és a 3 rooms; sense bypass seria rebutjada pel límit.
    m.rooms = {"a": [Y], "b": [Y], "c": [Y]}
    asyncio.run(m.join_room("anna", "d", ["bob", Y]))
    assert "anna" in m.rooms["d"]
    assert "bob" in m.rooms["d"]
    assert Y in m.rooms["d"]
```

- [ ] **Step 2: Executar els tests per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rooms_ai.py -v`
Expected: FAIL (`AttributeError: module 'main' has no attribute 'YUKI_MEMBER'` o falta `_ensure_room_history`).

- [ ] **Step 3: Afegir la constant `YUKI_MEMBER`** — a `backend/main.py`, just després de `MAX_ROOMS_PER_USER = 3`:

```python
YUKI_MEMBER = "Yuki"
```

- [ ] **Step 4: Afegir `room_ai_histories` i el helper** — a `ConnectionManager.__init__`, sota `self.rooms`:

```python
        self.room_ai_histories: dict[str, list[dict]] = {}
```

I afegir aquest mètode a `ConnectionManager` (p. ex. just abans de `_room_count`):

```python
    def _ensure_room_history(self, room_name: str) -> list[dict]:
        history = self.room_ai_histories.get(room_name)
        if history is None:
            history = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
            self.room_ai_histories[room_name] = history
        return history
```

- [ ] **Step 5: Bypass del límit per a la Yuki a `join_room`** — dins el bucle `for user in desired:`, canviar la condició del límit perquè exclogui `YUKI_MEMBER`:

Reemplaça:

```python
            if self._room_count(user) >= MAX_ROOMS_PER_USER:
```

per:

```python
            if user != YUKI_MEMBER and self._room_count(user) >= MAX_ROOMS_PER_USER:
```

- [ ] **Step 6: Executar els tests per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rooms_ai.py -v`
Expected: PASS (3 tests: el de l'historial i el de join; el tercer s'afegeix a la Task 2 — de moment 2 passen).

> Nota: a aquesta alçada hi ha 2 tests (`test_room_history_seeded_with_system_prompt`, `test_join_room_adds_yuki_without_limit`). Han de passar tots dos.

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/test_rooms_ai.py
git commit -m "feat(backend): Yuki com a membre reservat de sala amb historial per sala"
```

---

### Task 2: Backend — `send_to_room` crida la Yuki amb menció `@yuki`

**Files:**
- Modify: `backend/main.py`
- Test: `backend/test_rooms_ai.py`

**Interfaces:**
- Consumes: `YUKI_MEMBER`, `_ensure_room_history` (Task 1), `call_groq`, `logger` existents.
- Produces:
  - `send_to_room` amb lògica de Yuki.
  - `ConnectionManager._handle_room_ai(room_name: str, sender: str, message: str) -> None` (envia `ROOMAI:` a tots els membres quan hi ha menció).

- [ ] **Step 1: Afegir els tests que fallen** — afegir a `backend/test_rooms_ai.py`:

```python
def test_send_to_room_mention_calls_groq_and_broadcasts(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    Y = main.YUKI_MEMBER
    m.rooms = {"r1": ["anna", "bob", Y]}

    async def fake_call(messages):
        return "Hola a tothom!", {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        }

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to_room("anna", "r1", "ei @Yuki què tal?"))

    history = m.room_ai_histories["r1"]
    assert [x["role"] for x in history] == ["system", "user", "assistant"]
    assert history[1]["content"] == "anna: ei @Yuki què tal?"

    roomai = [(u, msg) for (u, msg) in sent if msg.startswith("ROOMAI:")]
    recipients = [u for (u, msg) in roomai]
    assert "anna" in recipients and "bob" in recipients  # inclòs el remitent
    payload = json.loads(roomai[0][1][len("ROOMAI:r1:"):])
    assert payload["text"] == "Hola a tothom!"
    assert payload["usage"]["total_tokens"] == 15


def test_send_to_room_no_mention_grows_history_without_groq(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    Y = main.YUKI_MEMBER
    m.rooms = {"r1": ["anna", Y]}
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


def test_send_to_room_without_yuki_unchanged(monkeypatch):
    m, sent = _mgr_with_capture(monkeypatch)
    m.rooms = {"r1": ["anna", "bob"]}
    called = []

    async def fake_call(messages):
        called.append(1)
        return "x", {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

    monkeypatch.setattr(main, "call_groq", fake_call)
    asyncio.run(m.send_to_room("anna", "r1", "@yuki ignored here"))

    assert called == []
    assert "r1" not in m.room_ai_histories
    assert any(msg.startswith("ROOM:r1:anna:") for (u, msg) in sent)
```

- [ ] **Step 2: Executar per veure'ls fallar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rooms_ai.py -v`
Expected: els 3 nous FALLEN (encara no hi ha la lògica de Yuki a `send_to_room`).

- [ ] **Step 3: Implementar la lògica a `send_to_room`** — a `backend/main.py`, substituir el mètode `send_to_room` sencer per:

```python
    async def send_to_room(self, sender: str, room_name: str, message: str):
        members = self.rooms.get(room_name, [])
        if sender not in members:
            return
        payload = f"ROOM:{room_name}:{sender}:{message}"
        for user in members:
            if user == sender:
                continue
            await self.send_text(user, payload)

        if YUKI_MEMBER in members:
            await self._handle_room_ai(room_name, sender, message)

    async def _handle_room_ai(self, room_name: str, sender: str, message: str):
        history = self._ensure_room_history(room_name)
        history.append({"role": "user", "content": f"{sender}: {message}"})
        if "@yuki" not in message.lower():
            return
        try:
            reply, usage = await call_groq(history)
        except Exception:
            logger.exception("Groq room call failed for %s", room_name)
            return
        history.append({"role": "assistant", "content": reply})
        payload = "ROOMAI:" + room_name + ":" + json.dumps(
            {"text": reply, "usage": usage}
        )
        for user in self.rooms.get(room_name, []):
            await self.send_text(user, payload)
```

- [ ] **Step 4: Executar per veure'ls passar**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest test_rooms_ai.py -v`
Expected: PASS (5 tests en total).

- [ ] **Step 5: Comprovar que la resta de tests segueixen verds**

Run (des de `backend/`): `./venv/Scripts/python.exe -m pytest -v`
Expected: PASS (test_ai.py 3 + test_rooms_ai.py 5 = 8).

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/test_rooms_ai.py
git commit -m "feat(backend): la Yuki respon a @yuki dins les rooms amb tokens"
```

---

### Task 3: Frontend — checkbox "Afegir la Yuki" i handler `ROOMAI:`

**Files:**
- Modify: `frontend/chat-app/src/app/chat/ai-protocol.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.html`
- Modify: `frontend/chat-app/src/app/chat/chat.scss`

**Interfaces:**
- Consumes: `parseAiPayload` (ja existent), `Room`/`Message` (ja existents).
- Produces: `YUKI_MEMBER` exportat de `ai-protocol.ts`; estat `addYuki`; `handleRoomAiMessage`.

- [ ] **Step 1: Exportar `YUKI_MEMBER`** — a `frontend/chat-app/src/app/chat/ai-protocol.ts`, sota `export const AI_ROOM = 'Chat amb IA';`:

```typescript
export const YUKI_MEMBER = 'Yuki';
```

- [ ] **Step 2: Importar `YUKI_MEMBER` al component** — a `chat.ts`, afegir-lo a la importació existent de `./ai-protocol`:

```typescript
import { AI_ROOM, AiUsage, parseAiPayload, YUKI_MEMBER } from './ai-protocol';
```

- [ ] **Step 3: Afegir l'estat `addYuki`** — a `chat.ts`, just sota `groupName = '';`:

```typescript
  addYuki = false;
```

- [ ] **Step 4: Resetejar `addYuki` en sortir del mode grup** — a `toggleGroupMode`, dins el bloc `if (!next) { ... }`, afegir:

```typescript
      this.addYuki = false;
```

- [ ] **Step 5: Incloure la Yuki al `JOIN:` i resetejar** — a `chat.ts`, substituir el cos de `createGroup` per:

```typescript
  createGroup() {
    const name = this.groupName.trim();
    const members = [...this.selectedForGroup()];
    if (!name || members.length === 0) return;

    if (this.socket?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not open; group not created');
      return;
    }

    if (this.addYuki) {
      members.push(YUKI_MEMBER);
    }

    this.socket.send(`JOIN:${name}:${members.join(',')}`);
    this.pendingRoom.set(name);

    this.groupName = '';
    this.selectedForGroup.set([]);
    this.addYuki = false;
    this.creatingGroup.set(false);
  }
```

- [ ] **Step 6: Afegir el routing de `ROOMAI:`** — a `chat.ts`, dins `this.socket.onmessage`, just després del bloc `if (data.startsWith('ROOM:')) { ... }`:

```typescript
      if (data.startsWith('ROOMAI:')) {
        this.handleRoomAiMessage(data.slice('ROOMAI:'.length));
        return;
      }
```

- [ ] **Step 7: Afegir `handleRoomAiMessage`** — a `chat.ts`, just després de `handleRoomMessage`:

```typescript
  // ROOMAI:roomname:{json}  — resposta de la Yuki repartida a una sala
  private handleRoomAiMessage(rest: string) {
    const idx = rest.indexOf(':');
    if (idx === -1) return;
    const roomName = rest.slice(0, idx);
    const json = rest.slice(idx + 1);

    const room = this.rooms().find(r => r.name === roomName);
    if (!room) return;

    let payload;
    try {
      payload = parseAiPayload(json);
    } catch {
      console.warn('Invalid ROOMAI payload', json);
      return;
    }

    room.messages.update(msgs => [...msgs, {
      text: payload.text,
      sender: YUKI_MEMBER,
      time: this.getTime(),
      isMe: false,
      usage: payload.usage ?? undefined
    }]);
    room.lastMessage.set(payload.text);
  }
```

- [ ] **Step 8: Afegir el checkbox a la plantilla** — a `chat.html`, dins el bloc `@if (creatingGroup()) { <div class="group-create"> ... }`, entre l'`<input>` del nom i el `<button>`:

```html
          <label class="yuki-check">
            <input type="checkbox" [(ngModel)]="addYuki" />
            Afegir la Yuki
          </label>
```

- [ ] **Step 9: Estil del checkbox** — al final de `frontend/chat-app/src/app/chat/chat.scss`:

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

- [ ] **Step 10: Verificar build i tests**

Run (des de `frontend/chat-app/`): `npm run build`
Expected: build OK, sense errors de TypeScript/plantilla (l'avís de budget CSS és acceptable).
Run (des de `frontend/chat-app/`): `npm run test:unit`
Expected: PASS (4 tests; `parseAiPayload` cobreix el format JSON que reaprofita `handleRoomAiMessage`).

- [ ] **Step 11: Commit**

```bash
git add frontend/chat-app/src/app/chat/ai-protocol.ts frontend/chat-app/src/app/chat/chat.ts frontend/chat-app/src/app/chat/chat.html frontend/chat-app/src/app/chat/chat.scss
git commit -m "feat(frontend): checkbox 'Afegir la Yuki' i handler ROOMAI a les sales"
```

---

## Verificació manual (extrem a extrem, després de les tasques)

Requereix `GROQ_API_KEY` al backend i el backend de Render redeployat des de `main` per a producció.

1. Backend local: `./venv/Scripts/python.exe -m uvicorn main:app --reload` (des de `backend/`).
2. Frontend: `npm start` (des de `frontend/chat-app/`); obrir a `http://localhost:4200` amb dos noms diferents (dues pestanyes).
3. Amb un usuari, "＋ grup", marcar **"Afegir la Yuki"**, triar l'altre usuari, crear.
4. Comprovar que "Yuki" surt a la llista de membres de la sala.
5. Escriure un missatge sense `@yuki` → els humans el reben, la Yuki no respon.
6. Escriure "@yuki hola" → la Yuki respon a tots els membres amb la línia de tokens i el tooltip kawaii.
