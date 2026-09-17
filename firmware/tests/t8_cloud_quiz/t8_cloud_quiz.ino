// t8: End-to-end cloud quiz -- corrected flow.
//
// Flow per round:
//   1. Tap a letter on remote_control.html
//   2. ESP32 picks it up from Supabase -> prints to Serial
//   3. DFPlayer plays the letter audio, waits for it to finish
//   4. Serial prints "Enter dots and press SUBMIT"
//   5. User presses dot buttons then the submit button
//   6. Correct  -> speaker plays "sothik" (track 51)
//   7. Wrong    -> speaker plays "wrong" (track 52)
//                  vibrator buzzes the correct dot pattern
//   8. Wait for the next letter from the web app
//
// Wiring: full board (6 dot buttons + submit + motors via ULN2803A + DFPlayer)
// Serial Monitor: 115200 baud

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <DFRobotDFPlayerMini.h>

#include "secrets.h"     // WIFI_SSID, WIFI_PASS
#include "pins.h"
#include "hardware.h"    // motors, buttons, g_df, g_df_ok
#include "braille_map.h" // BRAILLE_PATTERN[], BRAILLE_LETTER_COUNT

// ---------------------------------------------------------------------------

#define TRACK_CORRECT  51    // "sothik / correct"
#define TRACK_WRONG    52    // "wrong"
#define MOTOR_BUZZ_MS 1500
#define POLL_MS        700
#define DEVICE_ID   "esp32_01"

static const char *SUPABASE_URL      = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";

static long     g_last_id   = -1;  // -1 = not synced yet
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
    delay(400);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED)
    Serial.printf("\nWiFi connected. IP: %s\n", WiFi.localIP().toString().c_str());
  else
    Serial.println("\nWiFi FAILED -- will retry on next poll.");
}

// ---------------------------------------------------------------------------
// Supabase sync -- on first connect, skip all existing rows so old commands
// from previous test sessions are ignored.
// ---------------------------------------------------------------------------

static void sync_latest_id() {
  // Retry up to 3 times -- WiFi/SSL stack may need a moment after connect.
  for (int attempt = 1; attempt <= 3; attempt++) {
    if (WiFi.status() != WL_CONNECTED) { wifi_connect(); }
    delay(300);

    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;

    // No device_id filter -- get the global max id so we skip ALL existing
    // rows regardless of device, preventing old commands from replaying.
    String url = String(SUPABASE_URL)
      + "/rest/v1/remote_commands?order=id.desc&limit=1&select=id";

    http.begin(client, url);
    http.addHeader("apikey",        SUPABASE_ANON_KEY);
    http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);

    int code = http.GET();
    String body = http.getString();
    http.end();

    Serial.printf("[sync] attempt %d: HTTP %d  body: %s\n", attempt, code, body.c_str());

    if (code == 200) {
      int pos = body.indexOf("\"id\":");
      g_last_id = (pos >= 0) ? body.substring(pos + 5).toInt() : 0;
      Serial.printf("[sync] OK -- will ignore all rows up to id=%ld\n", g_last_id);
      return;
    }
    delay(1000);
  }
  // All retries failed -- safest fallback: set to a large value so nothing old fires.
  // The user will need to reset if this happens.
  Serial.println("[sync] FAILED after 3 attempts -- no commands will be accepted.");
  Serial.println("       Check WiFi credentials and Supabase key.");
  g_last_id = 2147483647L;  // INT32_MAX -- nothing will match gt. this
}

// ---------------------------------------------------------------------------
// Supabase poll  -- returns letter_id (0-49) or -1
// ---------------------------------------------------------------------------

static int poll_supabase() {
  if (WiFi.status() != WL_CONNECTED) { wifi_connect(); return -1; }

  WiFiClientSecure client;
  client.setInsecure();
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
        if (!after.startsWith("null"))
          letter_id = (int)after.toInt();
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
// Audio -- plays a track and blocks until finished or timeout
// ---------------------------------------------------------------------------

static void play_and_wait(int track, uint32_t timeout_ms = 6000) {
  if (!g_df_ok) {
    Serial.printf("  [audio] DFPlayer not ready, skipping track %d\n", track);
    delay(300);
    return;
  }
  Serial.printf("  [audio] playing track %d ...\n", track);
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
  Serial.println("  [audio] timeout -- continuing.");
}

// ---------------------------------------------------------------------------
// Wait for submit -- polls buttons continuously until submit is pressed.
// Returns the dot mask the user entered.
// ---------------------------------------------------------------------------

static uint8_t wait_for_submit() {
  buttons_reset_attempt();

  // Drain any leftover submit press so we don't react to it immediately
  // (hold off for 100ms -- the debounce window is only 20ms)
  uint32_t guard = millis();
  while (millis() - guard < 100) {
    submit_pressed();   // call but discard
    delay(5);
  }

  Serial.println("  [input] waiting for dot buttons + SUBMIT...");

  for (;;) {
    buttons_poll();
    if (submit_pressed()) return g_btn.mask;
    delay(5);
  }
}

// ---------------------------------------------------------------------------
// One quiz round
// ---------------------------------------------------------------------------

static void quiz_round(int letter_id) {
  if (letter_id < 0 || letter_id >= BRAILLE_LETTER_COUNT) {
    Serial.printf("[quiz] letter_id %d out of range -- ignored.\n", letter_id);
    return;
  }

  uint8_t expected = BRAILLE_PATTERN[letter_id];
  int     track    = letter_id + 1;   // letter 0 -> track 1

  Serial.printf("\n==============================\n");
  Serial.printf("[quiz] Letter #%d  track %d  expected dots: 0x%02X\n",
                letter_id, track, expected);
  Serial.printf("==============================\n");

  // Step 1: play the letter audio
  Serial.println("[quiz] Playing letter...");
  play_and_wait(track, 7000);

  // Step 2: wait for user input
  Serial.println("[quiz] Enter the dots and press SUBMIT.");
  uint8_t entered = wait_for_submit();

  bool correct = (entered == expected);
  Serial.printf("[quiz] Entered: 0x%02X  Expected: 0x%02X  -> %s\n",
                entered, expected, correct ? "CORRECT" : "WRONG");

  if (correct) {
    // Step 3a: correct feedback
    Serial.println("[quiz] Playing CORRECT cue...");
    play_and_wait(TRACK_CORRECT, 4000);
    Serial.println("[quiz] CORRECT! Well done.");
  } else {
    // Step 3b: wrong feedback
    Serial.println("[quiz] Playing WRONG cue...");
    play_and_wait(TRACK_WRONG, 4000);

    // Step 4: show correct pattern on motors, one dot at a time with 0.5s gap
    Serial.printf("[quiz] Buzzing correct dot pattern sequentially (0x%02X)...\n", expected);
    motors_show_sequential(expected, 500, 500);
    motors_all_off();
    Serial.println("[quiz] Motor feedback done.");
  }

  Serial.println("\n[quiz] Round done. Send the next letter from the web app.\n");
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n===================================");
  Serial.println("  t8: Cloud Quiz (end-to-end test) ");
  Serial.println("===================================");

  // Motors -- all off at start
  motors_begin();
  Serial.println("[init] Motors OK.");

  // Buttons + submit
  buttons_begin();
  submit_begin();
  Serial.println("[init] Buttons OK.");

  // DFPlayer on UART2
  Serial2.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(500);
  g_df_ok = g_df.begin(Serial2, /*isACK=*/true, /*doReset=*/true);
  if (g_df_ok) {
    g_df.volume(30);   // max volume
    Serial.printf("[init] DFPlayer OK -- %d files on card.\n", g_df.readFileCounts());
  } else {
    Serial.println("[init] DFPlayer NOT found -- audio will be skipped.");
    Serial.println("       Check wiring and run t9b_dfplayer_diagnostic first.");
  }

  // WiFi
  WiFi.persistent(false);
  wifi_connect();
  sync_latest_id();   // skip all old Supabase rows

  Serial.println("\n[ready] Open web/remote_control.html and tap a letter.\n");
}

void loop() {
  if (millis() - g_last_poll >= POLL_MS) {
    g_last_poll = millis();
    int letter_id = poll_supabase();
    if (letter_id >= 0) {
      quiz_round(letter_id);
    }
  }
}
