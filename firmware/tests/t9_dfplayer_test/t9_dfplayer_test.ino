// Bring-up 9: DFPlayer only -- type or tap a track number 1..50, hear it.
//
// Two input paths, both work at the same time:
//   - Serial Monitor: type a number 1-50, press Enter
//   - web/dfplayer_test.html: tap a number, sent via Supabase (same
//     remote_commands table t7/t8 use -- no new migration needed)
//
// This sketch only tests audio. No motors, no buttons, no braille map -- if
// you want to confirm a specific letter's mapping, use t3b_braille_patterns
// or t8_cloud_quiz instead. Here, "5" just means "play file 0005.mp3."
//
// SD card layout the DFPlayer requires -- it plays by NUMBER, not filename:
//     /mp3/0001.mp3 ... /mp3/0050.mp3   letters
//     /mp3/0051.mp3 ... /mp3/0060.mp3   system prompts
// Copy the generated sd_card/mp3/ folder to the DFPlayer's OWN microSD card
// (not the ESP32's separate SD module -- these are two different cards).
//
// Wiring: ESP32 GPIO17 -> 1k resistor -> DFPlayer RX
//         ESP32 GPIO16 <-              DFPlayer TX
//         DFPlayer VCC -> 5V, GND -> GND, SPK_1/SPK_2 -> speaker
//
// Testing the web path without opening the page -- insert a command with curl:
//   curl -X POST 'https://rufaacgatrebsyxnyfbq.supabase.co/rest/v1/remote_commands' \
//     -H "apikey: sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-" \
//     -H "Authorization: Bearer sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-" \
//     -H "Content-Type: application/json" \
//     -d '{"device_id":"esp32_01","letter_id":4}'
//   (letter_id 4 -> track 5, since the web page sends letter_id = track - 1,
//   matching braille_map.h's numbering elsewhere in this project)

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <DFRobotDFPlayerMini.h>

#include "secrets.h"   // WIFI_SSID, WIFI_PASS

#define PIN_DF_RX 16
#define PIN_DF_TX 17

static const char *SUPABASE_URL      = "https://rufaacgatrebsyxnyfbq.supabase.co";
static const char *SUPABASE_ANON_KEY = "sb_publishable_lI3qv5Xk44GAhzL4R7I2GA_4k1aUar-";
static const char *ESP_DEVICE_ID     = "esp32_01";

static const uint32_t POLL_INTERVAL_MS = 700;
static long g_last_id = 0;
static uint32_t g_last_poll = 0;

DFRobotDFPlayerMini df;
bool g_df_ok = false;

// ---------------------------------------------------------------------------

static void play_track(int n, const char *source) {
  if (n < 1 || n > 50) {
    Serial.printf("%s: %d out of range, tracks are 1-50\n", source, n);
    return;
  }
  Serial.printf("%s: play track %d\n", source, n);
  if (g_df_ok) df.play(n);
  else Serial.println("  (DFPlayer not connected -- nothing to play)");
}

static void handle_serial() {
  if (!Serial.available()) return;
  int n = Serial.parseInt();
  while (Serial.available()) Serial.read();   // clear the rest of the line
  if (n != 0) play_track(n, "serial");
}

// ---------------------------------------------------------------------------

static void wifi_connect() {
  WiFi.disconnect(true, true);   // clear any stuck "connecting" state first
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
    Serial.printf("\nFAILED to connect -- WiFi.status()=%d, will keep retrying\n", WiFi.status());
  }
}

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
  client.setInsecure();

  HTTPClient http;
  String url = String(SUPABASE_URL) + "/rest/v1/remote_commands"
             + "?device_id=eq." + ESP_DEVICE_ID
             + "&id=gt." + String(g_last_id)
             + "&order=id.asc&limit=1&select=id,letter_id";

  http.begin(client, url);
  http.addHeader("apikey", SUPABASE_ANON_KEY);
  http.addHeader("Authorization", String("Bearer ") + SUPABASE_ANON_KEY);

  int code = http.GET();
  if (code == 200) {
    String body = http.getString();
    long id, letterId;
    if (extract_field(body, "id", id)) {
      if (extract_field(body, "letter_id", letterId)) {
        play_track((int)letterId + 1, "web");   // letter_id is 0-49, track is 1-50
      }
      g_last_id = id;
    }
  } else {
    Serial.printf("poll failed, HTTP %d\n", code);
  }
  http.end();
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== t9: DFPlayer track test ===");
  Serial.println("type 1-50 + Enter here, or tap a number on dfplayer_test.html");

  Serial2.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(400);
  g_df_ok = df.begin(Serial2, /*isACK=*/true, /*doReset=*/true);
  if (g_df_ok) {
    df.volume(22);
    Serial.printf("DFPlayer ok, %d files on card (expect 60)\n", df.readFileCounts());
  } else {
    Serial.println("DFPlayer not found -- check wiring, card FAT32, /mp3 files present");
  }

  WiFi.persistent(false);
  wifi_connect();
}

void loop() {
  handle_serial();

  if (millis() - g_last_poll >= POLL_INTERVAL_MS) {
    g_last_poll = millis();
    poll_for_command();
  }
}
