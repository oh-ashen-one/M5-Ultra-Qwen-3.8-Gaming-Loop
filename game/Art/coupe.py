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


# --- lower body: single original silhouette, nose at +Y
box("body_lower", (1.84, 3.30, 0.56), (0, 0.05, 0.60), "paint")
box("body_nose", (1.70, 0.62, 0.46), (0, 2.02, 0.55), "paint2")
box("body_tail", (1.72, 0.60, 0.50), (0, -1.96, 0.57), "paint2")
box("rocker_L", (0.14, 2.60, 0.16), (-0.90, 0.05, 0.30), "trim")
box("rocker_R", (0.14, 2.60, 0.16), (0.90, 0.05, 0.30), "trim")
box("bumper_f", (1.72, 0.26, 0.30), (0, 2.32, 0.44), "trim")
box("bumper_r", (1.72, 0.24, 0.30), (0, -2.24, 0.46), "trim")
box("grille", (1.02, 0.08, 0.16), (0, 2.36, 0.62), "chrome")
for sx in (-0.62, 0.62):
    box("headlamp_%s" % ("L" if sx < 0 else "R"), (0.42, 0.10, 0.16), (sx, 2.33, 0.74), "lamp")
    box("tailamp_%s" % ("L" if sx < 0 else "R"), (0.40, 0.08, 0.15), (sx, -2.34, 0.76), "tail")
    box("mirror_%s" % ("L" if sx < 0 else "R"), (0.20, 0.12, 0.11), (sx * 1.08, 0.74, 1.00), "trim")

# --- greenhouse / cabin
box("cabin_floor", (1.66, 1.90, 0.10), (0, -0.10, 0.90), "trim")
slab("cabin_roof", 1.56, 1.62, 0.46, 0, 0, 1.00, 0.80, 1.06, 0.88, 1.12, "paint")
slab("cabin_glass", 1.48, 1.54, 0.40, 0, 0, 1.00, 0.80, 1.06, 0.88, 1.11, "glass")
box("windshield", (1.44, 0.10, 0.62), (0, 0.86, 1.02), "glass")
box("rear_window", (1.44, 0.10, 0.52), (0, -0.94, 1.02), "glass")
box("hood", (1.62, 1.10, 0.08), (0, 1.52, 0.92), "paint")
box("decklid", (1.62, 0.86, 0.08), (0, -1.60, 0.92), "paint")
box("spoiler", (1.44, 0.26, 0.07), (0, -2.02, 1.00), "paint2")
box("a-pillar_L", (0.10, 0.14, 0.60), (-0.72, 0.80, 1.06), "trim")
box("a-pillar_R", (0.10, 0.14, 0.60), (0.72, 0.80, 1.06), "trim")
box("door_line_L", (0.06, 1.05, 0.42), (-0.925, 0.10, 0.66), "trim")
box("door_line_R", (0.06, 1.05, 0.42), (0.925, 0.10, 0.66), "trim")

# --- wheels: axle along X, spin about X in Unity too
def wheel(nm, loc, r=0.345, w=0.26):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r, radius2=r, depth=w)
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


for nm, loc in (("wheel_FL", (-0.86, 1.42, 0.345)), ("wheel_FR", (0.86, 1.42, 0.345)),
                ("wheel_RL", (-0.86, -1.34, 0.345)), ("wheel_RR", (0.86, -1.34, 0.345))):
    wheel(nm, loc)

print("coupe objects:", len(scene.objects), "mats:", len(M))
