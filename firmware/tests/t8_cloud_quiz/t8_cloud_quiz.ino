// Bring-up 9b: DFPlayer diagnostic -- checks each step, prints WHY it failed.
//
// Pure hardware test, no WiFi, no cloud -- isolates the DFPlayer/SD card
// problem from everything else while you're debugging it.
//
// What it checks, in order, printed as [1/4] .. [4/4]:
//   1. UART2 opens (this basically can't fail -- confirms code is running)
//   2. df.begin() -- and if it fails, reads the module's own error message
//      back over the wire instead of just saying "failed"
//   3. File count on the card (expect 60: 0001-0050 letters, 0051-0060 prompts)
//   4. Actually plays track 1 and waits for the module's own "play finished"
//      feedback -- if THIS never arrives, the module isn't hearing commands
//      even though begin() succeeded
//
// Serial Monitor: 115200 baud, line ending "Newline".
//   d        re-run the full diagnostic without resetting the board
//   1-50     play that track directly, watch for feedback

#include <DFRobotDFPlayerMini.h>

#define PIN_DF_RX 16   // ESP32 receives  <- DFPlayer TX  (board may print "RX2")
#define PIN_DF_TX 17   // ESP32 transmits -> DFPlayer RX  (board may print "TX2", through 1k resistor)

DFRobotDFPlayerMini df;
bool g_df_ok = false;

// ---------------------------------------------------------------------------
// Turns the library's raw type/value codes into a plain-English diagnosis.
// This is the same mechanism the DFRobotDFPlayerMini library's own example
// sketch uses -- it's how you find out WHY, not just THAT, something failed.
// ---------------------------------------------------------------------------
static void print_detail(uint8_t type, int value) {
  switch (type) {
    case TimeOut:
      Serial.println("  -> TIMEOUT: nothing came back from the DFPlayer at all.");
      Serial.println("     Most likely: RX/TX swapped, DFPlayer not powered,");
      Serial.println("     or a wiring/ground fault between it and the ESP32.");
      break;
    case WrongStack:
      Serial.println("  -> Received a malformed reply (wrong stack).");
      Serial.println("     Usually noisy/loose wiring, or wrong baud rate.");
      break;
    case DFPlayerCardInserted:  Serial.println("  -> event: card inserted");   break;
    case DFPlayerCardRemoved:   Serial.println("  -> event: card removed");    break;
    case DFPlayerCardOnline:    Serial.println("  -> event: card online");    break;
    case DFPlayerUSBInserted:   Serial.println("  -> event: USB inserted");    break;
    case DFPlayerUSBRemoved:    Serial.println("  -> event: USB removed");     break;
    case DFPlayerPlayFinished:
      Serial.printf("  -> feedback: track %d finished playing (module IS responding)\n", value);
      break;
    case DFPlayerError:
      Serial.print("  -> DFPlayer reported an error: ");
      switch (value) {
        case Busy:
          Serial.println("NO SD CARD FOUND.");
          Serial.println("     Check: is a microSD card physically in the DFPlayer's");
          Serial.println("     OWN slot (not the ESP32's separate SD module)? FAT32?");
          break;
        case Sleeping:          Serial.println("module is sleeping");                  break;
        case SerialWrongStack:  Serial.println("wrong stack over serial");             break;
        case CheckSumNotMatch:  Serial.println("checksum mismatch (noisy wiring?)");    break;
        case FileIndexOut:      Serial.println("that track number doesn't exist on the card"); break;
        case FileMismatch:
          Serial.println("CANNOT FIND THAT FILE.");
          Serial.println("     Check: are files named exactly 0001.mp3 .. 0050.mp3,");
          Serial.println("     zero-padded to 4 digits, sitting in /mp3 at the card root?");
          break;
        case Advertise:         Serial.println("busy playing an advertisement track"); break;
        default:                Serial.printf("unknown code %d\n", value);             break;
      }
      break;
    default:
      Serial.printf("  -> unhandled message type %d, value %d\n", type, value);
  }
}

// Drains and prints every pending message/error from the module for a bit.
// Call this right after anything that might have triggered a response.
static void drain_feedback(uint32_t window_ms) {
  uint32_t start = millis();
  bool saw_any = false;
  while (millis() - start < window_ms) {
    if (df.available()) {
      saw_any = true;
      print_detail(df.readType(), df.read());
    }
    delay(10);
  }
  if (!saw_any) Serial.println("  -> (nothing came back in this window)");
}

// ---------------------------------------------------------------------------

static void run_diagnostic() {
  Serial.println("\n================ DFPlayer diagnostic ================");

  Serial.println("[1/4] UART2 open (GPIO16 RX2 <- DFPlayer TX, GPIO17 TX2 -> 1k -> DFPlayer RX)");
  Serial2.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(500);   // give the module time to power up before we talk to it
  Serial.println("  -> UART2 opened at 9600 baud (this step doesn't confirm the module heard it)");

  Serial.println("[2/4] df.begin() -- waiting for the module to acknowledge...");
  g_df_ok = df.begin(Serial2, /*isACK=*/true, /*doReset=*/true);
  if (g_df_ok) {
    Serial.println("  -> PASS: module acknowledged, two-way communication works");
  } else {
    Serial.println("  -> FAIL: begin() did not get a valid handshake");
    drain_feedback(2000);   // often reveals WHY (e.g. "Busy" = no SD card)
  }

  if (!g_df_ok) {
    Serial.println("=======================================================\n");
    return;   // steps 3-4 need a working begin(), no point continuing
  }

  Serial.println("[3/4] file count on card");
  int n = df.readFileCounts();
  Serial.printf("  -> %d files found (expect 60: 0001-0050 letters, 0051-0060 prompts)\n", n);
  if (n <= 0) {
    Serial.println("  -> 0 files: card present but unreadable, wrong format, or");
    Serial.println("     the /mp3 folder is missing/misnamed.");
  } else if (n < 60) {
    Serial.println("  -> fewer than 60: some tracks didn't copy across. Re-copy");
    Serial.println("     sd_card/mp3/ to the card root and check for gaps.");
  }

  Serial.println("[4/4] playback test -- playing track 1, watching for feedback");
  df.volume(22);
  df.play(1);
  drain_feedback(4000);
  Serial.println("  (if you saw 'track 1 finished playing' above, the module IS");
  Serial.println("   receiving commands -- if you still heard nothing, check the");
  Serial.println("   speaker wiring on SPK_1/SPK_2 and the volume level instead.)");

  Serial.println("=======================================================\n");
}

// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== t9b: DFPlayer diagnostic ===");
  run_diagnostic();
  Serial.println("type 'd' to re-run the diagnostic, or 1-50 to play a track");
}

void loop() {
  // Background: print any async event (card removed, play finished, error)
  // the instant it happens, not just right after we asked for something.
  if (df.available()) print_detail(df.readType(), df.read());

  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.equalsIgnoreCase("d")) {
      run_diagnostic();
    } else if (line.length() > 0) {
      int n = line.toInt();
      if (n >= 1 && n <= 50) {
        if (!g_df_ok) {
          Serial.println("DFPlayer not initialized -- run 'd' first to see why");
        } else {
          Serial.printf("playing track %d...\n", n);
          df.play(n);
          drain_feedback(3000);
        }
      } else {
        Serial.println("type a number 1-50, or 'd' to re-run diagnostics");
      }
    }
  }
}