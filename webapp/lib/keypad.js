// Braille cell rendering + the 6-key input surface.
//
// Ported verbatim (DOM-manipulation logic unchanged) from web/braille_cell.js.
// Deliberately NOT rewritten as "idiomatic React state" -- response_time and
// press_duration are timing-critical (performance.now()-based) and must match
// the ESP32 firmware's measurement exactly. Reusing the exact tested class,
// instantiated against a ref'd container in a useEffect, carries far less
// risk than re-deriving the same timing contract through render-driven state.

import { DOTS } from './brailleMap';

export class BrailleCell {
  constructor(root) {
    this.root = root;
    this.els = new Map();
    for (const el of root.querySelectorAll('.dot')) {
      this.els.set(Number(el.dataset.dot), el);
    }
  }

  clear() {
    for (const el of this.els.values()) {
      el.classList.remove('on', 'correct', 'wrong', 'pulse', 'hint');
    }
  }

  showHint(dots) {
    for (const d of DOTS) {
      const el = this.els.get(d);
      if (!el) continue;
      if (dots.includes(d)) el.classList.add('hint');
      else el.classList.remove('hint');
    }
  }

  clearHint() {
    for (const el of this.els.values()) el.classList.remove('hint');
  }

  setMask(mask, { pulse = false } = {}) {
    for (const d of DOTS) {
      const el = this.els.get(d);
      if (!el) continue;
      const on = Boolean(mask & (1 << (d - 1)));
      el.classList.toggle('on', on);
      if (on && pulse) {
        el.classList.remove('pulse');
        void el.offsetWidth;
        el.classList.add('pulse');
      }
    }
  }

  showComparison(expectedMask, enteredMask) {
    for (const d of DOTS) {
      const el = this.els.get(d);
      if (!el) continue;
      const exp = Boolean(expectedMask & (1 << (d - 1)));
      const got = Boolean(enteredMask & (1 << (d - 1)));
      el.classList.remove('on', 'correct', 'wrong');
      if (exp && got) el.classList.add('correct');
      else if (exp && !got) el.classList.add('wrong');
      else if (!exp && got) el.classList.add('wrong');
    }
  }
}

/**
 * 6-key input with per-dot press/release timing.
 * Uses performance.now() (monotonic) so response_time/press_duration can't
 * jump if the system clock is adjusted mid-session.
 */
export class KeyPad {
  constructor(container, { onChange } = {}) {
    this.container = container;
    this.onChange = onChange || (() => {});
    this.reset();

    this.keyEls = new Map();
    for (const el of container.querySelectorAll('.key')) {
      const dot = Number(el.dataset.dot);
      this.keyEls.set(dot, el);
      el.addEventListener('mousedown', (e) => { e.preventDefault(); this.press(dot); });
      el.addEventListener('mouseup', () => this.release(dot));
      el.addEventListener('mouseleave', () => { if (this.held.has(dot)) this.release(dot); });
      el.addEventListener('touchstart', (e) => { e.preventDefault(); this.press(dot); }, { passive: false });
      el.addEventListener('touchend', (e) => { e.preventDefault(); this.release(dot); }, { passive: false });
    }

    // Perkins brailler layout: S D F = dots 3 2 1, J K L = dots 4 5 6
    // Numpad 3x2 grid: 7 4 1 = dots 1 2 3 (Left), 8 5 2 = dots 4 5 6 (Right)
    this.keymap = {
      f: 1, d: 2, s: 3, j: 4, k: 5, l: 6,
      '7': 1, '4': 2, '1': 3,
      '8': 4, '5': 5, '2': 6,
      numpad7: 1, numpad4: 2, numpad1: 3,
      numpad8: 4, numpad5: 5, numpad2: 6,
    };
    this._down = (e) => {
      const k = e.key.toLowerCase();
      const c = e.code.toLowerCase();
      const dot = this.keymap[k] || this.keymap[c];
      if (dot && !e.repeat) { e.preventDefault(); this.press(dot); }
    };
    this._up = (e) => {
      const k = e.key.toLowerCase();
      const c = e.code.toLowerCase();
      const dot = this.keymap[k] || this.keymap[c];
      if (dot) { e.preventDefault(); this.release(dot); }
    };
    this.enabled = false;
  }

  enable() {
    if (this.enabled) return;
    addEventListener('keydown', this._down);
    addEventListener('keyup', this._up);
    this.enabled = true;
  }

  disable() {
    removeEventListener('keydown', this._down);
    removeEventListener('keyup', this._up);
    this.enabled = false;
  }

  destroy() { this.disable(); }

  reset() {
    this.mask = 0;
    this.held = new Map();
    this.events = [];
    this.pressOrder = [];
    this.firstPressMs = null;
    if (this.keyEls) for (const el of this.keyEls.values()) el.classList.remove('active');
  }

  showHint(dots) {
    if (!this.keyEls) return;
    for (const [d, el] of this.keyEls.entries()) el.classList.toggle('hint', dots.includes(d));
  }

  clearHint() {
    if (!this.keyEls) return;
    for (const el of this.keyEls.values()) el.classList.remove('hint');
  }

  press(dot) {
    if (this.held.has(dot)) return;
    const now = performance.now();
    if (this.firstPressMs === null) this.firstPressMs = now;
    this.held.set(dot, now);
    this.keyEls.get(dot)?.classList.add('active');
    if (!this.pressOrder.includes(dot)) this.pressOrder.push(dot);
    this.mask |= (1 << (dot - 1));
    this.onChange(this.mask, dot, true);
  }

  release(dot) {
    const downMs = this.held.get(dot);
    if (downMs === undefined) return;
    this.held.delete(dot);
    this.keyEls.get(dot)?.classList.remove('active');
    this.events.push({ dot, downMs, upMs: performance.now() });
    this.onChange(this.mask, dot, false);
  }

  /** Mean press->release duration across the keys used this attempt, in ms. */
  meanPressDuration(now = performance.now()) {
    const durations = this.events.map((e) => e.upMs - e.downMs);
    for (const downMs of this.held.values()) durations.push(now - downMs);
    if (durations.length === 0) return 0;
    return durations.reduce((a, b) => a + b, 0) / durations.length;
  }
}
