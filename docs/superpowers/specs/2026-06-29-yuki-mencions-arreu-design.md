# Disseny: la Yuki a totes les converses (@yuki) + zoom mòbil + igualtat de noms

**Data:** 2026-06-29
**Projecte:** Chat (Angular 21 + FastAPI + WebSocket, desplegat a Render)
**Relacionat:** [[2026-06-29-yuki-a-les-rooms-design]], [[2026-06-29-chat-amb-ia-groq-design]]

## Objectiu

Tres canvis:
1. La Yuki està **sempre disponible a totes les converses** (xats 1-a-1 amb persones
   i grups) i respon quan algú escriu **`@yuki`** (detecció estricta, com a les rooms).
   Es **treu el checkbox** "Afegir la Yuki" i el concepte de membre opcional. La
   conversa dedicada amb la Yuki es **manté** (respon a tot, sense `@yuki`) però es
   **reanomena "Yuki, la teva IA"**.
2. Arreglar el **zoom automàtic al mòbil** en enfocar un input (causat per `font-size`
   < 16px) a tots els inputs (xat, login, crear grup).
3. Assegurar que els **noms es comparen sempre amb igualtat exacta** (no substring), al
   backend i al frontend.

## Decisions preses

- **Disparador a 1-a-1 i grups:** `@yuki` estricte (`"@yuki" in message.lower()`).
- **Visibilitat a 1-a-1:** la resposta de la Yuki es veu a **tots dos** participants,
  dins el mateix fil 1-a-1, amb el camp `usage`/tokens. La Yuki recorda el context
  d'aquell fil (historial per parella).
- **Conversa dedicada:** es manté sempre activa; reanomenada **"Yuki, la teva IA"**;
  segueix responent a cada missatge sense `@yuki` (protocol `AI:`, historial per usuari).
- **Grups:** la Yuki és **ambient** a totes les sales (no és membre, no hi ha checkbox);
  respon a `@yuki` a qualsevol sala.
- **Etiqueta de remitent:** els missatges de la Yuki (1-a-1, grup i dedicat) es mostren
  amb el remitent **"Yuki"** (constant `YUKI_NAME`).

## Arquitectura

### Constants

- Frontend `ai-protocol.ts`:
  - `AI_ROOM = 'Yuki, la teva IA'` (nom/títol de la conversa dedicada).
  - `YUKI_NAME = 'Yuki'` (etiqueta de remitent de la Yuki a totes les converses).
  - S'**elimina** `YUKI_MEMBER`.
- Backend `main.py`: s'**elimina** `YUKI_MEMBER`. Es manté el literal de menció `"@yuki"`.

### Protocol

- **Client → servidor:** sense canvis.
- **Servidor → client (nou):** `DIRECTAI:<contacte>:` + JSON `{"text": ..., "usage": {...}}`
  — resposta de la Yuki dins un fil 1-a-1. `<contacte>` és l'**altra** persona des del
  punt de vista de cada receptor:
  - a qui ha escrit el missatge → `<contacte>` = el destinatari (l'altre humà);
  - a l'altre participant → `<contacte>` = qui ha escrit.
- `ROOMAI:<sala>:` + JSON — es manté igual; ara s'aplica a **qualsevol** sala.
- `AI:` (conversa dedicada) — es manté igual.
- En error de Groq: log; no s'envia `DIRECTAI:`/`ROOMAI:` i no s'afegeix resposta
  fallida a l'historial.

### Backend (`backend/main.py`)

- **Eliminar `YUKI_MEMBER`** i totes les seves referències.
- **`join_room`:** revertir la condició del límit a l'original (sense bypass de Yuki):
  `if self._room_count(user) >= MAX_ROOMS_PER_USER:`.
- **`send_to_room`:** eliminar la guarda `if YUKI_MEMBER in members`; cridar **sempre**
  `_handle_room_ai(room_name, sender, message)` després del repartiment normal. (La
  guarda `@yuki` interna ja decideix si es crida Groq.)
- **`_handle_room_ai`:** sense canvis interns (afegeix sempre el missatge a l'historial
  de la sala; si hi ha `@yuki`, crida Groq i fa broadcast `ROOMAI:` a tots els membres).
- **Historial 1-a-1:** `direct_ai_histories: dict[str, list[dict]]` a `ConnectionManager`.
  - `_pair_key(a, b) -> str`: `"|".join(sorted([a, b]))`.
  - `_ensure_direct_history(key)`: sembra amb `AI_SYSTEM_PROMPT` el primer cop (idempotent).
- **`send_to(sender, receiver, message)`:** després de lliurar `sender:message` al
  receptor (com ara), cridar `_handle_direct_ai(sender, receiver, message)`.
- **`_handle_direct_ai(sender, receiver, message)`:**
  1. `key = _pair_key(sender, receiver)`; `history = _ensure_direct_history(key)`.
  2. Afegir `{"role":"user","content": f"{sender}: {message}"}` (sempre).
  3. Si `"@yuki" not in message.lower()`: return.
  4. `reply, usage = await call_groq(history)` (try/except amb log; en error, return).
  5. Afegir `{"role":"assistant","content": reply}`.
  6. Enviar a `sender`: `DIRECTAI:{receiver}:` + json `{text, usage}`.
     Enviar a `receiver`: `DIRECTAI:{sender}:` + json `{text, usage}`.
- **Igualtat exacta:** el lliurament directe (`send_text` via `connections.get(name)`) i
  les comparacions de noms ja són exactes; s'afegeix un test de regressió.

### Frontend (`chat.ts` / `chat.html` / `chat.scss` / `ai-protocol.ts` / login)

- **Rename + remitent:** `AI_ROOM = 'Yuki, la teva IA'`; afegir `YUKI_NAME = 'Yuki'`;
  `handleAiMessage` posa `sender: YUKI_NAME` (en lloc de `AI_ROOM`).
- **Treure el checkbox:** eliminar a `chat.html` el `<label class="yuki-check">…`;
  eliminar el camp `addYuki` i el seu reset (`toggleGroupMode`, `createGroup`); eliminar
  l'afegit de Yuki als membres a `createGroup`; eliminar l'estil `.yuki-check`; eliminar
  l'import/ús de `YUKI_MEMBER`.
- **Handler `DIRECTAI:` (nou)** a `onmessage` (abans del fallback de missatge directe):
  `DIRECTAI:<contacte>:<json>` → separar pel **primer** `:`; trobar o **crear** el
  contacte `<contacte>` (com fa el handler de missatge directe); afegir un `Message`
  `{ sender: YUKI_NAME, text, usage, isMe: false }`; actualitzar `lastMessage`.
- **Handler `ROOMAI:`:** posar `sender: YUKI_NAME` (coherència).
- La línia de tokens + tooltip kawaii ja s'apliquen a qualsevol `Message` amb `usage`.

### Zoom mòbil (font-size)

- A `chat.scss`, dins el `@media (max-width: 768px)` existent: `.chat-input { font-size: 16px; }`
  (cobreix l'input del xat i el de crear grup, tots dos `.chat-input`).
- A `login.scss`, afegir `@media (max-width: 768px) { .login-input { font-size: 16px; } }`.
- Es posa a cada full d'estils del component (no global) perquè l'encapsulació d'Angular
  afegeix especificitat; un override global perdria contra el `font-size: 12px` base.
- Desktop (>768px) no canvia.

## Convencions (CLAUDE.md)

- Angular 21: `@if`/`@for`, class bindings (no `ngClass`/`ngStyle`), signals `.set`/`.update`
  (no `.mutate`), sense `standalone: true`.
- Accessibilitat mantinguda (la línia de tokens conserva `appTooltip`/`aria-label`).

## Gestió d'errors / edge cases

- La Yuki no té connexió pròpia, així que mai dispara missatges → cap bucle.
- `DIRECTAI:`/`ROOMAI:` per a una conversa desconeguda al frontend: per a 1-a-1 es crea
  el contacte; per a sala desconeguda s'ignora (com ara).
- Si un nom contingués `:` el protocol es trencaria (limitació pre-existent compartida
  amb `ROOM:`/`ROOMAI:`); fora d'abast.

## Testing

- **Backend (pytest):**
  - `send_to_room` amb `@yuki` en una sala **sense cap "Yuki" membre** → crida Groq
    (mock) + broadcast `ROOMAI:` + historial de sala creix.
  - `send_to_room` sense `@yuki` → historial creix, sense Groq.
  - `send_to` (1-a-1) amb `@yuki` → crida Groq + envia `DIRECTAI:` a **tots dos** amb el
    `<contacte>` correcte per a cadascun + historial de parella (user+assistant).
  - `send_to` (1-a-1) sense `@yuki` → historial de parella creix, sense Groq, sense `DIRECTAI:`.
  - **Regressió noms:** amb connexions "carme" i "carme-mobil", `send_to("carme",
    "carme-mobil", "hola")` fa `send_text` **només** a "carme-mobil" (mai a "carme" per
    prefix); i `_pair_key` és simètric (`_pair_key(a,b) == _pair_key(b,a)`).
- **Actualitzar tests existents:** els tests de `backend/test_rooms_ai.py` que depenen de
  `YUKI_MEMBER` i de la pertinença a la sala (p. ex. el bypass del límit, o el `ROOMAI`
  només quan "Yuki" és membre) s'han de **reescriure** per al nou comportament ambient
  (la Yuki respon a `@yuki` a qualsevol sala, sense membre reservat).
- **Frontend (vitest):** reaprofita el test de `parseAiPayload` (mateix format JSON).
- **Manual + build:** `npm run build` verd; prova al navegador (1-a-1 amb `@yuki` visible
  als dos; grup amb `@yuki`; conversa dedicada "Yuki, la teva IA"; inputs sense zoom al mòbil).

## Fora d'abast (YAGNI)

- Cap d'historial / rate-limiting (es manté en memòria, com la resta).
- Avatar per missatge dins rooms/1-a-1 (la Yuki s'identifica pel remitent "Yuki" + tokens).
- Mostrar la Yuki com a "membre" o "en línia" a la llista d'usuaris.

## Nota de desplegament

Cal **redeployar el backend a Render des de `main`** (actualment build vella) amb
`GROQ_API_KEY` perquè la Yuki (dedicada, 1-a-1 i grups) operi en producció.
