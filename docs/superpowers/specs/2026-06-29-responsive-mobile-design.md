# Disseny: responsive mòbil (patró Messenger/WhatsApp)

**Data:** 2026-06-29
**Projecte:** Chat (Angular 21 + FastAPI + WebSocket, desplegat a Render)

## Objectiu

Millorar el disseny responsive en pantalles petites. Actualment, per sota d'amplades
mòbil, la sidebar i el xat competeixen per l'espai, el botó d'enviar no es veu bé i la
zona d'escriure es desborda. Es vol el patró estàndard de Messenger/WhatsApp: una sola
vista alhora al mòbil, amb navegació entre la llista i la conversa; el comportament de
dues columnes del desktop es manté **idèntic**.

## Decisions preses

- **Breakpoint:** `768px`. `≤768px` = mòbil (una vista); `>768px` = desktop (dues columnes, com ara).
- **Enfocament:** CSS-driven amb una classe d'estat `show-chat` a `.app`, lligada a si
  hi ha conversa activa (`active()`). Tota la lògica mòbil viu dins un
  `@media (max-width: 768px)`; el desktop **no es modifica**.
- **Navegació enrere:** un botó "←" a la capçalera (només visible al mòbil) que
  deselecciona la conversa activa i torna a la llista.
- **Input fix a baix:** el chat-area ocupa tota l'alçada (`100dvh`) com a columna flex;
  `messages` amb `flex: 1` (scroll) i `input-row` amb `flex-shrink: 0`, de manera que
  l'input queda sempre visible a baix.

## Arquitectura

Estructura actual rellevant:
- `.app` és un grid `grid-template-columns: 175px 1fr; height: 100vh` amb `.sidebar`
  (esquerra) i `.chat-area` (dreta).
- `.chat-area` mostra `@if (active(); as a)` la conversa, si no l'`empty-state`.
- `active()` és un `computed` que retorna l'objecte de la conversa activa o `null`.
- La selecció de conversa es fa amb `selectContact`/`selectRoom`/`selectAi`, que ja
  posen els altres `active*` a `null`/`false`.

### Comportament responsive

- **>768px (desktop):** exactament com ara — grid `175px 1fr`, sidebar i chat-area
  totes dues visibles, botó "←" amagat. Cap canvi de comportament.
- **≤768px (mòbil):** una sola vista alhora.
  - **Sense** conversa activa (`active()` és `null`) → **Vista 1 (llista)**: la sidebar
    a pantalla completa (chats + rooms + usuaris + UI de "＋ grup"); el chat-area amagat.
  - **Amb** conversa activa → **Vista 2 (conversa)**: el chat-area a pantalla completa;
    la sidebar amagada. A la capçalera apareix el botó "←" que torna a la Vista 1.
  - En seleccionar un contacte/room/usuari/Yuki, `active()` passa a no-`null` i la vista
    canvia automàticament a la Vista 2 (via la classe `show-chat`).
  - L'`empty-state` (placeholder del panell dret) **no apareix mai** al mòbil: sense
    conversa es mostra la llista, no el panell buit.

### Mecanisme

- `.app` rep `[class.show-chat]="!!active()"`. Dins el `@media (max-width: 768px)`:
  - `.app` passa a una sola columna a tota l'alçada (`100dvh`), amb `padding`, `gap` i
    `border-radius` reduïts per aprofitar la pantalla.
  - Per defecte: `.sidebar` visible, `.chat-area` amagat (`display: none`).
  - Amb `.app.show-chat`: `.sidebar` amagada, `.chat-area` visible (flex), a tota
    l'amplada i alçada.
- Botó "←" (`.back-btn`) dins `.chat-header`: `display: none` per defecte (desktop),
  visible dins el `@media`. En clicar crida `closeConversation()`.
- `closeConversation()` posa `activeContact` i `activeRoom` a `null` i `activeAi` a
  `false` → `active()` retorna `null` → es treu `show-chat` → es mostra la Vista 1.

## Components / fitxers

- `frontend/chat-app/src/app/chat/chat.html`:
  - Afegir `[class.show-chat]="!!active()"` a l'element `.app`.
  - Afegir el botó "←" (`class="back-btn"`, `(click)="closeConversation()"`) a dins de
    `.chat-header` (abans de l'avatar/títol).
- `frontend/chat-app/src/app/chat/chat.ts`:
  - Afegir el mètode `closeConversation()` (posa `activeContact.set(null)`,
    `activeRoom.set(null)`, `activeAi.set(false)`).
- `frontend/chat-app/src/app/chat/chat.scss`:
  - Estil base de `.back-btn` amb `display: none` (amagat al desktop).
  - Bloc `@media (max-width: 768px)` amb: layout d'una columna a `100dvh`, toggle de
    visibilitat `.sidebar`/`.chat-area` segons `.show-chat`, i `.back-btn { display: inline-flex }`.

## Convencions (CLAUDE.md)

- Angular 21: `@if`/`@for`, class bindings (no `ngClass`/`ngStyle`), signals amb
  `.set`/`.update`, sense `standalone: true`.
- Accessibilitat: el botó "←" ha de tenir un nom accessible (`aria-label="Enrere"`).

## Gestió d'errors / edge cases

- Si l'usuari és a la Vista 2 i crea un grup o inicia un xat, la nova conversa s'obre
  (s'activa `active()`), mantenint-se a la Vista 2 amb la conversa nova — coherent.
- El botó "←" no esborra missatges: només deselecciona; els missatges segueixen als
  signals de cada conversa i es recuperen en tornar-hi.

## Testing

- El CSS responsive no és testejable per unitats de forma significativa.
- Verificació: `npm run build` ha de passar (l'avís de budget CSS és acceptable) i prova
  manual al navegador a amplada `<768px` (mode dispositiu de DevTools): Vista 1 → tocar
  una conversa → Vista 2 amb input fix a baix → "←" → Vista 1; i a `>768px` el layout de
  dues columnes intacte.
- Els tests existents (backend 8 pytest, frontend 4 vitest) han de seguir verds.

## Fora d'abast (YAGNI)

- Gestos de swipe per tornar enrere.
- Indicadors de "no llegits" a la llista quan arriba un missatge a una altra conversa.
- Animacions/transicions entre vistes.
