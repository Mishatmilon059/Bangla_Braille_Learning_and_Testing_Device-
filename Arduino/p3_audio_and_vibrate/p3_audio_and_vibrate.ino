// ============================================================
//  p3 — AUDIO + MOTORS: speak a letter, then vibrate its dots
// ============================================================
// Proves: DFPlayer Mini plays the right track AND the motors
// replay the same character's dots. Still no buttons.
//
// Use: Serial Monitor at 115200, type a number 1-50, Enter.
// Expect: the speaker names the letter, then after ~1 s each
// raised dot buzzes 400 ms with a 1 s gap.
//
// SD card: tracks must be /mp3/0001.mp3 .. /mp3/0050.mp3, where
// track N is letter N in the 50-letter table below.
//
// Pins (as built on the bench):
//   motors      GPIO 13, 14, 26, 27, 32, 33   (dots 1..6)
//   DFPlayer RX GPIO 25  <- DFPlayer TX
//   DFPlayer TX GPIO 23  -> DFPlayer RX, through 1k in series
//
// KNOWN BUG: dfPlayer.volume(50) is out of range. The DFPlayer
// accepts 0-30; p5/p6 use 30. Left unchanged so this sketch still
// reproduces what was on the bench.
// ============================================================

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

// --- DFPlayer Pin Configuration ---
#define PIN_DF_RX 25   // DFPlayer Pin 3 (TX) এখানে আসবে
#define PIN_DF_TX 23   // ESP32 GPIO 23 থেকে 1kΩ রেজিস্টর হয়ে DFPlayer Pin 2 (RX) এ যাবে

// --- 6 Braille Dot Vibration Motors Pin Configuration ---
const int PIN_MOTOR[6] = { 13, 14, 26, 27, 32, 33 }; 

HardwareSerial mySoftwareSerial(2); 
DFRobotDFPlayerMini dfPlayer;

// --- বাংলা ব্রেইল ডট প্যাটার্ন (50টি বর্ণ) ---
// bit 0 = Dot 1, bit 1 = Dot 2, bit 2 = Dot 3, bit 3 = Dot 4, bit 4 = Dot 5, bit 5 = Dot 6
const uint8_t BRAILLE_PATTERN[50] = {
  0x01,  //  1: অ  (Dot 1)
  0x1C,  //  2: আ  (Dots 3, 4, 5)
  0x0A,  //  3: ই  (Dots 2, 4)
  0x14,  //  4: ঈ  (Dots 3, 5)
  0x25,  //  5: উ  (Dots 1, 3, 6)
  0x33,  //  6: ঊ  (Dots 1, 2, 5, 6)
  0x17,  //  7: ঋ  (Dots 1, 2, 3, 5)
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
  "অ (o)", "আ (aa)", "ই (i)", "ঈ (ee)", "উ (u)", "ঊ (oo)", "ঋ (ri)", "এ (e)", "ঐ (oi)", "ও (o)", "ঔ (ou)",
  "ক (ka)", "খ (kha)", "গ (ga)", "ঘ (gha)", "ঙ (nga)", "চ (cha)", "ছ (chha)", "জ (ja)", "ঝ (jha)", "ঞ (nya)",
  "ট (tta)", "ঠ (ttha)", "ড (dda)", "ঢ (ddha)", "ণ (nna)", "ত (ta)", "থ (tha)", "দ (da)", "ধ (dha)", "ন (na)",
  "প (pa)", "ফ (pha)", "ব (ba)", "ভ (bha)", "ম (ma)", "য (ya)", "র (ra)", "ল (la)", "শ (sha)", "ষ (ssa)",
  "স (sa)", "হ (ha)", "ড় (rra)", "ঢ় (rha)", "য় (yya)", "ৎ (khanda_ta)", "ং (anushar)", "ঃ (bisharga)", "ঁ (chandrabindu)"
};

// নির্দিষ্ট অক্ষরের ব্রেইল ডটগুলো ১ সেকেন্ড বিরতিতে ভাইব্রেট করানোর ফাংশন
void vibrateBrailleDotsSequential(uint8_t pattern) {
  Serial.print("Active Dots: ");
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      Serial.printf("[Dot %d] ", i + 1);
    }
  }
  Serial.println();

  // প্যাটার্ন চেক করে অ্যাক্টিভ ডটগুলো একটার পর একটা ভাইব্রেট করাবে
  for (int i = 0; i < 6; i++) {
    if (pattern & (1 << i)) {
      Serial.printf("  >> Vibrate Dot %d (GPIO %d) ON\n", i + 1, PIN_MOTOR[i]);
      digitalWrite(PIN_MOTOR[i], HIGH);  // মোটর অন (৪০০ মিলি-সেকেন্ড)
      delay(400);                        
      digitalWrite(PIN_MOTOR[i], LOW);   // মোটর অফ
      
      // ডটগুলোর মাঝে ১ সেকেন্ড বিরতি
      delay(1000);
    }
  }
  Serial.println(">> Vibration Sequence Completed!\n");
}

void playAndVibrate(int letterNum) {
  if (letterNum < 1 || letterNum > 50) {
    Serial.println("⚠️ দয়া করে 1 থেকে 50 এর মধ্যে সংখ্যা ইনপুট দিন!");
    return;
  }

  int index = letterNum - 1;
  Serial.println("========================================");
  Serial.printf("Playing Sound & Vibration for Letter %d: %s\n", letterNum, LETTER_NAMES[index]);

  // DFPlayer এ ট্র্যাক প্লে (SD card এর /mp3/0001.mp3 ইত্যাদি)
  dfPlayer.play(letterNum);
  
  // অডিও শুরু হওয়ার জন্য সামান্য সময় দেওয়া
  delay(1000);

  // ব্রেইল ডট প্যাটার্ন অনুসারে মোটর ভাইব্রেশন শুরু করা
  uint8_t pattern = BRAILLE_PATTERN[index];
  vibrateBrailleDotsSequential(pattern);
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== Bangla Braille Tutor - Final System Ready ===");

  // মোটর পিনগুলো OUTPUT হিসেবে সেট করা এবং অফ রাখা
  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }

  // DFPlayer Serial2 সেটআপ
  mySoftwareSerial.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(500);

  if (!dfPlayer.begin(mySoftwareSerial, true, true)) {
    Serial.println("❌ DFPlayer Mini Init Failed!");
  } else {
    Serial.println("✅ DFPlayer Mini Connected Successfully!");
    dfPlayer.volume(50); // ভলিউম লেভেল (0-30)
  }

  Serial.println("\n➡️ Serial Monitor-এ 1 থেকে 50 লিখে Enter চাপুন (যেমন: 1 = অ, 2 = আ, 12 = ক):");
}

void loop() {
  if (Serial.available() > 0) {
    int inputVal = Serial.parseInt();
    if (inputVal > 0) {
      playAndVibrate(inputVal);
    }
  }
}