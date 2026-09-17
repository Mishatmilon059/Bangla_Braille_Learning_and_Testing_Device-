// ============================================================
//  p6 — TRIPLE MODE: menu, learn, test
//  FIXED: BRAILLE_PATTERN corrected from Bangladesh chart
// ============================================================

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

const int buttonPins[6]   = {4, 5, 15, 19, 21, 22};
const int submitButtonPin  = 18;
const int enterButtonPin   = 34;
const int PIN_MOTOR[6]    = {13, 14, 26, 27, 32, 33};

#define PIN_DF_ESP_RX 25
#define PIN_DF_ESP_TX 23

HardwareSerial mySoftwareSerial(2);
DFRobotDFPlayerMini dfPlayer;

// ============================================================
//  CORRECTED BANGLADESH BRAILLE PATTERNS
//  Dot layout: 1=top-left 4=top-right
//              2=mid-left 5=mid-right
//              3=bot-left 6=bot-right
//  Bits: Dot1=bit0, Dot2=bit1, Dot3=bit2,
//        Dot4=bit3, Dot5=bit4, Dot6=bit5
// ============================================================
const uint8_t BRAILLE_PATTERN[50] = {
  0x01,  // [ 1] অ   Dot1
  0x03,  // [ 2] আ   Dot1 Dot2
  0x09,  // [ 3] ই   Dot1 Dot4
  0x19,  // [ 4] ঈ   Dot1 Dot4 Dot5
  0x11,  // [ 5] উ   Dot1 Dot5
  0x13,  // [ 6] ঊ   Dot1 Dot2 Dot5
  0x1B,  // [ 7] ঋ   Dot1 Dot2 Dot4 Dot5  (2-cell: prefix Dot6 cell first)
  0x31,  // [ 8] এ   Dot1 Dot5 Dot6
  0x39,  // [ 9] ঐ   Dot1 Dot4 Dot5 Dot6
  0x3B,  // [10] ও   Dot1 Dot2 Dot4 Dot5 Dot6
  0x3A,  // [11] ঔ   Dot2 Dot4 Dot5 Dot6
  0x05,  // [12] ক   Dot1 Dot3
  0x07,  // [13] খ   Dot1 Dot2 Dot3
  0x1B,  // [14] গ   Dot1 Dot2 Dot4 Dot5
  0x0B,  // [15] ঘ   Dot1 Dot2 Dot4
  0x19,  // [16] ঙ   Dot1 Dot4 Dot5
  0x09,  // [17] চ   Dot1 Dot4
  0x29,  // [18] ছ   Dot1 Dot4 Dot6
  0x1A,  // [19] জ   Dot2 Dot4 Dot5
  0x2A,  // [20] ঝ   Dot2 Dot4 Dot6
  0x39,  // [21] ঞ   Dot1 Dot4 Dot5 Dot6
  0x3E,  // [22] ট   Dot2 Dot3 Dot4 Dot5 Dot6
  0x2E,  // [23] ঠ   Dot2 Dot3 Dot4 Dot6
  0x39,  // [24] ড   Dot1 Dot4 Dot5 Dot6
  0x3B,  // [25] ঢ   Dot1 Dot2 Dot4 Dot5 Dot6
  0x1D,  // [26] ণ   Dot1 Dot3 Dot4 Dot5
  0x1E,  // [27] ত   Dot2 Dot3 Dot4 Dot5
  0x36,  // [28] থ   Dot2 Dot3 Dot5 Dot6
  0x19,  // [29] দ   Dot1 Dot4 Dot5
  0x3A,  // [30] ধ   Dot2 Dot4 Dot5 Dot6
  0x1D,  // [31] ন   Dot1 Dot3 Dot4 Dot5
  0x0F,  // [32] প   Dot1 Dot2 Dot3 Dot4
  0x3F,  // [33] ফ   Dot1 Dot2 Dot3 Dot4 Dot5 Dot6
  0x07,  // [34] ব   Dot1 Dot2 Dot3
  0x27,  // [35] ভ   Dot1 Dot2 Dot3 Dot6
  0x0D,  // [36] ম   Dot1 Dot3 Dot4
  0x3D,  // [37] য   Dot1 Dot3 Dot4 Dot5 Dot6
  0x17,  // [38] র   Dot1 Dot2 Dot3 Dot5
  0x1F,  // [39] ল   Dot1 Dot2 Dot3 Dot4 Dot5
  0x29,  // [40] শ   Dot1 Dot4 Dot6
  0x3F,  // [41] ষ   Dot1 Dot2 Dot3 Dot4 Dot5 Dot6
  0x0E,  // [42] স   Dot2 Dot3 Dot4
  0x33,  // [43] হ   Dot1 Dot2 Dot5 Dot6
  0x3B,  // [44] ড়  Dot1 Dot2 Dot4 Dot5 Dot6
  0x3D,  // [45] ঢ়  Dot1 Dot3 Dot4 Dot5 Dot6
  0x35,  // [46] য়  Dot1 Dot3 Dot5 Dot6
  0x26,  // [47] ৎ   Dot2 Dot3 Dot6  (2-cell: prefix Dot6 cell first)
  0x1B,  // [48] ং   Dot1 Dot2 Dot4 Dot5
  0x05,  // [49] ঃ   Dot1 Dot3
  0x04,  // [50] ঁ   Dot3
};

const char* LETTER_NAMES[50] = {
  "অ", "আ", "ই", "ঈ", "উ", "ঊ", "ঋ", "এ", "ঐ", "ও", "ঔ",
  "ক", "খ", "গ", "ঘ", "ঙ", "চ", "ছ", "জ", "ঝ", "ঞ",
  "ট", "ঠ", "ড", "ঢ", "ণ", "ত", "থ", "দ", "ধ", "ন",
  "প", "ফ", "ব", "ভ", "ম", "য", "র", "ল", "শ", "ষ",
  "স", "হ", "ড়", "ঢ়", "য়", "ৎ", "ং", "ঃ", "ঁ"
};

#define MODE_MENU  0
#define MODE_LEARN 1
#define MODE_TEST  2

int currentMode = MODE_MENU;
bool waitingForButtonInput = false;
int  testTargetIndex       = -1;
int  testCorrect           = 0;
int  testWrong             = 0;

const unsigned long debounceDelay = 50;
bool activeChord[6] = {false, false, false, false, false, false};

int lastRawState[6], confirmedState[6];
unsigned long lastChangeTime[6];
int lastRawSubmit, confirmedSubmit;
unsigned long lastSubmitChangeTime;
int lastRawEnter, confirmedEnter;
unsigned long lastEnterChangeTime;

void showMenu();
void showLearnPrompt();
void showTestPrompt();
void runLearn(int index);
void runTestQuestion(int index);
void checkTestAnswer(byte typedPattern);
void resetChord();
void vibrateBrailleDotsSequential(uint8_t pattern);
void printDotPattern(uint8_t pattern);

void setup() {
  Serial.begin(115200);
  delay(500);

  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }
  for (int i = 0; i < 6; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
    lastRawState[i]  = digitalRead(buttonPins[i]);
    confirmedState[i] = lastRawState[i];
    lastChangeTime[i] = millis();
  }
  pinMode(submitButtonPin, INPUT_PULLUP);
  lastRawSubmit        = digitalRead(submitButtonPin);
  confirmedSubmit      = lastRawSubmit;
  lastSubmitChangeTime = millis();

  pinMode(enterButtonPin, INPUT);
  lastRawEnter        = digitalRead(enterButtonPin);
  confirmedEnter      = lastRawEnter;
  lastEnterChangeTime = millis();

  mySoftwareSerial.begin(9600, SERIAL_8N1, PIN_DF_ESP_RX, PIN_DF_ESP_TX);
  delay(1000);

  Serial.println("\n==========================================");
  Serial.println("  BANGLA BRAILLE SYSTEM");
  Serial.println("==========================================");
  Serial.print("DFPlayer: ");
  if (!dfPlayer.begin(mySoftwareSerial, false, true)) {
    Serial.println("FAILED - check wiring!");
  } else {
    Serial.println("OK");
    dfPlayer.volume(25);
  }
  delay(500);
  showMenu();
}

void loop() {
  unsigned long now = millis();

  if (Serial.available() > 0) {
    if (currentMode == MODE_MENU) {
      char c = Serial.read();
      if (c == 'L' || c == 'l') {
        currentMode = MODE_LEARN;
        Serial.println("\n>> LEARN MODE selected.");
        showLearnPrompt();
      } else if (c == 'T' || c == 't') {
        currentMode = MODE_TEST;
        testCorrect = 0;
        testWrong   = 0;
        Serial.println("\n>> TEST MODE selected.");
        showTestPrompt();
      } else if (c == '\n' || c == '\r' || c == ' ') {
      } else {
        Serial.println("Invalid. Type L for Learn or T for Test.");
      }
    } else if (currentMode == MODE_LEARN) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      if (input == "M" || input == "m") {
        currentMode = MODE_MENU;
        showMenu();
      } else {
        int val = input.toInt();
        if (val >= 1 && val <= 50) {
          runLearn(val - 1);
          showLearnPrompt();
        } else {
          Serial.println("Enter 1-50 or M for menu.");
        }
      }
    } else if (currentMode == MODE_TEST && !waitingForButtonInput) {
      String input = Serial.readStringUntil('\n');
      input.trim();
      if (input == "M" || input == "m") {
        currentMode           = MODE_MENU;
        waitingForButtonInput = false;
        testTargetIndex       = -1;
        Serial.printf("\n-- Session ended. Correct: %d | Wrong: %d --\n", testCorrect, testWrong);
        showMenu();
      } else {
        int val = input.toInt();
        if (val >= 1 && val <= 50) {
          runTestQuestion(val - 1);
        } else {
          Serial.println("Enter 1-50 or M for menu.");
        }
      }
    } else if (currentMode == MODE_TEST && waitingForButtonInput) {
      Serial.read();
      Serial.println(">> Press braille dots then hit SUBMIT button!");
    }
  }

  for (int i = 0; i < 6; i++) {
    int reading = digitalRead(buttonPins[i]);
    if (reading != lastRawState[i]) { lastChangeTime[i] = now; lastRawState[i] = reading; }
    if ((now - lastChangeTime[i]) > debounceDelay && reading != confirmedState[i]) {
      confirmedState[i] = reading;
      if (confirmedState[i] == LOW) {
        activeChord[i] = !activeChord[i];
        Serial.print("Dot "); Serial.print(i + 1);
        Serial.println(activeChord[i] ? " selected." : " removed.");
      }
    }
  }

  int submitReading = digitalRead(submitButtonPin);
  if (submitReading != lastRawSubmit) { lastSubmitChangeTime = now; lastRawSubmit = submitReading; }
  if ((now - lastSubmitChangeTime) > debounceDelay && submitReading != confirmedSubmit) {
    confirmedSubmit = submitReading;
    if (confirmedSubmit == LOW) {
      if (currentMode == MODE_TEST && waitingForButtonInput) {
        byte typedPattern = 0;
        for (int i = 0; i < 6; i++) {
          if (activeChord[i]) typedPattern |= (1 << i);
        }
        checkTestAnswer(typedPattern);
        resetChord();
      } else {
        Serial.println("(No active question - enter a number first)");
      }
    }
  }

  int enterReading = digitalRead(enterButtonPin);
  if (enterReading != lastRawEnter) { lastEnterChangeTime = now; lastRawEnter = enterReading; }
  if ((now - lastEnterChangeTime) > debounceDelay && enterReading != confirmedEnter) {
    confirmedEnter = enterReading;
    if (confirmedEnter == LOW) {
      currentMode           = MODE_MENU;
      waitingForButtonInput = false;
      testTargetIndex       = -1;
      resetChord();
      Serial.printf("\n-- Session ended. Correct: %d | Wrong: %d --\n", testCorrect, testWrong);
      showMenu();
    }
  }
}

void showMenu() {
  Serial.println("\n==========================================");
  Serial.println("  MAIN MENU");
  Serial.println("==========================================");
  Serial.println("  Type  L  -> Learn Mode");
  Serial.println("  Type  T  -> Test Mode");
  Serial.println("==========================================");
  Serial.print("Your choice: ");
}

void showLearnPrompt() {
  Serial.println("\n-- LEARN MODE --");
  Serial.println("   Type a number (1-50) to hear and feel the character.");
  Serial.println("   Type M to return to menu.");
  Serial.print("   Enter number: ");
}

void showTestPrompt() {
  Serial.println("\n-- TEST MODE --");
  Serial.println("   Type a number (1-50) to hear the character.");
  Serial.println("   Press the correct braille dots then hit SUBMIT.");
  Serial.println("   Type M to return to menu.");
  Serial.print("   Enter number: ");
}

void runLearn(int index) {
  Serial.println("\n----------------------------------------");
  Serial.printf("  LEARNING: [%d] %s\n", index + 1, LETTER_NAMES[index]);
  Serial.print("  Braille dots: ");
  printDotPattern(BRAILLE_PATTERN[index]);
  Serial.println("----------------------------------------");
  dfPlayer.play(index + 1);
  delay(1500);
  if (index == 6 || index == 46) {
    Serial.println("  (2-cell character)");
    Serial.println("  Vibrating prefix cell (Dot6)...");
    vibrateBrailleDotsSequential(0x20);
    delay(1200);
    Serial.println("  Vibrating main pattern...");
    vibrateBrailleDotsSequential(BRAILLE_PATTERN[index]);
  } else {
    vibrateBrailleDotsSequential(BRAILLE_PATTERN[index]);
  }
  Serial.println("  Done.");
}

void runTestQuestion(int index) {
  testTargetIndex       = index;
  waitingForButtonInput = true;
  resetChord();
  Serial.println("\n========================================");
  Serial.printf("  QUESTION: Braille pattern for [%d] %s ?\n", index + 1, LETTER_NAMES[index]);
  Serial.println("  Listen to speaker, then press dots + SUBMIT.");
  Serial.println("========================================");
  dfPlayer.play(index + 1);
}

void checkTestAnswer(byte typedPattern) {
  if (testTargetIndex < 0) return;
  int     index          = testTargetIndex;
  uint8_t correctPattern = BRAILLE_PATTERN[index];
  Serial.println("\n----------------------------------------");
  Serial.printf("  Character : %s\n", LETTER_NAMES[index]);
  Serial.print("  Your dots : "); printDotPattern(typedPattern);
  Serial.print("  Correct   : "); printDotPattern(correctPattern);
  if (typedPattern == correctPattern) {
    testCorrect++;
    Serial.println("  RESULT    : CORRECT!");
  } else {
    testWrong++;
    Serial.println("  RESULT    : WRONG!");
  }
  Serial.printf("  Score -> Correct: %d | Wrong: %d\n", testCorrect, testWrong);
  Serial.println("----------------------------------------");
  waitingForButtonInput = false;
  testTargetIndex       = -1;
  showTestPrompt();
}

void resetChord() {
  for (int i = 0; i < 6; i++) activeChord[i] = false;
}

void printDotPattern(uint8_t pattern) {
  bool any = false;
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) { Serial.printf("Dot%d ", i + 1); any = true; }
  }
  if (!any) Serial.print("(none)");
  Serial.println();
}

void vibrateBrailleDotsSequential(uint8_t pattern) {
  Serial.print("  Vibrating: "); printDotPattern(pattern);
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      digitalWrite(PIN_MOTOR[i], HIGH);
      delay(400);
      digitalWrite(PIN_MOTOR[i], LOW);
      delay(800);
    }
  }
}
