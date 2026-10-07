"""Original cobalt-blue hardtop coupe (art source, hollow-cabin revision).
One design, reused everywhere.  Pure bpy geometry, no imports.

Author: local Qwen builder.
Convention: forward = +Y (Unity +Z), up = +Z, left = -X.  Origin at ground
plane under the wheel centres.  Root empty = coupe_root (never transformed).
Footprint, wheel names / positions / radii and axle convention (spin about X)
are unchanged so existing physics / collision / route clearances stay valid.
The greenhouse is now a genuinely hollow sculpted shell: thin roof + connected
pillars + real openings; a single tinted coupe_glass material carries Alpha on
its Principled node and diffuse_color.  Named anchors (meters, coupe_root
local space):
  driver_hip_anchor     seated hip origin (LHD, left side).
  driver_forward_anchor hip + forward offset; the vector (hip->this) is the
                        body-forward / facing axis used by the runtime rig.
  steering_wheel_anchor steering-wheel centre (hand + camera alignment).
No driver is built here; the courier prefab is instantiated separately.
"""
import bpy
import bmesh
import math
from mathutils import Vector

NAME = "coupe"
scene = bpy.context.scene
scene.name = NAME
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


def mat(nm, col, rough=0.5, metal=0.0, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    try:
        b.inputs["Alpha"].default_value = alpha
    except Exception:
        pass
    m.diffuse_color = (col[0], col[1], col[2], alpha)
    if emit is not None:
        b.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        b.inputs["Emission Strength"].default_value = estr
    return m


M = {
    "paint":  mat("coupe_paint", (0.030, 0.130, 0.620), 0.28, 0.55),
    "paint2": mat("coupe_paint_dark", (0.016, 0.075, 0.380), 0.35, 0.55),
    "glass":  mat("coupe_glass", (0.040, 0.070, 0.095), 0.06, 0.0, alpha=0.32),
    "trim":   mat("coupe_trim", (0.020, 0.022, 0.026), 0.45, 0.20),
    "fabric": mat("coupe_seat", (0.040, 0.042, 0.050), 0.85, 0.0),
    "tire":   mat("coupe_tire", (0.028, 0.028, 0.030), 0.92, 0.0),
    "rim":    mat("coupe_rim", (0.520, 0.530, 0.550), 0.30, 1.0),
    "lamp":   mat("coupe_lamp", (0.900, 0.900, 0.850), 0.15, 0.0, (1.0, 0.95, 0.85), 3.0),
    "tail":   mat("coupe_tail", (0.450, 0.020, 0.020), 0.25, 0.0, (1.0, 0.05, 0.05), 3.0),
    "chrome": mat("coupe_chrome", (0.750, 0.760, 0.780), 0.18, 1.0),
}

root = bpy.data.objects.new("coupe_root", None)
scene.collection.objects.link(root)


def obj(nm, me, m, parent=root):
    ob = bpy.data.objects.new(nm, me)
    scene.collection.objects.link(ob)
    ob.data.materials.clear()
    ob.data.materials.append(M[m])
    ob.parent = parent
    return ob


def box(nm, dims, loc, m, parent=root):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dims[0]; v.co.y *= dims[1]; v.co.z *= dims[2]
    bm.to_mesh(me); bm.free()
    ob = obj(nm, me, m, parent)
    ob.location = loc
    return ob


def prism(nm, poly, axis, a0, a1, m):
    """Closed thin skin: extrude an in-plane polygon along one axis a0..a1."""
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    oax = [i for i in range(3) if i != axis]
    r0, r1 = [], []
    for (p, q) in poly:
        c0 = [0.0, 0.0, 0.0]; c0[oax[0]] = p; c0[oax[1]] = q; c0[axis] = a0
        c1 = list(c0); c1[axis] = a1
        r0.append(bm.verts.new(c0)); r1.append(bm.verts.new(c1))
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    return obj(nm, me, m)


def beam(nm, x, yb, zb, yt, zt, w, m):
    # Thin connected pillar along a line in the Y-Z plane, width w in X.
    dy = yt - yb; dz = zt - zb
    L = math.hypot(dy, dz)
    ob = box(nm, (w, 0.10, L), (x, 0.5 * (yb + yt), 0.5 * (zb + zt)), m)
    # The long local +Z axis must point from bottom to top. A Blender X
    # rotation sends +Z to (-sin, cos), so use -dy here.
    ob.rotation_euler.x = math.atan2(-dy, dz)
    return ob

def pane(nm, dx, dz, loc, ang, m):
    ob = box(nm, (dx, 0.07, dz), loc, m)
    ob.rotation_euler.x = ang
    return ob


# ---------------------------------------------------------------- lower body
# Coherent lower shell: keep cabin open, use corrected top-surface prisms for
# hood/deck (XY plan, thin Z skin) plus closed front/rear volumes and outer
# fenders that tie side/cowl/bulk to lamps/bumpers without crossing wheels.
prism('body_side_L', [(-0.55, 0.92), (0.98, 0.92), (1.06, 0.42), (-1.12, 0.42)],
      0, -0.80, -0.72, 'paint')
prism('body_side_R', [(-0.55, 0.92), (0.98, 0.92), (1.06, 0.42), (-1.12, 0.42)],
      0, 0.72, 0.80, 'paint')
prism('floor', [(-0.78, -1.10), (0.78, -1.10), (0.78, 1.02), (-0.78, 1.02)],
      2, 0.40, 0.46, 'trim')
prism('firewall', [(-0.74, 0.42), (0.74, 0.42), (0.74, 0.92), (-0.74, 0.92)],
      1, 0.92, 0.98, 'paint')
prism('rear_bulk', [(-0.70, 0.42), (0.70, 0.42), (0.70, 0.92), (-0.70, 0.92)],
      1, -1.06, -1.00, 'paint')
# hood: true hood deck as a thin horizontal XY/Z slab from cowl to nose.
prism('hood', [(-0.74, 0.96), (0.74, 0.96), (0.66, 1.96), (-0.66, 1.96)],
      2, 0.92, 0.98, 'paint')
# deck: true rear deck from rear bulkhead over trunk to tail.
prism('deck', [(-0.72, -1.06), (0.72, -1.06), (0.64, -2.02), (-0.64, -2.02)],
      2, 0.92, 0.98, 'paint')
# front and rear centre shells close hood/deck to the front/rear ends; width
# stays inside wheel inner faces so wheels remain separate.
prism('front_lower', [(-0.68, 0.44), (0.68, 0.44), (0.62, 0.96), (-0.62, 0.96)],
      1, 1.84, 2.24, 'paint')
prism('rear_lower', [(-0.66, 0.44), (0.66, 0.44), (0.60, 0.94), (-0.60, 0.94)],
      1, -2.20, -1.06, 'paint')
# front/rear end caps fill the last few centimetres to bumper/lamp mounts.
box('nose', (1.42, 0.16, 0.50), (0, 2.17, 0.70), 'paint2')
box('tail', (1.38, 0.16, 0.48), (0, -2.16, 0.70), 'paint2')
# outer fender quarters ride above the wheel crown and tie body sides to the
# end caps. They do not intersect actual wheel solids (wheel crown z=0.80).
for sx in (-0.90, 0.90):
    t = 'L' if sx < 0 else 'R'
    box('front_fender_' + t, (0.20, 0.88, 0.20), (sx, 1.16, 0.92), 'paint')
    box('rear_fender_' + t, (0.20, 0.88, 0.20), (sx, -1.16, 0.92), 'paint')
    box('front_shoulder_' + t, (0.22, 0.36, 0.16), (sx * 0.95, 0.78, 0.90), 'paint')
    box('rear_shoulder_' + t, (0.22, 0.40, 0.16), (sx * 0.95, -0.90, 0.90), 'paint')

box("rocker_L", (0.12, 2.20, 0.14), (-0.78, 0.00, 0.44), "trim")
box("rocker_R", (0.12, 2.20, 0.14), (0.78, 0.00, 0.44), "trim")
box("bumper_f", (1.50, 0.14, 0.24), (0, 2.30, 0.54), "trim")
box("bumper_r", (1.50, 0.14, 0.26), (0, -2.30, 0.58), "trim")
box("grille", (0.96, 0.06, 0.14), (0, 2.38, 0.68), "chrome")
box("spoiler", (1.36, 0.26, 0.06), (0, -2.00, 0.98), "paint2")
box("door_line_L", (0.04, 1.00, 0.40), (-0.81, 0.00, 0.66), "trim")
box("door_line_R", (0.04, 1.00, 0.40), (0.81, 0.00, 0.66), "trim")

for sx in (-0.56, 0.56):
    t = "L" if sx < 0 else "R"
    box("headlamp_" + t, (0.40, 0.16, 0.16), (sx, 2.26, 0.80), "lamp")
    box("tailamp_" + t, (0.44, 0.16, 0.14), (sx, -2.26, 0.74), "tail")
    box("mirror_" + t, (0.20, 0.12, 0.11), (sx * 1.06, 0.70, 1.00), "trim")

# --------------------------------------------------- hollow greenhouse shell
# roof/rails set the top envelope; the cabin volume stays open.
prism('roof', [(-0.64, 0.58), (0.64, 0.58), (0.64, -0.78), (-0.64, -0.78)],
      2, 1.29, 1.34, 'paint')
prism('rail_L', [(-0.82, 1.27), (0.62, 1.27), (0.62, 1.34), (-0.82, 1.34)],
      0, -0.76, -0.66, 'paint')
prism('rail_R', [(-0.82, 1.27), (0.62, 1.27), (0.62, 1.34), (-0.82, 1.34)],
      0, 0.66, 0.76, 'paint')
# Connected pillars.  The corrected beam helper rotates local +Z from bottom
# toward top, so these endpoints become real greenhouse corners.
for x in (-0.70, 0.70):
    t = 'L' if x < 0 else 'R'
    beam('apillar_' + t, x, 0.94, 0.92, 0.58, 1.31, 0.13, 'paint')
    beam('bpillar_' + t, x, -0.06, 0.92, -0.06, 1.32, 0.11, 'paint')
    beam('cpillar_' + t, x, -0.60, 0.94, -0.78, 1.31, 0.15, 'paint')

# Thin panes.  The bottom endpoint is local -Z after the derived angle; the
# pane length is the real slanted edge length. Rear window drops to deck.
wb_y = 0.94; wb_z = 0.92
wt_y = 0.58; wt_z = 1.29
pane('windshield', 1.36, math.hypot(wt_y - wb_y, wt_z - wb_z),
     (0, 0.5 * (wb_y + wt_y), 0.5 * (wb_z + wt_z)),
     math.atan2(-(wt_y - wb_y), wt_z - wb_z), 'glass')
rb_y = -1.12; rb_z = 0.98
rt_y = -0.78; rt_z = 1.29
pane('rear_window', 1.32, math.hypot(rt_y - rb_y, rt_z - rb_z),
     (0, 0.5 * (rb_y + rt_y), 0.5 * (rb_z + rt_z)),
     math.atan2(-(rt_y - rb_y), rt_z - rb_z), 'glass')

# ------------------------------------------------------------------ interior
box("dash", (1.46, 0.30, 0.30), (0, 0.74, 0.96), "trim")
box("dash_top", (1.46, 0.40, 0.10), (0, 0.66, 1.10), "trim")


def seat(nm, x):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    # cushion
    cu = [(sx, sy, sz) for sx in (-0.28, 0.28) for sy in (-0.27, 0.30) for sz in (0.0, 0.12)]
    # back (tapered top)
    pts = [
        (x - 0.28, -0.30, 0.10), (x + 0.28, -0.30, 0.10), (x + 0.28, -0.30, 0.62), (x - 0.28, -0.30, 0.62),
        (x - 0.24, -0.42, 0.18), (x + 0.24, -0.42, 0.18), (x + 0.24, -0.42, 0.70), (x - 0.24, -0.42, 0.70),
    ]
    vs = [bm.verts.new((p[0] - (x if p in pts[4:8] else 0) + (x if False else 0), 0, 0)) for p in []]
    # simpler: build via two boxes later; here just the cushion via cube
    bm.free()
    me2 = bpy.data.meshes.new(nm + "_cush")
    bm2 = bmesh.new()
    bmesh.ops.create_cube(bm2, size=1.0)
    for v in bm2.verts:
        v.co.x *= 0.58; v.co.y *= 0.62; v.co.z *= 0.14
    bm2.to_mesh(me2); bm2.free()
    o = obj(nm, me2, "fabric"); o.location = (x, -0.02, 0.50)
    bk = box(nm + "_back", (0.58, 0.12, 0.62), (x, -0.34, 0.80), "fabric")
    bk.rotation_euler.x = math.radians(-12)
    hd = box(nm + "_head", (0.40, 0.12, 0.18), (x, -0.44, 1.16), "fabric")
    return o


seat("seat_L", -0.42)
seat("seat_R", 0.42)

# steering wheel: genuine hollow torus rim plus restrained hub/spokes.
bm = bmesh.new()
nu, nv = 28, 8
major, minor = 0.170, 0.030
ring = []
for i in range(nu):
    u = 2.0 * math.pi * i / nu
    row = []
    for j in range(nv):
        v = 2.0 * math.pi * j / nv
        rr = major + minor * math.cos(v)
        row.append(bm.verts.new((rr * math.cos(u), minor * math.sin(v), rr * math.sin(u))))
    ring.append(row)
for i in range(nu):
    for j in range(nv):
        a = ring[i][j]
        b = ring[(i + 1) % nu][j]
        c = ring[(i + 1) % nu][(j + 1) % nv]
        d = ring[i][(j + 1) % nv]
        bm.faces.new((a, b, c, d))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.normal_update()
me = bpy.data.meshes.new('steering_wheel')
bm.to_mesh(me); bm.free()
sw = obj('steering_wheel', me, 'trim')
sw.location = (-0.42, 0.50, 0.86)
sw.rotation_euler.x = math.radians(18)
box('steering_hub', (0.070, 0.048, 0.070), (0, 0, 0), 'trim', parent=sw)
for deg in (90, 210, 330):
    a = math.radians(deg)
    rad = 0.095
    sp = box('steering_spoke_' + str(deg), (0.125, 0.030, 0.038),
             (rad * math.cos(a), 0, rad * math.sin(a)), 'trim', parent=sw)
    sp.rotation_euler.y = -a
box('steering_col', (0.10, 0.30, 0.10), (-0.42, 0.66, 0.92), 'trim')

# --------------------------------------------------------------------- wheels
def wheel(nm, loc, r=0.40, w=0.28):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=22, radius1=r, radius2=r, depth=w)
    for v in bm.verts:
        zc = v.co.z
        v.co.z = v.co.x
        v.co.x = -zc
    bm.to_mesh(me); bm.free()
    ob = obj(nm, me, "tire"); ob.location = loc
    box(nm + "_hub", (w + 0.04, 0.02, r * 1.30), loc, "rim", parent=root)
    return ob


for nm, loc in (("wheel_FL", (-0.88, 1.26, 0.40)), ("wheel_FR", (0.88, 1.26, 0.40)),
                ("wheel_RL", (-0.88, -1.20, 0.40)), ("wheel_RR", (0.88, -1.20, 0.40))):
    wheel(nm, loc)


# ------------------------------------------------------------------- anchors
def anchor(nm, loc, dtype='SINGLE_ARROW'):
    e = bpy.data.objects.new(nm, None)
    scene.collection.objects.link(e)
    e.empty_display_type = dtype
    e.empty_display_size = 0.18
    e.parent = root
    e.location = loc
    return e


anchor("driver_hip_anchor", (-0.42, -0.05, 0.46), 'PLAIN_AXES')
anchor('driver_forward_anchor', (-0.42, 0.55, 0.46), 'SINGLE_ARROW')

anchor("steering_wheel_anchor", (-0.42, 0.50, 0.86), 'SPHERE')

print("coupe objects:", len(scene.objects), "mats:", len(M))
