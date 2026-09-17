#!/usr/bin/env python3
"""Generate the top panel as a 3D solid: an STL to print and an HTML viewer.

The top panel ONLY -- a flat plate with every component hole. No walls, no
skirt, no base. Geometry comes from tools/gen_top_panel.py, the same constants
that produce top_panel_cutout.svg, so all three files describe one part.

    enclosure/top_panel.stl       binary STL, mm, ready for a slicer
    enclosure/top_panel_3d.html   Three.js viewer, orbit + preset views

    python tools/gen_top_panel_3d.py

There is no mesh library available here, so the solid is built by hand.

Plain Delaunay plus centroid filtering does NOT work: nothing forces a hole
boundary to appear as a triangulation edge, so triangles straddle it, get
discarded, and leave the mesh full of holes. Instead this refines to a
conforming Delaunay -- any boundary segment missing from the triangulation is
split at its midpoint and the triangulation is rebuilt, which leaves the
polygon unchanged because the midpoint of a chord lies on that chord. Once
every segment is an edge, no triangle can cross a boundary, so each one lies
wholly in the material or wholly in a hole and a centroid test is exact.

The result is checked for watertightness and against the analytic volume
before it is written.
"""
import math
import os
import struct
import sys

import numpy as np
from scipy.spatial import Delaunay, cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_top_panel as L   # noqa: E402  single source of truth

THICKNESS = L.PANEL_T       # 2.8 mm plate

# Boundary sampling. Chord error stays near 0.01 mm everywhere, which is well
# under the laser kerf and far under any printer's resolution.
N_OUTER_ARC = 24            # per 90 degree corner
N_MOTOR = 64
N_SCREW = 32
N_GRILL = 28
N_BTN_ARC = 10              # per corner of a rounded square

FILL_PITCH = 5.0            # interior points, purely for triangle shape
FILL_CLEAR = 1.0            # keep fill this far from any ring point
HOLE_TOL = 0.05             # allow the sampling sagitta when testing midpoints


# --------------------------------------------------------------- geometry ---
def to3d(x, y):
    """SVG frame (Y down, origin top-left) -> model frame (Y up)."""
    return x, L.PANEL_H - y


def outer_ring():
    """Rounded rectangle, counter-clockwise in the model frame."""
    w, h, r = L.PANEL_W, L.PANEL_H, L.CORNER_R
    pts = []
    # corner centres, counter-clockwise starting bottom-left
    corners = [(r, r, 180.0), (w - r, r, 270.0), (w - r, h - r, 0.0), (r, h - r, 90.0)]
    for cx, cy, a0 in corners:
        for k in range(N_OUTER_ARC + 1):
            a = math.radians(a0 + 90.0 * k / N_OUTER_ARC)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return dedupe(pts)


def circle_ring(cx, cy, r, n):
    """Clockwise in the model frame, so hole walls face into the cavity."""
    return [(cx + r * math.cos(-2 * math.pi * k / n),
             cy + r * math.sin(-2 * math.pi * k / n)) for k in range(n)]


def rounded_square_ring(cx, cy, size, rc, n_arc):
    """Clockwise rounded square."""
    h = size / 2 - rc
    pts = []
    # clockwise: bottom-right, bottom-left, top-left, top-right corner arcs
    corners = [(cx + h, cy - h, -90.0), (cx - h, cy - h, 180.0),
               (cx - h, cy + h, 90.0), (cx + h, cy + h, 0.0)]
    for ccx, ccy, a0 in corners:
        for k in range(n_arc + 1):
            a = math.radians(a0 - 90.0 * k / n_arc)
            pts.append((ccx + rc * math.cos(a), ccy + rc * math.sin(a)))
    return dedupe(pts)


def dedupe(pts, eps=1e-9):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > eps or abs(p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def build_rings():
    """Outer ring plus every hole ring, all in the model frame."""
    holes = []
    for _, x, y in L.motor_holes():
        cx, cy = to3d(x, y)
        holes.append(("motor", circle_ring(cx, cy, L.MOTOR_HOLE_DIA / 2, N_MOTOR),
                      (cx, cy)))
    for _, x, y in L.button_holes():
        cx, cy = to3d(x, y)
        holes.append(("button", rounded_square_ring(cx, cy, L.BTN_HOLE,
                                                    L.BTN_HOLE_R, N_BTN_ARC),
                      (cx, cy)))
    for x, y in L.grill_holes():
        cx, cy = to3d(x, y)
        holes.append(("grill", circle_ring(cx, cy, L.GRILL_HOLE_DIA / 2, N_GRILL),
                      (cx, cy)))
    for _, x, y in L.screw_holes():
        cx, cy = to3d(x, y)
        holes.append(("screw", circle_ring(cx, cy, L.SCREW_DIA / 2, N_SCREW),
                      (cx, cy)))
    return outer_ring(), holes


def shoelace(ring):
    a = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2.0


# ---------------------------------------------------------------- fields ----
def panel_sdf(p):
    """Signed distance to the rounded-rect outline. Negative inside."""
    qx = np.abs(p[:, 0] - L.PANEL_W / 2) - (L.PANEL_W / 2 - L.CORNER_R)
    qy = np.abs(p[:, 1] - L.PANEL_H / 2) - (L.PANEL_H / 2 - L.CORNER_R)
    outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
    inside = np.minimum(np.maximum(qx, qy), 0.0)
    return outside + inside - L.CORNER_R


def hole_sdf_min(p, holes):
    """Smallest signed distance to any hole. Negative means inside a hole."""
    best = np.full(len(p), 1e9)
    for kind, ring, (cx, cy) in holes:
        if kind in ("motor", "grill", "screw"):
            r = {"motor": L.MOTOR_HOLE_DIA / 2,
                 "grill": L.GRILL_HOLE_DIA / 2,
                 "screw": L.SCREW_DIA / 2}[kind]
            d = np.hypot(p[:, 0] - cx, p[:, 1] - cy) - r
        else:
            hx = L.BTN_HOLE / 2 - L.BTN_HOLE_R
            qx = np.abs(p[:, 0] - cx) - hx
            qy = np.abs(p[:, 1] - cy) - hx
            d = (np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
                 + np.minimum(np.maximum(qx, qy), 0.0) - L.BTN_HOLE_R)
        best = np.minimum(best, d)
    return best


def in_material(p, holes, hole_tol=0.0):
    return (panel_sdf(p) < -1e-9) & (hole_sdf_min(p, holes) > -hole_tol)


# ------------------------------------------------------------ face mesh -----
def cross2(o, a, b):
    """z of (a-o) x (b-o), for 2D points."""
    return (a[..., 0] - o[..., 0]) * (b[..., 1] - o[..., 1]) \
         - (a[..., 1] - o[..., 1]) * (b[..., 0] - o[..., 0])


def assemble(rings, holes):
    """Flatten rings to a point array, remembering each boundary segment."""
    pts = []
    segs = []
    for ri, ring in enumerate(rings):
        base = len(pts)
        pts.extend(ring)
        n = len(ring)
        for i in range(n):
            segs.append((ri, i, base + i, base + (i + 1) % n))
    ring_arr = np.asarray(pts, dtype=np.float64)
    n_ring = len(ring_arr)

    xs = np.arange(FILL_PITCH, L.PANEL_W, FILL_PITCH)
    ys = np.arange(FILL_PITCH, L.PANEL_H, FILL_PITCH)
    gx, gy = np.meshgrid(xs, ys)
    grid = np.column_stack([gx.ravel(), gy.ravel()])
    keep = (panel_sdf(grid) < -FILL_CLEAR) & (hole_sdf_min(grid, holes) > FILL_CLEAR)
    grid = grid[keep]
    if len(grid):
        grid = grid[cKDTree(ring_arr).query(grid)[0] > FILL_CLEAR]

    allp = np.vstack([ring_arr, grid]) if len(grid) else ring_arr
    return allp, segs, n_ring


def conforming_faces(rings, holes, max_passes=16):
    """Refine until every boundary segment is a Delaunay edge, then filter."""
    for p in range(max_passes):
        pts, segs, n_ring = assemble(rings, holes)
        tri = Delaunay(pts)
        present = set()
        for s in tri.simplices:
            i, j, k = int(s[0]), int(s[1]), int(s[2])
            present.add((min(i, j), max(i, j)))
            present.add((min(j, k), max(j, k)))
            present.add((min(i, k), max(i, k)))

        missing = [(ri, i) for (ri, i, a, b) in segs
                   if (min(a, b), max(a, b)) not in present]
        if not missing:
            print("conforming after %d refinement pass%s, %d boundary points"
                  % (p, "" if p == 1 else "es", n_ring))
            return pts, tri.simplices

        by_ring = {}
        for ri, i in missing:
            by_ring.setdefault(ri, []).append(i)
        for ri, idxs in by_ring.items():
            ring = rings[ri]
            for i in sorted(idxs, reverse=True):
                a = ring[i]
                b = ring[(i + 1) % len(ring)]
                ring.insert(i + 1, ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))

    raise RuntimeError("boundary never conformed after %d passes" % max_passes)


def point_in_poly(p, ring):
    """Ray crossing test. p is (M,2), ring is (N,2). Returns (M,) bool."""
    x = p[:, 0][:, None]
    y = p[:, 1][:, None]
    ax = ring[:, 0][None, :]
    ay = ring[:, 1][None, :]
    bx = np.roll(ring[:, 0], -1)[None, :]
    by = np.roll(ring[:, 1], -1)[None, :]
    straddles = (ay > y) != (by > y)
    dy = np.where(by - ay == 0.0, 1e-300, by - ay)
    xcross = ax + (bx - ax) * (y - ay) / dy
    return (np.sum(straddles & (x < xcross), axis=1) % 2) == 1


def in_material_exact(p, outer_ring_arr, hole_ring_arrs):
    """Inside the outer polygon and outside every hole polygon.

    The analytic circle SDF cannot be used here. Each hole polygon is
    inscribed in its true circle, so the sliver between a chord and its arc is
    material even though the circle test calls it hole. Testing against the
    actual refined rings has no such gap.
    """
    inside = panel_sdf(p) < 0.0          # outer polygon is inscribed, so safe
    for ring in hole_ring_arrs:
        lo = ring.min(axis=0) - 0.01
        hi = ring.max(axis=0) + 0.01
        cand = np.where(inside
                        & (p[:, 0] >= lo[0]) & (p[:, 0] <= hi[0])
                        & (p[:, 1] >= lo[1]) & (p[:, 1] <= hi[1]))[0]
        if len(cand):
            inside[cand] &= ~point_in_poly(p[cand], ring)
    return inside


def face_triangles(rings, holes):
    pts, simp = conforming_faces(rings, holes)

    # With every boundary segment present as an edge, no triangle can cross a
    # boundary, so each lies wholly in the material or wholly in a hole. The
    # centroid decides which.
    outer_arr = np.asarray(rings[0], dtype=np.float64)
    hole_arrs = [np.asarray(r, dtype=np.float64) for r in rings[1:]]
    a, b, c = pts[simp[:, 0]], pts[simp[:, 1]], pts[simp[:, 2]]
    simp = simp[in_material_exact((a + b + c) / 3.0, outer_arr, hole_arrs)]

    # counter-clockwise, so the top face normal is +Z
    a, b, c = pts[simp[:, 0]], pts[simp[:, 1]], pts[simp[:, 2]]
    cw = cross2(a, b, c) < 0
    simp[cw] = simp[cw][:, [0, 2, 1]]
    return pts, simp


def build_mesh():
    """Returns the STL triangle soup plus the indexed data the viewer needs.

    Ring points occupy the first sum(ring_lens) entries of pts2d, in ring
    order, so walls and outlines can reference the same vertices as the faces.
    """
    outer, holes = build_rings()
    rings = [list(outer)] + [list(h[1]) for h in holes]
    pts2d, faces = face_triangles(rings, holes)
    outer = rings[0]
    hole_rings = rings[1:]
    ring_lens = [len(r) for r in rings]
    t = THICKNESS
    tris = []

    for i, j, k in faces:
        p, q, r = pts2d[i], pts2d[j], pts2d[k]
        tris.append(((p[0], p[1], t), (q[0], q[1], t), (r[0], r[1], t)))   # top
        tris.append(((p[0], p[1], 0.0), (r[0], r[1], 0.0), (q[0], q[1], 0.0)))

    # Walls follow the SAME refined rings the faces were built from, so every
    # wall edge has a matching face edge and the mesh closes.
    for ring in [outer] + hole_rings:
        n = len(ring)
        for i in range(n):
            ax, ay = ring[i]
            bx, by = ring[(i + 1) % n]
            tris.append(((ax, ay, 0.0), (bx, by, 0.0), (bx, by, t)))
            tris.append(((ax, ay, 0.0), (bx, by, t), (ax, ay, t)))

    area2d = shoelace(outer) + sum(shoelace(r) for r in hole_rings)
    return tris, area2d, pts2d, faces, ring_lens


# ------------------------------------------------------------- checking -----
def check(tris, area2d):
    v = np.asarray(tris, dtype=np.float64)
    a, b, c = v[:, 0], v[:, 1], v[:, 2]

    vol = np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) / 6.0
    expect = area2d * THICKNESS

    n = np.cross(b - a, c - a)
    areas = 0.5 * np.linalg.norm(n, axis=1)
    degenerate = int(np.sum(areas < 1e-12))

    q = np.round(v, 6)
    edges = {}
    for tri in q:
        for i in range(3):
            p0 = tuple(tri[i])
            p1 = tuple(tri[(i + 1) % 3])
            edges[(p0, p1)] = edges.get((p0, p1), 0) + 1
    unmatched = 0
    for (p0, p1), cnt in edges.items():
        if cnt != 1 or edges.get((p1, p0), 0) != 1:
            unmatched += 1

    print("triangles            %d" % len(tris))
    print("degenerate           %d" % degenerate)
    print("volume               %.4f mm3" % vol)
    print("expected             %.4f mm3  (plan area %.4f x %.1f mm)"
          % (expect, area2d, THICKNESS))
    print("volume error         %.3e mm3 (%.2e relative)"
          % (abs(vol - expect), abs(vol - expect) / expect))
    print("non-manifold edges   %d" % unmatched)

    ok = (degenerate == 0 and unmatched == 0
          and abs(vol - expect) / expect < 1e-9 and vol > 0)
    print("\n%s: %s" % ("OK" if ok else "FAIL",
                        "watertight, outward normals, volume exact"
                        if ok else "mesh did not verify"))
    return ok


def write_stl(path, tris):
    v = np.asarray(tris, dtype=np.float64)
    a, b, c = v[:, 0], v[:, 1], v[:, 2]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    with open(path, "wb") as f:
        head = b"Bangla Braille Tutor top panel - mm - tools/gen_top_panel_3d.py"
        f.write(head.ljust(80, b" ")[:80])
        f.write(struct.pack("<I", len(tris)))
        for i in range(len(tris)):
            f.write(struct.pack("<12fH",
                                n[i, 0], n[i, 1], n[i, 2],
                                a[i, 0], a[i, 1], a[i, 2],
                                b[i, 0], b[i, 1], b[i, 2],
                                c[i, 0], c[i, 1], c[i, 2], 0))


# ----------------------------------------------------------------- html -----
def build_html(pts2d, faces, ring_lens):
    def fmt(x):
        s = "%.4f" % x
        s = s.rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"

    P = ",".join(fmt(v) for p in pts2d for v in p)
    F = ",".join(str(int(i)) for tri in faces for i in tri)
    RL = ",".join(str(n) for n in ring_lens)

    layout = "\n".join([
        "    const W = %g, H = %g, T = %g;" % (L.PANEL_W, L.PANEL_H, THICKNESS),
        "    // Verified mesh, identical to top_panel.stl. P = 2D points in the",
        "    // panel plane, F = triangle indices, RL = ring lengths (the ring",
        "    // points are the first sum(RL) entries of P, in ring order).",
        "    const P = [%s];" % P,
        "    const F = [%s];" % F,
        "    const RL = [%s];" % RL,
    ])

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Top Panel 3D</title>
<style>
  :root {
    --bg:#eceae4; --panel:#ffffff; --ink:#1c1c1a; --muted:#6b6b66;
    --line:#d6d3cb; --accent:#8a5a2b;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg:#17171a; --panel:#212127; --ink:#eceae4; --muted:#9a9a94;
      --line:#33333b; --accent:#d69a5c;
    }
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:14px/1.5 ui-sans-serif,system-ui,"Segoe UI",Roboto,sans-serif; }
  #wrap { position:fixed; inset:0; }
  #view { position:absolute; inset:0; }
  #hud { position:absolute; top:16px; left:16px; background:var(--panel);
         border:1px solid var(--line); border-radius:10px; padding:14px 16px;
         max-width:280px; box-shadow:0 6px 24px rgba(0,0,0,.10); }
  #hud h1 { margin:0 0 2px; font-size:15px; font-weight:650; }
  #hud p  { margin:0 0 10px; font-size:12px; color:var(--muted); }
  table { width:100%; border-collapse:collapse; font-size:12px; }
  td { padding:3px 0; vertical-align:top; }
  td:last-child { text-align:right; font-variant-numeric:tabular-nums;
                  color:var(--muted); white-space:nowrap; }
  #btns { position:absolute; bottom:16px; left:16px; display:flex; gap:6px;
          flex-wrap:wrap; }
  button { font:inherit; font-size:12px; padding:7px 12px; cursor:pointer;
           background:var(--panel); color:var(--ink);
           border:1px solid var(--line); border-radius:7px; }
  button:hover { border-color:var(--accent); color:var(--accent); }
  button[aria-pressed="true"] { background:var(--accent); color:#fff;
                                border-color:var(--accent); }
  #hint { position:absolute; bottom:16px; right:16px; font-size:11px;
          color:var(--muted); text-align:right; }
</style>
</head>
<body>
<div id="wrap">
  <div id="view"></div>
  <div id="hud">
    <h1>Top Panel</h1>
    <p>Bangla Braille Tutor. This part only, no walls or base.</p>
    <table>
      <tr><td>Plate</td><td>__W__ &times; __H__ &times; __T__ mm</td></tr>
      <tr><td>Corner radius</td><td>__R__ mm</td></tr>
      <tr><td>Motor holes</td><td>6 &times; &oslash; __MD__ mm</td></tr>
      <tr><td>Button holes</td><td>7 &times; __BS__ mm sq</td></tr>
      <tr><td>Speaker grill</td><td>__NG__ &times; &oslash; __GD__ mm</td></tr>
      <tr><td>Screw holes</td><td>4 &times; &oslash; __SD__ mm</td></tr>
    </table>
  </div>
  <div id="btns">
    <button id="v-iso">Iso</button>
    <button id="v-top">Top</button>
    <button id="v-front">Front</button>
    <button id="t-edges" aria-pressed="true">Edges</button>
    <button id="t-spin" aria-pressed="false">Spin</button>
  </div>
  <div id="hint">drag to orbit &middot; scroll to zoom</div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
(function () {
__LAYOUT__

  // ---- Build the solid from the verified triangulation.
  //
  // THREE.ExtrudeGeometry is deliberately NOT used. Its hole bridging emits
  // degenerate slivers, and EdgesGeometry then draws lines along them, which
  // shows up as a phantom line joining two neighbouring holes. This geometry
  // is the same one written to top_panel.stl, which is checked watertight and
  // volume-exact, so nothing here can drift from the printed part.
  //
  // Panel plane (x, y) maps to (x - W/2, level, H/2 - y). That is a rotation,
  // so triangle winding carries over and the normals stay outward.
  const N = P.length / 2;
  const pos = new Float32Array(N * 2 * 3);
  for (let i = 0; i < N; i++) {
    const x = P[2 * i] - W / 2;
    const z = H / 2 - P[2 * i + 1];
    pos[3 * i] = x;     pos[3 * i + 1] = T; pos[3 * i + 2] = z;   // top
    const j = N + i;
    pos[3 * j] = x;     pos[3 * j + 1] = 0; pos[3 * j + 2] = z;   // bottom
  }

  const idx = [];
  for (let t = 0; t < F.length; t += 3) {
    const a = F[t], b = F[t + 1], c = F[t + 2];
    idx.push(a, b, c);                       // top face,  normal +Y
    idx.push(N + a, N + c, N + b);           // bottom face, normal -Y
  }
  const loops = [];                          // ring index ranges, for walls
  let base = 0;
  for (const n of RL) { loops.push([base, n]); base += n; }
  for (const [b0, n] of loops) {
    for (let i = 0; i < n; i++) {
      const a = b0 + i, b = b0 + (i + 1) % n;
      idx.push(N + a, N + b, b);
      idx.push(N + a, b, a);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();                // flatShading overrides these

  // ---- scene
  const host = document.getElementById('view');
  const scene = new THREE.Scene();
  const dark = matchMedia('(prefers-color-scheme: dark)').matches;
  scene.background = new THREE.Color(dark ? 0x17171a : 0xeceae4);

  const camera = new THREE.PerspectiveCamera(38, 1, 1, 4000);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  host.appendChild(renderer.domElement);

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  const mat = new THREE.MeshStandardMaterial({
    color: dark ? 0xb8b4aa : 0xe8e4da, metalness: 0.08, roughness: 0.62,
    flatShading: true, side: THREE.DoubleSide
  });
  const mesh = new THREE.Mesh(geo, mat);
  scene.add(mesh);

  // Outlines drawn straight from the ring loops. EdgesGeometry is not used:
  // it infers edges from dihedral angles and invents them across the
  // triangulation, which is what produced the phantom hole-to-hole line.
  const eIdx = [];
  for (const [b0, n] of loops) {
    for (let i = 0; i < n; i++) {
      const a = b0 + i, b = b0 + (i + 1) % n;
      eIdx.push(a, b, N + a, N + b);
    }
  }
  const eGeo = new THREE.BufferGeometry();
  eGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  eGeo.setIndex(eIdx);
  const edges = new THREE.LineSegments(
    eGeo, new THREE.LineBasicMaterial({ color: dark ? 0x2a2a30 : 0x8d8a82 })
  );
  scene.add(edges);

  scene.add(new THREE.HemisphereLight(0xffffff, 0x5a5a52, dark ? 0.55 : 0.85));
  const key = new THREE.DirectionalLight(0xffffff, dark ? 0.75 : 0.65);
  key.position.set(-160, 260, 190);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.28);
  fill.position.set(200, 120, -160);
  scene.add(fill);

  // ---- views
  const views = {
    iso:   [ -170,  215,  225 ],
    top:   [    0,  330,    1 ],
    front: [    0,   40,  330 ]
  };
  function setView(name) {
    const v = views[name];
    camera.position.set(v[0], v[1], v[2]);
    controls.target.set(0, T / 2, 0);
    controls.update();
  }
  document.getElementById('v-iso')  .onclick = () => setView('iso');
  document.getElementById('v-top')  .onclick = () => setView('top');
  document.getElementById('v-front').onclick = () => setView('front');

  const eBtn = document.getElementById('t-edges');
  eBtn.onclick = () => {
    edges.visible = !edges.visible;
    eBtn.setAttribute('aria-pressed', String(edges.visible));
  };
  const sBtn = document.getElementById('t-spin');
  let spin = false;
  sBtn.onclick = () => {
    spin = !spin;
    sBtn.setAttribute('aria-pressed', String(spin));
  };

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  addEventListener('resize', resize);
  resize();
  setView('iso');

  (function loop() {
    requestAnimationFrame(loop);
    if (spin) { mesh.rotation.y += 0.0035; edges.rotation.y = mesh.rotation.y; }
    controls.update();
    renderer.render(scene, camera);
  })();
})();
</script>
</body>
</html>
""".replace("__LAYOUT__", layout) \
   .replace("__W__", "%g" % L.PANEL_W).replace("__H__", "%g" % L.PANEL_H) \
   .replace("__T__", "%g" % THICKNESS).replace("__R__", "%g" % L.CORNER_R) \
   .replace("__MD__", "%g" % L.MOTOR_HOLE_DIA).replace("__BS__", "%g" % L.BTN_HOLE) \
   .replace("__NG__", "%d" % len(L.grill_holes())).replace("__GD__", "%g" % L.GRILL_HOLE_DIA) \
   .replace("__SD__", "%g" % L.SCREW_DIA)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    enc = os.path.join(root, "enclosure")

    tris, area2d, pts2d, faces, ring_lens = build_mesh()
    ok = check(tris, area2d)

    stl = os.path.join(enc, "top_panel.stl")
    write_stl(stl, tris)
    print("\nstl     -> %s  (%.1f KB)" % (stl, os.path.getsize(stl) / 1024))

    html = os.path.join(enc, "top_panel_3d.html")
    with open(html, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_html(pts2d, faces, ring_lens))
    print("html    -> %s  (%.1f KB)" % (html, os.path.getsize(html) / 1024))

    raise SystemExit(0 if ok else 1)
