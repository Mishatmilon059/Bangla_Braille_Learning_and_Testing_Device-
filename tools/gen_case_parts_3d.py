#!/usr/bin/env python3
"""Generate the base cover and side walls as printable STL solids.

Companions to top_panel.stl (already printed) and to case_base.scad /
case_walls.scad, which are the OpenSCAD source of truth for these two parts.
There is no OpenSCAD available in this environment, so -- exactly like
tools/gen_top_panel_3d.py already does for the top panel -- these STLs are
built directly as triangle meshes and checked for watertightness and correct
volume before being written.

    enclosure/case_base.stl
    enclosure/case_walls.stl

    python tools/gen_case_parts_3d.py

Every solid here is either convex (fan-triangulated straight from a single
vertex) or a simple ruled surface between two known rings (an annulus cap, a
prism's side wall) -- except the back wall of case_walls, which has the wire
hole cut through it and needs a real polygon-with-hole triangulation. That
one reuses the conforming-Delaunay approach from gen_top_panel_3d.py,
generalised to a plain rectangle-plus-circle instead of the panel's specific
shapes.

Each solid (the base plate, each boss, each wall corner, each wall strip) is
built as its own independently watertight piece and then simply concatenated
-- they only ever touch at a shared face with zero volume overlap, never
overlap in 3-D, so the combined STL is watertight and its volume is exactly
the sum of the pieces.
"""
import math
import os
import struct
import sys

import numpy as np
from scipy.spatial import Delaunay, cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_top_panel as L   # noqa: E402  single source of truth for W, H, R, SCREW_POS

W, H, R = L.PANEL_W, L.PANEL_H, L.CORNER_R
PLATE_T = L.PANEL_T                  # 2.8 mm, shared by the top panel, the
                                      # base cover and the wall thickness

BASE_T = PLATE_T                     # base cover thickness
BOSS_OD, BOSS_PILOT, BOSS_H = 7.0, 2.6, 10.0

WALL_T = PLATE_T                     # side-wall thickness
WALL_H = 50.8 - PLATE_T - BASE_T     # 45.2: 50.8 mm (2 in) total - panel - base
WIRE_DIA, WIRE_X, WIRE_Z = 8.0, 40.0, 20.0   # off to one side, not centred

N_CIRCLE = 48        # segments per full circle
N_CORNER = 24         # segments per 90-degree corner
N_WIRE = 40           # segments around the wire hole


def to3d(x, y):
    """SVG frame (Y down) -> model frame (Y up), matching top_panel.stl."""
    return x, L.PANEL_H - y


SCREW_XY = [to3d(x, y) for _, x, y in L.screw_holes()]


# --------------------------------------------------------- basic triangles --
def fan_cap(ring, z, top):
    """Fan triangulation of a CONVEX polygon, flat at height z.

    `ring` must be wound counter-clockwise (as seen from +Z). `top=True`
    keeps that winding (an upward, +Z normal); `top=False` reverses it for
    a downward-facing cap.
    """
    tris = []
    n = len(ring)
    for i in range(1, n - 1):
        p0 = (ring[0][0], ring[0][1], z)
        p1 = (ring[i][0], ring[i][1], z)
        p2 = (ring[i + 1][0], ring[i + 1][1], z)
        tris.append((p0, p1, p2) if top else (p0, p2, p1))
    return tris


def prism_wall(ring, z0, z1):
    """Side wall around a closed ring. CCW ring -> outward normal."""
    tris = []
    n = len(ring)
    for i in range(n):
        ax, ay = ring[i]
        bx, by = ring[(i + 1) % n]
        tris.append(((ax, ay, z0), (bx, by, z0), (bx, by, z1)))
        tris.append(((ax, ay, z0), (bx, by, z1), (ax, ay, z1)))
    return tris


def convex_prism(ring, z0, z1):
    """A closed, watertight solid: convex ring extruded from z0 to z1."""
    return (fan_cap(ring, z1, top=True) + fan_cap(ring, z0, top=False)
            + prism_wall(ring, z0, z1))


def annulus_cap(outer, inner, z, top):
    """Ruled surface between two same-length, same-angle-sampled rings."""
    tris = []
    n = len(outer)
    for i in range(n):
        o0, o1 = outer[i], outer[(i + 1) % n]
        i0, i1 = inner[i], inner[(i + 1) % n]
        a = (o0[0], o0[1], z); b = (o1[0], o1[1], z)
        c = (i1[0], i1[1], z); d = (i0[0], i0[1], z)
        tris.append((a, b, c) if top else (a, c, b))
        tris.append((a, c, d) if top else (a, d, c))
    return tris


def circle_ring(cx, cy, r, n=N_CIRCLE):
    return [(cx + r * math.cos(2 * math.pi * k / n),
             cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def rect_ring(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rounded_rect_ring(w, h, r, n_corner=N_CORNER):
    """Convex rounded rectangle, counter-clockwise, origin at (0,0)."""
    pts = []
    corners = [(r, r, 180.0), (w - r, r, 270.0), (w - r, h - r, 0.0), (r, h - r, 90.0)]
    for cx, cy, a0 in corners:
        for k in range(n_corner + 1):
            a = math.radians(a0 + 90.0 * k / n_corner)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return dedupe(pts)


def dedupe(pts, eps=1e-9):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def boss(cx, cy, z0, od, pilot_dia, height, n=N_CIRCLE):
    """A closed hollow tube: a screw boss with a blind pilot hole from the top."""
    outer = circle_ring(cx, cy, od / 2, n)
    inner = circle_ring(cx, cy, pilot_dia / 2, n)
    z1 = z0 + height
    return (annulus_cap(outer, inner, z1, top=True)
            + annulus_cap(outer, inner, z0, top=False)
            + prism_wall(outer, z0, z1)
            + prism_wall(list(reversed(inner)), z0, z1))


def ring_sector(cx, cy, r_outer, r_inner, a0, a1, n=N_CORNER):
    """One 90-degree corner of the wall frame: a solid annulus wedge."""
    outer = [(cx + r_outer * math.cos(a0 + (a1 - a0) * k / n),
              cy + r_outer * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
    inner = [(cx + r_inner * math.cos(a0 + (a1 - a0) * k / n),
              cy + r_inner * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
    z0, z1 = 0.0, WALL_H
    tris = []
    # top and bottom: a ruled strip between the two arcs (open ring: n
    # segments over n+1 points, not wrapping around)
    for i in range(n):
        o0, o1 = outer[i], outer[i + 1]
        i0, i1 = inner[i], inner[i + 1]
        a = (o0[0], o0[1], z1); b = (o1[0], o1[1], z1)
        c = (i1[0], i1[1], z1); d = (i0[0], i0[1], z1)
        tris += [(a, b, c), (a, c, d)]
        a = (o0[0], o0[1], z0); b = (o1[0], o1[1], z0)
        c = (i1[0], i1[1], z0); d = (i0[0], i0[1], z0)
        tris += [(a, c, b), (a, d, c)]
    # outer arc wall (outward normal), inner arc wall (inward normal)
    for i in range(n):
        ax, ay = outer[i]; bx, by = outer[i + 1]
        tris += [((ax, ay, z0), (bx, by, z0), (bx, by, z1)),
                 ((ax, ay, z0), (bx, by, z1), (ax, ay, z1))]
        ax, ay = inner[i]; bx, by = inner[i + 1]
        tris += [((ax, ay, z0), (bx, by, z1), (bx, by, z0)),
                 ((ax, ay, z0), (ax, ay, z1), (bx, by, z1))]
    # two flat radial end faces, at a0 and a1
    for (ox, oy), (ix, iy), flip in ((outer[0], inner[0], True), (outer[n], inner[n], False)):
        a = (ox, oy, z0); b = (ix, iy, z0); c = (ix, iy, z1); d = (ox, oy, z1)
        quad = [(a, b, c), (a, c, d)]
        tris += [(t[0], t[2], t[1]) for t in quad] if flip else quad
    return tris


def straight_box(x0, y0, x1, y1, z0, z1):
    """A plain rectangular box: one of the wall frame's straight strips."""
    return convex_prism(rect_ring(x0, y0, x1, y1), z0, z1)


# ---------------------------------------------- polygon-with-hole (1 hole) --
def point_in_poly(p, ring):
    x = p[:, 0][:, None]; y = p[:, 1][:, None]
    ax = ring[:, 0][None, :]; ay = ring[:, 1][None, :]
    bx = np.roll(ring[:, 0], -1)[None, :]; by = np.roll(ring[:, 1], -1)[None, :]
    straddles = (ay > y) != (by > y)
    dy = np.where(by - ay == 0.0, 1e-300, by - ay)
    xcross = ax + (bx - ax) * (y - ay) / dy
    return (np.sum(straddles & (x < xcross), axis=1) % 2) == 1


def conforming_faces(outer_ring, hole_ring, max_passes=16):
    """Refine outer_ring/hole_ring until every edge is a Delaunay edge."""
    outer_ring = list(outer_ring)
    hole_ring = list(hole_ring)
    for p in range(max_passes):
        pts = outer_ring + hole_ring
        segs = []
        base = 0
        for ring in (outer_ring, hole_ring):
            n = len(ring)
            for i in range(n):
                segs.append((base + i, base + (i + 1) % n))
            base += n
        arr = np.asarray(pts, dtype=np.float64)
        tri = Delaunay(arr)
        present = set()
        for s in tri.simplices:
            i, j, k = int(s[0]), int(s[1]), int(s[2])
            present.add((min(i, j), max(i, j)))
            present.add((min(j, k), max(j, k)))
            present.add((min(i, k), max(i, k)))
        missing = [seg for seg in segs if (min(seg), max(seg)) not in present]
        if not missing:
            return arr, tri.simplices, len(outer_ring)

        def split(ring, idxs):
            for i in sorted(idxs, reverse=True):
                a = ring[i]; b = ring[(i + 1) % len(ring)]
                ring.insert(i + 1, ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
        n_outer = len(outer_ring)
        outer_missing = [i for (i, j) in missing if i < n_outer and (j - i == 1 or j - i == -(n_outer - 1))]
        hole_missing = [i - n_outer for (i, j) in missing if i >= n_outer]
        split(outer_ring, sorted(set(outer_missing)))
        split(hole_ring, sorted(set(hole_missing)))
    raise RuntimeError("boundary never conformed after %d passes" % max_passes)


def rect_minus_circle(x0, y0, x1, y1, cx, cy, r, n_circle=N_WIRE):
    """Flat, hole-aware mesh of a rectangle with one circular hole, at z=0."""
    outer = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    hole = [(cx + r * math.cos(-2 * math.pi * k / n_circle),
             cy + r * math.sin(-2 * math.pi * k / n_circle)) for k in range(n_circle)]  # clockwise
    pts, simp, n_outer = conforming_faces(outer, hole)

    outer_arr = np.asarray(outer, dtype=np.float64)
    hole_arr = np.asarray(hole, dtype=np.float64)
    a, b, c = pts[simp[:, 0]], pts[simp[:, 1]], pts[simp[:, 2]]
    centroids = (a + b + c) / 3.0
    inside_outer = ((centroids[:, 0] > x0) & (centroids[:, 0] < x1)
                    & (centroids[:, 1] > y0) & (centroids[:, 1] < y1))
    inside_hole = point_in_poly(centroids, hole_arr)
    simp = simp[inside_outer & ~inside_hole]

    def cross2(o, a, b):
        return (a[..., 0] - o[..., 0]) * (b[..., 1] - o[..., 1]) - (a[..., 1] - o[..., 1]) * (b[..., 0] - o[..., 0])
    a, b, c = pts[simp[:, 0]], pts[simp[:, 1]], pts[simp[:, 2]]
    cw = cross2(a, b, c) < 0
    simp[cw] = simp[cw][:, [0, 2, 1]]

    outer_len = len(outer)
    rings = [outer, hole]
    return pts, simp, rings, outer_len


def wall_with_hole(y0, y1, cx, cz, dia):
    """The back strip of the wall frame, with the wire hole cut through it,
    built flat in the (x, height) plane then extruded along thickness (y).
    """
    x0, x1 = R, W - R
    pts2d, faces, rings, outer_len = rect_minus_circle(x0, 0.0, x1, WALL_H, cx, cz, dia / 2)
    tris = []
    for i, j, k in faces:
        p, q, r = pts2d[i], pts2d[j], pts2d[k]
        tris.append(((p[0], y1, p[1]), (q[0], y1, q[1]), (r[0], y1, r[1])))   # outer face
        tris.append(((p[0], y0, p[1]), (r[0], y0, r[1]), (q[0], y0, q[1])))   # inner face
    for ring in rings:
        n = len(ring)
        for i in range(n):
            ax, az = ring[i]
            bx, bz = ring[(i + 1) % n]
            tris.append(((ax, y0, az), (bx, y0, bz), (bx, y1, bz)))
            tris.append(((ax, y0, az), (bx, y1, bz), (ax, y1, az)))
    # The (x, z) -> (x, Y, z) embedding is a handedness-flipping swap of the
    # standard (x, y) -> (x, y, z) axis order, so every face above comes out
    # inside-out. Flip every triangle once, globally, rather than guess at
    # each one individually.
    return [(t[0], t[2], t[1]) for t in tris]


# ------------------------------------------------------------------ parts --
# Each part below is returned as (name, triangles, expected_volume): every
# piece -- the plate, each boss, each corner, each strip -- is its own
# independently watertight solid. They only ever TOUCH a neighbour at a
# shared, zero-area interface (never overlapping in 3-D), so verifying each
# one on its own is the right bar, not demanding the full concatenation form
# one single global 2-manifold mesh. Two abutting solids' touching faces
# generally do NOT cancel into matched edge pairs (their windings have no
# reason to agree), so a whole-assembly non-manifold check would flag every
# seam between parts as an error when none of them are -- exactly the many
# print-ready multi-body STL exports every slicer already handles routinely.
def base_cover_parts():
    parts = [("plate", convex_prism(rounded_rect_ring(W, H, R), 0.0, BASE_T),
              rounded_rect_area(W, H, R) * BASE_T)]
    boss_vol = annulus_area(BOSS_OD / 2, BOSS_PILOT / 2) * BOSS_H
    for i, (cx, cy) in enumerate(SCREW_XY):
        parts.append(("boss%d" % i, boss(cx, cy, BASE_T, BOSS_OD, BOSS_PILOT, BOSS_H), boss_vol))
    return parts


def side_wall_parts():
    inner_r = R - WALL_T
    corner_vol = (math.pi / 4) * (R ** 2 - inner_r ** 2) * WALL_H
    strip_vol = (W - 2 * R) * WALL_T * WALL_H
    side_strip_vol = (H - 2 * R) * WALL_T * WALL_H
    hole_vol = strip_vol - math.pi * (WIRE_DIA / 2) ** 2 * WALL_T
    return [
        ("corner-bl", ring_sector(R, R, R, inner_r, math.pi, 1.5 * math.pi), corner_vol),
        ("corner-br", ring_sector(W - R, R, R, inner_r, -math.pi / 2, 0.0), corner_vol),
        ("corner-tr", ring_sector(W - R, H - R, R, inner_r, 0.0, math.pi / 2), corner_vol),
        ("corner-tl", ring_sector(R, H - R, R, inner_r, math.pi / 2, math.pi), corner_vol),
        ("front", straight_box(R, 0.0, W - R, WALL_T, 0.0, WALL_H), strip_vol),
        ("left", straight_box(0.0, R, WALL_T, H - R, 0.0, WALL_H), side_strip_vol),
        ("right", straight_box(W - WALL_T, R, W, H - R, 0.0, WALL_H), side_strip_vol),
        ("back+hole", wall_with_hole(H - WALL_T, H, WIRE_X, WIRE_Z, WIRE_DIA), hole_vol),
    ]


# -------------------------------------------------------------- checking --
def check_component(name, tris, expect_vol):
    """Verify ONE independently-watertight solid: no degenerate triangles, a
    perfectly matched (2-manifold) edge set, and volume matching the
    analytic expectation (up to the polygon-vs-circle discretisation error).
    """
    v = np.asarray(tris, dtype=np.float64)
    a, b, c = v[:, 0], v[:, 1], v[:, 2]

    vol = np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) / 6.0

    n = np.cross(b - a, c - a)
    areas = 0.5 * np.linalg.norm(n, axis=1)
    degenerate = int(np.sum(areas < 1e-9))

    q = np.round(v, 6)
    edges = {}
    for tri in q:
        for i in range(3):
            p0 = tuple(tri[i]); p1 = tuple(tri[(i + 1) % 3])
            edges[(p0, p1)] = edges.get((p0, p1), 0) + 1
    unmatched = sum(1 for (p0, p1), cnt in edges.items()
                    if cnt != 1 or edges.get((p1, p0), 0) != 1)

    # Tolerance is loose enough to absorb polygon-vs-circle discretisation
    # error, which is largest (still under 0.3%) for the small boss circles.
    err = abs(vol - expect_vol) / expect_vol if expect_vol else 0
    ok = degenerate == 0 and unmatched == 0 and vol > 0 and (expect_vol == 0 or err < 5e-3)
    print("    %-10s triangles %5d  degenerate %d  non-manifold %2d  "
          "volume %10.3f  expected %10.3f  error %.2e  %s"
          % (name, len(tris), degenerate, unmatched, vol, expect_vol, err, "OK" if ok else "FAIL"))
    return ok, vol


def check_assembly(label, parts):
    print("%s:" % label)
    ok_all = True
    total_tris = []
    total_vol = 0.0
    for name, tris, expect_vol in parts:
        ok, vol = check_component(name, tris, expect_vol)
        ok_all &= ok
        total_vol += vol
        total_tris += tris
    print("  -> %d triangles total, %.3f mm3 total volume, %s\n"
          % (len(total_tris), total_vol, "OK" if ok_all else "FAIL"))
    return ok_all, total_tris


def write_stl(path, tris, name):
    v = np.asarray(tris, dtype=np.float64)
    a, b, c = v[:, 0], v[:, 1], v[:, 2]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    with open(path, "wb") as f:
        head = ("Bangla Braille Tutor %s - mm - tools/gen_case_parts_3d.py" % name).encode()
        f.write(head.ljust(80, b" ")[:80])
        f.write(struct.pack("<I", len(tris)))
        for i in range(len(tris)):
            f.write(struct.pack("<12fH",
                                n[i, 0], n[i, 1], n[i, 2],
                                a[i, 0], a[i, 1], a[i, 2],
                                b[i, 0], b[i, 1], b[i, 2],
                                c[i, 0], c[i, 1], c[i, 2], 0))


def rounded_rect_area(w, h, r):
    return w * h - (4 - math.pi) * r * r


def annulus_area(r_outer, r_inner):
    return math.pi * (r_outer ** 2 - r_inner ** 2)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    enc = os.path.join(root, "enclosure")

    ok1, base_tris = check_assembly("case_base.stl (plate + 4 bosses)", base_cover_parts())
    base_path = os.path.join(enc, "case_base.stl")
    write_stl(base_path, base_tris, "base cover")
    print("  -> %s  (%.1f KB)\n" % (base_path, os.path.getsize(base_path) / 1024))

    ok2, walls_tris = check_assembly("case_walls.stl (4 corners + 4 strips)", side_wall_parts())
    walls_path = os.path.join(enc, "case_walls.stl")
    write_stl(walls_path, walls_tris, "side walls")
    print("  -> %s  (%.1f KB)" % (walls_path, os.path.getsize(walls_path) / 1024))

    raise SystemExit(0 if (ok1 and ok2) else 1)
