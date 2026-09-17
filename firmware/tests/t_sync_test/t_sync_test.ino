// Dot sync test -- press a button, its paired motor buzzes immediately.
// Use this to verify that button N and motor N are in the same physical position.
//
// Standard Braille cell layout:
//
//   [Dot 1]  [Dot 4]       Button  GPIO   Motor  GPIO
//   [Dot 2]  [Dot 5]         1      32      1      13
//   [Dot 3]  [Dot 6]         2      33      2       4
//                            3      25      3      21
// Left column = dots 1-2-3   4      26      4      22
// Right column = dots 4-5-6  5      27      5       2
//                            6      14      6      15
//
// Serial Monitor: 115200 baud
// Hold any dot button -> motor buzzes while held -> release -> motor stops.

static const int PIN_BUTTON[6] = { 32, 33, 25, 26, 27, 14 };
static const int PIN_MOTOR[6]  = { 21, 13, 22,  2, 15,  4 };

void setup() {
  Serial.begin(115200);
  delay(500);

  for (int i = 0; i < 6; i++) {
    pinMode(PIN_BUTTON[i], INPUT_PULLUP);
    pinMode(PIN_MOTOR[i],  OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }

  Serial.println("\n=== Dot Sync Test ===");
  Serial.println("Hold a dot button -> its motor buzzes");
  Serial.println("Release -> motor stops");
  Serial.println();
  Serial.println("Braille cell layout:");
  Serial.println("  [1] [4]");
  Serial.println("  [2] [5]");
  Serial.println("  [3] [6]");
}

void loop() {
  for (int i = 0; i < 6; i++) {
    bool pressed = (digitalRead(PIN_BUTTON[i]) == LOW);
    if (pressed) {
      digitalWrite(PIN_MOTOR[i], HIGH);
      Serial.printf("Dot %d pressed  (button GPIO%d -> motor GPIO%d)\n",
                    i + 1, PIN_BUTTON[i], PIN_MOTOR[i]);
      delay(80);  // simple debounce print rate limiter
    } else {
      digitalWrite(PIN_MOTOR[i], LOW);
    }
  }
  delay(10);
}
