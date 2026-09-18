// Braille map loader + dot<->mask helpers. Ported from web/braille_cell.js
// and the LETTERS derivation in web/teacher.js -- unified here so both pages
// read the exact same source (lib/brailleMap.json, a build-time copy of
// data/braille_map.json) instead of teacher.js's separate hand-written copy.

import rawMap from './brailleMap.json';

export const DOTS = [1, 2, 3, 4, 5, 6];

/** [1,3] -> 0b000101. Matches BRAILLE_PATTERN in firmware/braille_map.h. */
export function dotsToMask(dots) {
  return dots.reduce((m, d) => m | (1 << (d - 1)), 0);
}

export function maskToDots(mask) {
  return DOTS.filter((d) => mask & (1 << (d - 1)));
}

// ং ঃ ঁ are combining marks; shown alone they render over a dotted circle
// unless a base is attached. See web/app.js's displayChar for the same fix.
const COMBINING = new Set(['ঁ', 'ং', 'ঃ']);
export function displayChar(ch) {
  return COMBINING.has(ch) ? '◌' + ch : ch;
}

/** All 50 letters, each with a precomputed `mask` (and `prefixMask` for the
 *  two two-cell characters ঋ/ৎ), in braille_map.json's id order. */
export const LETTERS = rawMap.letters.map((l) => ({
  ...l,
  mask: dotsToMask(l.dots),
  prefixMask: l.cells ? dotsToMask(l.cells[0]) : 0,
}));

export function letterById(id) {
  return LETTERS[id];
}

export const BRAILLE_MAP_VERIFIED = Boolean(rawMap.verified);
