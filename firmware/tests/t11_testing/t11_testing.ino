// t11: Testing module
//
// Companion to t10_learning, but for ASSESSMENT rather than teaching. The
// teacher picks N letters in web/teacher.html's "পরীক্ষা" (Test) tab; this
// sketch plays each one's audio -- NO motor vibration, no hints, no retry --
// waits for one dot input + SUBMIT, scores it, and reports the result back
// to Supabase so the teacher panel can show it live and move to the next
// letter automatically.
//
// Flow per test item:
//   1. Teacher panel inserts {device_id, letter_id, command:'test',
//      test_index, test_total} into remote_commands. test_index is this
//      letter's 0-based position in the batch, test_total is the batch size
//      -- that's how this sketch knows when the WHOLE test is finished.
//   2. This sketch polls for that row, plays the letter's audio (audio only
//      -- the student must recall the pattern from memory, that's the test).
//      There is no web input path: the ONLY way to answer is the physical
//      dot buttons + SUBMIT on this device.
//   3. Student presses the dot buttons + SUBMIT once. Whatever they entered
//      is scored immediately -- there is no retry loop, right or wrong.
//   4. Result is POSTed to Supabase's `attempts` table. teacher.js polls
//      that table, matches it to the letter it just sent, and advances the
//      test queue to the next letter.
//   5. After the LAST letter (test_index+1 == test_total), a full pass/fail
//      summary for the whole batch is printed to the Serial Monitor.
//
// Two-cell characters (ঋ, ৎ) are NOT taught here: BRAILLE_PATTERN[id]
// already stores their single answer cell (verified in data/braille_map.json
// and mirrored in firmware/braille_tutor/braille_map.h), and the student is
// expected to already know the prefix from learning mode.
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

// ---------------------------------------------------------------------------

#define POLL_MS      250   // safe to poll fast now that the TLS connection is reused
#define DEVICE_ID    "esp32_01"
#define TEST_USER_ID "S01"     // matches teacher.js's default student id

static const char *SUPABASE_URL      = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";

static long     g_last_id     = -1;
static uint32_t g_last_poll   = 0;
static int      g_attempt_idx = 0;
static char     g_session_id[24];

// A fresh WiFiClientSecure means a full TLS handshake (0.5-3s on ESP32) --
// expensive enough that doing it on every 700ms poll makes the whole loop
// feel laggy even though it "works". Keeping one client + reusing the
// connection (setReuse) across requests to the same host avoids repeating
// that handshake for every poll and every reported result.
static WiFiClientSecure g_https;
static bool             g_https_ready = false;

static WiFiClientSecure &https_client() {
  if (!g_https_ready) {
    g_https.setInsecure();
    g_https_ready = true;
  }
  return g_https;
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

    HTTPClient http;
    http.begin(https_client(), String(SUPABASE_URL) +
      "/rest/v1/remote_commands?order=id.desc&limit=1&select=id");
    http.setReuse(true);
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
// Supabase poll -- only 'test' commands. Returns letter_id (0-49) or -1.
// Also fills g_cur_test_index/g_cur_test_total, which is how this sketch
// knows where it is in the teacher's batch and when to print the summary.
// ---------------------------------------------------------------------------

static int g_cur_test_index = 0;
static int g_cur_test_total = 1;

// Pulls one integer field out of a PostgREST JSON object. Returns false if
// the key is missing OR its value is JSON null.
static bool extract_int_field(const String &body, const char *key, int &out) {
  String needle = String("\"") + key + "\":";
  int pos = body.indexOf(needle);
  if (pos < 0) return false;
  int valueStart = pos + needle.length();
  if (body.startsWith("null", valueStart)) return false;
  out = body.substring(valueStart).toInt();
  return true;
}

static int poll_test_command() {
  if (WiFi.status() != WL_CONNECTED) { wifi_connect(); return -1; }

  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/remote_commands"
    + "?device_id=eq." + DEVICE_ID
    + "&command=eq.test"
    + "&id=gt."        + String(g_last_id)
    + "&order=id.asc&limit=1&select=id,letter_id,test_index,test_total";

  http.begin(https_client(), url);
  http.setReuse(true);
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
      // Defaults keep a manually-inserted test row (e.g. via curl, with no
      // batch fields) working as a one-item test that reports immediately.
      g_cur_test_index = 0;
      g_cur_test_total = 1;
      extract_int_field(body, "test_index", g_cur_test_index);
      extract_int_field(body, "test_total", g_cur_test_total);
      g_last_id = id;
    }
  } else if (code > 0) {
    Serial.printf("[poll] HTTP %d\n", code);
  }
  http.end();
  return letter_id;
}

// ---------------------------------------------------------------------------
// Heartbeat -- informs Supabase device_status that this ESP32 is online
// ---------------------------------------------------------------------------
#define HEARTBEAT_MS 4000
static uint32_t g_last_heartbeat = 0;

static void send_heartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/device_status?on_conflict=device_id";
  http.begin(https_client(), url);
  http.setReuse(true);
  http.addHeader("apikey",        SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
  http.addHeader("Content-Type",  "application/json");
  http.addHeader("Prefer",        "resolution=merge-duplicates,return=minimal");
  http.POST("{\"device_id\":\"" + String(DEVICE_ID) + "\"}");
  http.end();
}

// ---------------------------------------------------------------------------
// Audio
// ---------------------------------------------------------------------------

static void play_and_wait(int track, uint32_t timeout_ms = 7000) {
  if (!g_df_ok) {
    Serial.printf("  [audio] DFPlayer not ready, skipping track %d\n", track);
    delay(300); return;
  }
  Serial.printf("  [audio] track %d ...\n", track);
  g_df.play(track);
  delay(300);
  uint32_t t0 = millis();
  while (millis() - t0 < timeout_ms) {
    if (g_df.available() && g_df.readType() == DFPlayerPlayFinished) {
      Serial.println("  [audio] done.");
      return;
    }
    delay(20);
  }
  Serial.println("  [audio] timeout.");
}

// ---------------------------------------------------------------------------
// Wait for one dot input + SUBMIT -- single attempt, no retry.
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
      Serial.print("[test] waiting for release -- still held: ");
      for (int i = 0; i < 6; i++)
        if (g_btn.stable[i]) Serial.printf("dot%d(GPIO%d) ", i + 1, PIN_BUTTON[i]);
      if (submit_down) Serial.printf("SUBMIT(GPIO%d) ", PIN_SUBMIT);
      Serial.printf(" -- check wiring if this doesn't clear.\n");
    }
    delay(5);
  }
}

static uint8_t wait_for_submit() {
  wait_release_all();
  buttons_reset_attempt();

  Serial.println("[test] Waiting for dot buttons + SUBMIT...");
  for (;;) {
    buttons_poll();
    if (submit_pressed()) return g_btn.mask;
    delay(5);
  }
}

// ---------------------------------------------------------------------------
// Report one scored item back to Supabase, so teacher.js's poll picks it up
// and advances the test queue. Field values outside char_id/response_time/
// entered_pattern/expected_pattern/is_correct are placeholders -- a single
// test attempt has no adaptive-learning history to report.
// ---------------------------------------------------------------------------

static String press_order_json() {
  String s = "[";
  for (int i = 0; i < g_btn.press_count; i++) {
    if (i) s += ",";
    s += String(g_btn.press_order[i]);
  }
  s += "]";
  return s;
}

static void report_attempt(int letter_id, uint8_t expected, uint8_t entered,
                            double response_time_ms) {
  bool correct = (entered == expected);

  String body = "{";
  body += "\"user_id\":\""    + String(TEST_USER_ID) + "\",";
  body += "\"session_id\":\"" + String(g_session_id)  + "\",";
  body += "\"device_id\":\""  + String(DEVICE_ID)      + "\",";
  body += "\"attempt_index\":" + String(g_attempt_idx) + ",";
  body += "\"char_id\":"       + String(letter_id) + ",";
  body += "\"response_time\":" + String(response_time_ms, 1) + ",";
  body += "\"press_duration\":" + String(buttons_mean_press_duration(), 1) + ",";
  body += "\"retry_count\":0,";
  body += "\"prev_accuracy\":0,";
  body += "\"prev_mastery\":0,";
  body += "\"hint_count\":0,";
  body += "\"session_number\":1,";
  body += "\"difficulty_level\":1,";
  body += "\"time_since_last_practice\":0,";
  body += "\"prev_confidence\":0,";
  body += "\"current_streak\":0,";
  body += "\"wrong_streak\":0,";
  body += "\"prev_mistakes\":0,";
  body += "\"teaching_action\":"  + String(correct ? 2 : 0) + ",";
  body += "\"confidence_state\":" + String(correct ? 0 : 1) + ",";
  body += "\"expected_pattern\":" + String(expected) + ",";
  body += "\"entered_pattern\":"  + String(entered) + ",";
  body += "\"is_correct\":"       + String(correct ? "true" : "false") + ",";
  body += "\"press_order\":\""    + press_order_json() + "\",";
  body += "\"source\":\"esp32\",";
  body += "\"is_synthetic\":false,";
  body += "\"spec_version\":2,";
  body += "\"braille_map_verified\":true";
  body += "}";

  HTTPClient http;
  http.begin(https_client(), String(SUPABASE_URL) + "/rest/v1/attempts");
  http.setReuse(true);
  http.addHeader("apikey",        SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
  http.addHeader("Content-Type",  "application/json");
  http.addHeader("Prefer",        "return=minimal");

  int code = http.POST(body);
  Serial.printf("[test] reported attempt -> HTTP %d\n", code);
  if (code < 200 || code >= 300) Serial.println(http.getString());
  http.end();

  g_attempt_idx++;
}

// ---------------------------------------------------------------------------
// Batch tally -- accumulates across one teacher-selected test run so the
// final score can be printed to Serial once the last letter is answered.
// Reset whenever a command arrives with test_index == 0 (a new batch
// starting), so a stale tally from a previous run never bleeds into this one.
// ---------------------------------------------------------------------------

struct TestItemResult { int letter_id; bool correct; double response_time_ms; };
static TestItemResult g_batch_results[BRAILLE_LETTER_COUNT];
static int            g_batch_count = 0;

static void print_test_summary() {
  int correct = 0;
  for (int i = 0; i < g_batch_count; i++) if (g_batch_results[i].correct) correct++;
  int total = g_batch_count;
  int pct   = total > 0 ? (correct * 100) / total : 0;

  Serial.println("\n==================================================");
  Serial.println("[TEST COMPLETE]");
  Serial.printf("  Total: %d   Correct: %d   Wrong: %d   Score: %d%%\n",
                total, correct, total - correct, pct);
  Serial.println("--------------------------------------------------");
  for (int i = 0; i < g_batch_count; i++) {
    TestItemResult &r = g_batch_results[i];
    Serial.printf("  #%-2d letter_id=%-2d track=%-2d  %-7s  rt=%.0fms\n",
                  i + 1, r.letter_id, r.letter_id + 1,
                  r.correct ? "CORRECT" : "WRONG", r.response_time_ms);
  }
  Serial.println("==================================================\n");
}

// ---------------------------------------------------------------------------
// One test item: audio only, one input, one submit, score, report.
// ---------------------------------------------------------------------------

static void run_test_item(int letter_id) {
  if (letter_id < 0 || letter_id >= BRAILLE_LETTER_COUNT) {
    Serial.printf("[test] letter_id %d out of range -- ignored.\n", letter_id);
    return;
  }

  if (g_cur_test_index == 0) {
    g_batch_count = 0;   // fresh batch starting
    Serial.println("[test] Audio: 'পরীক্ষা শুরু হচ্ছে' (Track 61)");
    play_and_wait(61, 4000);
    delay(400);
  }

  uint8_t expected = BRAILLE_PATTERN[letter_id];
  int     track     = letter_id + 1;

  Serial.printf("\n==============================\n");
  Serial.printf("[test] Item %d/%d  Letter #%d track=%d expected=0x%02X (NO vibration cue)\n",
                g_cur_test_index + 1, g_cur_test_total, letter_id, track, expected);
  Serial.printf("==============================\n");

  play_and_wait(track, 7000);
  uint32_t prompt_end = millis();

  uint8_t entered = wait_for_submit();
  double response_time = (double)(millis() - prompt_end);

  bool correct = (entered == expected);
  Serial.printf("[test] entered=0x%02X expected=0x%02X -> %s  (%.0f ms)\n",
                entered, expected, correct ? "CORRECT" : "WRONG", response_time);

  report_attempt(letter_id, expected, entered, response_time);

  if (g_batch_count < BRAILLE_LETTER_COUNT) {
    g_batch_results[g_batch_count++] = { letter_id, correct, response_time };
  }

  if (g_cur_test_index + 1 >= g_cur_test_total) {
    print_test_summary();

    int correct_cnt = 0;
    for (int i = 0; i < g_batch_count; i++) if (g_batch_results[i].correct) correct_cnt++;
    int wrong_cnt = g_batch_count - correct_cnt;

    delay(600);
    play_and_wait(62, 3500); // "পরীক্ষা শেষ"
    delay(300);
    play_and_wait(51, 2000); // "সঠিক"
    delay(200);
    int c_num = (correct_cnt < 0) ? 0 : (correct_cnt > 10 ? 10 : correct_cnt);
    play_and_wait(70 + c_num, 2000);
    delay(300);
    play_and_wait(52, 2000); // "ভুল"
    delay(200);
    int w_num = (wrong_cnt < 0) ? 0 : (wrong_cnt > 10 ? 10 : wrong_cnt);
    play_and_wait(70 + w_num, 2000);
    delay(400);
    play_and_wait(63, 3500); // "ধন্যবাদ"
  }
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n===================================");
  Serial.println("  t11: Testing Module              ");
  Serial.println("===================================");

  motors_begin();   // idle-off; test mode never vibrates a hint
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
  send_heartbeat();

  snprintf(g_session_id, sizeof(g_session_id), "esp32_test_%lu", millis());

  Serial.println("\n[ready] Waiting for the teacher panel to start a test...\n");
}

void loop() {
  if (millis() - g_last_heartbeat >= HEARTBEAT_MS) {
    g_last_heartbeat = millis();
    send_heartbeat();
  }

  if (millis() - g_last_poll >= POLL_MS) {
    g_last_poll = millis();
    int letter_id = poll_test_command();
    if (letter_id >= 0) run_test_item(letter_id);
  }
}
