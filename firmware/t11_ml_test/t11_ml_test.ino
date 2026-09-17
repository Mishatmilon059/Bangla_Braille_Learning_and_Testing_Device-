// t11_ml_test: Learning module + ML inference comparison
//
// Identical to t10_learning BUT after every attempt it prints:
//   Rule Engine: TA=...  CS=...
//   ML Model:    TA=...  CS=...
//   TA:MATCH/MISMATCH  CS:MATCH/MISMATCH
//
// This lets you see where the neural network agrees or disagrees with the
// hard-coded rule engine -- the interesting cases are the MISMATCHes.
//
// Serial Monitor: 115200 baud

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <DFRobotDFPlayerMini.h>

#include "secrets.h"
#include "pins.h"
#include "hardware.h"
#include "braille_map.h"
#include "rule_engine.h"
#include "model_weights.h"
#include "inference.h"

// ---------------------------------------------------------------------------

#define TRACK_CORRECT  51
#define DOT_ON_MS     500
#define DOT_GAP_MS    500
#define STAGE_GAP_MS  1200
#define POLL_MS       700
#define DEVICE_ID  "esp32_01"

static const char *SUPABASE_URL      = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";

static long     g_last_id   = -1;
static uint32_t g_last_poll = 0;

// ---------------------------------------------------------------------------
// Per-character state (resets on reboot, tracks within-session history)
// ---------------------------------------------------------------------------

struct CharState {
  double accuracy;        // correct_count / total_attempts
  double mastery;         // EMA mastery (spec: alpha_correct=0.25, alpha_wrong=0.35)
  double current_streak;  // consecutive correct (post-attempt)
  double wrong_streak;    // consecutive wrong   (post-attempt)
  double prev_confidence; // last ML confidence state output
  int    total_attempts;
  int    correct_count;
};
static CharState char_state[BRAILLE_LETTER_COUNT]; // zeroed in setup()

// ---------------------------------------------------------------------------
// ML comparison -- called after EVERY attempt (wrong or correct)
// ---------------------------------------------------------------------------

static void log_ml_comparison(int letter_id, uint32_t rt_ms,
                               int retry_count, bool is_correct) {
  CharState &st = char_state[letter_id];

  // Update streaks (must be post-attempt, per spec)
  if (is_correct) {
    st.current_streak += 1.0;
    st.wrong_streak    = 0.0;
  } else {
    st.wrong_streak   += 1.0;
    st.current_streak  = 0.0;
  }
  st.total_attempts++;
  if (is_correct) st.correct_count++;
  st.accuracy = (st.total_attempts > 0)
    ? (double)st.correct_count / st.total_attempts : 0.0;
  st.mastery = update_mastery(st.mastery, is_correct ? 1 : 0);

  // Build full Features struct
  Features f;
  f.char_id                  = (double)letter_id;
  f.response_time            = (double)rt_ms;
  f.press_duration           = 200.0;  // not measured in learning mode; under CONFIDENT threshold
  f.retry_count              = (double)retry_count;
  f.prev_accuracy            = st.accuracy;
  f.prev_mastery             = st.mastery;
  f.hint_count               = 0.0;    // no hint button in learning mode
  f.session_number           = 1.0;
  f.difficulty_level         = 1.0;
  f.time_since_last_practice = 0.0;
  f.prev_confidence          = st.prev_confidence;
  f.current_streak           = st.current_streak;
  f.wrong_streak             = st.wrong_streak;
  f.prev_mistakes            = (double)(st.total_attempts - st.correct_count);

  // Rule engine (hard-coded rules, deterministic)
  int rule_ta = (int)evaluate_teaching_action(&f);
  int rule_cs = (int)evaluate_confidence(&f);

  // ML model (neural network forward pass, ~0.1ms)
  int ml_ta, ml_cs;
  ml_infer(&f, &ml_ta, &ml_cs);

  // Save CS output for next attempt's prev_confidence
  st.prev_confidence = (double)ml_cs;

  // Print side-by-side comparison
  bool ta_match = (rule_ta == ml_ta);
  bool cs_match = (rule_cs == ml_cs);

  Serial.printf("  +-- ML vs Rule Engine (letter=%d rt=%ums retry=%d %s)\n",
                letter_id, (unsigned)rt_ms, retry_count,
                is_correct ? "CORRECT" : "WRONG");
  Serial.printf("  | Rule Engine: TA=%-16s CS=%s\n",
                TEACHING_ACTION_NAMES[rule_ta], CONFIDENCE_STATE_NAMES[rule_cs]);
  Serial.printf("  | ML Model:    TA=%-16s CS=%s\n",
                TEACHING_ACTION_NAMES[ml_ta], CONFIDENCE_STATE_NAMES[ml_cs]);
  Serial.printf("  | TA:%-8s  CS:%-8s  streak c=%d w=%d  acc=%.2f mastery=%.2f\n",
                ta_match ? "MATCH" : "MISMATCH",
                cs_match ? "MATCH" : "MISMATCH",
                (int)st.current_streak, (int)st.wrong_streak,
                st.accuracy, st.mastery);
  Serial.printf("  +--\n");
}

// ---------------------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------------------

static void wifi_connect() {
  WiFi.disconnect(true, true);
  delay(200);
  Serial.printf("\nConnecting to WiFi \"%s\"", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(400); Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("\nConnected. IP: %s\n", WiFi.localIP().toString().c_str());
  else
    Serial.println("\nWiFi failed -- will retry.");
}

// ---------------------------------------------------------------------------
// Supabase: skip all rows that existed before boot
// ---------------------------------------------------------------------------

static void sync_latest_id() {
  for (int attempt = 1; attempt <= 3; attempt++) {
    if (WiFi.status() != WL_CONNECTED) wifi_connect();
    delay(300);
    WiFiClientSecure client; client.setInsecure();
    HTTPClient http;
    http.begin(client, String(SUPABASE_URL) +
      "/rest/v1/remote_commands?order=id.desc&limit=1&select=id");
    http.addHeader("apikey",        SUPABASE_ANON_KEY);
    http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
    int code = http.GET();
    String body = http.getString();
    http.end();
    Serial.printf("[sync] attempt %d: HTTP %d  body: %s\n", attempt, code, body.c_str());
    if (code == 200) {
      int pos = body.indexOf("\"id\":");
      g_last_id = (pos >= 0) ? body.substring(pos + 5).toInt() : 0;
      Serial.printf("[sync] OK -- ignoring rows up to id=%ld\n", g_last_id);
      return;
    }
    delay(1000);
  }
  Serial.println("[sync] FAILED -- no commands will be accepted.");
  g_last_id = 2147483647L;
}

// ---------------------------------------------------------------------------
// Supabase poll -- returns letter_id (0-49) or -1
// ---------------------------------------------------------------------------

static int poll_supabase() {
  if (WiFi.status() != WL_CONNECTED) { wifi_connect(); return -1; }
  WiFiClientSecure client; client.setInsecure();
  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/remote_commands"
    + "?device_id=eq." + DEVICE_ID
    + "&id=gt."        + String(g_last_id)
    + "&order=id.asc&limit=1&select=id,letter_id";
  http.begin(client, url);
  http.addHeader("apikey",        SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
  int letter_id = -1;
  int code = http.GET();
  if (code == 200) {
    String body = http.getString();
    int id_pos = body.indexOf("\"id\":");
    if (id_pos >= 0) {
      long id = body.substring(id_pos + 5).toInt();
      int lid_pos = body.indexOf("\"letter_id\":");
      if (lid_pos >= 0) {
        String after = body.substring(lid_pos + 12);
        if (!after.startsWith("null")) letter_id = (int)after.toInt();
      }
      g_last_id = id;
    }
  } else if (code > 0) {
    Serial.printf("[poll] HTTP %d\n", code);
  }
  http.end();
  return letter_id;
}

// ---------------------------------------------------------------------------
// Audio
// ---------------------------------------------------------------------------

static void play_and_wait(int track, uint32_t timeout_ms = 7000) {
  if (!g_df_ok) { delay(300); return; }
  Serial.printf("  [audio] track %d ...\n", track);
  g_df.play(track);
  delay(300);
  uint32_t t0 = millis();
  while (millis() - t0 < timeout_ms) {
    if (g_df.available() && g_df.readType() == DFPlayerPlayFinished) {
      Serial.println("  [audio] done."); return;
    }
    delay(20);
  }
  Serial.println("  [audio] timeout.");
}

// ---------------------------------------------------------------------------
// Buttons
// ---------------------------------------------------------------------------

static void wait_release_all() {
  uint32_t start = millis(), last_report = 0;
  for (;;) {
    buttons_poll();
    bool submit_down = (digitalRead(PIN_SUBMIT) == LOW);
    if (!buttons_any_held() && !submit_down) return;
    uint32_t elapsed = millis() - start;
    if (elapsed - last_report >= 2000) {
      last_report = elapsed;
      Serial.print("[learn] waiting for release -- still held: ");
      for (int i = 0; i < 6; i++)
        if (g_btn.stable[i]) Serial.printf("dot%d(GPIO%d) ", i + 1, PIN_BUTTON[i]);
      if (submit_down) Serial.printf("SUBMIT(GPIO%d) ", PIN_SUBMIT);
      Serial.println(" -- check wiring if this doesn't clear.");
    }
    delay(5);
  }
}

static void print_dot_bits(uint8_t mask) {
  for (int i = 0; i < 6; i++) Serial.printf("dot%d=%d ", i + 1, (mask >> i) & 1);
}

// Returns dot mask; writes time-from-call-to-submit into *out_rt_ms if non-null.
static uint8_t wait_for_submit(uint32_t *out_rt_ms = nullptr) {
  wait_release_all();
  buttons_reset_attempt();
  Serial.println("[learn] Waiting for dot buttons + SUBMIT...");
  uint32_t t0 = millis();
  for (;;) {
    buttons_poll();
    if (submit_pressed()) {
      if (out_rt_ms) *out_rt_ms = millis() - t0;
      Serial.print("[learn] raw at submit: ");
      print_dot_bits(g_btn.mask);
      Serial.printf(" (mask=0x%02X)\n", g_btn.mask);
      return g_btn.mask;
    }
    delay(5);
  }
}

// ---------------------------------------------------------------------------
// Two-stage characters
// ---------------------------------------------------------------------------

struct TwoStageEntry { int id; uint8_t s1; uint8_t s2; };
static const TwoStageEntry TWO_STAGE_CHARS[] = {
  {  6, 0x10, 0x17 },   // ঋ
  { 46, 0x10, 0x1E },   // ৎ
};
static const int TWO_STAGE_COUNT = sizeof(TWO_STAGE_CHARS) / sizeof(TWO_STAGE_CHARS[0]);

static bool get_two_stage(int letter_id, uint8_t &s1, uint8_t &s2) {
  for (int i = 0; i < TWO_STAGE_COUNT; i++) {
    if (TWO_STAGE_CHARS[i].id == letter_id) {
      s1 = TWO_STAGE_CHARS[i].s1; s2 = TWO_STAGE_CHARS[i].s2; return true;
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Learning round (t10 logic + ML logging after every attempt)
// ---------------------------------------------------------------------------

static void learning_round(int letter_id) {
  if (letter_id < 0 || letter_id >= BRAILLE_LETTER_COUNT) {
    Serial.printf("[learn] letter_id %d out of range -- ignored.\n", letter_id);
    return;
  }

  int track = letter_id + 1;
  uint8_t s1, s2;
  bool two_stage = get_two_stage(letter_id, s1, s2);

  Serial.printf("\n==============================\n");

  if (two_stage) {
    Serial.printf("[learn] Letter #%d (TWO-STAGE) track=%d  s1=0x%02X s2=0x%02X\n",
                  letter_id, track, s1, s2);
    Serial.printf("==============================\n");
    int retry_count = 0;

    for (;;) {
      play_and_wait(track, 7000);
      motors_show_sequential(s1, DOT_ON_MS, DOT_GAP_MS);
      delay(STAGE_GAP_MS);
      motors_show_sequential(s2, DOT_ON_MS, DOT_GAP_MS);
      delay(1300);

      // Stage 1 input
      uint32_t rt1;
      uint8_t in1 = wait_for_submit(&rt1);
      bool ok1 = (in1 == s1);
      Serial.printf("[learn] stage1: 0x%02X vs 0x%02X -> %s\n", in1, s1, ok1 ? "OK" : "WRONG");
      if (!ok1) {
        log_ml_comparison(letter_id, rt1, retry_count, false);
        retry_count++; delay(300); continue;
      }

      // Stage 2 input
      uint32_t rt2;
      uint8_t in2 = wait_for_submit(&rt2);
      bool ok2 = (in2 == s2);
      Serial.printf("[learn] stage2: 0x%02X vs 0x%02X -> %s\n", in2, s2, ok2 ? "OK" : "WRONG");
      // Log with average of both stage response times
      log_ml_comparison(letter_id, (rt1 + rt2) / 2, retry_count, ok2);
      if (!ok2) { retry_count++; delay(300); continue; }
      break;
    }

  } else {
    uint8_t expected = BRAILLE_PATTERN[letter_id];
    Serial.printf("[learn] Letter #%d track=%d  dots=0x%02X\n", letter_id, track, expected);
    Serial.printf("==============================\n");
    int retry_count = 0;

    for (;;) {
      play_and_wait(track, 7000);
      motors_show_sequential(expected, DOT_ON_MS, DOT_GAP_MS);
      delay(800);

      uint32_t rt_ms;
      uint8_t entered = wait_for_submit(&rt_ms);
      bool correct = (entered == expected);
      Serial.printf("[learn] entered=0x%02X expected=0x%02X -> %s  rt=%ums\n",
                    entered, expected, correct ? "CORRECT" : "WRONG", (unsigned)rt_ms);

      log_ml_comparison(letter_id, rt_ms, retry_count, correct);
      if (correct) break;
      retry_count++;
      delay(400);
    }
  }

  Serial.println("[learn] Correct! Playing success cue.");
  play_and_wait(TRACK_CORRECT, 4000);
  Serial.println("\n[learn] Round done.\n");
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n===================================");
  Serial.println("  t11: Learning + ML Comparison    ");
  Serial.println("===================================");

  memset(char_state, 0, sizeof(char_state));

  motors_begin();
  Serial.println("[init] Motors OK.");

  buttons_begin();
  submit_begin();
  Serial.println("[init] Buttons OK.");

  Serial2.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(500);
  g_df_ok = g_df.begin(Serial2, true, true);
  if (g_df_ok) {
    g_df.volume(30);
    Serial.printf("[init] DFPlayer OK -- %d files on card.\n", g_df.readFileCounts());
  } else {
    Serial.println("[init] DFPlayer NOT found -- audio will be skipped.");
  }

  WiFi.persistent(false);
  wifi_connect();
  sync_latest_id();

  Serial.println("\n[ready] Select a letter on remote_control.html to begin.\n");
}

void loop() {
  if (millis() - g_last_poll >= POLL_MS) {
    g_last_poll = millis();
    int letter_id = poll_supabase();
    if (letter_id >= 0) learning_round(letter_id);
  }
}
