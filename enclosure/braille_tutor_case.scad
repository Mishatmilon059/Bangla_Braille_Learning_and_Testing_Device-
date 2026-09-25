// ====================================================================
// AI-Assisted Bangla Braille Tutor - top lid, parametric
//
// SUPERSEDED: this file builds the top panel and its 48 mm skirt as one
// merged solid. That duplicates top_panel.stl, which gets printed and
// used on its own. The current three-piece enclosure is:
//   1. top_panel.stl   -- the flat top panel (printed separately)
//   2. case_walls.scad -- an open-top/open-bottom frame the panel rests on
//   3. case_base.scad  -- the flat cover underneath
// Use case_walls.scad + case_base.scad for a new build; this file is kept
// for reference (and for anyone who wants a single all-printed top half
// instead of a separate panel).
//
// This is the TOP half only: a rounded shell with a downward skirt and
// every component hole in its top face. Nothing decorative -- no text,
// no engraved zones, no dividers. Just the shell and the cutouts.
//
// The hole layout is NOT defined here. It comes from
// top_panel_layout.scad, which tools/gen_top_panel.py generates from the
// same numbers as top_panel_cutout.svg. That way the printed lid and the
// laser-cut panel are the same part by construction. To move a hole,
// edit tools/gen_top_panel.py and re-run it.
//
// Compatible with OpenSCAD / FreeCAD.
// ====================================================================

include <top_panel_layout.scad>

$fn = 72;   // smooth circles

// --- Shell ----------------------------------------------------------
case_width     = PANEL_W;    // 210
case_depth     = PANEL_H;    // 140
case_height    = 48.0;       // clearance for ESP32, ULN2803A, DFPlayer, wiring
wall_thickness = 2.8;
top_thickness  = PANEL_T;    // 2.8
corner_radius  = CORNER_R;   // 8

// Cutting plane for the top face: start below it and run past it, so every
// hole is an unambiguous through cut with no coincident-face artefacts.
cut_z = case_height - top_thickness - 1;
cut_h = top_thickness + 2;


// --- Modules --------------------------------------------------------

module rounded_box(w, d, h, r) {
    hull() {
        translate([r, r, 0])     cylinder(r = r, h = h);
        translate([w - r, r, 0]) cylinder(r = r, h = h);
        translate([r, d - r, 0]) cylinder(r = r, h = h);
        translate([w - r, d - r, 0]) cylinder(r = r, h = h);
    }
}

// A square hole with relieved corners, matching the SVG's rx/ry.
module rounded_square_hole(size, r, h) {
    hull() {
        for (dx = [-1, 1], dy = [-1, 1])
            translate([dx * (size / 2 - r), dy * (size / 2 - r), 0])
                cylinder(r = r, h = h);
    }
}

// 6 coin vibration motors, dia 10 x 3 mm.
// Through holes, not pockets: the motor is bonded in with its face flush to
// the panel top so the fingertip touches the motor itself.
module motor_cutouts() {
    for (p = MOTOR_POS)
        translate([p[0], p[1], cut_z])
            cylinder(d = MOTOR_HOLE_DIA, h = cut_h);
}

// 6 dot buttons + 1 submit, 12 x 12 x 6 mm 4-pin tactile switches.
// Square cutouts: the switch body presses up through the panel, which then
// captures it just below the cap.
module button_cutouts() {
    for (p = BTN_POS)
        translate([p[0], p[1], cut_z])
            rounded_square_hole(BTN_HOLE, BTN_HOLE_R, cut_h);
}

// Acoustic grill for the dia 40 mm speaker. The perforated area spans the
// cone only, so the speaker frame lands on solid material.
module speaker_grill() {
    for (p = GRILL_POS)
        translate([p[0], p[1], cut_z])
            cylinder(d = GRILL_HOLE_DIA, h = cut_h);
}

// M3 clearance holes. The mating standoffs belong to the base half, which
// this file does not model. Use pan-head or washered screws: at 2.8 mm the
// top face is too thin to countersink an M3 head without breaking through.
module screw_cutouts() {
    for (p = SCREW_POS)
        translate([p[0], p[1], cut_z])
            cylinder(d = SCREW_DIA, h = cut_h);
}

// Wire pass-through: a round hole through the back wall, offset to one
// side rather than centred, for the power/USB cable to leave the case.
wire_hole_dia = 8.0;
wire_hole_x   = 40;   // off to one side of the back wall, not its centre (105)
wire_hole_z   = 20;   // within the wall's solid height, clear of the top cap

module wire_pass_hole() {
    translate([wire_hole_x, case_depth - wall_thickness - 1, wire_hole_z])
        rotate([-90, 0, 0])
            cylinder(d = wire_hole_dia, h = wall_thickness + 2, $fn = 48);
}


// --- Assembly -------------------------------------------------------

module top_lid() {
    difference() {
        rounded_box(case_width, case_depth, case_height, corner_radius);

        // hollow out everything below the top face
        translate([wall_thickness, wall_thickness, -1])
            rounded_box(
                case_width  - 2 * wall_thickness,
                case_depth  - 2 * wall_thickness,
                case_height - top_thickness + 1,
                corner_radius - 1
            );

        motor_cutouts();
        button_cutouts();
        speaker_grill();
        screw_cutouts();
        wire_pass_hole();
    }
}

top_lid();
