# Bangla Braille Tutor — enclosure & fabrication

Mechanical files for the ESP32 Bangla Braille Tutor console. The top face is
the part that matters: it carries every component the learner touches.

## Files

### The top panel, which is the part that gets made

| File | Purpose | Opens in |
|---|---|---|
| `top_panel.stl` | **The 3D top panel.** Watertight solid, mm, print or view it. **Generated.** | Cura, PrusaSlicer, Bambu Studio, any mesh viewer |
| `top_panel_3d.html` | **3D viewer for the top panel.** Orbit, preset views. **Generated.** | any browser (needs internet for the CDN) |
| `top_panel_cutout.svg` | 1:1 cut file for the same panel. **Generated.** | Laser cutter, Illustrator, CorelDRAW, Inkscape |
| `top_panel_layout.scad` | The same coordinates as OpenSCAD constants. **Generated.** | included by the case file |

### The rest

| File | Purpose |
|---|---|
| `braille_tutor_case.scad` | Full top lid: the same panel plus a 48 mm skirt, for a closed box |
| `3d_preview.html` | Superseded. An older mockup of the whole console with a layout that no longer matches anything. Nothing is made from it. |

Every generated file traces to one place. Re-run these after any change; never
hand-edit the outputs.

```
python tools/gen_top_panel.py       # SVG + SCAD layout, validates clearances
python tools/gen_top_panel_3d.py    # STL + HTML viewer, validates the mesh
```

[`tools/gen_top_panel.py`](../tools/gen_top_panel.py) holds the numbers.
[`tools/gen_top_panel_3d.py`](../tools/gen_top_panel_3d.py) imports them, so
the printed panel, the laser panel and the viewer cannot disagree.

### The STL

A flat plate, 210 x 140 x 2.8 mm, with all 54 holes. No walls, no skirt, no
base. It is built without a mesh library, so it is verified rather than
trusted:

| Check | Result |
|---|---|
| Triangles | 12,184 |
| Non-manifold edges | 0, watertight |
| Volume vs analytic | agrees to 1.7e-15 relative |
| Bounding box | 210.000 x 140.000 x 2.800 mm |
| Degenerate triangles | 0 |

Printed in PLA at 100% that is about 96 g of material. Print it flat on the
bed, holes vertical, no supports needed.

### The viewer renders the same mesh

`top_panel_3d.html` embeds the verified triangulation rather than rebuilding
the shape in the browser. `THREE.ExtrudeGeometry` is deliberately not used:
its hole bridging emits degenerate slivers, and `EdgesGeometry` then infers
edges along them, which drew a phantom line joining two neighbouring button
holes. The panel itself was solid there the whole time. Outlines are now drawn
straight from the ring loops, so nothing is inferred and the viewer cannot
disagree with the STL.

### Spacing between holes

Both grids share a 30 mm pitch, horizontally and vertically.

| Between | Pitch | Hole | Gap of material |
|---|---|---|---|
| Button to button, left-right | 30 mm | 12.4 mm | 17.6 mm |
| Button to button, top-down | 30 mm | 12.4 mm | 17.6 mm |
| Motor to motor, left-right | 30 mm | 10.4 mm | 19.6 mm |
| Motor to motor, top-down | 30 mm | 10.4 mm | 19.6 mm |

The submit button keeps the same 30 mm pitch below the last button row, so it
also has 17.6 mm of material above it.

The generator refuses to pass if any two cuts come within 2 mm of each other
or of the panel rim. Current worst cases: 6.40 mm of material from a corner
screw to the rim, and a 2.50 mm web between two adjacent grill holes.

## Parts the top face is cut for

| Component | Qty | Part size | Cutout |
|---|---|---|---|
| Tactile push button, 4-pin | 7 | 12.0 × 12.0 mm body, 6.0 mm tall | 12.4 mm square, 0.5 mm corner relief |
| Coin vibration motor | 6 | Ø 10.0 mm, 3.0 mm thick | Ø 10.4 mm |
| Speaker | 1 | Ø 40.0 mm | 37 × Ø 2.5 mm over a Ø 34.5 mm area |
| M3 machine screw | 4 | M3 | Ø 3.2 mm |

Button caps are white for dots 1–3, red for dots 4–6, and yellow for submit.

**Fit.** Every cutout is 0.4 mm larger than its part, 0.2 mm per side. Cut on
the path centreline and let the kerf give the running clearance; on a laser
that typically lands within a tenth of a millimetre.

Button bodies press **up** through their square holes, so the 2.8 mm panel
captures each switch just under its cap and 3.2 mm of body stands proud.
Motors bond into their round holes with the face **flush** to the panel top,
so the fingertip rests on the motor itself rather than on plastic over it.
Motor leads pass back down through the same hole.

## Layout

210 × 140 mm, 8 mm corner radius, 2.8 mm sheet.

Two 3 × 2 blocks share one 30 mm grid, with rows at y = 26, 56 and 86 mm.
Dots 1-2-3 run down the left column of each block and 4-5-6 down the right,
so dot N sits on the same line whether the learner is feeling it or pressing
it. The motor block centres on x = 52, the button block on x = 158, and the
submit button sits between the two button columns at x = 158, y = 116,
carrying the same 30 mm pitch down from the last row.

The speaker grill centres on x = 105, the exact panel centre line, at
y = 112. Its perforated area stops at Ø 34.5 mm so the Ø 40 mm speaker frame
seats against solid material.

Corner screws sit 8 mm in from both edges, on the corner-radius centres.

## 3D printing the lid

- **Material:** PLA, PETG or ABS
- **Layer height:** 0.20 mm, or 0.16 mm for a smoother top face
- **Infill:** 20–30% gyroid or grid
- **Supports:** none needed for the top face; the holes are all vertical
- **Fasteners:** 4 × M3 pan-head. Do not countersink: at 2.8 mm the top face
  is too thin to sink an M3 head without breaking through. The mating
  standoffs belong to the base half, which is not modelled here.

## Known gap

`3d_preview.html` hardcodes its own copy of the geometry and still shows the
older layout: round button holes, a different grid, and a smaller grill. It is
a presentation mockup, not a fabrication source, so nothing is cut or printed
from it. Regenerate or retire it before using it to check dimensions.
