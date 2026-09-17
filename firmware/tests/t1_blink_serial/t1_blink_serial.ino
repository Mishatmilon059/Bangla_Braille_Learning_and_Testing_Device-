#include <Arduino.h>

// --- New Safe Button Input Pins ---
const int buttonPins[6] = {4, 5, 15, 19, 21, 22};
const int submitButtonPin = 23;

// --- Braille Dictionary (A-Z) ---
const byte brailleAlphabet[26] = {
  0b000001, // A: 1
  0b000011, // B: 1,2
  0b001001, // C: 1,4
  0b011001, // D: 1,4,5
  0b010001, // E: 1,5
  0b001011, // F: 1,2,4
  0b011011, // G: 1,2,4,5
  0b010011, // H: 1,2,5
  0b001010, // I: 2,4
  0b011010, // J: 2,4,5
  0b000101, // K: 1,3
  0b000111, // L: 1,2,3
  0b001101, // M: 1,3,4
  0b011101, // N: 1,3,4,5
  0b010101, // O: 1,3,5
  0b001111, // P: 1,2,3,4
  0b011111, // Q: 1,2,3,4,5
  0b010111, // R: 1,2,3,5
  0b001110, // S: 2,3,4
  0b011110, // T: 2,3,4,5
  0b100101, // U: 1,3,6
  0b100111, // V: 1,2,3,6
  0b111010, // W: 2,4,5,6
  0b101101, // X: 1,3,4,6
  0b111101, // Y: 1,3,4,5,6
  0b110101  // Z: 1,3,5,6
};

// State tracking variables
bool activeChord[6] = {false, false, false, false, false, false};
bool lastButtonState[6] = {HIGH, HIGH, HIGH, HIGH, HIGH, HIGH};
bool lastSubmitState = HIGH;

// Forward declaration
void decodeAndPrintChord();

void setup() {
  Serial.begin(115200);
  Serial.println("Button array ready. Tap dots, then press Submit...");

  // Setup dot buttons with internal pull-ups
  for (int i = 0; i < 6; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
  }
  
  // Setup the Submit button
  pinMode(submitButtonPin, INPUT_PULLUP);
}

void loop() {
  // 1. CHECK FOR DOT BUTTON PRESSES
  for (int i = 0; i < 6; i++) {
    bool currentReading = digitalRead(buttonPins[i]);
    
    // Detect when the button is first pressed down (falling edge)
    if (currentReading == LOW && lastButtonState[i] == HIGH) {
      activeChord[i] = !activeChord[i]; // Toggle the dot on or off
      
      Serial.print("Dot "); 
      Serial.print(i + 1);
      Serial.println(activeChord[i] ? " added." : " removed.");
      
      delay(150); // Software debounce to prevent accidental double-clicks
    }
    lastButtonState[i] = currentReading; 
  }

  // 2. CHECK FOR SUBMIT BUTTON
  bool currentSubmitReading = digitalRead(submitButtonPin);
  
  if (currentSubmitReading == LOW && lastSubmitState == HIGH) {
    delay(50); // Debounce
    decodeAndPrintChord();
    delay(200); // Prevent accidental double-submits
  }
  lastSubmitState = currentSubmitReading;
}

// --- Helper Function ---
void decodeAndPrintChord() {
  byte typedPattern = 0;
  bool isBlank = true;
  
  // Reconstruct the 6-bit binary pattern
  for (int i = 0; i < 6; i++) {
    if (activeChord[i]) {
      typedPattern |= (1 << i); 
      isBlank = false;
    }
  }
  
  if (isBlank) {
    Serial.println("Submitted empty cell. Interpreted as space.");
    return;
  }
  
  // Search dictionary
  char foundChar = '?';
  for (int i = 0; i < 26; i++) {
    if (brailleAlphabet[i] == typedPattern) {
      foundChar = 'A' + i;
      break;
    }
  }
  
  if (foundChar != '?') {
    Serial.print("SUCCESS! You typed: ");
    Serial.println(foundChar);
  } else {
    Serial.println("Unknown Braille pattern submitted.");
  }
  
  // Reset the chord array for the next character
  for (int i = 0; i < 6; i++) {
    activeChord[i] = false;
  }
}
