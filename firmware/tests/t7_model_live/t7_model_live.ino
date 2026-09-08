// ============================================================
//  t7 — TRIPLE MODE + live model scoring
//
//  This is p6 (menu / learn / test) with the trained model wired into the
//  test loop, so every answer you give is scored twice: once by the rule
//  engine and once by the network running on the ESP32. Type P for the
//  agreement report.
//
//  READ THIS BEFORE QUOTING ANY NUMBER IT PRINTS
//  ---------------------------------------------
//  The model's training labels came FROM the rule engine below. So the
//  agreement figure measures how faithfully 790 parameters reproduce those
//  rules on real button-press timings -- a legitimate TinyML result, and the
//  honest claim to make. It is NOT accuracy against what a learner actually
//  needed, because nothing here knows that. A disagreement is not
//  automatically the model being wrong; it is the model and the rules
//  differing on one input, and those are the rows worth reading.
//
//  Run t6_model first. If its golden self-test does not pass, everything
//  here is measuring an unknown function. This sketch re-runs that same
//  self-test at boot for exactly that reason, and disables the model if it
//  fails rather than reporting numbers you cannot trust.
// ============================================================

#include <Arduino.h>
#include <DFRobotDFPlayerMini.h>

#include "rule_engine.h"
#include "model_data.h"

#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

const int buttonPins[6]   = {4, 5, 15, 19, 21, 22};
const int submitButtonPin  = 18;
const int enterButtonPin   = 34;
const int PIN_MOTOR[6]    = {13, 14, 26, 27, 32, 33};

#define PIN_DF_ESP_RX 25
#define PIN_DF_ESP_TX 23

HardwareSerial mySoftwareSerial(2);
DFRobotDFPlayerMini dfPlayer;
bool g_df_ok = false;

// Spoken prompt tracks on the SD card. Numbering comes from SYSTEM_PROMPTS in
// tools/gen_audio.py; letters occupy 1..50 and the prompts start at 51.
#define TRK_CORRECT        51   // সঠিক
#define TRK_WRONG          52   // ভুল
#define TRK_TRY_AGAIN      53   // আবার চেষ্টা করুন
#define TRK_HINT           54   // ইঙ্গিত
#define TRK_WELL_DONE      55   // খুব ভালো
#define TRK_SESSION_START  59   // শুরু করা যাক
#define TRK_SESSION_END    60   // অনুশীলন শেষ

// dfPlayer.play() returns the moment the command is sent, not when the audio
// ends. Two consequences, and the second one is the one that bites: back-to-back
// prompts cut each other off, and response_time would include however long the
// prompt took to speak -- which on a ~1.5 s clip is enough on its own to push
// every attempt past the 6000 ms GUESSING threshold.
static void audioPlayBlocking(uint16_t track, uint32_t timeout_ms = 4000) {
  if (!g_df_ok) { delay(250); return; }
  dfPlayer.play(track);
  uint32_t t0 = millis();
  delay(120);
  while (millis() - t0 < timeout_ms) {
    if (dfPlayer.available() && dfPlayer.readType() == DFPlayerPlayFinished) return;
    delay(15);
  }
}

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

// ============================================================
//  MODEL
// ============================================================
namespace {
const tflite::Model *g_model = nullptr;
tflite::MicroInterpreter *g_interpreter = nullptr;
TfLiteTensor *g_input = nullptr;
TfLiteTensor *g_out_conf = nullptr;
TfLiteTensor *g_out_teach = nullptr;
alignas(16) uint8_t g_arena[MODEL_ARENA_SIZE];
bool g_model_ok = false;
}  // namespace

static void model_infer(const float *norm, uint8_t *teaching, uint8_t *confidence) {
  for (int i = 0; i < FEATURE_COUNT; i++) {
    int32_t q = (int32_t)lroundf(norm[i] / MODEL_INPUT_SCALE) + MODEL_INPUT_ZERO_POINT;
    q = q < -128 ? -128 : (q > 127 ? 127 : q);
    g_input->data.int8[i] = (int8_t)q;
  }
  g_interpreter->Invoke();
  int b = 0;
  for (int i = 1; i < MODEL_TEACH_CLASSES; i++)
    if (g_out_teach->data.int8[i] > g_out_teach->data.int8[b]) b = i;
  *teaching = (uint8_t)b;
  b = 0;
  for (int i = 1; i < MODEL_CONF_CLASSES; i++)
    if (g_out_conf->data.int8[i] > g_out_conf->data.int8[b]) b = i;
  *confidence = (uint8_t)b;
}

static bool model_begin() {
  g_model = tflite::GetModel(MODEL_DATA);
  if (g_model->version() != TFLITE_SCHEMA_VERSION) {
    Serial.printf("  schema %lu != %d -- regenerate model_data.h\n",
                  (unsigned long)g_model->version(), TFLITE_SCHEMA_VERSION);
    return false;
  }
  // Four kernels, not AllOpsResolver: linking ~80 unused ones costs flash and
  // buys nothing.
  static tflite::MicroMutableOpResolver<4> resolver;
  resolver.AddFullyConnected();
  resolver.AddSoftmax();
  resolver.AddQuantize();
  resolver.AddDequantize();

  static tflite::MicroErrorReporter micro_error_reporter;
  static tflite::MicroInterpreter iface(g_model, resolver, g_arena, sizeof(g_arena),
                                        &micro_error_reporter);
  g_interpreter = &iface;
  if (g_interpreter->AllocateTensors() != kTfLiteOk) {
    Serial.println("  AllocateTensors failed -- raise MODEL_ARENA_SIZE");
    return false;
  }
  g_input = g_interpreter->input(0);
  // Head positions come from model_data.h, resolved from the flatbuffer
  // signature when the header was generated. Matching by class count would
  // bind the same tensor twice -- both heads are 3 wide.
  g_out_conf  = g_interpreter->output(MODEL_CONF_OUTPUT_INDEX);
  g_out_teach = g_interpreter->output(MODEL_TEACH_OUTPUT_INDEX);
  if (!g_input || !g_out_conf || !g_out_teach) {
    Serial.println("  could not bind model outputs");
    return false;
  }
  return true;
}

// The same check t6_model runs.
static bool model_self_test() {
  int fails = 0;
  for (int i = 0; i < GOLDEN_VECTOR_COUNT; i++) {
    uint8_t ta, cs;
    model_infer(GOLDEN_VECTORS[i].features_norm, &ta, &cs);
    if (ta != GOLDEN_VECTORS[i].expect_teaching ||
        cs != GOLDEN_VECTORS[i].expect_confidence) fails++;
  }
  Serial.printf("  golden self-test: %d/%d passed\n",
                GOLDEN_VECTOR_COUNT - fails, GOLDEN_VECTOR_COUNT);
  return fails == 0;
}

// ============================================================
//  LIVE SCORING STATE
// ============================================================

// Per-character history, so retry_count and wrong_streak mean on the device
// what they meant during training.
int  wrongStreak[50];
int  attemptsOnChar   = 0;   // becomes retry_count for the attempt in flight
int  currentDrillChar = -1;

// Timing for the attempt in flight.
unsigned long promptEndMs   = 0;
unsigned long holdTotalMs   = 0;
uint8_t       holdSamples   = 0;
unsigned long pressStartMs[6];

// Agreement tallies. Rows = rule engine, columns = model.
int  nAttempts = 0;
int  taAgree = 0, csAgree = 0;
int  taMatrix[3][3];
int  csMatrix[3][3];
unsigned long inferTotalUs = 0;

void showMenu();
void showLearnPrompt();
void showTestPrompt();
void runLearn(int index);
void runTestQuestion(int index);
void checkTestAnswer(byte typedPattern);
void resetChord();
void vibrateBrailleDotsSequential(uint8_t pattern);
void printDotPattern(uint8_t pattern);
void printPerformanceReport();

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
    pressStartMs[i]   = 0;
  }
  pinMode(submitButtonPin, INPUT_PULLUP);
  lastRawSubmit        = digitalRead(submitButtonPin);
  confirmedSubmit      = lastRawSubmit;
  lastSubmitChangeTime = millis();

  pinMode(enterButtonPin, INPUT);
  lastRawEnter        = digitalRead(enterButtonPin);
  confirmedEnter      = lastRawEnter;
  lastEnterChangeTime = millis();

  for (int i = 0; i < 50; i++) wrongStreak[i] = 0;
  for (int i = 0; i < 3; i++)
    for (int j = 0; j < 3; j++) { taMatrix[i][j] = 0; csMatrix[i][j] = 0; }

  mySoftwareSerial.begin(9600, SERIAL_8N1, PIN_DF_ESP_RX, PIN_DF_ESP_TX);
  delay(1000);

  Serial.println("\n==========================================");
  Serial.println("  BANGLA BRAILLE SYSTEM + MODEL SCORING");
  Serial.println("==========================================");
  Serial.print("DFPlayer: ");
  if (!dfPlayer.begin(mySoftwareSerial, false, true)) {
    Serial.println("FAILED - check wiring!");
  } else {
    Serial.println("OK");
    g_df_ok = true;
    dfPlayer.volume(30);
  }

  Serial.printf("Model   : %u bytes, spec v%d\n", (unsigned)MODEL_DATA_LEN, SPEC_VERSION);
  g_model_ok = model_begin();
  if (g_model_ok) {
    Serial.printf("  arena used %u of %u bytes\n",
                  (unsigned)g_interpreter->arena_used_bytes(), (unsigned)sizeof(g_arena));
    if (!model_self_test()) {
      Serial.println("  >>> GOLDEN TEST FAILED. Scoring the model against the");
      Serial.println("      rules would be meaningless. Rule engine only.");
      g_model_ok = false;
    } else {
      uint8_t ta, cs;
      unsigned long t0 = micros();
      for (int i = 0; i < 100; i++) model_infer(GOLDEN_VECTORS[0].features_norm, &ta, &cs);
      Serial.printf("  inference: %lu us per call\n",
                    (unsigned long)((micros() - t0) / 100));
    }
  }
  if (!g_model_ok) Serial.println("  MODEL DISABLED -- rule engine only.");

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
        audioPlayBlocking(TRK_SESSION_START);   // শুরু করা যাক
        showTestPrompt();
      } else if (c == 'P' || c == 'p') {
        printPerformanceReport();
        showMenu();
      } else if (c == '\n' || c == '\r' || c == ' ') {
      } else {
        Serial.println("Invalid. Type L for Learn, T for Test, P for model report.");
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
        audioPlayBlocking(TRK_SESSION_END);   // অনুশীলন শেষ
        printPerformanceReport();
        showMenu();
      } else if (input == "P" || input == "p") {
        printPerformanceReport();
        showTestPrompt();
      } else {
        int val = input.toInt();
        if (val >= 1 && val <= 50) {
          runTestQuestion(val - 1);
        } else {
          Serial.println("Enter 1-50, P for report, or M for menu.");
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
        // Press: start the hold timer, then toggle exactly as before.
        pressStartMs[i] = now;
        activeChord[i] = !activeChord[i];
        Serial.print("Dot "); Serial.print(i + 1);
        Serial.println(activeChord[i] ? " selected." : " removed.");
      } else if (pressStartMs[i]) {
        // Release: press_duration is the mean hold time over this attempt.
        holdTotalMs += (now - pressStartMs[i]);
        holdSamples++;
        pressStartMs[i] = 0;
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
      audioPlayBlocking(TRK_SESSION_END);   // অনুশীলন শেষ
      printPerformanceReport();
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
  Serial.println("  Type  P  -> Model agreement report");
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
  Serial.println("   Re-enter the SAME number after a miss -- that is what");
  Serial.println("   drives retry_count and wrong_streak, and those are the");
  Serial.println("   features the teaching head actually keys on.");
  Serial.println("   Type P for the report, M to return to menu.");
  Serial.print("   Enter number: ");
}

void runLearn(int index) {
  Serial.println("\n----------------------------------------");
  Serial.printf("  LEARNING: [%d] %s\n", index + 1, LETTER_NAMES[index]);
  Serial.print("  Braille dots: ");
  printDotPattern(BRAILLE_PATTERN[index]);
  Serial.println("----------------------------------------");
  audioPlayBlocking(index + 1);
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

  // A different character is a fresh prompt, so retries start over.
  if (index != currentDrillChar) {
    currentDrillChar = index;
    attemptsOnChar   = 0;
  }
  holdTotalMs = 0;
  holdSamples = 0;
  for (int i = 0; i < 6; i++) pressStartMs[i] = 0;

  Serial.println("\n========================================");
  Serial.printf("  QUESTION: Braille pattern for [%d] %s ?\n", index + 1, LETTER_NAMES[index]);
  Serial.println("  Listen to speaker, then press dots + SUBMIT.");
  Serial.println("========================================");
  // Blocking, then start the clock: response_time runs from the END of the
  // prompt to the SUBMIT press, the same span train.py measured. Timing from
  // the start of playback would charge the learner for the audio.
  audioPlayBlocking(index + 1);
  promptEndMs = millis();
}

void checkTestAnswer(byte typedPattern) {
  if (testTargetIndex < 0) return;
  int     index          = testTargetIndex;
  uint8_t correctPattern = BRAILLE_PATTERN[index];
  bool    correct        = (typedPattern == correctPattern);

  unsigned long submitMs = millis();
  double responseTime = (double)(submitMs - promptEndMs);
  if (responseTime < 0) responseTime = 0;

  // Any dot still held down at SUBMIT still counts toward the mean hold time.
  unsigned long total = holdTotalMs;
  uint8_t       n     = holdSamples;
  for (int i = 0; i < 6; i++) {
    if (pressStartMs[i]) { total += (submitMs - pressStartMs[i]); n++; }
  }
  double pressDuration = (n == 0) ? 0.0 : (double)total / (double)n;

  int retryCount = attemptsOnChar;

  // Score the attempt, THEN read the streak: every field the rule engine sees
  // is the state after the current attempt has been scored.
  if (correct) { testCorrect++; wrongStreak[index] = 0; }
  else         { testWrong++;   wrongStreak[index]++; }

  // Only four of these feed the model (response_time, press_duration,
  // retry_count, wrong_streak). The rest are the logging schema; they are
  // filled with neutral values here because this sketch keeps no session
  // history on an SD card.
  Features f;
  f.char_id                  = (double)index;
  f.response_time            = responseTime;
  f.press_duration           = pressDuration;
  f.retry_count              = (double)retryCount;
  f.prev_accuracy            = 0.0;
  f.prev_mastery             = 0.0;
  f.hint_count               = 0.0;
  f.session_number           = 1.0;
  f.difficulty_level         = 1.0;
  f.time_since_last_practice = 0.0;
  f.prev_confidence          = 0.0;
  f.current_streak           = correct ? 1.0 : 0.0;
  f.wrong_streak             = (double)wrongStreak[index];
  f.prev_mistakes            = 0.0;

  uint8_t taRule = (uint8_t)evaluate_teaching_action(&f);
  uint8_t csRule = (uint8_t)evaluate_confidence(&f);

  // Whoever decided is who the learner hears. With the model live this is the
  // point of the whole build: the network picks what comes out of the speaker.
  uint8_t action = taRule;

  Serial.println("\n----------------------------------------");
  Serial.printf("  Character : %s\n", LETTER_NAMES[index]);
  Serial.print("  Your dots : "); printDotPattern(typedPattern);
  Serial.print("  Correct   : "); printDotPattern(correctPattern);
  Serial.println(correct ? "  RESULT    : CORRECT!" : "  RESULT    : WRONG!");
  Serial.printf("  Score -> Correct: %d | Wrong: %d\n", testCorrect, testWrong);

  Serial.println("  --- model input (the 4 features) ---");
  Serial.printf("  response_time  %.0f ms\n", f.response_time);
  Serial.printf("  press_duration %.0f ms\n", f.press_duration);
  Serial.printf("  retry_count    %d\n", retryCount);
  Serial.printf("  wrong_streak   %d\n", wrongStreak[index]);

  if (g_model_ok) {
    float norm[FEATURE_COUNT];
    normalize_features(&f, norm);
    uint8_t taModel, csModel;
    unsigned long t0 = micros();
    model_infer(norm, &taModel, &csModel);
    inferTotalUs += (micros() - t0);

    action = taModel;
    bool taOk = (taModel == taRule);
    bool csOk = (csModel == csRule);
    nAttempts++;
    if (taOk) taAgree++;
    if (csOk) csAgree++;
    taMatrix[taRule][taModel]++;
    csMatrix[csRule][csModel]++;

    Serial.println("  --- decision ---");
    Serial.printf("  teaching   rules=%-16s model=%-16s %s\n",
                  TEACHING_ACTION_NAMES[taRule], TEACHING_ACTION_NAMES[taModel],
                  taOk ? "agree" : "DIFFER");
    Serial.printf("  confidence rules=%-16s model=%-16s %s\n",
                  CONFIDENCE_STATE_NAMES[csRule], CONFIDENCE_STATE_NAMES[csModel],
                  csOk ? "agree" : "DIFFER");
    Serial.printf("  running agreement: teaching %d/%d  confidence %d/%d\n",
                  taAgree, nAttempts, csAgree, nAttempts);
  } else {
    Serial.println("  --- decision (rule engine only, model disabled) ---");
    Serial.printf("  teaching   %s\n", TEACHING_ACTION_NAMES[taRule]);
    Serial.printf("  confidence %s\n", CONFIDENCE_STATE_NAMES[csRule]);
  }
  Serial.println("----------------------------------------");

  // --- speak the result, then act on the decision -------------------------
  Serial.printf("  audio: %s\n", correct ? "51 sothik" : "52 vul");
  audioPlayBlocking(correct ? TRK_CORRECT : TRK_WRONG);

  switch (action) {
    case TA_REPEAT:
      Serial.println("  audio: 53 abar chesta korun");
      audioPlayBlocking(TRK_TRY_AGAIN);
      break;
    case TA_HINT:
      // The word "hint" alone is not a hint. Buzzing the right pattern is.
      Serial.println("  audio: 54 ingit  + vibrate the correct pattern");
      audioPlayBlocking(TRK_HINT);
      vibrateBrailleDotsSequential(correctPattern);
      break;
    case TA_NORMAL_PRACTICE:
      if (correct) {
        Serial.println("  audio: 55 khub bhalo");
        audioPlayBlocking(TRK_WELL_DONE);
      }
      break;
  }

  attemptsOnChar++;
  if (correct) { currentDrillChar = -1; attemptsOnChar = 0; }

  waitingForButtonInput = false;
  testTargetIndex       = -1;
  showTestPrompt();
}

static void printMatrix(const char *title, int m[3][3], const char **names) {
  Serial.printf("\n  %s   (rows = rule engine, cols = model)\n", title);
  Serial.printf("  %-18s", "");
  for (int j = 0; j < 3; j++) Serial.printf("%10s", names[j]);
  Serial.println();
  for (int i = 0; i < 3; i++) {
    Serial.printf("  %-18s", names[i]);
    for (int j = 0; j < 3; j++) Serial.printf("%10d", m[i][j]);
    Serial.println();
  }
}

void printPerformanceReport() {
  Serial.println("\n==========================================");
  Serial.println("  MODEL vs RULE ENGINE");
  Serial.println("==========================================");
  if (!g_model_ok) {
    Serial.println("  Model disabled -- nothing to report.");
    Serial.println("==========================================");
    return;
  }
  if (nAttempts == 0) {
    Serial.println("  No attempts scored yet. Run Test Mode first.");
    Serial.println("==========================================");
    return;
  }
  Serial.printf("  attempts scored : %d\n", nAttempts);
  Serial.printf("  teaching agree  : %d/%d  (%.1f%%)\n",
                taAgree, nAttempts, 100.0 * taAgree / nAttempts);
  Serial.printf("  confidence agree: %d/%d  (%.1f%%)\n",
                csAgree, nAttempts, 100.0 * csAgree / nAttempts);
  Serial.printf("  mean inference  : %lu us\n",
                (unsigned long)(inferTotalUs / (unsigned long)nAttempts));
  printMatrix("TEACHING ACTION", taMatrix, TEACHING_ACTION_NAMES);
  printMatrix("CONFIDENCE STATE", csMatrix, CONFIDENCE_STATE_NAMES);
  Serial.println("\n  The model was TRAINED on these rules, so agreement is a");
  Serial.println("  fidelity measure, not accuracy against a real learner's");
  Serial.println("  needs. The off-diagonal cells are the interesting ones.");
  Serial.println("==========================================");
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
