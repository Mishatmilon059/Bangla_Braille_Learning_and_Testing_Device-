// t12_ml_complete: Learning + ML comparison + PER-STUDENT PERSONALIZATION
//
// Identical to t11_ml_test, with one addition: every attempt is now scored
// and logged under the REAL student who is at the device, not a hardcoded
// placeholder --
//
//   1. The teacher panel now sends a `student_id` alongside each letter
//      command (see webapp/app/teacher/teacherApp.js -- sendPlay()).
//   2. This sketch reads that student_id out of the polled command and
//      reports every attempt under it (attempts.user_id), instead of the
//      literal "S01" t11_ml_test always used.
//   3. Whenever the ACTIVE student changes, this sketch fetches that
//      student's own saved per-letter state (mastery, streaks, accuracy)
//      from Supabase's `student_weaknesses` table and loads it into
//      char_state[], so prev_accuracy/prev_mastery -- the two features that
//      let the model see history the rule engine cannot -- reflect THAT
//      student's real history, not whichever student last used this board
//      since the last reboot.
//   4. After every attempt, the updated state is written back to
//      student_weaknesses (an UPSERT, same table the teacher panel's new
//      /students profile page reads), so the next session -- on this board
//      or any other -- picks up exactly where this student left off.
//
// This is deliberately ONE shared model for every student (the 1,734
// trained parameters never change here) -- personalization comes entirely
// from feeding it each student's own history as input, not from training a
// separate network per student. See docs note in the project report:
// per-student data volume (a few hundred attempts each) is far too small to
// train a separate model per student without overfitting.
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

#define TRACK_CORRECT      51
#define TRACK_WRONG        52
#define TRACK_TEST_START   61
#define TRACK_TEST_END     62
#define TRACK_THANK_YOU    63
#define TRACK_SPECIAL_CHAR 64
#define TRACK_NUMBER_BASE  70

#define DOT_ON_MS     500
#define DOT_GAP_MS    500
#define STAGE_GAP_MS  1200
#define POLL_MS       250   // safe to poll fast now that the TLS connection is reused
#define DEVICE_ID  "esp32_01"
#define DEFAULT_STUDENT_ID "S01"   // used only until the first real command arrives

static const char *SUPABASE_URL      = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";

static long     g_last_id     = -1;
static uint32_t g_last_poll   = 0;
static int      g_attempt_idx = 0;
static char     g_session_id[24];
static char     g_command[16]         = "play";
static int      g_test_index          = 0;
static int      g_test_total          = 1;
static int      g_test_correct_count  = 0;
static int      g_test_wrong_count    = 0;

// The student currently named by the last-polled command, and the student
// char_state[] currently reflects. They differ for exactly one loop() pass
// after a switch -- that's the signal to reload state before scoring.
static char g_student_id[24]        = DEFAULT_STUDENT_ID;
static char g_loaded_student_id[24] = "";

// A fresh WiFiClientSecure means a full TLS handshake (0.5-3s on ESP32) per
// request -- reusing one connection avoids paying that on every poll and
// every reported attempt.
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
// Per-character state -- now understood to belong to whichever student is
// named by g_loaded_student_id, not to "the board" in general.
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
static CharState char_state[BRAILLE_LETTER_COUNT]; // filled by load_student_state()

// ---------------------------------------------------------------------------
// Tiny JSON helpers -- pulling one named numeric field out of a flat object.
// Not a general parser: student_weaknesses rows have no nested objects or
// arrays, so indexOf+toInt/toDouble is enough and needs no library.
// ---------------------------------------------------------------------------

static long json_int(const String &obj, const char *key, long def) {
  int p = obj.indexOf(key);
  if (p < 0) return def;
  String after = obj.substring(p + strlen(key));
  if (after.startsWith("null")) return def;
  return after.toInt();
}

static double json_double(const String &obj, const char *key, double def) {
  int p = obj.indexOf(key);
  if (p < 0) return def;
  String after = obj.substring(p + strlen(key));
  if (after.startsWith("null")) return def;
  return after.toDouble();
}

// ---------------------------------------------------------------------------
// Per-student state load/save
// ---------------------------------------------------------------------------

// Replaces char_state[] with the named student's own saved history. Called
// only when the active student actually changes, so a normal single-student
// session pays this cost exactly once, not on every attempt.
static void load_student_state(const char *student_id) {
  memset(char_state, 0, sizeof(char_state));
  if (WiFi.status() != WL_CONNECTED) { wifi_connect(); return; }

  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/student_weaknesses"
    + "?student_id=eq." + String(student_id)
    + "&select=char_id,correct_count,wrong_count,mastery,current_streak,wrong_streak,prev_confidence";
  http.begin(https_client(), url);
  http.setReuse(true);
  http.addHeader("apikey",        SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);

  int code = http.GET();
  if (code == 200) {
    String body = http.getString();
    int loaded = 0, pos = 0;
    for (;;) {
      int obj_start = body.indexOf('{', pos);
      if (obj_start < 0) break;
      int obj_end = body.indexOf('}', obj_start);
      if (obj_end < 0) break;
      String obj = body.substring(obj_start, obj_end + 1);

      int cid = (int)json_int(obj, "\"char_id\":", -1);
      if (cid >= 0 && cid < BRAILLE_LETTER_COUNT) {
        CharState &st      = char_state[cid];
        int wrong_count    = (int)json_int(obj, "\"wrong_count\":", 0);
        st.correct_count   = (int)json_int(obj, "\"correct_count\":", 0);
        st.total_attempts  = st.correct_count + wrong_count;
        st.accuracy        = st.total_attempts > 0
                              ? (double)st.correct_count / st.total_attempts : 0.0;
        st.mastery         = json_double(obj, "\"mastery\":", 0.0);
        st.current_streak  = json_double(obj, "\"current_streak\":", 0.0);
        st.wrong_streak    = json_double(obj, "\"wrong_streak\":", 0.0);
        st.prev_confidence = json_double(obj, "\"prev_confidence\":", 0.0);
        loaded++;
      }
      pos = obj_end + 1;
    }
    Serial.printf("[personalize] loaded %d saved letters for student '%s'\n", loaded, student_id);
  } else if (code > 0) {
    Serial.printf("[personalize] load HTTP %d -- starting '%s' fresh\n", code, student_id);
  }
  http.end();
}

// Writes one letter's updated state back for this student, so the teacher
// panel's /students profile and the next session's load_student_state() both
// see it. Same table+conflict-key convention as web/teacher.js's own
// student_weaknesses upsert -- this is the same table, kept in sync.
static void save_student_weakness(int letter_id) {
  const CharState &st = char_state[letter_id];

  String body = "{";
  body += "\"student_id\":\""    + String(g_student_id) + "\",";
  body += "\"char_id\":"         + String(letter_id) + ",";
  body += "\"correct_count\":"   + String(st.correct_count) + ",";
  body += "\"wrong_count\":"     + String(st.total_attempts - st.correct_count) + ",";
  body += "\"mastery\":"         + String(st.mastery, 6) + ",";
  body += "\"current_streak\":"  + String((int)st.current_streak) + ",";
  body += "\"wrong_streak\":"    + String((int)st.wrong_streak) + ",";
  body += "\"prev_confidence\":" + String((int)st.prev_confidence);
  body += "}";

  HTTPClient http;
  http.begin(https_client(), String(SUPABASE_URL) +
    "/rest/v1/student_weaknesses?on_conflict=student_id,char_id");
  http.setReuse(true);
  http.addHeader("apikey",        SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);
  http.addHeader("Content-Type",  "application/json");
  http.addHeader("Prefer",        "resolution=merge-duplicates,return=minimal");

  int code = http.POST(body);
  if (code < 200 || code >= 300) {
    Serial.printf("[personalize] weakness upsert HTTP %d\n", code);
  }
  http.end();
}

// ---------------------------------------------------------------------------
// ML comparison -- called after EVERY attempt (wrong or correct)
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

// Reports one attempt to Supabase's `attempts` table under the REAL active
// student (g_student_id) -- t11_ml_test always wrote "S01" here regardless
// of who was actually practising; that placeholder is the one thing this
// sketch exists to fix.
static void report_attempt(int letter_id, uint8_t expected, uint8_t entered,
                            const Features &f, int ml_ta, int ml_cs) {
  bool correct = (entered == expected);

  String body = "{";
  body += "\"user_id\":\""     + String(g_student_id) + "\",";
  body += "\"session_id\":\"" + String(g_session_id) + "\",";
  body += "\"device_id\":\""  + String(DEVICE_ID)     + "\",";
  body += "\"attempt_index\":" + String(g_attempt_idx) + ",";
  body += "\"char_id\":"       + String(letter_id) + ",";
  body += "\"response_time\":" + String(f.response_time, 1) + ",";
  body += "\"press_duration\":" + String(f.press_duration, 1) + ",";
  body += "\"retry_count\":"   + String((int)f.retry_count) + ",";
  body += "\"prev_accuracy\":" + String(f.prev_accuracy, 4) + ",";
  body += "\"prev_mastery\":"  + String(f.prev_mastery, 4) + ",";
  body += "\"hint_count\":"    + String((int)f.hint_count) + ",";
  body += "\"session_number\":" + String((int)f.session_number) + ",";
  body += "\"difficulty_level\":" + String((int)f.difficulty_level) + ",";
  body += "\"time_since_last_practice\":" + String(f.time_since_last_practice, 1) + ",";
  body += "\"prev_confidence\":" + String((int)f.prev_confidence) + ",";
  body += "\"current_streak\":"  + String((int)f.current_streak) + ",";
  body += "\"wrong_streak\":"    + String((int)f.wrong_streak) + ",";
  body += "\"prev_mistakes\":"   + String((int)f.prev_mistakes) + ",";
  body += "\"teaching_action\":"  + String(ml_ta) + ",";
  body += "\"confidence_state\":" + String(ml_cs) + ",";
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
  Serial.printf("  [report] student=%s -> HTTP %d\n", g_student_id, code);
  if (code < 200 || code >= 300) Serial.println(http.getString());
  http.end();

  g_attempt_idx++;
}

static void log_ml_comparison(int letter_id, uint8_t expected, uint8_t entered,
                               uint32_t rt_ms, int retry_count, bool is_correct) {
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

  Serial.printf("  +-- ML vs Rule Engine (student=%s letter=%d rt=%ums retry=%d %s)\n",
                g_student_id, letter_id, (unsigned)rt_ms, retry_count,
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

  report_attempt(letter_id, expected, entered, f, ml_ta, ml_cs);
  save_student_weakness(letter_id);
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
// Supabase poll -- returns letter_id (0-49) or -1. Also updates g_student_id
// whenever the polled command names one (a command with no student_id -- an
// older teacher panel, or a stale row -- leaves the currently active
// student unchanged rather than silently reverting to the default).
// ---------------------------------------------------------------------------

static int poll_supabase() {
  if (WiFi.status() != WL_CONNECTED) { wifi_connect(); return -1; }
  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/remote_commands"
    + "?device_id=eq." + DEVICE_ID
    + "&id=gt."        + String(g_last_id)
    + "&order=id.asc&limit=1&select=id,letter_id,student_id,command,test_index,test_total";
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

      int sid_pos = body.indexOf("\"student_id\":");
      if (sid_pos >= 0) {
        String after = body.substring(sid_pos + 13);
        if (after.startsWith("\"")) {
          int end_q = after.indexOf('"', 1);
          if (end_q > 0) {
            String sid = after.substring(1, end_q);
            // g_student_id is later concatenated raw into JSON bodies
            // (report_attempt/save_student_weakness) with no escaping, so a
            // stray '"' or '\' here would corrupt that JSON downstream.
            sid.replace("\"", "");
            sid.replace("\\", "");
            sid.toCharArray(g_student_id, sizeof(g_student_id));
          }
        }
        // startsWith("null") -> no student on this row -> keep g_student_id as-is
      }

      int cmd_pos = body.indexOf("\"command\":");
      if (cmd_pos >= 0) {
        String after = body.substring(cmd_pos + 10);
        if (after.startsWith("\"")) {
          int end_q = after.indexOf('"', 1);
          if (end_q > 0) {
            String cmd = after.substring(1, end_q);
            cmd.toCharArray(g_command, sizeof(g_command));
          }
        }
      } else {
        strcpy(g_command, "play");
      }

      int t_idx_pos = body.indexOf("\"test_index\":");
      if (t_idx_pos >= 0) {
        String after = body.substring(t_idx_pos + 13);
        if (!after.startsWith("null")) g_test_index = after.toInt();
        else g_test_index = 0;
      } else {
        g_test_index = 0;
      }

      int t_tot_pos = body.indexOf("\"test_total\":");
      if (t_tot_pos >= 0) {
        String after = body.substring(t_tot_pos + 13);
        if (!after.startsWith("null")) g_test_total = after.toInt();
        else g_test_total = 1;
      } else {
        g_test_total = 1;
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
    Serial.printf("[learn] Letter #%d (TWO-STAGE SPECIAL) track=%d  s1=0x%02X s2=0x%02X\n",
                  letter_id, track, s1, s2);
    Serial.printf("==============================\n");
    int retry_count = 0;

    for (;;) {
      Serial.println("[learn] Audio: 'বিশেষ বর্ণ' (Track 64)");
      play_and_wait(TRACK_SPECIAL_CHAR, 2500);
      delay(200);
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
        log_ml_comparison(letter_id, s1, in1, rt1, retry_count, false);
        retry_count++; delay(300); continue;
      }

      // Stage 2 input
      uint32_t rt2;
      uint8_t in2 = wait_for_submit(&rt2);
      bool ok2 = (in2 == s2);
      Serial.printf("[learn] stage2: 0x%02X vs 0x%02X -> %s\n", in2, s2, ok2 ? "OK" : "WRONG");
      // Log with average of both stage response times
      log_ml_comparison(letter_id, s2, in2, (rt1 + rt2) / 2, retry_count, ok2);
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

      log_ml_comparison(letter_id, expected, entered, rt_ms, retry_count, correct);
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
// Testing mode: NO vibration motors, audio prompt, single submit, and scoring
// ---------------------------------------------------------------------------

static void report_test_attempt(int letter_id, uint8_t expected, uint8_t entered,
                                uint32_t rt_ms, bool correct) {
  String body = "{";
  body += "\"user_id\":\""     + String(g_student_id) + "\",";
  body += "\"session_id\":\"" + String(g_session_id) + "\",";
  body += "\"device_id\":\""  + String(DEVICE_ID)     + "\",";
  body += "\"attempt_index\":" + String(g_attempt_idx) + ",";
  body += "\"char_id\":"       + String(letter_id) + ",";
  body += "\"response_time\":" + String(rt_ms) + ",";
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
  Serial.printf("  [test-report] student=%s letter=%d -> HTTP %d\n", g_student_id, letter_id, code);
  if (code < 200 || code >= 300) Serial.println(http.getString());
  http.end();

  g_attempt_idx++;
}

static void test_round(int letter_id, int test_index, int test_total) {
  if (letter_id < 0 || letter_id >= BRAILLE_LETTER_COUNT) {
    Serial.printf("[test] letter_id %d out of range\n", letter_id);
    return;
  }

  // 1. CRITICAL: Vibration motors are ALWAYS OFF in test mode!
  motors_all_off();

  // 2. If first question of test: announce start
  if (test_index == 0) {
    g_test_correct_count = 0;
    g_test_wrong_count   = 0;
    Serial.println("\n[test] === NEW TEST STARTED ===");
    Serial.println("[test] Audio: 'পরীক্ষা শুরু হচ্ছে' (Track 61)");
    play_and_wait(TRACK_TEST_START, 4000);
    delay(400);
  }

  uint8_t s1, s2;
  bool two_stage = get_two_stage(letter_id, s1, s2);
  uint8_t expected = BRAILLE_PATTERN[letter_id];
  int track = letter_id + 1;

  Serial.printf("\n=========================================\n");
  Serial.printf("[test] Item %d/%d -- Letter #%d track=%d expected=0x%02X%s\n",
                test_index + 1, test_total, letter_id, track, expected,
                two_stage ? " (SPECIAL CHAR - TWO STAGE)" : "");
  Serial.println("[test] (Vibration motors DISABLED)");
  Serial.printf("=========================================\n");

  // If this is a special letter (ঋ or ৎ), announce "বিশেষ বর্ণ" first!
  if (two_stage) {
    Serial.println("[test] Audio: 'বিশেষ বর্ণ' (Track 64)");
    play_and_wait(TRACK_SPECIAL_CHAR, 2500);
    delay(200);
  }

  // Play audio prompt for the letter
  play_and_wait(track, 7000);

  bool correct = false;
  uint32_t rt_ms = 0;

  if (two_stage) {
    // Stage 1 input
    uint32_t rt1 = 0;
    uint8_t in1 = wait_for_submit(&rt1);
    bool ok1 = (in1 == s1);

    // Stage 2 input
    uint32_t rt2 = 0;
    uint8_t in2 = wait_for_submit(&rt2);
    bool ok2 = (in2 == s2);

    correct = (ok1 && ok2);
    rt_ms = (rt1 + rt2) / 2;
    report_test_attempt(letter_id, s2, in2, rt_ms, correct);
  } else {
    // Single attempt from student (no vibration, no hints)
    uint8_t entered = wait_for_submit(&rt_ms);
    correct = (entered == expected);
    report_test_attempt(letter_id, expected, entered, rt_ms, correct);
  }

  if (correct) {
    g_test_correct_count++;
    Serial.printf("[test] CORRECT! (rt=%ums)\n", (unsigned)rt_ms);
  } else {
    g_test_wrong_count++;
    Serial.printf("[test] WRONG! (rt=%ums)\n", (unsigned)rt_ms);
  }

  // If last item of the test: announce summary
  if (test_index + 1 >= test_total) {
    Serial.println("\n=========================================");
    Serial.printf("[test] TEST COMPLETE! Correct: %d, Wrong: %d\n",
                  g_test_correct_count, g_test_wrong_count);
    Serial.println("=========================================");

    delay(600);
    // 1. "পরীক্ষা শেষ"
    Serial.println("[test] Audio: 'পরীক্ষা শেষ' (Track 62)");
    play_and_wait(TRACK_TEST_END, 3500);
    delay(300);

    // 2. "সঠিক"
    Serial.println("[test] Audio: 'সঠিক' (Track 51)");
    play_and_wait(TRACK_CORRECT, 2000);
    delay(200);

    // 3. Spoken number for correct count (0..10)
    int c_num = g_test_correct_count;
    if (c_num < 0) c_num = 0;
    if (c_num > 10) c_num = 10;
    Serial.printf("[test] Audio: number %d (Track %d)\n", c_num, TRACK_NUMBER_BASE + c_num);
    play_and_wait(TRACK_NUMBER_BASE + c_num, 2000);
    delay(300);

    // 4. "ভুল"
    Serial.println("[test] Audio: 'ভুল' (Track 52)");
    play_and_wait(TRACK_WRONG, 2000);
    delay(200);

    // 5. Spoken number for wrong count (0..10)
    int w_num = g_test_wrong_count;
    if (w_num < 0) w_num = 0;
    if (w_num > 10) w_num = 10;
    Serial.printf("[test] Audio: number %d (Track %d)\n", w_num, TRACK_NUMBER_BASE + w_num);
    play_and_wait(TRACK_NUMBER_BASE + w_num, 2000);
    delay(400);

    // 6. "ধন্যবাদ"
    Serial.println("[test] Audio: 'ধন্যবাদ' (Track 63)");
    play_and_wait(TRACK_THANK_YOU, 3500);
    Serial.println("[test] Audio cues complete.\n");
  }
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n===================================");
  Serial.println("  t12: Learning + ML + Personalized ");
  Serial.println("===================================");

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
  send_heartbeat();

  // No command has named a student yet -- load the default's own history
  // rather than starting it from zero every boot.
  load_student_state(g_student_id);
  strncpy(g_loaded_student_id, g_student_id, sizeof(g_loaded_student_id));

  snprintf(g_session_id, sizeof(g_session_id), "esp32_mlcomplete_%lu", millis());

  Serial.println("\n[ready] Select a student and letter on the teacher panel to begin.\n");
}

void loop() {
  if (millis() - g_last_heartbeat >= HEARTBEAT_MS) {
    g_last_heartbeat = millis();
    send_heartbeat();
  }

  if (millis() - g_last_poll >= POLL_MS) {
    g_last_poll = millis();
    int letter_id = poll_supabase();
    if (strcmp(g_command, "stop") == 0) {
      Serial.println("\n[cmd] STOP command received -- lesson ended.");
      play_and_wait(TRACK_TEST_END, 3500);  // Track 62: 'পরীক্ষা শেষ'
      delay(300);
      play_and_wait(TRACK_THANK_YOU, 3500); // Track 63: 'ধন্যবাদ'
      strcpy(g_command, "");
    } else if (letter_id >= 0) {
      if (strcmp(g_student_id, g_loaded_student_id) != 0) {
        load_student_state(g_student_id);
        strncpy(g_loaded_student_id, g_student_id, sizeof(g_loaded_student_id));
      }
      if (strcmp(g_command, "test") == 0) {
        test_round(letter_id, g_test_index, g_test_total);
      } else {
        learning_round(letter_id);
      }
      strcpy(g_command, "");
    }
  }
}
