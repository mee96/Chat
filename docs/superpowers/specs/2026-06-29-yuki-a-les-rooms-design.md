# Disseny: la Yuki dins les rooms de grup

**Data:** 2026-06-29
**Projecte:** Chat (Angular 21 + FastAPI + WebSocket, desplegat a Render)
**Relacionat:** [[2026-06-29-chat-amb-ia-groq-design]] (xat 1-a-1 amb la Yuki)

## Objectiu

Permetre afegir la Yuki (l'assistent IA de Groq) com a membre d'una sala de grup.
Quan algú la **menciona** amb `@yuki` dins la sala, el backend crida Groq amb
l'historial de la **conversa de grup** (no l'individual) i reparteix la resposta a
tots els membres com un missatge de sala amb el camp `usage`/tokens inclòs. Tots els
missatges del grup entren a l'historial de context de la Yuki, encara que no la
mencionin. La Yuki **no compta** per al límit de 3 rooms per usuari. Es manté el
mateix system prompt dolç/kawaii.

## Decisions preses

- **Disparador:** la Yuki només respon quan el missatge **menciona `@yuki`**
  (detecció estricta: el missatge conté la subcadena `@yuki`, insensible a
  majúscules). La resta de missatges no la disparen però **sí** entren al seu
  historial de context de la sala.
- **Representació (Opció A):** la Yuki és un **membre reservat** anomenat `"Yuki"`
  dins la llista de membres de la sala. El frontend afegeix `"Yuki"` als membres del
  `JOIN:` existent quan el checkbox està marcat; el protocol `JOIN:` no canvia.
- **Historial:** per sala (separat de l'individual), sembrat amb el mateix
  `AI_SYSTEM_PROMPT` kawaii. Cada missatge del grup s'hi afegeix com
  `{"role":"user","content":"<remitent>: <missatge>"}` perquè la Yuki sàpiga qui
  parla. La seva resposta s'afegeix com `{"role":"assistant","content":<resposta>}`.
- **Tokens:** la resposta de la Yuki a la sala inclou `usage` i es mostra com a les
  altres respostes (línia de tokens + tooltip kawaii), reaprofitant la UI existent.

## Arquitectura

### Protocol

- **Client → servidor:** sense canvis. El frontend afegeix `"Yuki"` a la llista de
  membres del `JOIN:<sala>:<membres>` quan el checkbox "Afegir la Yuki" està marcat.
  L'enviament de missatges de sala (`ROOM:<sala>:<missatge>`) no canvia.
- **Servidor → client (nou):** `ROOMAI:<sala>:` + JSON
  `{"text": <resposta>, "usage": {"prompt_tokens","completion_tokens","total_tokens"}}`.
  Es reparteix a **tots** els membres de la sala (inclòs qui ha mencionat la Yuki, ja
  que la Yuki no té client propi que pinti la resposta localment).
- **Error de Groq:** mateixa gestió que al xat 1-a-1 (log de l'excepció); en cas
  d'error no s'envia cap `ROOMAI:` i no s'afegeix cap resposta fallida a l'historial.

### Backend (`backend/main.py`)

- Constant `YUKI_MEMBER = "Yuki"`.
- `room_ai_histories: dict[str, list[dict]]` a `ConnectionManager`, amb un helper
  `_ensure_room_history(room_name)` que el sembra amb `AI_SYSTEM_PROMPT` el primer cop.
- `join_room`: en construir la llista de membres, el nom `YUKI_MEMBER` s'afegeix
  **sense** comprovar ni comptar el límit `MAX_ROOMS_PER_USER` (el límit només
  s'aplica a usuaris reals). La resta de la lògica de límit no canvia.
- `send_to_room(sender, room_name, message)`: després del repartiment normal als
  membres humans, si `YUKI_MEMBER in members`:
  1. Afegeix `{"role":"user","content": f"{sender}: {message}"}` a l'historial de la
     sala (sempre, encara que no hi hagi menció).
  2. Si el missatge menciona la Yuki (`"@yuki" in message.lower()`): crida
     `call_groq(historial_sala)`, afegeix la resposta com a `assistant`, i fa
     broadcast `ROOMAI:<sala>:` + JSON `{text, usage}` a **tots** els membres.
- Reaprofita `call_groq` i `AI_SYSTEM_PROMPT` existents. Cap canvi al xat 1-a-1.

### Frontend (`chat.ts` / `chat.html` / `chat.scss`)

- **UI de "＋ grup":** checkbox **"Afegir la Yuki"** al costat del camp del nom del
  grup, lligat a un signal `addYuki`. Es reseteja en cancel·lar/crear (com `groupName`).
- `createGroup`: si `addYuki()`, afegeix el nom de la Yuki a la llista de membres
  abans d'enviar el `JOIN:`, i reseteja `addYuki` després. S'afegeix una constant de
  frontend `YUKI_MEMBER = 'Yuki'` a `ai-protocol.ts` (mateix valor literal que la del
  backend) i s'hi referencia tant aquí com al handler `ROOMAI:`.
- **Handler `ROOMAI:`** a `onmessage`: parseja `<sala>` i el JSON (reaprofitant
  `parseAiPayload`), troba la sala i hi afegeix un `Message`
  `{ sender: 'Yuki', text, usage, isMe: false }`; actualitza `lastMessage`. Si la sala
  encara no existeix localment, s'ignora (com fa `handleRoomMessage`).
- La línia de tokens i el tooltip kawaii del loop de missatges ja s'apliquen a
  qualsevol `Message` amb `usage`, així que la resposta de la Yuki a la sala mostrarà
  els tokens automàticament.

## Gestió d'errors

- Groq falla → es registra l'excepció; no s'envia `ROOMAI:` i no es contamina
  l'historial amb una resposta fallida.
- `ROOMAI:` per a una sala desconeguda al frontend → s'ignora sense trencar res.

## Casos límit

- La Yuki no envia mai missatges `ROOM:` (no té connexió), així que no hi ha bucle de
  auto-resposta.
- `"Yuki"` és un nom **reservat**: si un usuari real es digués Yuki hi hauria
  col·lisió (s'accepta com a limitació coneguda).
- Un usuari que ja té 3 rooms pot crear-ne una amb la Yuki: la Yuki no consumeix slot.

## Testing

- **Backend (pytest):**
  - Crear sala amb la Yuki quan el creador ja té 3 rooms → la Yuki s'afegeix igualment
    i no es rebutja per límit.
  - `send_to_room` amb la Yuki membre i missatge amb `@yuki` → crida `call_groq`
    (mock), fa broadcast `ROOMAI:` amb `usage` a tots els membres, i l'historial de la
    sala creix (user + assistant).
  - `send_to_room` amb la Yuki membre i missatge **sense** `@yuki` → **no** crida Groq
    però l'historial de la sala creix amb el missatge de l'usuari.
  - `send_to_room` en una sala **sense** Yuki → comportament intacte, sense historial.
- **Frontend (vitest):** reaprofita el test de `parseAiPayload` (mateix format JSON).

## Fora d'abast (YAGNI)

- Afegir/treure la Yuki d'una sala ja existent (només en el moment de crear-la).
- Avatar per missatge dins les rooms (les sales no mostren avatars per missatge; la
  Yuki s'identifica pel nom del remitent "Yuki" i la línia de tokens).
- Streaming i persistència de l'historial (en memòria del procés, com la resta).

## Nota de desplegament

El backend de Render ha d'estar **redeployat des de `main`** amb el codi de la Yuki
(actualment està en una build vella que no respon a `AI:`/`ROOMAI:`), i amb
`GROQ_API_KEY` configurada, perquè aquesta funcionalitat operi en producció.
