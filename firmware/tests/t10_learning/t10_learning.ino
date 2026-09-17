// t10: Learning module
//
// Flow per round:
//   1. Select a letter on remote_control.html
//   2. Speaker plays the letter audio
//   3. Motors vibrate each dot sequentially (500ms on, 400ms gap) -- teaches the pattern
//   4. User presses the dot buttons then SUBMIT
//   5. Correct  -> speaker says "sothik" (track 51), round done
//   6. Wrong    -> replay audio + motor pattern, wait for input again (infinite retry)
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

#define TRACK_CORRECT  51
#define DOT_ON_MS     500    // how long each dot's motor buzzes
#define DOT_GAP_MS    500    // silence after each motor, within a pattern
#define STAGE_GAP_MS  1200   // silence between stage1 and stage2 vibrations
#define POLL_MS       700
#define DEVICE_ID  "esp32_01"

static const char *SUPABASE_URL      = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";

static long     g_last_id   = -1;
static uint32_t g_last_poll = 0;

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
// Wait for submit
// ---------------------------------------------------------------------------

// Blocks until every dot button AND the submit button are physically
// released. Called before buttons_reset_attempt() so a button still held
// over from the previous stage/attempt (very likely right after the user
// just pressed SUBMIT) can't leak into the next reading.
//
// If this never clears, it means a GPIO is stuck reading "pressed" (LOW) --
// a wiring fault (short, loose pull-up, stuck switch), not a firmware bug.
// Reports which pin every 2s instead of hanging silently, so that is visible
// on the Serial Monitor rather than looking like a frozen sketch.
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
      Serial.printf(" -- check wiring if this doesn't clear.\n");
    }
    delay(5);
  }
}

static void print_dot_bits(uint8_t mask) {
  for (int i = 0; i < 6; i++) Serial.printf("dot%d=%d ", i + 1, (mask >> i) & 1);
}

static uint8_t wait_for_submit() {
  wait_release_all();       // clean baseline -- nothing carried over
  buttons_reset_attempt();

  Serial.println("[learn] Waiting for dot buttons + SUBMIT...");
  for (;;) {
    buttons_poll();
    if (submit_pressed()) {
      Serial.print("[learn] raw at submit: ");
      print_dot_bits(g_btn.mask);
      Serial.printf(" (mask=0x%02X)\n", g_btn.mask);
      return g_btn.mask;
    }
    delay(5);
  }
}

// ---------------------------------------------------------------------------
// Two-stage characters -- ONLY these two need two sequential cell inputs.
// Every other letter uses the single-stage path below (whole pattern
// vibrates together once, one input, one submit).
//
// Bit convention (same as BRAILLE_PATTERN):
//   bit0=dot1  bit1=dot2  bit2=dot3  bit3=dot4  bit4=dot5  bit5=dot6
//
//  ঋ  (id= 6): stage1 = dot 5           (0x10)
//               stage2 = dots 1,2,3,5    (0x17)
//  ৎ  (id=46): stage1 = dot 5           (0x10)
//               stage2 = dots 2,3,4,5    (0x1E)
// ---------------------------------------------------------------------------

struct TwoStageEntry { int id; uint8_t s1; uint8_t s2; };
static const TwoStageEntry TWO_STAGE_CHARS[] = {
  {  6, 0x10, 0x17 },   // ঋ  stage1=dot5      stage2=dots1,2,3,5
  { 46, 0x10, 0x1E },   // ৎ  stage1=dot5      stage2=dots2,3,4,5
};
static const int TWO_STAGE_COUNT =
  sizeof(TWO_STAGE_CHARS) / sizeof(TWO_STAGE_CHARS[0]);

static bool get_two_stage(int letter_id, uint8_t &s1, uint8_t &s2) {
  for (int i = 0; i < TWO_STAGE_COUNT; i++) {
    if (TWO_STAGE_CHARS[i].id == letter_id) {
      s1 = TWO_STAGE_CHARS[i].s1;
      s2 = TWO_STAGE_CHARS[i].s2;
      return true;
    }
  }
  return false;
}

// ---------------------------------------------------------------------------
// Learning round
//
// Two-stage flow:
//   1. Play audio
//   2. Vibrate stage1 (all dots together) → pause → vibrate stage2 (all together)
//   3. User presses stage1 buttons → SUBMIT
//   4. User presses stage2 buttons → SUBMIT
//   If either input is wrong → back to step 1 (replay audio + both vibrations)
//
// Single-stage flow:
//   1. Play audio → vibrate pattern (all dots together)
//   2. User presses buttons → SUBMIT
//   Wrong → back to step 1
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
    Serial.printf("[learn] Letter #%d (TWO-STAGE) track=%d s1=0x%02X s2=0x%02X\n",
                  letter_id, track, s1, s2);
    Serial.printf("==============================\n");

    for (;;) {
      // 1. Audio
      play_and_wait(track, 7000);

      // 2. Show both stages before any input -- each dot buzzes one at a
      //    time, 0.5s gap after every motor, so individual dots stay
      //    distinguishable by touch.
      Serial.printf("[learn] Vibrate stage1=0x%02X...\n", s1);
      motors_show_sequential(s1, DOT_ON_MS, DOT_GAP_MS);
      delay(STAGE_GAP_MS);
      Serial.printf("[learn] Vibrate stage2=0x%02X...\n", s2);
      motors_show_sequential(s2, DOT_ON_MS, DOT_GAP_MS);
      delay(1300);  // pause so user knows the vibration sequence is done

      // 3. Input stage 1
      Serial.println("[learn] Input stage1 then SUBMIT...");
      uint8_t in1 = wait_for_submit();
      Serial.printf("[learn] stage1: entered=0x%02X expected=0x%02X\n", in1, s1);
      if (in1 != s1) {
        Serial.println("[learn] stage1 WRONG -- replaying from start.");
        delay(300); continue;
      }

      // 4. Input stage 2
      Serial.println("[learn] Input stage2 then SUBMIT...");
      uint8_t in2 = wait_for_submit();
      Serial.printf("[learn] stage2: entered=0x%02X expected=0x%02X\n", in2, s2);
      if (in2 != s2) {
        Serial.println("[learn] stage2 WRONG -- replaying from start.");
        delay(300); continue;
      }

      break;  // both correct
    }

  } else {
    uint8_t expected = BRAILLE_PATTERN[letter_id];
    Serial.printf("[learn] Letter #%d track=%d dots=0x%02X\n",
                  letter_id, track, expected);
    Serial.printf("==============================\n");

    for (;;) {
      play_and_wait(track, 7000);
      Serial.printf("[learn] Vibrate 0x%02X...\n", expected);
      motors_show_sequential(expected, DOT_ON_MS, DOT_GAP_MS);
      delay(800);

      uint8_t entered = wait_for_submit();
      Serial.printf("[learn] entered=0x%02X expected=0x%02X -> %s\n",
                    entered, expected, entered == expected ? "CORRECT" : "WRONG");
      if (entered == expected) break;
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
  Serial.println("  t10: Learning Module             ");
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

  Serial.println("\n[ready] Select a letter on remote_control.html to begin.\n");
}

void loop() {
  if (millis() - g_last_poll >= POLL_MS) {
    g_last_poll = millis();
    int letter_id = poll_supabase();
    if (letter_id >= 0) learning_round(letter_id);
  }
}
