#!/usr/bin/env python3
"""
Generate the corrected neural network architecture diagram:
  - 8 inputs
  - Dense 32 (ReLU): 288 parameters
  - Dense 16 (ReLU): 528 parameters
  - Head 1: Dense 3 (softmax) Confidence State: 51 parameters
  - Head 2: Dense 3 (softmax) Teaching Action: 51 parameters
  - Total: 6 Outputs (3 + 3), 918 Trainable Parameters
"""

import os
import subprocess

SVG_CONTENT = """<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="720" viewBox="0 0 1600 720">
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 1 L 8 5 L 0 9 z" fill="#94A3B8"/>
  </marker>
  <filter id="card-shadow" x="-5%" y="-5%" width="110%" height="115%">
    <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#0F172A" flood-opacity="0.06"/>
  </filter>
</defs>

<!-- Background -->
<rect width="1600" height="720" fill="#FFFFFF"/>

<!-- Header Title -->
<text x="800" y="60" font-family="'Segoe UI', Arial, sans-serif" font-size="28" font-weight="800" fill="#0F172A" text-anchor="middle" letter-spacing="-0.5">Dual-Head Multi-Task Neural Network Architecture</text>
<text x="800" y="92" font-family="'Segoe UI', Arial, sans-serif" font-size="16" font-weight="600" fill="#64748B" text-anchor="middle">8 Normalized Input Features • 2 Hidden Layers • 6 Total Outputs (3 + 3) • 918 Trainable Parameters</text>

<!-- ═════════ 1. INPUT LAYER (8 Features) ═════════ -->
<g transform="translate(60, 140)">
  <rect width="210" height="460" rx="18" fill="#FBF9FE" stroke="#8B5CF6" stroke-width="2.5" filter="url(#card-shadow)"/>
  <text x="105" y="48" font-family="'Segoe UI', Arial, sans-serif" font-size="20" font-weight="800" fill="#0F172A" text-anchor="middle">INPUT</text>
  <text x="105" y="74" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="600" fill="#7C3AED" text-anchor="middle">8 features</text>
  
  <!-- 8 Input Dots -->
  <g fill="#8B5CF6">
    <circle cx="105" cy="115" r="8"/>
    <circle cx="105" cy="150" r="8"/>
    <circle cx="105" cy="185" r="8"/>
    <circle cx="105" cy="220" r="8"/>
    <circle cx="105" cy="255" r="8"/>
    <circle cx="105" cy="290" r="8"/>
    <circle cx="105" cy="325" r="8"/>
    <circle cx="105" cy="360" r="8"/>
  </g>
  
  <text x="105" y="415" font-family="'Segoe UI', Arial, sans-serif" font-size="13" font-weight="700" fill="#6D28D9" text-anchor="middle">0 parameters</text>
  <text x="105" y="435" font-family="'Segoe UI', Arial, sans-serif" font-size="11.5" font-weight="500" fill="#94A3B8" text-anchor="middle">(raw input vector)</text>
</g>

<!-- Arrow 1 -> 2 -->
<path d="M 285 370 L 345 370" fill="none" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round" marker-end="url(#arrow)"/>

<!-- ═════════ 2. DENSE 32 (ReLU) ═════════ -->
<g transform="translate(360, 140)">
  <rect width="210" height="460" rx="18" fill="#F0FDF4" stroke="#10B981" stroke-width="2.5" filter="url(#card-shadow)"/>
  <text x="105" y="48" font-family="'Segoe UI', Arial, sans-serif" font-size="20" font-weight="800" fill="#0F172A" text-anchor="middle">DENSE 32</text>
  <text x="105" y="74" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="600" fill="#059669" text-anchor="middle">ReLU</text>
  
  <!-- Dots -->
  <g fill="#10B981">
    <circle cx="105" cy="115" r="8"/>
    <circle cx="105" cy="148" r="8"/>
    <circle cx="105" cy="181" r="8"/>
    <circle cx="105" cy="214" r="8"/>
    <circle cx="105" cy="247" r="8"/>
    <circle cx="105" cy="280" r="8"/>
    <circle cx="105" cy="313" r="8"/>
    <circle cx="105" cy="346" r="3"/>
    <circle cx="105" cy="358" r="3"/>
    <circle cx="105" cy="370" r="3"/>
  </g>
  
  <text x="105" y="415" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="800" fill="#047857" text-anchor="middle">288</text>
  <text x="105" y="433" font-family="'Segoe UI', Arial, sans-serif" font-size="12" font-weight="600" fill="#059669" text-anchor="middle">parameters</text>
  <text x="105" y="449" font-family="'Segoe UI', Arial, sans-serif" font-size="10.5" font-weight="500" fill="#6B7280" text-anchor="middle">(8 × 32 + 32)</text>
</g>

<!-- Arrow 2 -> 3 -->
<path d="M 585 370 L 645 370" fill="none" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round" marker-end="url(#arrow)"/>

<!-- ═════════ 3. DENSE 16 (ReLU) ═════════ -->
<g transform="translate(660, 140)">
  <rect width="210" height="460" rx="18" fill="#F0FDF4" stroke="#10B981" stroke-width="2.5" filter="url(#card-shadow)"/>
  <text x="105" y="48" font-family="'Segoe UI', Arial, sans-serif" font-size="20" font-weight="800" fill="#0F172A" text-anchor="middle">DENSE 16</text>
  <text x="105" y="74" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="600" fill="#059669" text-anchor="middle">ReLU</text>
  
  <!-- Dots -->
  <g fill="#10B981">
    <circle cx="105" cy="115" r="8"/>
    <circle cx="105" cy="150" r="8"/>
    <circle cx="105" cy="185" r="8"/>
    <circle cx="105" cy="220" r="8"/>
    <circle cx="105" cy="255" r="8"/>
    <circle cx="105" cy="290" r="8"/>
    <circle cx="105" cy="330" r="3"/>
    <circle cx="105" cy="342" r="3"/>
    <circle cx="105" cy="354" r="3"/>
  </g>
  
  <text x="105" y="415" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="800" fill="#047857" text-anchor="middle">528</text>
  <text x="105" y="433" font-family="'Segoe UI', Arial, sans-serif" font-size="12" font-weight="600" fill="#059669" text-anchor="middle">parameters</text>
  <text x="105" y="449" font-family="'Segoe UI', Arial, sans-serif" font-size="10.5" font-weight="500" fill="#6B7280" text-anchor="middle">(32 × 16 + 16)</text>
</g>

<!-- Split Branching Arrows -->
<!-- Path to Head 1 (Top) -->
<path d="M 885 370 L 965 370 L 965 245 L 1035 245" fill="none" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"/>
<!-- Path to Head 2 (Bottom) -->
<path d="M 885 370 L 965 370 L 965 495 L 1035 495" fill="none" stroke="#94A3B8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"/>

<!-- ═════════ 4. HEAD 1: CONFIDENCE STATE (Dense 3) ═════════ -->
<g transform="translate(1050, 150)">
  <rect width="480" height="190" rx="18" fill="#FDF2F8" stroke="#EC4899" stroke-width="2.5" filter="url(#card-shadow)"/>
  <text x="240" y="40" font-family="'Segoe UI', Arial, sans-serif" font-size="20" font-weight="800" fill="#0F172A" text-anchor="middle">DENSE 3 – softmax</text>
  <text x="240" y="66" font-family="'Segoe UI', Arial, sans-serif" font-size="15" font-weight="700" fill="#DB2777" text-anchor="middle">confidence state (3 outputs)</text>
  
  <text x="240" y="105" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="800" fill="#BE185D" text-anchor="middle">51 parameters</text>
  <text x="240" y="125" font-family="'Segoe UI', Arial, sans-serif" font-size="12" font-weight="500" fill="#9D174D" text-anchor="middle">Calculation: 16 × 3 + 3 = 51</text>
  
  <!-- Classes Badge Box -->
  <rect x="35" y="142" width="410" height="34" rx="8" fill="#FFFFFF" stroke="#FBCFE8" stroke-width="1.5"/>
  <text x="240" y="164" font-family="'Segoe UI', Arial, sans-serif" font-size="12.5" font-weight="600" fill="#475569" text-anchor="middle">
    Classes: <tspan font-weight="700" fill="#DB2777">CONFIDENT</tspan> • <tspan font-weight="700" fill="#DB2777">HESITANT</tspan> • <tspan font-weight="700" fill="#DB2777">GUESSING</tspan>
  </text>
</g>

<!-- ═════════ 5. HEAD 2: TEACHING ACTION (Dense 3) ═════════ -->
<g transform="translate(1050, 400)">
  <rect width="480" height="190" rx="18" fill="#F0FDF4" stroke="#0284C7" stroke-width="2.5" filter="url(#card-shadow)"/>
  <text x="240" y="40" font-family="'Segoe UI', Arial, sans-serif" font-size="20" font-weight="800" fill="#0F172A" text-anchor="middle">DENSE 3 – softmax</text>
  <text x="240" y="66" font-family="'Segoe UI', Arial, sans-serif" font-size="15" font-weight="700" fill="#0369A1" text-anchor="middle">teaching action (3 outputs)</text>
  
  <text x="240" y="105" font-family="'Segoe UI', Arial, sans-serif" font-size="14" font-weight="800" fill="#0369A1" text-anchor="middle">51 parameters</text>
  <text x="240" y="125" font-family="'Segoe UI', Arial, sans-serif" font-size="12" font-weight="500" fill="#075985" text-anchor="middle">Calculation: 16 × 3 + 3 = 51  (Fixed from Dense 4/68)</text>
  
  <!-- Classes Badge Box -->
  <rect x="35" y="142" width="410" height="34" rx="8" fill="#FFFFFF" stroke="#BAE6FD" stroke-width="1.5"/>
  <text x="240" y="164" font-family="'Segoe UI', Arial, sans-serif" font-size="12.5" font-weight="600" fill="#475569" text-anchor="middle">
    Classes: <tspan font-weight="700" fill="#0284C7">REPEAT</tspan> • <tspan font-weight="700" fill="#0284C7">HINT</tspan> • <tspan font-weight="700" fill="#0284C7">NORMAL_PRACTICE</tspan>
  </text>
</g>

<!-- Bottom Summary Bar -->
<g transform="translate(60, 630)">
  <rect width="1470" height="60" rx="14" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1.5"/>
  <text x="30" y="36" font-family="'Segoe UI', Arial, sans-serif" font-size="15" font-weight="700" fill="#0F172A">
    Total Trainable Parameters: <tspan fill="#059669">288 + 528 + 51 + 51 = 918 Parameters</tspan>
  </text>
  <text x="1440" y="36" font-family="'Segoe UI', Arial, sans-serif" font-size="14.5" font-weight="700" fill="#0369A1" text-anchor="end">
    Total Outputs: <tspan fill="#0284C7">3 (Confidence) + 3 (Teaching) = 6 Outputs</tspan>
  </text>
</g>

</svg>
"""

def main():
    out_dir = r"D:\eee-416 project\presentation_assets"
    os.makedirs(out_dir, exist_ok=True)
    
    svg_path = os.path.join(out_dir, "fixed_model_architecture.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(SVG_CONTENT)
    print(f"Saved SVG: {svg_path}")

    # Render high-res PNG via Chrome
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    png_path = os.path.join(out_dir, "fixed_model_architecture.png")
    cmd = [
        chrome_exe,
        "--headless",
        "--disable-gpu",
        f"--screenshot={png_path}",
        "--window-size=1600,740",
        "--force-device-scale-factor=2",
        "file:///" + svg_path.replace("\\", "/")
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Saved High-Res PNG: {png_path}")
    else:
        print("Chrome render error:", res.stderr)

if __name__ == "__main__":
    main()
