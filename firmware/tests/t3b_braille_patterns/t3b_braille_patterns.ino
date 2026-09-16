// Bring-up 3b: play a real Braille cell on the six motors.
//
// t3 proves the six motors turn on. This proves the pattern a learner FEELS is
// the pattern in data/braille_map.json -- which is the thing that actually has
// to be right before any of the tutoring logic matters.
//
// Open the Serial Monitor at 115200, set the line ending to Newline, and type:
//
//     14            letter 14 by number (1..50)
//     gha           the same letter by name
//     l             list all 50
//     r             replay the last one
//     m             cycle sequential / together / both
//     + -           step the playback speed
//     t             raw motor sweep 1..6, no map involved
//     ?             this help
//
// Dots fire in reading order: 1 2 3 down the left column of the cell, then
// 4 5 6 down the right.
//
// Needs the generated map. From the repo root:
//     python3 tools/gen_braille_header.py
//     cp firmware/braille_tutor/braille_map.h firmware/tests/t3b_braille_patterns/
//
// The header is included rather than retyped on purpose: a second copy of the
// dot table is a second thing to keep in sync, and this project fails loudly
// when the web app and the hardware disagree about a pattern.
//
// Wiring is identical to t3 -- ULN2803A inputs on pins 1-6, outputs 18-13 to
// the motor low sides, COM (pin 10) to +5V, and 10k pulldowns on GPIO 2 and 15.

#include <stdlib.h>
#include <string.h>
#include <strings.h>

#include "braille_map.h"

static const int PIN_MOTOR[6] = { 13, 4, 21, 22, 2, 15 };

// Playback speeds, slowest first. "hint" and "normal" are lifted from
// braille_tutor.ino, so stepping to them lets you feel what a learner actually
// feels in a session. The default is deliberately slower than either: a full
// second of buzz with 400 ms of silence after it means a coin motor has clearly
// spun down before the next dot starts, so you are reading one dot at a time
// instead of a blur.
struct Speed { const char *name; uint16_t on_ms; uint16_t gap_ms; };
static const Speed SPEEDS[] = {
  { "slowest", 1000, 400 },
  { "slow",     560, 320 },
  { "hint",     400, 220 },   // braille_tutor.ino: TA_HINT
  { "normal",   320, 180 },   // braille_tutor.ino: wrong-answer correction
  { "fast",     220, 120 },
};
static const int SPEED_COUNT = sizeof(SPEEDS) / sizeof(SPEEDS[0]);
static int g_speed = 0;

static const char *const MODE_NAME[] = { "sequential", "together", "both" };
static int g_mode = 0;

static int g_last = -1;

// ---------------------------------------------------------------------------

static void motors_all_off() {
  for (int i = 0; i < 6; i++) digitalWrite(PIN_MOTOR[i], LOW);
}

static void dots_string(uint8_t mask, char *out, size_t n) {
  size_t k = 0;
  for (int i = 0; i < 6 && k + 2 < n; i++) {
    if (!(mask & (1 << i))) continue;
    if (k) out[k++] = '-';
    out[k++] = (char)('1' + i);
  }
  out[k] = '\0';
}

// Left column is dots 1-2-3, right column 4-5-6.
static void print_cell(uint8_t mask) {
  for (int row = 0; row < 3; row++) {
    Serial.print("      ");
    Serial.print((mask & (1 << row))       ? "*" : ".");
    Serial.print("   ");
    Serial.println((mask & (1 << (row + 3))) ? "*" : ".");
  }
}

static void play_sequential(uint8_t mask) {
  for (int i = 0; i < 6; i++) {
    if (!(mask & (1 << i))) continue;
    Serial.printf("      dot %d  ->  GPIO %d\n", i + 1, PIN_MOTOR[i]);
    digitalWrite(PIN_MOTOR[i], HIGH);
    delay(SPEEDS[g_speed].on_ms);
    digitalWrite(PIN_MOTOR[i], LOW);
    delay(SPEEDS[g_speed].gap_ms);
  }
}

static void play_together(uint8_t mask) {
  Serial.println("      all raised dots at once");
  for (int i = 0; i < 6; i++) if (mask & (1 << i)) digitalWrite(PIN_MOTOR[i], HIGH);
  delay(SPEEDS[g_speed].on_ms + 200);
  motors_all_off();
}

static void play_letter(int id) {
  uint8_t mask = BRAILLE_PATTERN[id];
  char dots[16];
  dots_string(mask, dots, sizeof(dots));

  Serial.printf("\n[%d] %s / %s   dots %s   mask 0x%02X   %s\n",
                id + 1, BRAILLE_NAME[id], BRAILLE_ROMAN[id], dots, mask,
                BRAILLE_VERIFIED[id] ? "verified" : "PLACEHOLDER");
  if (!BRAILLE_VERIFIED[id]) {
    Serial.println("    ! this pattern was never read from a reference image --");
    Serial.println("      the motors are faithful to the map, the map is a guess");
  }
  print_cell(mask);

  if (g_mode == 0 || g_mode == 2) play_sequential(mask);
  if (g_mode == 2) delay(500);
  if (g_mode == 1 || g_mode == 2) play_together(mask);

  motors_all_off();
  g_last = id;
}

static int find_by_name(const char *s) {
  for (int i = 0; i < BRAILLE_LETTER_COUNT; i++) {
    if (strcasecmp(s, BRAILLE_NAME[i]) == 0) return i;
  }
  return -1;
}

static void print_list() {
  Serial.println("\n  id  name            dots        ");
  Serial.println("  --  --------------  ----------  ");
  char dots[16];
  for (int i = 0; i < BRAILLE_LETTER_COUNT; i++) {
    dots_string(BRAILLE_PATTERN[i], dots, sizeof(dots));
    Serial.printf("  %2d  %-14s  %-10s  %s\n",
                  i + 1, BRAILLE_NAME[i], dots,
                  BRAILLE_VERIFIED[i] ? "" : "placeholder");
  }
  Serial.printf("\n  %d of %d verified from reference images\n\n",
                BRAILLE_VERIFIED_COUNT, BRAILLE_LETTER_COUNT);
}

static void sweep_motors() {
  Serial.println("\nraw sweep, no map: motor 1..6 in order");
  for (int i = 0; i < 6; i++) {
    Serial.printf("      motor %d  ->  GPIO %d\n", i + 1, PIN_MOTOR[i]);
    digitalWrite(PIN_MOTOR[i], HIGH);
    delay(350);
    digitalWrite(PIN_MOTOR[i], LOW);
    delay(200);
  }
  motors_all_off();
  Serial.println("if one stayed silent here, that channel is the fault -- not the map\n");
}

static void print_help() {
  Serial.println("\n  1..50     play that letter");
  Serial.println("  <name>    play by name, e.g. ka, aa, chandrabindu");
  Serial.println("  l         list all 50");
  Serial.println("  r         replay the last one");
  Serial.println("  m         cycle mode: sequential / together / both");
  Serial.println("  + -       step playback speed");
  Serial.println("  t         raw motor sweep 1..6");
  Serial.println("  ?         this help");
  Serial.printf("\n  mode %s, speed %s (%u ms on, %u ms gap)\n\n",
                MODE_NAME[g_mode], SPEEDS[g_speed].name,
                SPEEDS[g_speed].on_ms, SPEEDS[g_speed].gap_ms);
}

static void handle(char *s) {
  while (*s == ' ' || *s == '\t') s++;
  char *end = s + strlen(s);
  while (end > s && (end[-1] == ' ' || end[-1] == '\t')) *--end = '\0';
  if (!*s) return;

  if (!strcmp(s, "?") || !strcasecmp(s, "help")) { print_help(); return; }
  if (!strcasecmp(s, "l") || !strcasecmp(s, "list")) { print_list(); return; }
  if (!strcasecmp(s, "t")) { sweep_motors(); return; }

  if (!strcasecmp(s, "m")) {
    g_mode = (g_mode + 1) % 3;
    Serial.printf("mode: %s\n", MODE_NAME[g_mode]);
    return;
  }
  if (!strcasecmp(s, "r")) {
    if (g_last < 0) Serial.println("nothing played yet");
    else play_letter(g_last);
    return;
  }
  if (!strcmp(s, "+") || !strcmp(s, "-")) {
    g_speed += (*s == '+') ? 1 : -1;
    g_speed = constrain(g_speed, 0, SPEED_COUNT - 1);
    Serial.printf("speed: %s (%u ms on, %u ms gap)\n",
                  SPEEDS[g_speed].name, SPEEDS[g_speed].on_ms, SPEEDS[g_speed].gap_ms);
    return;
  }

  char *stop;
  long n = strtol(s, &stop, 10);
  if (*stop == '\0') {
    if (n < 1 || n > BRAILLE_LETTER_COUNT) {
      Serial.printf("out of range: %ld -- letters are 1..%d\n", n, BRAILLE_LETTER_COUNT);
      return;
    }
    play_letter((int)n - 1);
    return;
  }

  int id = find_by_name(s);
  if (id < 0) {
    Serial.printf("unknown: \"%s\" -- type a number 1..%d, or 'l' to list\n",
                  s, BRAILLE_LETTER_COUNT);
    return;
  }
  play_letter(id);
}

// ---------------------------------------------------------------------------

static char g_line[32];
static uint8_t g_len = 0;

void setup() {
  Serial.begin(115200);
  delay(500);
  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }
  Serial.println("\n=== t3b: Braille patterns on the motors ===");
  Serial.printf("map: %d of %d letters verified\n",
                BRAILLE_VERIFIED_COUNT, BRAILLE_LETTER_COUNT);
  print_help();
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (g_len == 0) continue;
      g_line[g_len] = '\0';
      g_len = 0;
      handle(g_line);
      continue;
    }
    if (g_len < sizeof(g_line) - 1) g_line[g_len++] = c;
  }
}
