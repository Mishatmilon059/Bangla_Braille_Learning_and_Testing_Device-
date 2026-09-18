# AI Driven Bangla Braille Learning Device

**Department of Electrical and Electronic Engineering (EEE)**  
**Bangladesh University of Engineering and Technology (BUET)**  
**Course:** EEE 416 — Microprocessor and Embedded Systems Sessional  
**Project Group:** Group 08 (Section A2)  

---

## Project Team Members

| Student Name | Student ID | Academic Affiliation |
|---|:---:|---|
| **Santu Nag** | `2106055` | Department of EEE, Bangladesh University of Engineering and Technology (BUET) |
| **Md. Adib Hasan Audhi** | `2106056` | Department of EEE, Bangladesh University of Engineering and Technology (BUET) |
| **Mishat Hasan Milon** | `2106059` | Department of EEE, Bangladesh University of Engineering and Technology (BUET) |
| **Khalid Mehebub** | `2106065` | Department of EEE, Bangladesh University of Engineering and Technology (BUET) |

---

## Table of Contents

1. [Abstract](#abstract)
2. [System Architecture](#system-architecture)
3. [Hardware Specifications](#hardware-specifications)
4. [Bangla Braille Encoding Standard (50 Characters)](#bangla-braille-encoding-standard-50-characters)
5. [TinyML Pedagogical Model & Empirical Validation](#tinyml-pedagogical-model--empirical-validation)
6. [Repository File & Directory Structure](#repository-file--directory-structure)
7. [Cloning the Repository](#cloning-the-repository)

---

## Abstract

The **Bangla Braille Learning and Testing Device** is an accessible assistive pedagogical system designed for visually impaired learners. Developed as the final capstone design project for **EEE 416 (Microprocessor and Embedded Systems Sessional) at BUET**, the device combines a **6-dot tactile haptic matrix** (coin vibration motors) with **synchronized auditory speech feedback** and an **on-device dual-head neural network** that runs fully offline on an ESP32 microcontroller with zero machine learning runtime overhead. It supports both standalone offline practice and real-time remote classroom assessment via a web-connected teacher portal.

---

## System Architecture

The following diagram illustrates the end-to-end dataflow between specification, training pipelines, the web instrumentation platform, and the physical ESP32 embedded tutor:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CENTRAL SPECIFICATION                          │
│  spec/engine_spec.json (Features, Thresholds, Normalization Bounds)    │
│  data/braille_map.json (50 Letters, 6-Dot Patterns, Audio Tracks)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
  [tools/gen_engine.py]   [tools/gen_braille_header.py] [tools/gen_audio.py]
           │                        │                        │
  ┌────────┼────────┐               ▼                        ▼
  ▼        ▼        ▼      firmware/braille_map.h       web/audio/ &
web JS   Py Gen   C Header  assets/braille/*.svg         sd_card/mp3/
  │        │        │
  ▼        ▼        │
┌──────┐ ┌──────┐   │
│ Web  │ │ Synth│   │
│ MVP  │ │ Sim  │   │
└──┬───┘ └──┬───┘   │
   │        │       │
   ▼        ▼       │
┌──────────────┐    │
│ 2,242 Rows   │    │
│ (1000 Real + │    │
│  1242 Synth) │    │
└──────┬───────┘    │
       ▼            │
[tools/train.py]    │
       │            │
       ▼            ▼
 ┌──────────────────────────────────────┐
 │       firmware/braille_tutor/        │
 │  model_weights.h (1,734 Floats, 7KB) │
 │  inference.h (0.1ms Forward Pass)    │
 │  rule_engine.h (Fixed Normalization) │
 └──────────────────┬───────────────────┘
                    ▼
 ┌──────────────────────────────────────┐
 │     PHYSICAL EMBEDDED HARDWARE       │
 │ ESP32 · 6 Buttons · 6 Coin Motors    │
 │ ULN2803A · DFPlayer · MicroSD · RTC   │
 └──────────────────────────────────────┘
```

Detailed architectural vector diagrams (SVG and high-resolution PNG) are located in [`docs/diagrams_v2/`](docs/diagrams_v2/).

---

## Hardware Specifications

### Component List

| Component | Specification | Quantity | Function |
|---|---|:---:|---|
| **Microcontroller** | ESP32-WROOM-32 (38-pin, 240 MHz Dual Core) | 1 | Core compute, TinyML inference, GPIO debounce |
| **Haptic Actuators** | 1027 Coin Vibration Motors (10mm, 3V, 80mA) | 6 | Tactile 6-dot Braille matrix |
| **Motor Driver** | ULN2803A Darlington Transistor Array (DIP-18) | 1 | Inductive load sink & integrated flyback clamping |
| **Input Buttons** | 12×12×7.3mm Tactile Push Buttons | 7 | 6 dot input buttons + 1 submit button |
| **Audio Module** | DFPlayer Mini (FN-M16P MP3 Player) | 1 | Hardware MP3 decoding via UART |
| **Loudspeaker** | 3W 8Ω Enclosed Speaker (40mm) | 1 | Spoken letter pronunciation & audio cues |
| **External Storage** | MicroSD Card SPI Adapter + 16GB MicroSD Card | 1 | Offline storage for 60 spoken audio prompt files |
| **Real-Time Clock** | DS3231 I2C RTC Module | 1 | Session epoch tracking across power cycles |
| **Power Supply** | 5V 2A DC Adapter + 1000 µF 16V Electrolytic Cap | 1 | High-current power rail with inrush decoupling |
| **Resistors & Misc** | 6× 1 kΩ (LED/Pull), 3× 10 kΩ (Strapping pulldowns) | - | Pin protection & pull resistors |
| **Enclosure** | 3D Printed PLA Case & Acrylic Cutout Panel | 1 | Ergonomic desk console housing |

### Canonical Pinout Configuration

The canonical pin assignments (configured in [`firmware/braille_tutor/pins.h`](firmware/braille_tutor/pins.h)) are engineered to avoid ESP32 boot strapping conflicts:

| Peripherals | GPIO Pin | Hardware Configuration & Notes |
|---|:---:|---|
| **Dot Buttons (1–6)** | `GPIO 32, 33, 25, 26, 27, 14` | Internal pull-up enabled (`INPUT_PULLUP`). Active LOW when pressed to GND. |
| **Submit Button** | `GPIO 12` | Boot strapping pin. Pulled to GND during boot; pressed to GND via active switch. |
| **Coin Motors (1–6)** | `GPIO 21, 13, 22, 2, 15, 4` | Connected to ULN2803A Inputs 1–6. Active HIGH drive. ULN2803A COM pin tied to +5V. |
| **DFPlayer Audio** | `GPIO 16 (RX), GPIO 17 (TX)` | ESP32 HardwareSerial (UART2). 1 kΩ series resistor on TX line to suppress noise. |
| **MicroSD Module** | `GPIO 18 (SCK), 19 (MISO), 23 (MOSI), 5 (CS)` | Hardware VSPI interface operating at 20 MHz. |
| **I2C RTC (DS3231)** | `GPIO 21 (SDA), GPIO 22 (SCL)` | Standard I2C bus (optional, activated via `USE_RTC 1` in `pins.h`). |

> [!CAUTION]
> **Electrical Safety & Circuit Protection**:
> **Never drive vibration motors directly from ESP32 GPIOs**: All six coin motors firing simultaneously draw ~480 mA. A ULN2803A Darlington array must be used, with its COM pin tied to +5V for inductive flyback protection.

---

## Bangla Braille Encoding Standard (50 Characters)

The repository implements the official **Bangladesh National Braille Code**, verified against Wikipedia's Bengali Braille standard: [বাংলা ব্রেইল - উইকিপিডিয়া](https://bn.wikipedia.org/wiki/%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE_%E0%A6%AC%E0%A7%8D%E0%A6%B0%E0%A7%87%E0%A6%87%E0%A6%B2) and cross-referenced with *World Braille Usage (3rd Edition, Perkins/ICEB)*.

- **11 Vowels**: অ (`1`), আ (`345`), ই (`24`), ঈ (`35`), উ (`136`), ঊ (`1256`), ঋ (`5 + 1235`), এ (`15`), ঐ (`34`), ও (`135`), ঔ (`246`).
- **39 Consonants**: ক (`13`), খ (`1346`), গ (`1245`), ঘ (`126`), ঙ (`346`), চ (`14`), ছ (`16`), জ (`245`), ঝ (`1356`), ঞ (`25`), ট (`23456`), ঠ (`2456`), ড (`1246`), ঢ (`123456`), ণ (`3456`), ত (`2345`), থ (`1456`), দ (`145`), ধ (`2346`), ন (`1345`), প (`1234`), ফ (`124`), ব (`12`), ভ (`1236`), ম (`134`), য (`13456`), র (`1235`), ল (`123`), শ (`146`), ষ (`12346`), স (`234`), হ (`125`), ড় (`12456`), ঢ় (`12356`), য় (`26`), ৎ (`5 + 2345`), ং (`56`), ঃ (`6`), ঁ (`3`).

### Two-Cell Compound Characters (ঋ and ৎ)
In Bengali orthography, ঋ (*ri*) and র (*ra*) share the primary dot matrix `[1, 2, 3, 5]`, while ত (*ta*) and ৎ (*khanda ta*) share `[2, 3, 4, 5]`. To resolve this collision haptically without tactile ambiguity:
- **Two-Cell Representation**: ঋ and ৎ are encoded as two sequential Braille cells.
- **Haptic Timing**: In Learn and Tutor modes, an initial 150 ms pulse on **Dot 5** serves as the indicator prefix, followed by a 200 ms pause, followed by the vibration of the primary letter cell.

---

## TinyML Pedagogical Model & Empirical Validation

### Network Architecture

The on-device pedagogical agent uses a dual-head feedforward neural network:

$$\mathbf{x} \in \mathbb{R}^8 \longrightarrow \text{Dense}(32, \text{ReLU}) \longrightarrow \text{Dense}(16, \text{ReLU}) \longrightarrow \begin{cases} \text{Head}_{\text{TA}} \in \mathbb{R}^3 & (\text{Teaching Action}) \\ \text{Head}_{\text{CS}} \in \mathbb{R}^3 & (\text{Confidence State}) \end{cases}$$

1. **Total Parameters**: 1,734 trainable floating-point weights (6,936 bytes).
2. **Execution Latency**: **~0.1 milliseconds** on an ESP32 at 240 MHz.
3. **Memory Footprint**: 6,936 bytes in Flash (`PROGMEM`) + 192 bytes temporary stack RAM during forward pass. Total memory required: **~7.1 KB of 520 KB SRAM** (< 1.4% capacity).

### Feature Formulation (8 Model Inputs of 14 Logged)

| Feature Name | Type | Range | Description |
|---|:---:|:---:|---|
| `response_time` | float | 0–30,000 ms | Elapsed time from prompt completion to debounced submit press |
| `press_duration` | float | 0–5,000 ms | Average hold duration across raised dot keys |
| `retry_count` | int | 0–10 | Number of re-attempts within the current character trial |
| `prev_accuracy` | float | 0.0–1.0 | Exponential moving average of learner accuracy across past attempts |
| `prev_mastery` | float | 0.0–1.0 | Historical mastery score for the specific character prompt |
| `hint_count` | int | 0–10 | Frequency of tactile/audio hints requested during the trial |
| `current_streak` | int | 0–50 | Number of consecutive correct submissions |
| `wrong_streak` | int | 0–20 | Number of consecutive incorrect submissions |

### Experimental Results (Evaluated on 2,242 Total Trials)

| Task Head | Class Label | Test Support ($N$) | Precision | Recall | F1-Score | Combined Accuracy | Real-Only Accuracy | Majority Baseline |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Teaching Action** | `REPEAT` | 90 | 1.000 | 0.989 | **0.994** | **99.41%** | **98.56%** | 46.59% |
| | `HINT` | 90 | 0.978 | 1.000 | **0.989** | | | |
| | `NORMAL_PRACTICE` | 157 | 1.000 | 0.994 | **0.997** | | | |
| **Confidence State** | `CONFIDENT` | 94 | 0.910 | 0.968 | **0.938** | **94.07%** | **91.37%** | 42.43% |
| | `HESITANT` | 143 | 0.956 | 0.902 | **0.928** | | | |
| | `GUESSING` | 100 | 0.951 | 0.970 | **0.960** | | | |

---

## Repository File & Directory Structure

```
.
├── assets/
│   └── braille/                     # Generated vector SVGs and PNG contact sheets for all 50 characters
├── Bangla_Braille_39_Consonants_PNG/# 39 Consonant reference cards citing World Braille Usage (3rd Ed.)
├── braille_img/                     # Ground-truth reference images for Bengali vowels
├── data/
│   ├── braille_map.json             # Primary ground truth: 50 letters, dot arrays, audio mappings
│   ├── braille_verified/            # Cropped verification cell images
│   └── braille_verified.zip         # Packaged visual verification archives
├── dataset/
│   ├── real.csv                     # Raw human participant trial logs (P01-P04)
│   ├── real_v2.csv, real_v3.csv     # Preprocessed and validated human attempt datasets (1,000 trials)
│   ├── synthetic.csv                # Calibrated synthetic learner simulations
│   ├── synthetic_2k.csv             # 1,242 synthetic rows matched to empirical distributions
│   └── synthetic_targeted.csv       # Targeted rare-class training samples
├── docs/
│   ├── diagrams/                    # System diagrams v1 (PNG & SVG)
│   ├── diagrams_v2/                 # High-resolution diagrams (Architecture, BOM, Flow)
│   ├── presentation/                # Academic presentation slide decks and progress reports
│   │   ├── BraillePresentation.pptx # Technical presentation slides
│   │   ├── EEE416_G8_FinalDemo.pptx # Final demonstration deck
│   │   └── G8 Project Progress.pdf  # Project milestone documentation
│   ├── screenshots/                 # Web interface and teacher dashboard captures
│   ├── FINAL_DEMO_CHECKLIST.md      # Hardware demonstration and QA checklist
│   ├── PROJECT_REPORT.md            # Comprehensive scientific technical report
│   └── TEAM_TECHNICAL_GUIDE.md      # File-by-file technical guide and viva Q&A
├── enclosure/
│   ├── 3d_preview.html              # Interactive Three.js 3D web preview of the enclosure
│   ├── braille_tutor_case.scad      # OpenSCAD 3D parametric desk console case
│   ├── top_panel.stl                # Ready-to-print 3D mesh for top button/motor panel
│   ├── top_panel_cutout.svg         # 1:1 scale 2D vector file for laser-cut acrylic top plates
│   └── top_panel_layout.scad        # Parametric layout generator for component cutouts
├── firmware/
│   ├── braille_tutor/               # Main autonomous offline embedded firmware
│   │   ├── braille_map.h            # [Generated] 50-letter dot lookup tables & prefix flags
│   │   ├── braille_tutor.ino        # Core microcontroller application loop
│   │   ├── hardware.h               # Peripheral abstractions (audio, motors, debounce)
│   │   ├── inference.h              # Pure C forward pass for 1,734-param neural network
│   │   ├── learner_state.h          # On-device feature tracker and moving average calculator
│   │   ├── model_weights.h          # [Generated] Static C float arrays of trained MLP weights
│   │   ├── pins.h                   # Canonical GPIO pin mappings and hardware macros
│   │   ├── platformio.ini           # PlatformIO project configuration
│   │   └── rule_engine.h            # [Generated] Feature normalizer & rule fallback logic
│   ├── t11_ml_test/                 # Side-by-side firmware comparing TinyML decisions vs rule engine
│   └── tests/                       # Staged bring-up sketches (t1_blink to t11_testing)
├── models/
│   ├── golden_vectors.json          # 20 boot self-test vectors with expected model outputs
│   ├── metrics_final.json           # Comprehensive evaluation metrics, confusion matrices & F1 scores
│   └── model.tflite                 # 8-bit quantized reference model
├── sd_card/
│   └── mp3/                         # 60 zero-padded MP3 audio files (0001.mp3 to 0060.mp3) for DFPlayer
├── spec/
│   └── engine_spec.json             # Central specification for features, thresholds, and outputs
├── supabase/
│   ├── full_setup.sql               # Complete idempotent database schema (commands, attempts, telemetry)
│   └── schema.sql                   # Base attempts table schema
├── tools/                           # Python pipelines for code generation, training & validation
│   ├── gen_audio.py                 # Generates spoken audio prompts via TTS
│   ├── gen_braille_header.py        # Generates firmware/braille_tutor/braille_map.h
│   ├── gen_braille_images.py        # Generates vector and PNG character visual representations
│   ├── gen_engine.py                # Transpiles engine_spec.json into JS, C, and Python rule engines
│   ├── run_all_tests.py             # Master automated validation suite
│   ├── test_parity.py               # Cross-runtime parity verification (JS == C == Python)
│   ├── train_and_export.py          # Trains dual-head MLP and exports model_weights.h
│   └── validate_braille_map.py      # Verifies 50 characters against national standard
├── web/                             # Browser data-collection application & teacher telemetry portal
│   ├── audio/                       # Web-optimized audio assets
│   ├── data/braille_map.json        # Frontend character configuration
│   ├── app.js                       # Core interactive student tutor web client
│   ├── config.js                    # Supabase public client connection configuration
│   ├── index.html                   # Student practice & data collection interface
│   ├── teacher.html, teacher.js     # Real-time remote teacher control & assessment dashboard
│   ├── remote_control.html          # Lightweight single-character trigger panel
│   └── rule_engine.js               # [Generated] In-browser pedagogical classification engine
├── package.json                     # Project manifest and dev server scripts
├── requirements.txt                 # Python dependencies
└── USER_MANUAL.md                   # Bengali user guide for participant testing
```

---

## Cloning the Repository

To clone this repository and inspect the project files:

```bash
git clone https://github.com/Mishatmilon059/Bangla_Braille_Learning_and_Testing_Device-.git
cd Bangla_Braille_Learning_and_Testing_Device-
```
