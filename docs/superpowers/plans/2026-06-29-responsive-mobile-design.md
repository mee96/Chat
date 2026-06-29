# Responsive mòbil (Messenger/WhatsApp) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Al mòbil (≤768px) mostrar una sola vista alhora (llista ↔ conversa) amb un botó "←" per tornar i l'input fix a baix; al desktop (>768px) mantenir el layout de dues columnes idèntic.

**Architecture:** CSS-driven. S'afegeix `[class.show-chat]="!!active()"` a `.app` i tota la lògica mòbil viu dins un `@media (max-width: 768px)` que alterna la visibilitat de `.sidebar`/`.chat-area`. Un botó "←" a la capçalera (només visible al mòbil) crida `closeConversation()`, que deselecciona la conversa i torna a la llista. El desktop no es toca.

**Tech Stack:** Angular 21 (signals, control flow), SCSS.

## Global Constraints

- Breakpoint: `768px` (`@media (max-width: 768px)` = mòbil).
- El comportament del desktop (>768px, grid `175px 1fr`, dues columnes) **no es modifica**.
- Classe d'estat `show-chat` a `.app`, lligada a `!!active()`.
- Botó "←" només visible al mòbil; `aria-label="Enrere"` (accessibilitat WCAG).
- Input fix a baix via chat-area flex a `100dvh` (`messages` flex:1 scroll, `input-row` flex-shrink:0).
- Angular 21: `@if`/`@for`, class bindings (no `ngClass`/`ngStyle`), signals amb `.set` (no `.mutate`), sense `standalone: true`.
- Frontend: comandes des de `frontend/chat-app/`; build `npm run build`; tests `npm run test:unit`.

---

### Task 1: Responsive mòbil — classe d'estat, botó enrere i media query

**Files:**
- Modify: `frontend/chat-app/src/app/chat/chat.ts`
- Modify: `frontend/chat-app/src/app/chat/chat.html`
- Modify: `frontend/chat-app/src/app/chat/chat.scss`

**Interfaces:**
- Consumes: `active()` (computed existent, retorna la conversa activa o `null`), i els signals `activeContact`, `activeRoom`, `activeAi` existents.
- Produces: mètode `closeConversation()` a `ChatComponent`.

> Aquesta tasca no té tests unitaris (és CSS responsive + un mètode trivial de
> deselecció). La verificació és `npm run build` + prova manual al navegador.

- [ ] **Step 1: Afegir el mètode `closeConversation()`** — a `frontend/chat-app/src/app/chat/chat.ts`, just després del mètode `selectRoom(...)`:

```typescript
  closeConversation() {
    this.activeContact.set(null);
    this.activeRoom.set(null);
    this.activeAi.set(false);
  }
```

- [ ] **Step 2: Afegir la classe d'estat `show-chat`** — a `frontend/chat-app/src/app/chat/chat.html`, a l'element arrel `.app`:

Reemplaça:

```html
<div class="app">
```

per:

```html
<div class="app" [class.show-chat]="!!active()">
```

- [ ] **Step 3: Afegir el botó "←" a la capçalera** — a `chat.html`, dins `.chat-header`, com a primer fill de `.chat-with` (abans de l'avatar):

Reemplaça:

```html
      <div class="chat-header">
        <div class="chat-with">
          <div class="avatar small" [class.online]="a.online" [class.room]="a.isRoom" [class.ai]="a.isAi">
```

per:

```html
      <div class="chat-header">
        <div class="chat-with">
          <button class="back-btn" type="button" aria-label="Enrere" (click)="closeConversation()">←</button>
          <div class="avatar small" [class.online]="a.online" [class.room]="a.isRoom" [class.ai]="a.isAi">
```

- [ ] **Step 4: Estil base del botó "←" (amagat al desktop)** — a `frontend/chat-app/src/app/chat/chat.scss`, afegir (p. ex. just abans del bloc final de `.yuki-check`, o al final de fitxer però abans del `@media` del Step 5):

```scss
.back-btn {
  display: none;
  background: none;
  border: none;
  color: #0c447c;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
}
```

- [ ] **Step 5: Afegir el bloc `@media` mòbil** — al **final** de `frontend/chat-app/src/app/chat/chat.scss`:

```scss
@media (max-width: 768px) {
  .app {
    grid-template-columns: 1fr;
    height: 100dvh;
    padding: 0;
    gap: 0;
    border-radius: 0;
  }

  .sidebar {
    height: 100dvh;
  }

  .chat-area {
    display: none;
    height: 100dvh;
  }

  .app.show-chat .sidebar {
    display: none;
  }

  .app.show-chat .chat-area {
    display: flex;
  }

  .back-btn {
    display: inline-flex;
    align-items: center;
  }
}
```

- [ ] **Step 6: Verificar el build**

Run (des de `frontend/chat-app/`): `npm run build`
Expected: build OK, sense errors de TypeScript/plantilla (l'avís de budget CSS és acceptable).

- [ ] **Step 7: Verificar que els tests existents segueixen verds**

Run (des de `frontend/chat-app/`): `npm run test:unit`
Expected: PASS (4 tests).

- [ ] **Step 8: Verificació manual (responsive)**

Obrir l'app i, amb el mode dispositiu de DevTools (o amplada de finestra `<768px`):
1. **Vista 1:** es veu la llista (chats/rooms/usuaris) a pantalla completa; el panell de conversa no apareix.
2. Tocar una conversa → **Vista 2:** la conversa ocupa tota la pantalla, amb el botó "←" a la capçalera i l'input fix a baix (sempre visible).
3. Tocar "←" → torna a la **Vista 1**; els missatges de la conversa es conserven en reobrir-la.
4. Eixamplar a `>768px` → es veuen les **dues columnes** alhora, sense botó "←" (layout desktop intacte).

- [ ] **Step 9: Commit**

```bash
git add frontend/chat-app/src/app/chat/chat.ts frontend/chat-app/src/app/chat/chat.html frontend/chat-app/src/app/chat/chat.scss
git commit -m "feat(frontend): disseny responsive mòbil (una vista, botó enrere, input fix)"
```

---

## Notes

- Tot el comportament mòbil està confinat al `@media (max-width: 768px)`; per sobre del
  breakpoint res canvia, així que el desktop queda exactament com abans.
- `closeConversation()` només deselecciona (posa els `active*` a buit); no esborra cap
  missatge — els missatges viuen als signals de cada conversa i es recuperen en reobrir-la.
