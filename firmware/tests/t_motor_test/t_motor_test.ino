// Motor test -- no ULN2803A assumed yet.
//
// Tests each GPIO directly and then through the ULN2803A so you can tell
// exactly where the fault is.
//
// Serial Monitor: 115200 baud
//   Press Enter or send any key to advance to the next motor.
//   Commands:
//     a    -- buzz ALL motors at once (checks COM/power rail)
//     1-6  -- buzz that specific motor only
//     r    -- run automatic sequence (all motors one by one)

// Motor pins (same as pins.h)
static const int PIN_MOTOR[6] = { 21, 13, 22, 2, 15, 4 };
#define BUZZ_MS 1000

void setup() {
  Serial.begin(115200);
  delay(500);

  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }

  Serial.println("\n=== Motor Test ===");
  Serial.println("Commands: r=run all  a=all at once  1-6=single motor");
  Serial.println("Measuring voltages with a multimeter: GPIO HIGH should read ~3.3V");
  Serial.println("ULN2803A OUT should read near 0V when motor is ON (open-collector)");
  Serial.println();
  run_sequence();
}

void buzz(int i, uint32_t ms) {
  Serial.printf("Motor %d (GPIO %d) ON...\n", i + 1, PIN_MOTOR[i]);
  digitalWrite(PIN_MOTOR[i], HIGH);
  delay(ms);
  digitalWrite(PIN_MOTOR[i], LOW);
  Serial.printf("Motor %d OFF\n", i + 1);
}

void all_on(uint32_t ms) {
  Serial.println("ALL motors ON...");
  for (int i = 0; i < 6; i++) digitalWrite(PIN_MOTOR[i], HIGH);
  delay(ms);
  for (int i = 0; i < 6; i++) digitalWrite(PIN_MOTOR[i], LOW);
  Serial.println("ALL motors OFF");
}

void run_sequence() {
  Serial.println("--- Automatic sequence: motor 1 to 6 ---");
  for (int i = 0; i < 6; i++) {
    buzz(i, BUZZ_MS);
    delay(400);
  }
  Serial.println("--- Sequence done ---\n");
}

void loop() {
  if (!Serial.available()) return;

  String line = Serial.readStringUntil('\n');
  line.trim();

  if (line.equalsIgnoreCase("r")) {
    run_sequence();
  } else if (line.equalsIgnoreCase("a")) {
    all_on(BUZZ_MS);
  } else if (line.length() > 0) {
    int n = line.toInt();
    if (n >= 1 && n <= 6) {
      buzz(n - 1, BUZZ_MS);
    } else {
      Serial.println("r=run all  a=all at once  1-6=single motor");
    }
  }
}
