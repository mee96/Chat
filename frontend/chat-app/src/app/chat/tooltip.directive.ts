import { Directive, ElementRef, inject, input } from '@angular/core';

// A single tooltip element shared by every instance, appended to <body> so it
// is never clipped by scroll containers. Styled globally via `.kawaii-tooltip`.
let sharedTip: HTMLDivElement | null = null;

function getSharedTip(): HTMLDivElement {
  if (!sharedTip) {
    sharedTip = document.createElement('div');
    sharedTip.className = 'kawaii-tooltip';
    document.body.appendChild(sharedTip);
  }
  return sharedTip;
}

const CURSOR_OFFSET_X = 12;
const CURSOR_OFFSET_Y = 16;
const VIEWPORT_PAD = 8;

@Directive({
  selector: '[appTooltip]',
  host: {
    '(mouseenter)': 'showAtElement()',
    '(mousemove)': 'follow($event)',
    '(mouseleave)': 'hide()',
    '(focusin)': 'showAtElement()',
    '(focusout)': 'hide()',
  },
})
export class TooltipDirective {
  readonly text = input.required<string>({ alias: 'appTooltip' });

  private readonly hostEl = inject(ElementRef<HTMLElement>);

  private show(): HTMLDivElement {
    const tip = getSharedTip();
    tip.textContent = this.text();
    tip.style.opacity = '1';
    return tip;
  }

  // Follow the cursor, clamped to the viewport (native-title-like behaviour).
  follow(event: MouseEvent) {
    this.position(event.clientX + CURSOR_OFFSET_X, event.clientY + CURSOR_OFFSET_Y);
  }

  // Used on keyboard focus (and as the initial mouseenter anchor): place the
  // tooltip just to the right of the element.
  showAtElement() {
    const rect = this.hostEl.nativeElement.getBoundingClientRect();
    this.position(rect.right + VIEWPORT_PAD, rect.top);
  }

  private position(x: number, y: number) {
    const tip = this.show();
    const { width, height } = tip.getBoundingClientRect();

    let left = x;
    let top = y;

    if (left + width + VIEWPORT_PAD > window.innerWidth) {
      left = window.innerWidth - width - VIEWPORT_PAD;
    }
    if (left < VIEWPORT_PAD) {
      left = VIEWPORT_PAD;
    }
    if (top + height + VIEWPORT_PAD > window.innerHeight) {
      top = y - height - CURSOR_OFFSET_Y - 4; // flip above the cursor
    }
    if (top < VIEWPORT_PAD) {
      top = VIEWPORT_PAD;
    }

    tip.style.left = `${left}px`;
    tip.style.top = `${top}px`;
  }

  hide() {
    if (sharedTip) {
      sharedTip.style.opacity = '0';
    }
  }
}
