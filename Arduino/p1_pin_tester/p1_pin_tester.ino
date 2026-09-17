// ============================================================
//  p1 — INDIVIDUAL PIN TESTER: bounce & wiring diagnostic
// ============================================================
// Purpose:
//   Test each button's physical connection in isolation, with
//   NO debounce filtering at all. Every raw transition is
//   printed with a timestamp so you can see exactly what the
//   pin is doing.
//
// How to use:
//   1. Upload this sketch, open Serial Monitor at 115200 baud.
//   2. Press ONE button at a time and watch the output.
//   3. A clean, healthy button press produces exactly:
//        PRESSED
//        RELEASED
//      with the gap between them being how long you held it.
//   4. A flaky wire/connection/switch produces MANY
//      PRESSED/RELEASED lines in a burst — sometimes spread
//      over hundreds of ms or even seconds. Whichever pin does
//      this is the one to physically re-check (reseat wires,
//      move to a different breadboard row, check with a
//      multimeter, etc).
//
// Pins (as built on the bench):
//   dots   GPIO 4, 5, 15, 19, 21, 22   (INPUT_PULLUP, to GND)
//   submit GPIO 23
//
// NOTE: the 7th pin is labelled "Submit" here on GPIO 23, but p4
// wires Enter there and p5/p6 use GPIO 23 for DFPlayer TX. Check
// which sketch you are about to flash before trusting the label.
// ============================================================

const int pins[7] = {4, 5, 15, 19, 21, 22, 23};
const char* pinLabels[7] = {
  "Dot 1", "Dot 2", "Dot 3", "Dot 4", "Dot 5", "Dot 6", "Submit"
};

bool lastState[7];
unsigned long lastChangeTime[7];
unsigned long transitionCount[7];

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println();
  Serial.println("=== Individual Pin Tester ===");
  Serial.println("Press each button ONE AT A TIME.");
  Serial.println("Multiple PRESSED/RELEASED lines from a single press = bad connection.");
  Serial.println();

  for (int i = 0; i < 7; i++) {
    pinMode(pins[i], INPUT_PULLUP);
    lastState[i] = digitalRead(pins[i]);   // should read HIGH at rest
    lastChangeTime[i] = millis();
    transitionCount[i] = 0;
  }
}

void loop() {
  unsigned long now = millis();

  for (int i = 0; i < 7; i++) {
    bool reading = digitalRead(pins[i]);

    if (reading != lastState[i]) {
      unsigned long gap = now - lastChangeTime[i];
      transitionCount[i]++;

      Serial.print("[");
      Serial.print(now);
      Serial.print(" ms] ");
      Serial.print(pinLabels[i]);
      Serial.print(" (GPIO ");
      Serial.print(pins[i]);
      Serial.print(") -> ");
      Serial.print(reading == LOW ? "PRESSED" : "RELEASED");
      Serial.print("   [gap since last change: ");
      Serial.print(gap);
      Serial.print(" ms]   [total transitions: ");
      Serial.print(transitionCount[i]);
      Serial.println("]");

      if (gap < 100) {
        Serial.println("      ^^ WARNING: rapid re-trigger. Likely bounce/chatter/loose wire.");
      }

      Serial.flush();

      lastState[i] = reading;
      lastChangeTime[i] = now;
    }
  }
}
