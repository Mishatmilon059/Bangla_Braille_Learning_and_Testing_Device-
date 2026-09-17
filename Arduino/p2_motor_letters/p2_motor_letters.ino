// ============================================================
//  p2 — MOTORS ONLY: play one letter's dots on demand
// ============================================================
// Proves: all six vibration motors fire, one dot at a time, in
// the right order for a given character. No buttons, no audio.
//
// Use: open Serial Monitor at 115200, type a number 1-37, Enter.
// Expect: each raised dot of that letter buzzes for 400 ms with a
// 1 s gap, and the fired dot numbers are printed as they go.
//
// Pins (as built on the bench):
//   motors  GPIO 13, 14, 26, 27, 32, 33   (dots 1..6, via ULN2803A)
//
// CAUTION: this sketch carries its own 37-letter dictionary, and
// three of its codes disagree with the canonical 50-letter table
// used by p3/p5/p6 and by firmware/braille_tutor/braille_map.h:
//   খ 0x2D here vs 0x28 canonical
//   ঝ 0x35 here vs 0x34 canonical
//   ভ 0x27 here vs 0x18 canonical
// Trust the canonical table; this one is kept as-is for bench
// comparison only.
// ============================================================

// Motor output pins (Left side of ESP32)
const int motorPins[6] = {13, 14, 26, 27, 32, 33};

// --- Bangla Braille Dictionary (1-Cell Characters) ---
struct BrailleEntry {
  byte pattern;
  const char* character; 
};

// Total 37 single-cell characters
const BrailleEntry banglaBraille[] = {
  {0b000001, "অ"},   // 1  (Dot 1)
  {0b011100, "আ"},   // 2  (Dots 3,4,5)
  {0b001010, "ই"},   // 3  (Dots 2,4)
  {0b010100, "ঈ"},   // 4  (Dots 3,5)
  {0b100101, "উ"},   // 5  (Dots 1,3,6)
  {0b110011, "ঊ"},   // 6  (Dots 1,2,5,6)
  {0b010001, "এ"},   // 7  (Dots 1,5)
  {0b001100, "ঐ"},   // 8  (Dots 3,4)
  {0b010101, "ও"},   // 9  (Dots 1,3,5)
  {0b101010, "ঔ"},   // 10 (Dots 2,4,6)
  {0b000101, "ক"},   // 11
  {0b101101, "খ"},   // 12
  {0b011011, "গ"},   // 13
  {0b100011, "ঘ"},   // 14
  {0b101100, "ঙ"},   // 15
  {0b001001, "চ"},   // 16
  {0b100001, "ছ"},   // 17
  {0b011010, "জ"},   // 18
  {0b110101, "ঝ"},   // 19
  {0b010010, "ঞ"},   // 20
  {0b111110, "ট"},   // 21
  {0b111010, "ঠ"},   // 22
  {0b101011, "ড"},   // 23
  {0b111111, "ঢ"},   // 24
  {0b111100, "ণ"},   // 25
  {0b011110, "ত"},   // 26
  {0b111001, "থ"},   // 27
  {0b011001, "দ"},   // 28
  {0b101110, "ধ"},   // 29
  {0b011101, "ন"},   // 30
  {0b001111, "প"},   // 31
  {0b001011, "ফ"},   // 32
  {0b000011, "ব"},   // 33
  {0b100111, "ভ"},   // 34
  {0b001101, "ম"},   // 35
  {0b111101, "য"},   // 36
  {0b010111, "র"}    // 37 
};
const int banglaBrailleCount = sizeof(banglaBraille) / sizeof(banglaBraille[0]);

void setup() {
  Serial.begin(115200);
  delay(300);
  
  Serial.println("==========================================");
  Serial.println(" SINGLE LETTER LEARNING MODE READY!");
  Serial.println("==========================================");
  Serial.println("Type a number (1-37) to feel that specific letter.");
  Serial.println("For example, type '4' to feel ONLY 'ঈ'.");
  Serial.println("==========================================\n");
  
  // Set all motor pins as outputs and ensure they are OFF
  for (int i = 0; i < 6; i++) {
    pinMode(motorPins[i], OUTPUT);
    digitalWrite(motorPins[i], LOW);
  }
}

void loop() {
  if (Serial.available() > 0) {
    int inputNum = Serial.parseInt(); 
    
    if (inputNum > 0) {
      if (inputNum <= banglaBrailleCount) {
        
        // Array index is always 1 less than the typed number (Number 4 is index 3)
        int index = inputNum - 1; 
        byte pattern = banglaBraille[index].pattern;
        
        Serial.print("▶ Playing Letter ");
        Serial.print(inputNum);
        Serial.print(": ");
        Serial.println(banglaBraille[index].character);
        Serial.println("------------------------------------");
        
        // --- DOT BY DOT PLAYBACK FOR ONLY THIS LETTER ---
        for (int dot = 0; dot < 6; dot++) {
          if (pattern & (1 << dot)) {
            Serial.print("  -> Firing Dot ");
            Serial.println(dot + 1);
            
            // Turn on this specific dot
            digitalWrite(motorPins[dot], HIGH);
            delay(400); // Motor vibrates for 400ms 
            digitalWrite(motorPins[dot], LOW);
            
            // Wait exactly 1 second (1000ms) before playing the next dot
            delay(1000); 
          }
        }
        
        Serial.println("⏹ Done! Type another number.\n");
        
      } else {
        Serial.print("Number too high! Please enter a number between 1 and ");
        Serial.println(banglaBrailleCount);
      }
    }
  }
}