#!/usr/bin/env python3
"""
Generate ultra-realistic smartphone mockups using Chrome headless.
Builds HTML+CSS templates with pixel-perfect modern mobile chassis,
status bars, dynamic island, and native typography.
"""

import os
import base64
import subprocess
from PIL import Image

def get_base64_data_uri(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return "data:image/png;base64," + base64.b64encode(data).decode("utf-8")

def crop_screen1_parts(img_path):
    """Splits screen 1 into body and bottom nav for docked mobile layout."""
    im = Image.open(img_path).convert("RGBA")
    w, h = im.size
    # Body: 0 to 648
    body = im.crop((0, 0, w, 648))
    nav = im.crop((0, 648, w, h))

    body_path = r"D:\eee-416 project\presentation_assets\temp_screen1_body.png"
    nav_path = r"D:\eee-416 project\presentation_assets\temp_screen1_nav.png"
    body.save(body_path, "PNG")
    nav.save(nav_path, "PNG")

    return get_base64_data_uri(body_path), get_base64_data_uri(nav_path)

def create_phone_css():
    return """
    :root {
      --phone-w: 400px;
      --phone-h: 840px;
      --bezel: 12px;
      --radius-outer: 50px;
      --radius-inner: 38px;
    }

    .phone-wrapper {
      position: relative;
      display: inline-block;
      margin: 30px 40px;
      filter: drop-shadow(0 30px 50px rgba(15, 23, 42, 0.28))
              drop-shadow(0 10px 20px rgba(15, 23, 42, 0.15));
    }

    /* Side physical buttons */
    .btn-action {
      position: absolute;
      left: -3px;
      top: 130px;
      width: 4px;
      height: 28px;
      background: #334155;
      border-radius: 2px 0 0 2px;
    }
    .btn-vol-up {
      position: absolute;
      left: -3px;
      top: 175px;
      width: 4px;
      height: 52px;
      background: #334155;
      border-radius: 2px 0 0 2px;
    }
    .btn-vol-down {
      position: absolute;
      left: -3px;
      top: 238px;
      width: 4px;
      height: 52px;
      background: #334155;
      border-radius: 2px 0 0 2px;
    }
    .btn-power {
      position: absolute;
      right: -3px;
      top: 185px;
      width: 4px;
      height: 75px;
      background: #334155;
      border-radius: 0 2px 2px 0;
    }

    /* Metallic phone body */
    .phone-chassis {
      width: calc(var(--phone-w) + var(--bezel) * 2);
      height: calc(var(--phone-h) + var(--bezel) * 2);
      background: linear-gradient(145deg, #2d3748, #0f172a 40%, #1e293b 80%, #334155);
      border-radius: var(--radius-outer);
      padding: var(--bezel);
      position: relative;
      box-shadow: 
        inset 0 0 0 1.5px rgba(255, 255, 255, 0.2),
        inset 0 0 0 3px rgba(0, 0, 0, 0.8);
    }

    /* Top speaker grill */
    .phone-speaker {
      position: absolute;
      top: 5px;
      left: 50%;
      transform: translateX(-50%);
      width: 60px;
      height: 3.5px;
      background: #090d16;
      border-radius: 3px;
      z-index: 100;
    }

    /* Phone display area */
    .phone-screen {
      width: var(--phone-w);
      height: var(--phone-h);
      border-radius: var(--radius-inner);
      overflow: hidden;
      background: #f8fafc;
      position: relative;
      display: flex;
      flex-direction: column;
      box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.15);
    }

    /* Status Bar */
    .status-bar {
      height: 42px;
      min-height: 42px;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 24px;
      position: relative;
      z-index: 50;
      border-bottom: 1px solid rgba(0, 0, 0, 0.02);
    }
    .status-time {
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-weight: 700;
      font-size: 14px;
      color: #0f172a;
      letter-spacing: -0.2px;
    }

    /* Dynamic Island */
    .dynamic-island {
      position: absolute;
      left: 50%;
      top: 8px;
      transform: translateX(-50%);
      width: 108px;
      height: 27px;
      background: #090a0f;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      padding-right: 10px;
      gap: 6px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
    .camera-lens {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #1e293b, #090d16 70%);
      box-shadow: inset 0 0 2px rgba(56, 189, 248, 0.4);
    }
    .camera-sensor {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: #042f2e;
    }

    /* Status Icons */
    .status-icons {
      display: flex;
      align-items: center;
      gap: 6px;
      color: #0f172a;
    }
    .signal-bars {
      display: flex;
      align-items: flex-end;
      gap: 1.5px;
      height: 11px;
    }
    .signal-bars span {
      width: 2.5px;
      background: #0f172a;
      border-radius: 0.5px;
    }
    .signal-bars span:nth-child(1) { height: 3px; }
    .signal-bars span:nth-child(2) { height: 5px; }
    .signal-bars span:nth-child(3) { height: 8px; }
    .signal-bars span:nth-child(4) { height: 11px; }

    .battery-icon {
      width: 21px;
      height: 11px;
      border: 1.5px solid #0f172a;
      border-radius: 3px;
      padding: 1px;
      position: relative;
      display: flex;
      align-items: center;
    }
    .battery-icon::after {
      content: '';
      position: absolute;
      right: -3px;
      top: 2.5px;
      width: 2px;
      height: 4px;
      background: #0f172a;
      border-radius: 0 1px 1px 0;
    }
    .battery-fill {
      height: 100%;
      width: 85%;
      background: #16a34a;
      border-radius: 1px;
    }

    /* Screen content viewport */
    .screen-body {
      flex: 1;
      position: relative;
      overflow: hidden;
      background: #f3f4f6;
      display: flex;
      flex-direction: column;
    }
    .screen-img-full {
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: top center;
      display: block;
    }

    /* Screen 1 Docked nav */
    .screen1-body-img {
      width: 100%;
      height: auto;
      display: block;
    }
    .screen1-spacer {
      flex: 1;
      background: #f3f4f6;
    }
    .screen1-nav-img {
      width: 100%;
      height: auto;
      display: block;
    }

    /* Bottom Home Indicator */
    .home-indicator-bar {
      height: 22px;
      min-height: 22px;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 50;
    }
    .home-indicator {
      width: 125px;
      height: 4px;
      background: #94a3b8;
      border-radius: 2px;
    }
    """

def generate_slide_html(uri1_body, uri1_nav, uri2, uri3):
    css = create_phone_css()
    html = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<title>Bangla Braille Presentation Mockups</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Nirmala UI', 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(160deg, #f8fafc 0%, #edf2f7 50%, #e2e8f0 100%);
    width: 2560px;
    height: 1440px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    -webkit-font-smoothing: antialiased;
  }}

  {css}

  /* Presentation Header */
  .slide-header {{
    text-align: center;
    margin-bottom: 25px;
    margin-top: -15px;
  }}
  .badge-tag {{
    display: inline-block;
    padding: 6px 20px;
    background: #dcfce7;
    border: 1.5px solid #86efac;
    color: #15803d;
    border-radius: 999px;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.8px;
    margin-bottom: 12px;
  }}
  .slide-title {{
    font-size: 46px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
    margin-bottom: 8px;
  }}
  .slide-subtitle {{
    font-size: 21px;
    color: #64748b;
    font-weight: 500;
  }}

  /* Phones Container */
  .phones-row {{
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 70px;
  }}

  /* Phone Card Item */
  .phone-card {{
    display: flex;
    flex-direction: column;
    align-items: center;
  }}

  /* Label Box Below Phone */
  .phone-label-box {{
    margin-top: 18px;
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 18px;
    padding: 16px 26px;
    text-align: center;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.07);
    width: 380px;
  }}
  .phone-label-num {{
    font-size: 14px;
    font-weight: 700;
    color: #16a34a;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 3px;
  }}
  .phone-label-title {{
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
  }}
  .phone-label-desc {{
    font-size: 14px;
    color: #64748b;
    line-height: 1.35;
  }}
</style>
</head>
<body>

  <!-- Slide Header -->
  <div class="slide-header">
    <div class="badge-tag">BUET EEE 416 • GROUP 08 • HARDWARE-SYNCHRONIZED SYSTEM</div>
    <h1 class="slide-title">স্মার্ট বাংলা ব্রেইল শিক্ষক ড্যাশবোর্ড — মোবাইল ইন্টারফেস</h1>
    <p class="slide-subtitle">ESP32 Hardware-Integrated Bangla Braille Learning, Practice & Examination Suite</p>
  </div>

  <!-- 3 Phones Row -->
  <div class="phones-row">

    <!-- Phone 1: Sequential Lesson -->
    <div class="phone-card">
      <div class="phone-wrapper">
        <div class="btn-action"></div>
        <div class="btn-vol-up"></div>
        <div class="btn-vol-down"></div>
        <div class="btn-power"></div>
        <div class="phone-chassis">
          <div class="phone-speaker"></div>
          <div class="phone-screen">
            <!-- Status Bar -->
            <div class="status-bar">
              <span class="status-time">9:41</span>
              <div class="dynamic-island">
                <div class="camera-lens"></div>
                <div class="camera-sensor"></div>
              </div>
              <div class="status-icons">
                <div class="signal-bars"><span></span><span></span><span></span><span></span></div>
                <div class="battery-icon"><div class="battery-fill"></div></div>
              </div>
            </div>
            <!-- Screen Body -->
            <div class="screen-body">
              <img src="{uri1_body}" class="screen1-body-img" alt="Lesson View" />
              <div class="screen1-spacer"></div>
              <img src="{uri1_nav}" class="screen1-nav-img" alt="Nav Bar" />
            </div>
            <!-- Home Indicator -->
            <div class="home-indicator-bar">
              <div class="home-indicator"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="phone-label-box">
        <div class="phone-label-num">Screen 01 • Sequential Mode</div>
        <div class="phone-label-title">বর্ণমালা পাঠদান ও ডট পর্যবেক্ষণ</div>
        <div class="phone-label-desc">৬-ডট ভাইব্রেশন প্যাটার্ন প্রদর্শন, সুস্পষ্ট অডিও উচ্চারণ ও রিয়েল-টাইম কিপ্যাড নির্দেশনা</div>
      </div>
    </div>

    <!-- Phone 2: Random Practice -->
    <div class="phone-card">
      <div class="phone-wrapper">
        <div class="btn-action"></div>
        <div class="btn-vol-up"></div>
        <div class="btn-vol-down"></div>
        <div class="btn-power"></div>
        <div class="phone-chassis">
          <div class="phone-speaker"></div>
          <div class="phone-screen">
            <!-- Status Bar -->
            <div class="status-bar">
              <span class="status-time">9:41</span>
              <div class="dynamic-island">
                <div class="camera-lens"></div>
                <div class="camera-sensor"></div>
              </div>
              <div class="status-icons">
                <div class="signal-bars"><span></span><span></span><span></span><span></span></div>
                <div class="battery-icon"><div class="battery-fill"></div></div>
              </div>
            </div>
            <!-- Screen Body -->
            <div class="screen-body">
              <img src="{uri2}" class="screen-img-full" alt="Random Practice" />
            </div>
            <!-- Home Indicator -->
            <div class="home-indicator-bar">
              <div class="home-indicator"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="phone-label-box">
        <div class="phone-label-num">Screen 02 • Random Mode</div>
        <div class="phone-label-title">এলোমেলো অনুশীলন ও হিটম্যাপ</div>
        <div class="phone-label-desc">৫০টি বাংলা বর্ণের গ্রিড, শিক্ষার্থীর সঠিক/ভুল ইনপুটের কালার-কোডেড দুর্বলতা ট্র্যাকিং</div>
      </div>
    </div>

    <!-- Phone 3: Examination -->
    <div class="phone-card">
      <div class="phone-wrapper">
        <div class="btn-action"></div>
        <div class="btn-vol-up"></div>
        <div class="btn-vol-down"></div>
        <div class="btn-power"></div>
        <div class="phone-chassis">
          <div class="phone-speaker"></div>
          <div class="phone-screen">
            <!-- Status Bar -->
            <div class="status-bar">
              <span class="status-time">9:41</span>
              <div class="dynamic-island">
                <div class="camera-lens"></div>
                <div class="camera-sensor"></div>
              </div>
              <div class="status-icons">
                <div class="signal-bars"><span></span><span></span><span></span><span></span></div>
                <div class="battery-icon"><div class="battery-fill"></div></div>
              </div>
            </div>
            <!-- Screen Body -->
            <div class="screen-body">
              <img src="{uri3}" class="screen-img-full" alt="Examination Mode" />
            </div>
            <!-- Home Indicator -->
            <div class="home-indicator-bar">
              <div class="home-indicator"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="phone-label-box">
        <div class="phone-label-num">Screen 03 • Test Mode</div>
        <div class="phone-label-title">ব্রেইল মূল্যায়ন পরীক্ষা</div>
        <div class="phone-label-desc">নির্দিষ্ট বর্ণ নির্বাচন, সময়-সীমিত পরীক্ষা পরিচালনা ও ক্লাউডে ফলাফল সংরক্ষণ</div>
      </div>
    </div>

  </div>

</body>
</html>"""
    return html

def generate_single_phone_html(img_body_uri, img_nav_uri=None, is_split=False):
    css = create_phone_css()
    inner_body = ""
    if is_split and img_nav_uri:
        inner_body = f"""
        <img src="{img_body_uri}" class="screen1-body-img" alt="Screen Body" />
        <div class="screen1-spacer"></div>
        <img src="{img_nav_uri}" class="screen1-nav-img" alt="Nav Bar" />
        """
    else:
        inner_body = f'<img src="{img_body_uri}" class="screen-img-full" alt="Screen Full" />'

    html = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    width: 600px;
    height: 1050px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }}
  {css}
  .phone-wrapper {{
    margin: 0;
  }}
</style>
</head>
<body>
  <div class="phone-wrapper">
    <div class="btn-action"></div>
    <div class="btn-vol-up"></div>
    <div class="btn-vol-down"></div>
    <div class="btn-power"></div>
    <div class="phone-chassis">
      <div class="phone-speaker"></div>
      <div class="phone-screen">
        <div class="status-bar">
          <span class="status-time">9:41</span>
          <div class="dynamic-island">
            <div class="camera-lens"></div>
            <div class="camera-sensor"></div>
          </div>
          <div class="status-icons">
            <div class="signal-bars"><span></span><span></span><span></span><span></span></div>
            <div class="battery-icon"><div class="battery-fill"></div></div>
          </div>
        </div>
        <div class="screen-body">
          {inner_body}
        </div>
        <div class="home-indicator-bar">
          <div class="home-indicator"></div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>"""
    return html

def render_chrome(html_path, out_png_path, width, height, transparent=False):
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    file_url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    cmd = [
        chrome_exe,
        "--headless",
        "--disable-gpu",
        f"--screenshot={os.path.abspath(out_png_path)}",
        f"--window-size={width},{height}",
        "--hide-scrollbars",
        "--force-device-scale-factor=1.5",
        file_url
    ]
    if transparent:
        cmd.insert(3, "--default-background-color=00000000")

    print(f"Rendering {os.path.basename(out_png_path)} via Chrome ({width}x{height})...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error rendering {out_png_path}: {res.stderr}")
    else:
        print(f"Successfully generated: {out_png_path}")

def main():
    assets_dir = r"D:\eee-416 project\presentation_assets"
    os.makedirs(assets_dir, exist_ok=True)

    img1 = r"C:\Users\Milon\.gemini\antigravity\brain\4175c8a7-a5ac-45e2-ac6d-4e86feb1c969\.user_uploaded\media_1789756191394.png"
    img2 = r"C:\Users\Milon\.gemini\antigravity\brain\4175c8a7-a5ac-45e2-ac6d-4e86feb1c969\.user_uploaded\media_1789756191393.png"
    img3 = r"C:\Users\Milon\.gemini\antigravity\brain\4175c8a7-a5ac-45e2-ac6d-4e86feb1c969\.user_uploaded\media_1789756191428.png"

    print("Extracting Screen 1 docked elements...")
    u1_body, u1_nav = crop_screen1_parts(img1)
    print("Loading base64 data for Screen 2 and 3...")
    u2 = get_base64_data_uri(img2)
    u3 = get_base64_data_uri(img3)

    # 1. Generate Full 16:9 Presentation Slide
    slide_html_file = os.path.join(assets_dir, "slide_template.html")
    with open(slide_html_file, "w", encoding="utf-8") as f:
        f.write(generate_slide_html(u1_body, u1_nav, u2, u3))

    slide_png_out = os.path.join(assets_dir, "presentation_slide_3_mobiles_light.png")
    render_chrome(slide_html_file, slide_png_out, 2560, 1440, transparent=False)

    # 2. Generate Individual Phone Mockups with Transparent Backgrounds
    # Phone 1
    p1_html = os.path.join(assets_dir, "phone1.html")
    with open(p1_html, "w", encoding="utf-8") as f:
        f.write(generate_single_phone_html(u1_body, u1_nav, is_split=True))
    p1_png = os.path.join(assets_dir, "mobile_mockup_1_lesson.png")
    render_chrome(p1_html, p1_png, 600, 1050, transparent=True)

    # Phone 2
    p2_html = os.path.join(assets_dir, "phone2.html")
    with open(p2_html, "w", encoding="utf-8") as f:
        f.write(generate_single_phone_html(u2, is_split=False))
    p2_png = os.path.join(assets_dir, "mobile_mockup_2_practice.png")
    render_chrome(p2_html, p2_png, 600, 1050, transparent=True)

    # Phone 3
    p3_html = os.path.join(assets_dir, "phone3.html")
    with open(p3_html, "w", encoding="utf-8") as f:
        f.write(generate_single_phone_html(u3, is_split=False))
    p3_png = os.path.join(assets_dir, "mobile_mockup_3_testing.png")
    render_chrome(p3_html, p3_png, 600, 1050, transparent=True)

    print("\nAll presentation assets created successfully!")

if __name__ == "__main__":
    main()
