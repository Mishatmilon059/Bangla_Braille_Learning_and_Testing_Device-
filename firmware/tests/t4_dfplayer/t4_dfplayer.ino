// Bring-up 4: DFPlayer Mini audio.
//
// Expect: a file count of 60, then tracks 1, 2, 3 (Bangla letters) and 51
// ("সঠিক") play in turn, then track 1 again by a different addressing mode.
//
// SD card layout the DFPlayer requires -- it plays by NUMBER, not filename:
//     /mp3/0001.mp3 ... /mp3/0050.mp3   letters
//     /mp3/0051.mp3 ... /mp3/0060.mp3   system prompts
// Copy the CONTENTS of the generated sd_card/ folder to the card root, so the
// card holds /mp3/0001.mp3 and not /sd_card/mp3/0001.mp3. FAT32 only.
//
// Wiring: ESP32 PIN_DF_TX -> 1k resistor -> DFPlayer RX
//         ESP32 PIN_DF_RX <-              DFPlayer TX
//         DFPlayer VCC -> 5V (not 3V3), GND -> GND, common ground everywhere
//         Speaker across SPK_1 and SPK_2. Neither leg goes to GND: grounding
//         one is silent and can destroy the internal amplifier. 4-8 ohm, 3 W.
//         Driving an external amp instead? Use DAC_L/DAC_R + GND and leave
//         SPK_1/SPK_2 open. Never both outputs at once.
//
// "begin() failed" almost always means the card is not FAT32, the mp3 folder
// is missing, or RX/TX are swapped.
//
// Keep isACK true below. begin() ends in `|| !isACK`, so with it false the
// call returns true even with the module unplugged and this test proves
// nothing.
#include <DFRobotDFPlayerMini.h>

// Defaults match firmware/braille_tutor/pins.h. The Arduino/ bench prototypes
// wire the DFPlayer to different pins -- RX 25, TX 23 -- so override these two
// when testing that build.
#ifndef PIN_DF_RX
#define PIN_DF_RX 16   // ESP32 receives  <- DFPlayer TX   (bench build: 25)
#endif
#ifndef PIN_DF_TX
#define PIN_DF_TX 17   // ESP32 transmits -> DFPlayer RX   (bench build: 23)
#endif

DFRobotDFPlayerMini df;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== t4: DFPlayer ===");
  Serial.printf("UART2 rx=%d tx=%d\n", PIN_DF_RX, PIN_DF_TX);
  Serial2.begin(9600, SERIAL_8N1, PIN_DF_RX, PIN_DF_TX);
  delay(400);
  if (!df.begin(Serial2, /*isACK=*/true, /*doReset=*/true)) {
    Serial.println("FAIL: DFPlayer begin() failed.");
    Serial.println("  - card FAT32 formatted?");
    Serial.println("  - files in /mp3 named 0001.mp3 ... ?");
    Serial.println("  - RX/TX swapped?");
    Serial.println("  - VCC on 5V, and a common ground with the ESP32?");
    while (true) delay(1000);
  }
  df.volume(22);
  Serial.printf("ok. files on card: %d (expect 60)\n", df.readFileCounts());
  Serial.println("A count of 0 or -1 means the module is talking but cannot");
  Serial.println("read the card. Any silence past this point is the speaker.");
}

void loop() {
  // playMp3Folder() addresses /mp3/000N.mp3 by number. This is what
  // braille_tutor.ino and the p6 bench sketch use, so test it first.
  Serial.println("\n-- playMp3Folder(): needs the files in /mp3");
  const uint16_t tracks[] = { 1, 2, 3, 51 };
  for (uint16_t t : tracks) {
    Serial.printf("   playMp3Folder(%u)\n", t);
    df.playMp3Folder(t);
    delay(2000);
  }

  // play() ignores folders and takes the Nth file in the card's index order.
  // If this one sounds and the folder version above stayed silent, the files
  // are not where playMp3Folder() looks for them.
  Serial.println("-- play(1): Nth file in index order, folders ignored");
  df.play(1);
  delay(2000);

  Serial.println("PASS if you heard five clips.");
  delay(1500);
}
