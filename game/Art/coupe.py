"""Original cobalt-blue coupe (art source). One design, reused everywhere.

Author: local Qwen builder. Pure bpy geometry, no imports.
Convention: forward = +Y (Unity +Z), up = +Z, length 4.55 m, width 1.84 m,
height 1.34 m. Origin at ground plane under the wheel centres.
"""
import bpy
import bmesh

NAME = "coupe"
scene = bpy.context.scene
scene.name = NAME
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


def mat(nm, col, rough=0.5, metal=0.0, emit=None, estr=0.0):
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = (emit[0], emit[1], emit[2], 1.0)
        b.inputs["Emission Strength"].default_value = estr
    return m


M = {
    "paint":  mat("coupe_paint", (0.030, 0.130, 0.620), 0.28, 0.55),
    "paint2": mat("coupe_paint_dark", (0.016, 0.075, 0.380), 0.35, 0.55),
    "glass":  mat("coupe_glass", (0.020, 0.035, 0.055), 0.08, 0.0),
    "trim":   mat("coupe_trim", (0.020, 0.022, 0.026), 0.45, 0.20),
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
        v.co.x *= dims[0]
        v.co.y *= dims[1]
        v.co.z *= dims[2]
    bm.to_mesh(me)
    bm.free()
    ob = obj(nm, me, m, parent)
    ob.location = loc
    return ob


def slab(nm, dx, dy, dz, y_bot, y_top, xbot, xtop, ybot, ytop, z, m):
    """Box with independent taper along Y (nose/tail) and X (roof)."""
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dx
        v.co.y *= dy
        v.co.z *= dz
        tx = xbot if v.co.y < 0 else xtop
        v.co.x = v.co.x * tx + 0.0
        ty = ybot if v.co.z < dz else ytop
        v.co.y = v.co.y * ty
    bm.to_mesh(me)
    bm.free()
    ob = obj(nm, me, m)
    ob.location = (0, 0, z)
    return ob


# --- main body: ONE extruded side silhouette (hood->trunk), tapered nose
def extrude(nm, prof, xw, xfront, m):
    """prof = ordered list of (y, z) outlining the side profile in Y-Z plane.
    Extruded along X from -xw..xw with front (highest-Y) verts narrowed by xfront
    to give a tapered nose/tail plan view. Produces a single closed solid."""
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    ymax = max(p[0] for p in prof)
    ymin = min(p[0] for p in prof)
    span = (ymax - ymin) or 1.0
    left, right = [], []
    for (y, z) in prof:
        # narrowing factor: 1.0 at centre, xfront toward the nose/tail ends
        t = abs(y - (ymax + ymin) * 0.5) / (span * 0.5)
        k = 1.0 - (1.0 - xfront) * (t ** 1.6)
        left.append(bm.verts.new((-xw * k, y, z)))
        right.append(bm.verts.new((xw * k, y, z)))
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((left[i], left[j], right[j], right[i]))
    bm.faces.new(list(reversed(left)))
    bm.faces.new(right)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = obj(nm, me, m)
    return ob


# side silhouette: ONE continuous hood->trunk volume (name preserved: body_lower)
_body_prof = [
    (2.05, 0.50),   # nose bottom front
    (2.18, 0.82),   # nose front top (tapered)
    (1.05, 0.92),   # cowl / windscreen base
    (-1.05, 0.92),  # cabin base rear
    (-1.95, 0.88),  # deck
    (-2.18, 0.80),  # tail top
    (-2.16, 0.48),  # tail bottom
    (-1.30, 0.42),  # underbody rear
    (1.30, 0.42),   # underbody front
]
body_lower = extrude("body_lower", _body_prof, 0.80, 0.74, "paint")

# flush nose/tail extensions (names preserved) keep the volume continuous,
# painted a tone darker so they read as sculpted ends, not stacked slabs.
box("body_nose", (1.34, 0.50, 0.40), (0, 2.20, 0.62), "paint2")
box("body_tail", (1.34, 0.46, 0.42), (0, -2.20, 0.64), "paint2")

# rocker sills tying the wheel arches together
box("rocker_L", (0.12, 2.20, 0.14), (-0.80, 0.00, 0.44), "trim")
box("rocker_R", (0.12, 2.20, 0.14), (0.80, 0.00, 0.44), "trim")

# bumpers integrated flush into nose/tail faces
box("bumper_f", (1.50, 0.14, 0.24), (0, 2.32, 0.54), "trim")
box("bumper_r", (1.50, 0.14, 0.26), (0, -2.32, 0.58), "trim")
box("grille", (0.96, 0.06, 0.14), (0, 2.40, 0.68), "chrome")

# head/tail lamps INSET into the body faces (not floating quads)
for sx in (-0.56, 0.56):
    box("headlamp_%s" % ("L" if sx < 0 else "R"), (0.40, 0.18, 0.16), (sx, 2.30, 0.80), "lamp")
    box("tailamp_%s" % ("L" if sx < 0 else "R"), (0.44, 0.18, 0.14), (sx, -2.30, 0.74), "tail")
    box("mirror_%s" % ("L" if sx < 0 else "R"), (0.20, 0.12, 0.11), (sx * 1.02, 0.72, 1.02), "trim")

# --- greenhouse / cabin: one raked roof volume, glass inset
box("cabin_floor", (1.60, 1.90, 0.10), (0, -0.05, 0.92), "trim")
slab("cabin_roof", 1.48, 1.50, 0.42, 0, 0, 0.92, 0.66, 0.92, 0.78, 1.16, "paint")
slab("cabin_glass", 1.40, 1.42, 0.38, 0, 0, 0.92, 0.66, 0.92, 0.78, 1.15, "glass")
box("windshield", (1.42, 0.12, 0.58), (0, 0.90, 1.08), "glass")
box("rear_window", (1.42, 0.12, 0.50), (0, -0.96, 1.06), "glass")
# thin hood/deck cap panels now sit ON the single volume (subtle shut lines)
box("hood", (1.50, 1.00, 0.06), (0, 1.52, 0.90), "paint")
box("decklid", (1.50, 0.80, 0.06), (0, -1.50, 0.90), "paint")
box("spoiler", (1.38, 0.24, 0.06), (0, -1.96, 0.96), "paint2")
box("a-pillar_L", (0.10, 0.14, 0.56), (-0.70, 0.74, 1.08), "trim")
box("a-pillar_R", (0.10, 0.14, 0.56), (0.70, 0.74, 1.08), "trim")
box("door_line_L", (0.05, 1.00, 0.38), (-0.805, 0.00, 0.70), "trim")
box("door_line_R", (0.05, 1.00, 0.38), (0.805, 0.00, 0.70), "trim")

# --- wheels: axle along X, spin about X in Unity too. Bigger + protrude past
# body sides (body half-width 0.80) so the wheels are clearly readable.
def wheel(nm, loc, r=0.40, w=0.28):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=22, radius1=r, radius2=r, depth=w)
    for v in bm.verts:
        c = v.co.z
        v.co.z = v.co.x
        v.co.x = -c
    bm.to_mesh(me)
    bm.free()
    ob = obj(nm, me, "tire")
    ob.location = loc
    hub = box(nm + "_hub", (w + 0.04, 0.02, r * 1.30), (loc[0], loc[1], loc[2]), "rim", parent=root)
    return ob


for nm, loc in (("wheel_FL", (-0.88, 1.26, 0.40)), ("wheel_FR", (0.88, 1.26, 0.40)),
                ("wheel_RL", (-0.88, -1.20, 0.40)), ("wheel_RR", (0.88, -1.20, 0.40))):
    wheel(nm, loc)

print("coupe objects:", len(scene.objects), "mats:", len(M))
