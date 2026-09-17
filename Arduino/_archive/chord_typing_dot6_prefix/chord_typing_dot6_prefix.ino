// ============================================================
//  BANGLA (BENGALI) BRAILLE CHORD INPUT — Full 6-Button + Enter
//  Includes single-cell letters & 2-cell letters (ঋ and ৎ)
// ============================================================

const int buttonPins[6] = {4, 5, 15, 19, 21, 22};
const int submitButtonPin = 18;   
const int enterButtonPin = 23;    

// --- Bangla Braille Dictionary (1-Cell Characters) ---
struct BrailleEntry {
  byte pattern;
  const char* character; 
};

const BrailleEntry banglaBraille[] = {
  // Independent vowels
  {0b000001, "অ"},   // a
  {0b011100, "আ"},   // ā
  {0b001010, "ই"},   // i
  {0b010100, "ঈ"},   // ī
  {0b100101, "উ"},   // u
  {0b110011, "ঊ"},   // ū
  {0b010001, "এ"},   // ē
  {0b001100, "ঐ"},   // ai
  {0b010101, "ও"},   // ō
  {0b101010, "ঔ"},   // au

  // Consonants
  {0b000101, "ক"},   // ka
  {0b101101, "খ"},   // kha
  {0b011011, "গ"},   // ga
  {0b100011, "ঘ"},   // gha
  {0b101100, "ঙ"},   // ṅa
  {0b001001, "চ"},   // ca
  {0b100001, "ছ"},   // cha
  {0b011010, "জ"},   // ja
  {0b110101, "ঝ"},   // jha
  {0b010010, "ঞ"},   // ña
  {0b111110, "ট"},   // ṭa
  {0b111010, "ঠ"},   // ṭha
  {0b101011, "ড"},   // ḍa
  {0b111111, "ঢ"},   // ḍha
  {0b111100, "ণ"},   // ṇa
  {0b011110, "ত"},   // ta
  {0b111001, "থ"},   // tha
  {0b011001, "দ"},   // da
  {0b101110, "ধ"},   // dha
  {0b011101, "ন"},   // na
  {0b001111, "প"},   // pa
  {0b001011, "ফ"},   // pha
  {0b000011, "ব"},   // ba
  {0b100111, "ভ"},   // bha
  {0b001101, "ম"},   // ma
  {0b111101, "য"},   // ya
  {0b010111, "র"},   // ra
  {0b000111, "ল"},   // la
  {0b101001, "শ"},   // śa
  {0b101111, "ষ"},   // ṣa
  {0b001110, "স"},   // sa
  {0b010011, "হ"},   // ha
  {0b111011, "ড়"},   // ɽa
  {0b110111, "ঢ়"},   // ɽha
  {0b100010, "য়"},   // ẏa
  {0b011111, "ক্ষ"}, // kṣa (conjunct)
  {0b110001, "জ্ঞ"}  // jña (conjunct)
};
const int banglaBrailleCount = sizeof(banglaBraille) / sizeof(banglaBraille[0]);

// --- Debounce configuration ---
const unsigned long debounceDelay = 50; 

// --- Core State Variables ---
bool activeChord[6] = {false, false, false, false, false, false};
String typedMessage = "";
byte pendingPrefix = 0; // Memory for 2-cell characters

// --- Debounce Tracking Arrays ---
int lastRawState[6];
int confirmedState[6];
unsigned long lastChangeTime[6];

int lastRawSubmit;
int confirmedSubmit;
unsigned long lastSubmitChangeTime;

int lastRawEnter;
int confirmedEnter;
unsigned long lastEnterChangeTime;

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("Bangla Braille system ready!");
  Serial.println("- Tap dots, then press Submit to decode a letter.");
  Serial.println("- For ঋ: Submit Dot 5, then Submit Dots 1,2,3,5.");
  Serial.println("- For ৎ: Submit Dot 6, then Submit Dots 2,3,4,5.");
  Serial.println("- Press Enter to finish and print the message.");

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
}

void loop() {
  unsigned long now = millis();

  // ---------------- 1. DOT BUTTONS ----------------
  for (int i = 0; i < 6; i++) {
    int reading = digitalRead(buttonPins[i]);

    if (reading != lastRawState[i]) {
      lastChangeTime[i] = now;
      lastRawState[i] = reading;
    }

    if ((now - lastChangeTime[i]) > debounceDelay && reading != confirmedState[i]) {
      confirmedState[i] = reading;

      if (confirmedState[i] == LOW) { // Button was firmly pressed
        activeChord[i] = !activeChord[i];
        
        Serial.print("Dot ");
        Serial.print(i + 1);
        Serial.println(activeChord[i] ? " added." : " removed.");
        Serial.flush();
      }
    }
  }

  // ---------------- 2. SUBMIT BUTTON ----------------
  int submitReading = digitalRead(submitButtonPin);
  if (submitReading != lastRawSubmit) {
    lastSubmitChangeTime = now;
    lastRawSubmit = submitReading;
  }

  if ((now - lastSubmitChangeTime) > debounceDelay && submitReading != confirmedSubmit) {
    confirmedSubmit = submitReading;

    if (confirmedSubmit == LOW) { 
      decodeAndPrintChord();
    }
  }

  // ---------------- 3. ENTER BUTTON ----------------
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
// HELPER FUNCTIONS
// ============================================================

void resetChord() {
  for (int i = 0; i < 6; i++) {
    activeChord[i] = false;
  }
}

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

  // Handle Space (Empty Cell)
  if (isBlank) {
    Serial.println("Submitted empty cell. Interpreted as space.");
    Serial.flush();
    typedMessage += ' ';
    pendingPrefix = 0; // Clear any pending prefix memory
    return;
  }

  // -------------------------------------------------------------
  // STEP 1: Are we waiting for the 2nd half of a 2-cell character?
  // -------------------------------------------------------------
  if (pendingPrefix != 0) {
    const char* foundLetter = nullptr;

    // Evaluate combinations
    if (pendingPrefix == 0b010000 && typedPattern == 0b010111) {
      // Dot 5 followed by Dots 1,2,3,5
      foundLetter = "ঋ";
    } 
    else if (pendingPrefix == 0b100000 && typedPattern == 0b011110) {
      // Dot 6 followed by Dots 2,3,4,5
      foundLetter = "ৎ";
    }

    if (foundLetter != nullptr) {
      Serial.print("SUCCESS! You typed 2-cell char: ");
      Serial.println(foundLetter);
      typedMessage += foundLetter;
    } else {
      Serial.println("Invalid 2-cell combination. Resetting.");
    }
    
    Serial.flush();
    pendingPrefix = 0; // Clear the memory after resolving
    resetChord();
    return;
  }

  // -------------------------------------------------------------
  // STEP 2: Is the current input a prefix for a 2-cell character?
  // -------------------------------------------------------------
  if (typedPattern == 0b010000) { // Dot 5 only
    pendingPrefix = typedPattern;
    Serial.println("Prefix (Dot 5) entered. Submit 2nd cell for 'ঋ'...");
    Serial.flush();
    resetChord();
    return;
  } 
  else if (typedPattern == 0b100000) { // Dot 6 only
    pendingPrefix = typedPattern;
    Serial.println("Prefix (Dot 6) entered. Submit 2nd cell for 'ৎ'...");
    Serial.flush();
    resetChord();
    return;
  }

  // -------------------------------------------------------------
  // STEP 3: Standard 1-cell dictionary search
  // -------------------------------------------------------------
  const char* foundLetter = nullptr;
  for (int i = 0; i < banglaBrailleCount; i++) {
    if (banglaBraille[i].pattern == typedPattern) {
      foundLetter = banglaBraille[i].character;
      break;
    }
  }

  if (foundLetter != nullptr) {
    Serial.print("SUCCESS! You typed: ");
    Serial.println(foundLetter);
    typedMessage += foundLetter;
  } else {
    Serial.println("Unknown Braille pattern submitted.");
  }
  
  Serial.flush();
  resetChord();
}

void handleEnterPress() {
  Serial.println("----------------------------");
  Serial.print("MESSAGE: ");
  Serial.println(typedMessage);
  Serial.println("----------------------------");
  Serial.flush();

  typedMessage = ""; // Clear buffer for the next message
  pendingPrefix = 0; // Clear any stuck prefixes just in case
}