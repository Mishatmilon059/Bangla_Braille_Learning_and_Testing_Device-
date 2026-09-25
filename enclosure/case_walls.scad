// ====================================================================
// AI-Assisted Bangla Braille Tutor - side walls, parametric
//
// This is the middle part of a THREE-piece enclosure:
//
//   1. top_panel.stl        -- the flat top panel (already printed).
//   2. case_walls.scad      -- THIS FILE: an open-top, open-bottom frame
//                               that the top panel rests on.
//   3. case_base.scad       -- a flat cover that closes the bottom.
//
// It shares PANEL_W, PANEL_H and CORNER_R with the top panel (via
// top_panel_layout.scad), so its footprint and corner radius match the
// already-printed panel exactly -- the panel sits flush on this frame's
// top rim, no separate measuring needed.
//
// It carries no top face and none of the panel's cutouts (motor, button,
// speaker, screw) -- those already exist on the printed panel. It is
// just a hollow tube, plus the wire pass-through hole.
//
// Height: the brief is a total assembled height of 2 in (50.8 mm), ground
// to top panel. The top panel (2.8 mm) sits on top of these walls, and
// the base cover (2.8 mm) sits underneath, so:
//     wall_height = 50.8 - 2.8 (panel) - 2.8 (base) = 45.2 mm
//
// The four M3 screws drop straight down through the panel's SCREW_POS,
// through this frame's open interior (the screw positions sit inboard of
// the wall thickness, so nothing here needs its own screw holes), into
// the bosses on case_base.scad.
//
// Compatible with OpenSCAD / FreeCAD.
// ====================================================================

include <top_panel_layout.scad>

$fn = 72;   // smooth circles

// --- Frame ----------------------------------------------------------
wall_width     = PANEL_W;    // 210, identical to the top panel
wall_depth     = PANEL_H;    // 140, identical to the top panel
wall_height    = 45.2;       // 50.8 total - 2.8 top panel - 2.8 base cover
wall_thickness = 2.8;        // matches the top panel's thickness
corner_radius  = CORNER_R;   // 8, identical to the top panel -> edges always align

// Wire pass-through: a round hole through the back wall, offset to one
// side rather than centred, for the power/USB cable to leave the case.
wire_hole_dia = 8.0;
wire_hole_x   = 40;   // off to one side of the back wall, not its centre (105)
wire_hole_z   = 20;   // within the wall's height, clear of both rims


// --- Modules ----------------------------------------------------------

module rounded_box(w, d, h, r) {
    hull() {
        translate([r, r, 0])         cylinder(r = r, h = h);
        translate([w - r, r, 0])     cylinder(r = r, h = h);
        translate([r, d - r, 0])     cylinder(r = r, h = h);
        translate([w - r, d - r, 0]) cylinder(r = r, h = h);
    }
}

module wire_pass_hole() {
    translate([wire_hole_x, wall_depth - wall_thickness - 1, wire_hole_z])
        rotate([-90, 0, 0])
            cylinder(d = wire_hole_dia, h = wall_thickness + 2, $fn = 48);
}

module side_walls() {
    difference() {
        rounded_box(wall_width, wall_depth, wall_height, corner_radius);

        // hollow out the interior -- open top, open bottom
        translate([wall_thickness, wall_thickness, -1])
            rounded_box(
                wall_width  - 2 * wall_thickness,
                wall_depth  - 2 * wall_thickness,
                wall_height + 2,
                corner_radius - wall_thickness
            );

        wire_pass_hole();
    }
}

side_walls();
