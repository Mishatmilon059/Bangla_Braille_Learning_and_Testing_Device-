// ============================================================
//  p6 — DUAL MODE: buttons speak, serial teaches
//  FIXED VERSION 2 — playMp3Folder() replaced with play()
// ============================================================

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

const int buttonPins[6]  = {4, 5, 15, 19, 21, 22};
const int submitButtonPin = 18;
const int enterButtonPin  = 34;
const int PIN_MOTOR[6]   = {13, 14, 26, 27, 32, 33};

#define PIN_DF_ESP_RX 25
#define PIN_DF_ESP_TX 23

HardwareSerial mySoftwareSerial(2);
DFRobotDFPlayerMini dfPlayer;

const uint8_t BRAILLE_PATTERN[50] = {
  0x01, 0x1C, 0x0A, 0x14, 0x25, 0x33, 0x17, 0x11, 0x0C, 0x15, 0x2A,
  0x05, 0x28, 0x1B, 0x23, 0x2C, 0x09, 0x21, 0x1A, 0x34, 0x12,
  0x3E, 0x3A, 0x2B, 0x3F, 0x3C, 0x1E, 0x39, 0x19, 0x2E, 0x1D,
  0x0F, 0x0B, 0x03, 0x18, 0x0D, 0x3D, 0x17, 0x07, 0x29, 0x2F,
  0x0E, 0x13, 0x3B, 0x37, 0x36, 0x26, 0x30, 0x06, 0x08
};

const char* LETTER_NAMES[50] = {
  "অ", "আ", "ই", "ঈ", "উ", "ঊ", "ঋ", "এ", "ঐ", "ও", "ঔ",
  "ক", "খ", "গ", "ঘ", "ঙ", "চ", "ছ", "জ", "ঝ", "ঞ",
  "ট", "ঠ", "ড", "ঢ", "ণ", "ত", "থ", "দ", "ধ", "ন",
  "প", "ফ", "ব", "ভ", "ম", "য", "র", "ল", "শ", "ষ",
  "স", "হ", "ড়", "ঢ়", "য়", "ৎ", "ং", "ঃ", "ঁ"
};

const unsigned long debounceDelay = 50;

bool activeChord[6] = {false, false, false, false, false, false};
String typedMessage  = "";
byte pendingPrefix   = 0;

int lastRawState[6], confirmedState[6];
unsigned long lastChangeTime[6];

int lastRawSubmit, confirmedSubmit;
unsigned long lastSubmitChangeTime;

int lastRawEnter, confirmedEnter;
unsigned long lastEnterChangeTime;

void resetChord();
void vibrateBrailleDotsSequential(uint8_t pattern);
void decodeAndProcessChord();
void handleEnterPress();

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("\n==========================================");
  Serial.println("  BANGLA BRAILLE DUAL-MODE SYSTEM READY!");
  Serial.println("==========================================");
  Serial.println("[MODE 1] Tap dots + Submit -> Speaker names the letter.");
  Serial.println("[MODE 2] Type number (1-50) in Serial -> Speaker + Motors.");
  Serial.println("==========================================\n");

  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }

  for (int i = 0; i < 6; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
    lastRawState[i]   = digitalRead(buttonPins[i]);
    confirmedState[i]  = lastRawState[i];
    lastChangeTime[i]  = millis();
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

  Serial.println("Initializing DFPlayer Mini...");
  if (!dfPlayer.begin(mySoftwareSerial, false, true)) {
    Serial.println("DFPlayer Mini Init Failed!");
    Serial.println("   Check: VCC on 5V (VIN pin)?");
    Serial.println("   Check: TX/RX not swapped?");
    Serial.println("   Check: 1k resistor on DFPlayer RX?");
    Serial.println("   Check: SD card inserted?");
  } else {
    Serial.println("DFPlayer Mini Connected!");
    dfPlayer.volume(25);
    Serial.println("   Volume set to 25/30.");
  }

  Serial.println("\nSystem Ready. Waiting for input...\n");
}

void loop() {
  unsigned long now = millis();

  if (Serial.available() > 0) {
    int inputVal = Serial.parseInt();
    if (inputVal >= 1 && inputVal <= 50) {
      int index = inputVal - 1;
      Serial.println("\n----------------------------------------");
      Serial.printf("SERIAL INPUT: %d -> %s\n", inputVal, LETTER_NAMES[index]);

      dfPlayer.play(inputVal);
      delay(1500);

      if (index == 6 || index == 46) {
        Serial.println(">> 2-Cell Character!");
        vibrateBrailleDotsSequential(0x10);
        delay(1200);
        vibrateBrailleDotsSequential(BRAILLE_PATTERN[index]);
      } else {
        vibrateBrailleDotsSequential(BRAILLE_PATTERN[index]);
      }

      Serial.println("----------------------------------------\n");
    }
  }

  for (int i = 0; i < 6; i++) {
    int reading = digitalRead(buttonPins[i]);
    if (reading != lastRawState[i]) {
      lastChangeTime[i] = now;
      lastRawState[i]   = reading;
    }
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
  if (submitReading != lastRawSubmit) {
    lastSubmitChangeTime = now;
    lastRawSubmit        = submitReading;
  }
  if ((now - lastSubmitChangeTime) > debounceDelay && submitReading != confirmedSubmit) {
    confirmedSubmit = submitReading;
    if (confirmedSubmit == LOW) {
      decodeAndProcessChord();
    }
  }

  int enterReading = digitalRead(enterButtonPin);
  if (enterReading != lastRawEnter) {
    lastEnterChangeTime = now;
    lastRawEnter        = enterReading;
  }
  if ((now - lastEnterChangeTime) > debounceDelay && enterReading != confirmedEnter) {
    confirmedEnter = enterReading;
    if (confirmedEnter == LOW) {
      handleEnterPress();
    }
  }
}

void resetChord() {
  for (int i = 0; i < 6; i++) {
    activeChord[i] = false;
  }
}

void vibrateBrailleDotsSequential(uint8_t pattern) {
  Serial.print("Vibrating: ");
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      Serial.printf("[Dot %d] ", i + 1);
    }
  }
  Serial.println();

  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      digitalWrite(PIN_MOTOR[i], HIGH);
      delay(400);
      digitalWrite(PIN_MOTOR[i], LOW);
      delay(800);
    }
  }
}

void decodeAndProcessChord() {
  byte typedPattern = 0;
  bool isBlank      = true;

  for (int i = 0; i < 6; i++) {
    if (activeChord[i]) {
      typedPattern |= (1 << i);
      isBlank = false;
    }
  }

  if (isBlank) {
    Serial.println("Space input detected.");
    typedMessage += " ";
    pendingPrefix  = 0;
    return;
  }

  if (typedPattern == 0x10 && pendingPrefix == 0) {
    pendingPrefix = 0x10;
    Serial.println("Prefix (Dot 5) entered. Enter 2nd cell for ঋ or ৎ...");
    resetChord();
    return;
  }

  int matchedIndex = -1;

  if (pendingPrefix == 0x10) {
    if (typedPattern == 0x17) {
      matchedIndex = 6;
    } else if (typedPattern == 0x26 || typedPattern == 0x1E) {
      matchedIndex = 46;
    } else {
      Serial.println("Invalid 2-cell combination. Resetting.");
      pendingPrefix = 0;
      resetChord();
      return;
    }
  } else {
    for (int i = 0; i < 50; i++) {
      if (i == 6 || i == 46) continue;
      if (BRAILLE_PATTERN[i] == typedPattern) {
        matchedIndex = i;
        break;
      }
    }
  }

  if (matchedIndex != -1) {
    int trackNum = matchedIndex + 1;
    Serial.println("========================================");
    Serial.printf("SUCCESS! Button Input Decoded: %s\n", LETTER_NAMES[matchedIndex]);
    Serial.println("========================================");
    typedMessage += LETTER_NAMES[matchedIndex];
    dfPlayer.play(trackNum);
  } else {
    Serial.println("Unknown Braille pattern. Check dot combination.");
  }

  pendingPrefix = 0;
  resetChord();
}

void handleEnterPress() {
  Serial.println("\n----------------------------------------");
  Serial.print("TYPED MESSAGE: ");
  Serial.println(typedMessage);
  Serial.println("----------------------------------------\n");
  typedMessage  = "";
  pendingPrefix = 0;
}
