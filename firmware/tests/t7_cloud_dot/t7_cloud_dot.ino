// Bring-up 7: play a full Braille letter, from a phone, over the cloud.
//
// A web page inserts a row into Supabase's `remote_commands` table:
// { device_id: "esp32_01", letter_id: 12 }. This sketch polls that table
// every POLL_INTERVAL_MS for rows newer than the last one it handled, looks
// up that letter's dot pattern in braille_map.h, and buzzes the motors in
// the same sequence a learner would feel on the real tutor. No port
// forwarding, no static IP -- the browser and the ESP32 both just talk to
// Supabase, from anywhere.
//
// A row can also carry a bare `dot` (1..6) instead of a `letter_id`, which
// just buzzes that one motor -- kept for the earlier single-dot testing.
//
// This is a SEPARATE mode from the offline tutor, on purpose. The rest of
// this project is deliberately WiFi-free ("no WiFi, inference on-device") so
// the tutor works with no signal at all -- see README.md. Bringing WiFi back
// for a remote-control demo is a reasonable, different thing; keep it in its
// own sketch rather than folding it into braille_tutor.ino.
//
// Setup:
//   1. Run supabase/schema.sql's remote_commands section (fresh install) or
//      the migration that adds letter_id (existing table) in the SQL editor.
//   2. cp secrets.h.example secrets.h, fill in your WiFi SSID/password.
//   3. Wiring is identical to t3_motors -- GPIO -> ULN2003A/2803A -> motor.
//   4. Needs braille_map.h copied in from firmware/braille_tutor/ -- already
//      done in this folder, but re-copy after any tools/gen_braille_header.py.
//
// Testing without the web page -- insert a command with curl:
//
//   curl -X POST 'https://rufaacgatrebsyxnyfbq.supabase.co/rest/v1/remote_commands' \
//     -H "apikey: sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-" \
//     -H "Authorization: Bearer sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-" \
//     -H "Content-Type: application/json" \
//     -d '{"device_id":"esp32_01","letter_id":12}'
//
// Known gap: this only buzzes the motors. There is no spoken confirmation --
// the DFPlayer isn't wired into this test sketch. Ask if you want that added.

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

#include "secrets.h"       // WIFI_SSID, WIFI_PASS -- copy from secrets.h.example
#include "braille_map.h"   // BRAILLE_PATTERN, BRAILLE_NAME, BRAILLE_VERIFIED

// Same publishable key already used in web/config.js. It is designed to ship
// in every client and only allows what supabase/schema.sql's RLS permits.
static const char *SUPABASE_URL       = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY  = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";
static const char *ESP_DEVICE_ID      = "esp32_01";   // must match what the app sends

static const int PIN_MOTOR[6] = { 21, 13, 22, 2, 15, 4 };   // dot 1..6, from pins.h
static const uint16_t DOT_ON_MS  = 1000;   // per-dot buzz duration
static const uint16_t DOT_GAP_MS = 400;    // silence between dots, same cell
static const uint32_t POLL_INTERVAL_MS = 700;

static long g_last_id = 0;   // commands with id <= this are already handled
static uint32_t g_last_poll = 0;

// ---------------------------------------------------------------------------

static void wifi_connect() {
  // A bare repeat of WiFi.begin() after a failed attempt can leave the
  // ESP-IDF driver thinking it is still mid-connection, which then rejects
  // the next begin() with "sta is connecting, return error" -- a stuck
  // internal state, not a real auth failure. disconnect() first forces a
  // clean reset so every attempt starts from the same known state.
  WiFi.disconnect(true, true);
  delay(200);

  Serial.printf("connecting to WiFi \"%s\"", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(400);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nconnected, IP %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.printf("\nFAILED to connect -- WiFi.status()=%d (see codes below), will keep retrying\n",
                  WiFi.status());
    Serial.println("  0 idle  1 no-SSID-found  4 connect-failed  6 disconnected");
    Serial.println("  If this repeats: wrong password, or the network is 5GHz-only");
    Serial.println("  (ESP32 only joins 2.4GHz), or the SSID is out of range/hidden.");
  }
}

static void motors_all_off() {
  for (int i = 0; i < 6; i++) digitalWrite(PIN_MOTOR[i], LOW);
}

static void buzz_dot(int dot) {
  if (dot < 1 || dot > 6) {
    Serial.printf("ignoring out-of-range dot %d\n", dot);
    return;
  }
  int pin = PIN_MOTOR[dot - 1];
  Serial.printf("buzz dot %d -> GPIO %d\n", dot, pin);
  digitalWrite(pin, HIGH);
  delay(DOT_ON_MS);
  digitalWrite(pin, LOW);
}

// Plays a full letter: every raised dot in reading order (1,2,3 then 4,5,6),
// one at a time, same pacing t3b_braille_patterns uses on the bench.
static void play_letter(int letter_id) {
  if (letter_id < 0 || letter_id >= BRAILLE_LETTER_COUNT) {
    Serial.printf("ignoring out-of-range letter_id %d\n", letter_id);
    return;
  }
  uint8_t mask = BRAILLE_PATTERN[letter_id];
  Serial.printf("letter #%d %s   mask 0x%02X   %s\n",
                letter_id, BRAILLE_NAME[letter_id], mask,
                BRAILLE_VERIFIED[letter_id] ? "verified" : "PLACEHOLDER");

  for (int i = 0; i < 6; i++) {
    if (!(mask & (1 << i))) continue;
    Serial.printf("  dot %d -> GPIO %d\n", i + 1, PIN_MOTOR[i]);
    digitalWrite(PIN_MOTOR[i], HIGH);
    delay(DOT_ON_MS);
    digitalWrite(PIN_MOTOR[i], LOW);
    delay(DOT_GAP_MS);
  }
  motors_all_off();
}

// Pulls one integer field out of a PostgREST JSON object, e.g. finds "dot":5
// in {"id":57,"dot":5,"letter_id":null}. Returns false if the key is missing
// OR its value is JSON null -- both mean "this field wasn't set," which
// matters here since 0 is a valid letter_id and must not be confused with
// "absent."
static bool extract_field(const String &body, const char *key, long &out) {
  String needle = String("\"") + key + "\":";
  int pos = body.indexOf(needle);
  if (pos < 0) return false;
  int valueStart = pos + needle.length();
  if (body.startsWith("null", valueStart)) return false;
  out = body.substring(valueStart).toInt();
  return true;
}

static void poll_for_command() {
  if (WiFi.status() != WL_CONNECTED) { wifi_connect(); return; }

  WiFiClientSecure client;
  client.setInsecure();   // skip TLS cert validation -- fine for a bench demo,
                           // not for anything handling sensitive data

  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/remote_commands"
             + "?device_id=eq." + ESP_DEVICE_ID
             + "&id=gt." + String(g_last_id)
             + "&order=id.asc&limit=1&select=id,dot,letter_id";

  http.begin(client, url);
  http.addHeader("apikey", SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);

  int code = http.GET();
  if (code == 200) {
    String body = http.getString();
    long id;
    if (extract_field(body, "id", id)) {
      long letterId, dotVal;
      if (extract_field(body, "letter_id", letterId)) {
        Serial.printf("command #%ld: letter_id %ld\n", id, letterId);
        play_letter((int)letterId);
      } else if (extract_field(body, "dot", dotVal)) {
        Serial.printf("command #%ld: dot %ld\n", id, dotVal);
        buzz_dot((int)dotVal);
      }
      g_last_id = id;
    }
    // body == "[]" -> no new command, nothing to do
  } else {
    Serial.printf("poll failed, HTTP %d\n", code);
  }
  http.end();
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  for (int i = 0; i < 6; i++) {
    pinMode(PIN_MOTOR[i], OUTPUT);
    digitalWrite(PIN_MOTOR[i], LOW);
  }
  Serial.println("\n=== t7: cloud-controlled letters ===");
  Serial.printf("map: %d of %d letters verified\n",
                BRAILLE_VERIFIED_COUNT, BRAILLE_LETTER_COUNT);
  WiFi.persistent(false);   // don't write WiFi config to flash on every begin()
  wifi_connect();
}

void loop() {
  if (millis() - g_last_poll >= POLL_INTERVAL_MS) {
    g_last_poll = millis();
    poll_for_command();
  }
}