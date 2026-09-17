#!/usr/bin/env python3
"""Generate the top-panel geometry for the Bangla Braille Tutor.

Single source of truth for the top-face hole layout. Emits two files, so the
laser template and the 3D-printed lid cannot drift apart:

  enclosure/top_panel_cutout.svg   1:1 cut file, geometry only -- no text,
                                   no fills, no decoration
  enclosure/top_panel_layout.scad  the same coordinates as OpenSCAD constants,
                                   included by braille_tutor_case.scad

Also validates every clearance and can render a PNG proof sheet.

    python tools/gen_top_panel.py            # write both files, run checks
    python tools/gen_top_panel.py --preview  # also write a PNG proof

Component sizes come from the parts actually used in the build:
  * tactile push button  12.0 x 12.0 mm body, 6.0 mm tall, 4 pins
  * coin vibration motor 10.0 mm diameter, 3.0 mm thick
  * speaker              40.0 mm diameter
"""
import argparse
import math
import os

# ---------------------------------------------------------------- panel -----
PANEL_W = 210.0
PANEL_H = 140.0
CORNER_R = 8.0
PANEL_T = 2.8          # material thickness, quoted in the fit notes

# ------------------------------------------------------------ components ----
BTN_BODY = 12.0        # square body, 6.0 mm tall, 4 pins
MOTOR_DIA = 10.0       # 3.0 mm thick coin motor
MOTOR_T = 3.0
SPEAKER_DIA = 40.0

# Fit clearance, total across the hole: 0.2 mm per side. The button body
# presses UP through its square hole so the panel captures it just under the
# cap. The motor bonds into its hole with its face flush to the panel top.
FIT = 0.4

BTN_HOLE = BTN_BODY + FIT           # 12.4 mm square
BTN_HOLE_R = 0.5                    # inner corner relief
MOTOR_HOLE_DIA = MOTOR_DIA + FIT    # 10.4 mm

# Speaker grill. A 40 mm speaker's moving cone is smaller than its frame, so
# the perforated area covers the cone only and the frame lands on solid panel.
GRILL_HOLE_DIA = 2.5
GRILL_RINGS = [(0.0, 1), (5.5, 6), (11.0, 12), (16.0, 18)]   # (radius, count)

# Assembly fasteners: M3 clearance.
SCREW_DIA = 3.2
SCREW_INSET = 8.0

# Minimum material anywhere on the panel.
MIN_WEB = 2.0

# --------------------------------------------------------------- layout -----
# Two 3x2 blocks on a shared 30 mm grid: the motor cell plays a pattern back on
# the left, the button cell takes input on the right. Rows are common to both,
# so dot N sits on the same line in each block. Speaker on the bottom centre.
COL_PITCH = 30.0
ROW_PITCH = 30.0
ROW_Y = (26.0, 56.0, 86.0)

MOTOR_CX = 52.0                       # motor block centre
BTN_CX = 158.0                        # button block centre
SUBMIT_Y = ROW_Y[2] + ROW_PITCH       # 116.0, stays on the 30 mm grid

SPEAKER_C = (105.0, 112.0)            # 105.0 is the exact panel centre line


def motor_holes():
    """Dots 1-6: dots 1,2,3 down the left column, 4,5,6 down the right."""
    left = MOTOR_CX - COL_PITCH / 2
    right = MOTOR_CX + COL_PITCH / 2
    out = []
    for i, y in enumerate(ROW_Y):
        out.append(("motor-dot%d" % (i + 1), left, y))
    for i, y in enumerate(ROW_Y):
        out.append(("motor-dot%d" % (i + 4), right, y))
    return out


def button_holes():
    """Six dot buttons plus submit, centred under the two dot columns."""
    left = BTN_CX - COL_PITCH / 2
    right = BTN_CX + COL_PITCH / 2
    out = []
    for i, y in enumerate(ROW_Y):
        out.append(("button-dot%d" % (i + 1), left, y))       # white caps
    for i, y in enumerate(ROW_Y):
        out.append(("button-dot%d" % (i + 4), right, y))      # red caps
    out.append(("button-submit", BTN_CX, SUBMIT_Y))           # yellow cap
    return out


def grill_holes():
    cx, cy = SPEAKER_C
    out = []
    for r, n in GRILL_RINGS:
        for k in range(n):
            a = 2 * math.pi * k / n - math.pi / 2
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def screw_holes():
    i = SCREW_INSET
    return [
        ("screw-tl", i, i),
        ("screw-tr", PANEL_W - i, i),
        ("screw-bl", i, PANEL_H - i),
        ("screw-br", PANEL_W - i, PANEL_H - i),
    ]


def grill_extent():
    return max(r for r, _ in GRILL_RINGS) * 2 + GRILL_HOLE_DIA


# ------------------------------------------------------------ validation ----
def panel_sdf(x, y):
    """Signed distance to the rounded-rect boundary. Negative inside."""
    qx = abs(x - PANEL_W / 2) - (PANEL_W / 2 - CORNER_R)
    qy = abs(y - PANEL_H / 2) - (PANEL_H / 2 - CORNER_R)
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0))
    inside = min(max(qx, qy), 0.0)
    return outside + inside - CORNER_R


def circle_pts(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * k / n),
             cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def square_pts(cx, cy, size, n=64):
    h = size / 2
    pts = []
    for k in range(n):
        t = k / n
        if t < 0.25:
            pts.append((cx - h + size * (t / 0.25), cy - h))
        elif t < 0.5:
            pts.append((cx + h, cy - h + size * ((t - 0.25) / 0.25)))
        elif t < 0.75:
            pts.append((cx + h - size * ((t - 0.5) / 0.25), cy + h))
        else:
            pts.append((cx - h, cy + h - size * ((t - 0.75) / 0.25)))
    return pts


def validate(verbose=True):
    shapes = []
    for name, x, y in motor_holes():
        shapes.append((name, circle_pts(x, y, MOTOR_HOLE_DIA / 2)))
    for name, x, y in button_holes():
        shapes.append((name, square_pts(x, y, BTN_HOLE)))
    for i, (x, y) in enumerate(grill_holes()):
        shapes.append(("grill%02d" % i, circle_pts(x, y, GRILL_HOLE_DIA / 2, 24)))
    for name, x, y in screw_holes():
        shapes.append((name, circle_pts(x, y, SCREW_DIA / 2, 24)))

    problems = []

    # 1. every cut fully inside the panel, with material left to the rim
    min_edge = (1e9, None)
    for name, pts in shapes:
        d = min(-panel_sdf(px, py) for px, py in pts)
        if d < min_edge[0]:
            min_edge = (d, name)
        if d < MIN_WEB:
            problems.append("%s: only %.2f mm of material to the panel rim"
                            % (name, d))

    # 2. no two cuts closer than the web minimum
    min_gap = (1e9, None, None)
    for i in range(len(shapes)):
        ni, pi = shapes[i]
        for j in range(i + 1, len(shapes)):
            nj, pj = shapes[j]
            d = min(math.hypot(ax - bx, ay - by)
                    for ax, ay in pi for bx, by in pj)
            if d < min_gap[0]:
                min_gap = (d, ni, nj)
            if d < MIN_WEB:
                problems.append("%s <-> %s: web only %.2f mm" % (ni, nj, d))

    # 3. the speaker frame must land on solid panel
    if grill_extent() >= SPEAKER_DIA:
        problems.append("grill spans %g mm, wider than the %g mm speaker"
                        % (grill_extent(), SPEAKER_DIA))

    if verbose:
        print("cut count            %d" % len(shapes))
        print("panel                %g x %g mm, r%g, %g mm sheet"
              % (PANEL_W, PANEL_H, CORNER_R, PANEL_T))
        print("button hole          %g mm square  (body %g, %g mm clearance)"
              % (BTN_HOLE, BTN_BODY, FIT))
        print("motor hole           %g mm dia     (motor %g x %g)"
              % (MOTOR_HOLE_DIA, MOTOR_DIA, MOTOR_T))
        print("grill perforation    %g mm dia over a %g mm speaker"
              % (grill_extent(), SPEAKER_DIA))
        print("min material to rim  %.2f mm  (%s)" % min_edge)
        print("min web between cuts %.2f mm  (%s <-> %s)" % min_gap)
        if problems:
            print("\nFAIL")
            for p in problems:
                print("  - %s" % p)
        else:
            print("\nOK: every clearance >= %.1f mm" % MIN_WEB)
    return not problems


# ----------------------------------------------------------------- svg ------
def rounded_rect_path(w, h, r):
    return ("M %g,0 H %g A %g,%g 0 0 1 %g,%g V %g A %g,%g 0 0 1 %g,%g "
            "H %g A %g,%g 0 0 1 0,%g V %g A %g,%g 0 0 1 %g,0 Z"
            % (r, w - r, r, r, w, r, h - r, r, r, w - r, h,
               r, r, r, h - r, r, r, r, r))


def build_svg():
    L = []
    a = L.append
    # NB: a double hyphen is illegal inside an XML comment, so the banner text
    # below must never contain one. assert_wellformed() enforces this.
    a('<?xml version="1.0" encoding="UTF-8"?>')
    a('<!-- GENERATED by tools/gen_top_panel.py . DO NOT EDIT BY HAND -->')
    a('<!--')
    a('  Bangla Braille Tutor - top panel, 1:1 laser cutting template.')
    a('  Units: mm. Material: %g mm sheet. Every path is a through cut.'
      % PANEL_T)
    a('')
    a('  panel-outline  %g x %g mm, %g mm corner radius'
      % (PANEL_W, PANEL_H, CORNER_R))
    a('  motor-holes    6 x dia %g mm    for dia %g x %g mm coin motors'
      % (MOTOR_HOLE_DIA, MOTOR_DIA, MOTOR_T))
    a('  button-holes   7 x %g mm sq   for %g x %g x 6 mm 4-pin tactile switches'
      % (BTN_HOLE, BTN_BODY, BTN_BODY))
    a('  speaker-grill  %d x dia %g mm   over a dia %g mm speaker'
      % (len(grill_holes()), GRILL_HOLE_DIA, SPEAKER_DIA))
    a('  screw-holes    4 x dia %g mm    M3 clearance' % SCREW_DIA)
    a('')
    a('  Grid: two 3x2 blocks on a shared %g mm pitch, rows at y=%s.'
      % (COL_PITCH, ", ".join("%g" % y for y in ROW_Y)))
    a('  Motor block centre x=%g, button block centre x=%g, submit at y=%g.'
      % (MOTOR_CX, BTN_CX, SUBMIT_Y))
    a('  Left motor column is dots 1-2-3, right is 4-5-6; same for the buttons.')
    a('')
    a('  Fit: button bodies press UP through the square holes so the panel')
    a('  captures them below the caps. Motors bond into their holes with the')
    a('  face flush to the panel top. Cut on the path centreline and let the')
    a('  kerf provide the running clearance.')
    a('-->')
    a('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
      'width="%gmm" height="%gmm" viewBox="0 0 %g %g">'
      % (PANEL_W, PANEL_H, PANEL_W, PANEL_H))
    a('  <g fill="none" stroke="#000000" stroke-width="0.1" '
      'stroke-linejoin="round">')

    a('')
    a('    <g id="panel-outline">')
    a('      <path d="%s"/>' % rounded_rect_path(PANEL_W, PANEL_H, CORNER_R))
    a('    </g>')

    a('')
    a('    <g id="motor-holes">')
    for name, x, y in motor_holes():
        a('      <circle id="%s" cx="%g" cy="%g" r="%g"/>'
          % (name, x, y, MOTOR_HOLE_DIA / 2))
    a('    </g>')

    a('')
    a('    <g id="button-holes">')
    h = BTN_HOLE / 2
    for name, x, y in button_holes():
        a('      <rect id="%s" x="%g" y="%g" width="%g" height="%g" '
          'rx="%g" ry="%g"/>'
          % (name, x - h, y - h, BTN_HOLE, BTN_HOLE, BTN_HOLE_R, BTN_HOLE_R))
    a('    </g>')

    a('')
    a('    <g id="speaker-grill">')
    for x, y in grill_holes():
        a('      <circle cx="%.4f" cy="%.4f" r="%g"/>'
          % (x, y, GRILL_HOLE_DIA / 2))
    a('    </g>')

    a('')
    a('    <g id="screw-holes">')
    for name, x, y in screw_holes():
        a('      <circle id="%s" cx="%g" cy="%g" r="%g"/>'
          % (name, x, y, SCREW_DIA / 2))
    a('    </g>')

    a('')
    a('  </g>')
    a('</svg>')
    return "\n".join(L) + "\n"


def assert_wellformed(svg):
    """A cut file that no tool can open is worse than no cut file."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    for tag in ("text", "tspan", "style", "image"):
        n = len(root.findall(".//%s%s" % (ns, tag)))
        if n:
            raise AssertionError("%d <%s> element(s) in a geometry-only file"
                                 % (n, tag))
    shapes = sum(len(root.findall(".//%s%s" % (ns, t)))
                 for t in ("path", "circle", "rect"))
    return shapes


# ---------------------------------------------------------------- scad ------
# OpenSCAD works in a Y-up frame with the origin at the front-left corner,
# while the SVG is Y-down from the top-left. Flip Y so both describe the same
# physical panel.
def to_scad_y(y):
    return PANEL_H - y


def scad_vec(pairs):
    return "[ " + ", ".join("[%g, %g]" % (x, to_scad_y(y)) for x, y in pairs) + " ]"


def build_scad_layout():
    L = []
    a = L.append
    a("// GENERATED by tools/gen_top_panel.py -- DO NOT EDIT BY HAND")
    a("//")
    a("// Top-panel layout shared by the laser template and the printed lid.")
    a("// enclosure/top_panel_cutout.svg is generated from these same numbers,")
    a("// so a change here reaches both routes at once. Edit the generator, not")
    a("// this file.")
    a("//")
    a("// Coordinates are OpenSCAD-native: origin front-left, Y up, mm.")
    a("")
    a("PANEL_W  = %g;" % PANEL_W)
    a("PANEL_H  = %g;   // depth in plan view" % PANEL_H)
    a("CORNER_R = %g;" % CORNER_R)
    a("PANEL_T  = %g;   // top face thickness" % PANEL_T)
    a("")
    a("// dia %g x %g mm coin motors, %g mm total fit clearance"
      % (MOTOR_DIA, MOTOR_T, FIT))
    a("MOTOR_DIA_NOM  = %g;" % MOTOR_DIA)
    a("MOTOR_T        = %g;" % MOTOR_T)
    a("MOTOR_HOLE_DIA = %g;" % MOTOR_HOLE_DIA)
    a("// dots 1-6 in order")
    a("MOTOR_POS = %s;" % scad_vec([(x, y) for _, x, y in motor_holes()]))
    a("")
    a("// %g x %g x 6 mm 4-pin tactile switches, square cutout"
      % (BTN_BODY, BTN_BODY))
    a("BTN_BODY     = %g;" % BTN_BODY)
    a("BTN_HOLE     = %g;" % BTN_HOLE)
    a("BTN_HOLE_R   = %g;" % BTN_HOLE_R)
    a("// dots 1-6 then submit")
    a("BTN_POS = %s;" % scad_vec([(x, y) for _, x, y in button_holes()]))
    a("")
    a("// perforated area dia %g mm, under a dia %g mm speaker"
      % (grill_extent(), SPEAKER_DIA))
    a("SPEAKER_DIA    = %g;" % SPEAKER_DIA)
    a("GRILL_HOLE_DIA = %g;" % GRILL_HOLE_DIA)
    a("GRILL_POS = %s;" % scad_vec(grill_holes()))
    a("")
    a("// M3 clearance")
    a("SCREW_DIA = %g;" % SCREW_DIA)
    a("SCREW_POS = %s;" % scad_vec([(x, y) for _, x, y in screw_holes()]))
    return "\n".join(L) + "\n"


def preview(path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch, BoxStyle

    fig, ax = plt.subplots(figsize=(PANEL_W / 25.4, PANEL_H / 25.4), dpi=170)
    ax.add_patch(FancyBboxPatch(
        (CORNER_R, CORNER_R), PANEL_W - 2 * CORNER_R, PANEL_H - 2 * CORNER_R,
        boxstyle=BoxStyle("Round", pad=0, rounding_size=CORNER_R),
        fill=False, ec="black", lw=1.4))
    for _, x, y in motor_holes():
        ax.add_patch(Circle((x, y), MOTOR_HOLE_DIA / 2,
                            fill=False, ec="black", lw=1.1))
    hh = BTN_HOLE / 2
    for _, x, y in button_holes():
        ax.add_patch(FancyBboxPatch(
            (x - hh + BTN_HOLE_R, y - hh + BTN_HOLE_R),
            BTN_HOLE - 2 * BTN_HOLE_R, BTN_HOLE - 2 * BTN_HOLE_R,
            boxstyle=BoxStyle("Round", pad=0, rounding_size=BTN_HOLE_R),
            fill=False, ec="black", lw=1.1))
    for x, y in grill_holes():
        ax.add_patch(Circle((x, y), GRILL_HOLE_DIA / 2,
                            fill=False, ec="black", lw=0.8))
    for _, x, y in screw_holes():
        ax.add_patch(Circle((x, y), SCREW_DIA / 2,
                            fill=False, ec="black", lw=1.1))
    ax.set_xlim(-5, PANEL_W + 5)
    ax.set_ylim(PANEL_H + 5, -5)          # y downward, same as the SVG
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    print("preview -> %s" % path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", metavar="PNG", nargs="?",
                    const="top_panel_preview.png", default=None)
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    enc = os.path.join(root, "enclosure")
    svg_out = os.path.join(enc, "top_panel_cutout.svg")
    scad_out = os.path.join(enc, "top_panel_layout.scad")

    ok = validate()
    svg = build_svg()
    shapes = assert_wellformed(svg)
    with open(svg_out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("svg     -> %s  (%d shapes, parses clean, no text)"
          % (svg_out, shapes))
    with open(scad_out, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_scad_layout())
    print("scad    -> %s" % scad_out)
    if args.preview:
        preview(args.preview)
    raise SystemExit(0 if ok else 1)
