// ====================================================================
// AI-Assisted Bangla Braille Tutor - bottom base, parametric
//
// This is the BASE half that closes underneath braille_tutor_case.scad's
// top lid. It shares PANEL_W, PANEL_H and CORNER_R with the top panel
// (via top_panel_layout.scad), so the footprint and corner radius always
// line up exactly with the lid -- nothing here is measured independently.
//
// The brief is a total assembled height of 2 in (50.8 mm) measured from
// the ground to the top panel. The lid alone (braille_tutor_case.scad) is
// already 48 mm, so this base is a flat cover, not a second deep shell:
// base_thickness = 50.8 - 48 = 2.8 mm, the same thickness as the top
// panel itself. That is what keeps the assembly a single 50.8 mm box
// instead of stacking two full-height shells into a doubled-up one.
//
// Screw bosses rise from this cover, up into the lid's hollow interior,
// under the top lid's SCREW_POS -- the same four M3 screws that pass
// through the lid's clearance holes thread into these bosses. The wire
// pass-through hole lives in the top lid's back wall instead (see
// braille_tutor_case.scad), not here, so this cover stays a plain panel.
//
// Compatible with OpenSCAD / FreeCAD.
// ====================================================================

include <top_panel_layout.scad>

$fn = 72;   // smooth circles

// --- Cover --------------------------------------------------------------
base_width     = PANEL_W;     // 210, identical to the top lid
base_depth     = PANEL_H;     // 140, identical to the top lid
base_thickness = PANEL_T;     // 2.8 mm: 50.8 mm assembled - 48 mm lid = 2.8 mm cover
corner_radius  = CORNER_R;    // 8, identical to the top lid -> corners always align

// M3 screw bosses, centred on the same four points as the top lid's
// screw_cutouts(). They rise into the lid's ~45 mm clear interior, so
// only need enough length for a secure screw grip, not the full height.
boss_od        = 7.0;
boss_pilot_dia = 2.6;   // self-tapping pilot for an M3 screw in PLA/PETG
boss_height    = 10.0;


// --- Modules ------------------------------------------------------------

module rounded_box(w, d, h, r) {
    hull() {
        translate([r, r, 0])         cylinder(r = r, h = h);
        translate([w - r, r, 0])     cylinder(r = r, h = h);
        translate([r, d - r, 0])     cylinder(r = r, h = h);
        translate([w - r, d - r, 0]) cylinder(r = r, h = h);
    }
}

module base_cover() {
    rounded_box(base_width, base_depth, base_thickness, corner_radius);

    // Screw bosses, aligned to the top lid's SCREW_POS so a single M3
    // screw clamps through both halves.
    for (p = SCREW_POS)
        translate([p[0], p[1], base_thickness])
            difference() {
                cylinder(d = boss_od, h = boss_height);
                cylinder(d = boss_pilot_dia, h = boss_height + 1);
            }
}

base_cover();
