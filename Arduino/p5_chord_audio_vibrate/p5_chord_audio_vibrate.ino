// ============================================================
//  p5 — FULL CHAIN: chord input -> speak -> vibrate
// ============================================================
// Proves: buttons, DFPlayer and motors working together. Submit
// decodes the chord, the speaker names the letter, then the
// motors replay that letter's dots one at a time.
//
// Use: tap dots, Submit to decode and play, Enter to print the
// accumulated message.
//
// Pins (as built on the bench):
//   dots        GPIO 4, 5, 15, 19, 21, 22
//   submit      GPIO 18
//   enter       GPIO 34   <-- see warning below
//   motors      GPIO 13, 14, 26, 27, 32, 33
//   DFPlayer RX GPIO 25 / TX GPIO 23 (1k in series on DFPlayer RX)
//
// WARNING: GPIO 34 is input-only and has NO internal pull-up, so
// the pinMode(INPUT_PULLUP) below does nothing for the Enter
// button. It needs an external 10k pull-up to 3V3 or it will read
// as random noise. Same caveat as PIN_SUBMIT in
// firmware/braille_tutor/pins.h.
// ============================================================

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

// ============================================================
//  HARDWARE PIN CONFIGURATIONS (STRICTLY UNCHANGED)
// ============================================================

// --- 6 Braille Dot Push Buttons ---
const int buttonPins[6] = {4, 5, 15, 19, 21, 22};

// --- Action Buttons ---
const int submitButtonPin = 18;   
const int enterButtonPin = 34;    

// --- 6 Braille Dot Vibration Motors ---
const int PIN_MOTOR[6] = { 13, 14, 26, 27, 32, 33 }; 

// --- DFPlayer Pin Configuration ---
#define PIN_DF_RX 25   // DFPlayer TX থেকে আসবে
#define PIN_DF_TX 23   // ESP32 থেকে 1kΩ রেজিস্টর হয়ে DFPlayer RX এ যাবে

HardwareSerial mySoftwareSerial(2); 
DFRobotDFPlayerMini dfPlayer;


// ============================================================
//  BRAILLE DATA DICTIONARY
// ============================================================

const uint8_t BRAILLE_PATTERN[50] = {
  0x01,  //  1: অ  (Dot 1)
  0x1C,  //  2: আ  (Dots 3, 4, 5)
  0x0A,  //  3: ই  (Dots 2, 4)
  0x14,  //  4: ঈ  (Dots 3, 5)
  0x25,  //  5: উ  (Dots 1, 3, 6)
  0x33,  //  6: ঊ  (Dots 1, 2, 5, 6)
  0x17,  //  7: ঋ  (Dots 1, 2, 3, 5)  **2-cell prefix req**
  0x11,  //  8: এ  (Dots 1, 5)
  0x0C,  //  9: ঐ  (Dots 3, 4)
  0x15,  // 10: ও  (Dots 1, 3, 5)
  0x2A,  // 11: ঔ  (Dots 2, 4, 6)
  0x05,  // 12: ক  (Dots 1, 3)
  0x28,  // 13: খ  (Dots 4, 6)
  0x1B,  // 14: গ  (Dots 1, 2, 4, 5)
  0x23,  // 15: ঘ  (Dots 1, 2, 6)
  0x2C,  // 16: ঙ  (Dots 3, 4, 6)
  0x09,  // 17: চ  (Dots 1, 4)
  0x21,  // 18: ছ  (Dots 1, 6)
  0x1A,  // 19: জ  (Dots 2, 4, 5)
  0x34,  // 20: ঝ  (Dots 3, 5, 6)
  0x12,  // 21: ঞ  (Dots 2, 5)
  0x3E,  // 22: ট  (Dots 2, 3, 4, 5, 6)
  0x3A,  // 23: ঠ  (Dots 2, 4, 5, 6)
  0x2B,  // 24: ড  (Dots 1, 2, 4, 6)
  0x3F,  // 25: ঢ  (Dots 1, 2, 3, 4, 5, 6)
  0x3C,  // 26: ণ  (Dots 3, 4, 5, 6)
  0x1E,  // 27: ত  (Dots 2, 3, 4, 5)
  0x39,  // 28: থ  (Dots 1, 4, 5, 6)
  0x19,  // 29: দ  (Dots 1, 4, 5)
  0x2E,  // 30: ধ  (Dots 2, 3, 4, 6)
  0x1D,  // 31: ন  (Dots 1, 3, 4, 5)
  0x0F,  // 32: প  (Dots 1, 2, 3, 4)
  0x0B,  // 33: ফ  (Dots 1, 2, 4)
  0x03,  // 34: ব  (Dots 1, 2)
  0x18,  // 35: ভ  (Dots 4, 5)
  0x0D,  // 36: ম  (Dots 1, 3, 4)
  0x3D,  // 37: য  (Dots 1, 3, 4, 5, 6)
  0x17,  // 38: র  (Dots 1, 2, 3, 5)
  0x07,  // 39: ল  (Dots 1, 2, 3)
  0x29,  // 40: শ  (Dots 1, 4, 6)
  0x2F,  // 41: ষ  (Dots 1, 2, 3, 4, 6)
  0x0E,  // 42: স  (Dots 2, 3, 4)
  0x13,  // 43: হ  (Dots 1, 2, 5)
  0x3B,  // 44: ড়  (Dots 1, 2, 4, 5, 6)
  0x37,  // 45: ঢ়  (Dots 1, 2, 3, 5, 6)
  0x36,  // 46: য়  (Dots 2, 3, 5, 6)
  0x26,  // 47: ৎ  (Dots 2, 3, 6)     
  0x30,  // 48: ং  (Dots 5, 6)
  0x06,  // 49: ঃ  (Dots 2, 3)
  0x08   // 50: ঁ  (Dot 4)
};

const char* LETTER_NAMES[50] = {
  "অ", "আ", "ই", "ঈ", "উ", "ঊ", "ঋ", "এ", "ঐ", "ও", "ঔ",
  "ক", "খ", "গ", "ঘ", "ঙ", "চ", "ছ", "জ", "ঝ", "ঞ",
  "ট", "ঠ", "ড", "ঢ", "ণ", "ত", "থ", "দ", "ধ", "ন",
  "প", "ফ", "ব", "ভ", "ম", "য", "র", "ল", "শ", "ষ",
  "স", "হ", "ড়", "ঢ়", "য়", "ৎ", "ং", "ঃ", "ঁ"
};


// ============================================================
//  SYSTEM VARIABLES & DEBOUNCING
// ============================================================

const unsigned long debounceDelay = 50; 

bool activeChord[6] = {false, false, false, false, false, false};
String typedMessage = "";
byte pendingPrefix = 0; 

int lastRawState[6], confirmedState[6];
unsigned long lastChangeTime[6];

int lastRawSubmit, confirmedSubmit;
unsigned long lastSubmitChangeTime;

int lastRawEnter, confirmedEnter;
unsigned long lastEnterChangeTime;


// ============================================================
//  SETUP FUNCTION
// ============================================================

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n==========================================");
  Serial.println("  BANGLA BRAILLE FULL SYSTEM READY!");
  Serial.println("==========================================");

  // Initialize Motors
  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }

  // Initialize Dot Buttons
  for (int i = 0; i < 6; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
    lastRawState[i] = digitalRead(buttonPins[i]);
    confirmedState[i] = lastRawState[i];
    lastChangeTime[i] = millis();
  }

  // Initialize Action Buttons
  pinMode(submitButtonPin, INPUT_PULLUP);
  lastRawSubmit = digitalRead(submitButtonPin);
  confirmedSubmit = lastRawSubmit;
  lastSubmitChangeTime = millis();

  pinMode(enterButtonPin, INPUT_PULLUP);
  lastRawEnter = digitalRead(enterButtonPin);
  confirmedEnter = lastRawEnter;
  lastEnterChangeTime = millis();

  // Initialize DFPlayer
  mySoftwareSerial.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(500);

  if (!dfPlayer.begin(mySoftwareSerial, true, true)) {
    Serial.println("❌ DFPlayer Mini Init Failed!");
  } else {
    Serial.println("✅ DFPlayer Mini Connected!");
    dfPlayer.volume(30); 
  }
  Serial.println("==========================================\n");
}


// ============================================================
//  MAIN LOOP
// ============================================================

void loop() {
  unsigned long now = millis();

  // 1. Process Dot Buttons (Toggle ON/OFF)
  for (int i = 0; i < 6; i++) {
    int reading = digitalRead(buttonPins[i]);
    if (reading != lastRawState[i]) {
      lastChangeTime[i] = now;
      lastRawState[i] = reading;
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

  // 2. Process Submit Button (Decode -> Speak -> Vibrate Sequence)
  int submitReading = digitalRead(submitButtonPin);
  if (submitReading != lastRawSubmit) {
    lastSubmitChangeTime = now;
    lastRawSubmit = submitReading;
  }
  if ((now - lastSubmitChangeTime) > debounceDelay && submitReading != confirmedSubmit) {
    confirmedSubmit = submitReading;
    if (confirmedSubmit == LOW) { 
      decodeAndProcessChord();
    }
  }

  // 3. Process Enter Button (Print full message)
  int enterReading = digitalRead(enterButtonPin);
  if (enterReading != lastRawEnter) {
    lastEnterChangeTime = now;
    lastRawEnter = enterReading;
  }
  if ((now - lastEnterChangeTime) > debounceDelay && enterReading != confirmedEnter) {
    confirmedEnter = enterReading;
    if (confirmedEnter == LOW) { 
      handleEnterPress();
    }
  }
}


// ============================================================
//  CORE LOGIC & ACTION FUNCTIONS
// ============================================================

void resetChord() {
  for (int i = 0; i < 6; i++) {
    activeChord[i] = false;
  }
}

// -------------------------------------------------------------
// VIBRATE IN SEQUENCE: নির্দিষ্ট অক্ষরের ডটগুলো পর্যায়ক্রমে কাঁপবে
// -------------------------------------------------------------
void vibrateBrailleDotsSequential(uint8_t pattern) {
  Serial.print("Vibrating Sequence: ");
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      Serial.printf("[Dot %d] ", i + 1);
    }
  }
  Serial.println();

  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      digitalWrite(PIN_MOTOR[i], HIGH);
      delay(400);   // ৪০০ মিলি-সেকেন্ড মোটর চলবে                     
      digitalWrite(PIN_MOTOR[i], LOW);   
      delay(800);   // পরবর্তী ডট ভাইব্রেট করার আগে ৮০০ মিলি-সেকেন্ড বিরতি
    }
  }
}

// -------------------------------------------------------------
// DECODE PATTERN: বাটন ইনপুট মেলাবে, অডিও বাজাবে এবং ভাইব্রেট করবে
// -------------------------------------------------------------
void decodeAndProcessChord() {
  byte typedPattern = 0;
  bool isBlank = true;

  for (int i = 0; i < 6; i++) {
    if (activeChord[i]) {
      typedPattern |= (1 << i);
      isBlank = false;
    }
  }

  if (isBlank) {
    Serial.println("Space input detected.");
    typedMessage += " ";
    pendingPrefix = 0; 
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

  // ✅ MATCH FOUND: Speak -> Vibrate 
  if (matchedIndex != -1) {
    int trackNum = matchedIndex + 1;
    Serial.println("========================================");
    Serial.printf("SUCCESS! Decoded Letter: %s\n", LETTER_NAMES[matchedIndex]);
    
    typedMessage += LETTER_NAMES[matchedIndex];

    // ১. প্রথমে স্পিকার উচ্চারণ করবে (Speaker Speaks)
    dfPlayer.play(trackNum);
    
    // অডিও প্লে শুরু হওয়ার জন্য ১ সেকেন্ড সময় দেওয়া হলো
    delay(1000); 

    // ২. তারপর মোটরগুলো সিকোয়েন্স অনুযায়ী ভাইব্রেট করবে (Motors Vibrate)
    vibrateBrailleDotsSequential(typedPattern);
    
    Serial.println("========================================");

  } else {
    Serial.println("❌ Unknown Braille pattern submitted.");
  }
  
  pendingPrefix = 0; 
  resetChord(); // পরবর্তী ইনপুটের জন্য পুশ বাটনগুলো রিসেট করা
}

// -------------------------------------------------------------
// PRINT MESSAGE
// -------------------------------------------------------------
void handleEnterPress() {
  Serial.println("\n----------------------------------------");
  Serial.print("📝 TYPED MESSAGE: ");
  Serial.println(typedMessage);
  Serial.println("----------------------------------------\n");

  typedMessage = ""; 
  pendingPrefix = 0; 
}