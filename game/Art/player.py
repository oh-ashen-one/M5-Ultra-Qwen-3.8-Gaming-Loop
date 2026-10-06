"""Original player character (art source). Pure bpy, no imports.

Author: local Qwen builder. Convention: up = +Z, forward = +Y, origin at feet
(Unity: +Z forward, ground plane at 0). Height 1.80 m, shoulder width 0.50 m.
Named *_root empties are animation pivots: the game rotates these for the
walk/aim pose (legL_root, legR_root, armL_root, armR_root, head_root).
"""
import bpy
import math

NAME = "player"
scene = bpy.context.scene
scene.name = NAME
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


def mat(nm, col, rough=0.8, metal=0.0):
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M = {
    "jacket": mat("pl_jacket", (0.055, 0.060, 0.068), 0.78),
    "shirt":  mat("pl_shirt", (0.720, 0.720, 0.700), 0.85),
    "jeans":  mat("pl_jeans", (0.075, 0.095, 0.140), 0.88),
    "skin":   mat("pl_skin", (0.330, 0.215, 0.155), 0.62),
    "hair":   mat("pl_hair", (0.030, 0.028, 0.028), 0.70),
    "shoe":   mat("pl_shoe", (0.040, 0.040, 0.045), 0.70),
    "steel":  mat("pl_steel", (0.230, 0.235, 0.250), 0.40, 1.0),
}
root = bpy.data.objects.new("player_root", None)
scene.collection.objects.link(root)


def pivot(nm, loc, parent):
    o = bpy.data.objects.new(nm, None)
    scene.collection.objects.link(o)
    o.location = loc
    o.parent = parent
    return o


def box(nm, dims, loc, m, parent, rz=0.0, rx=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc,
                                   rotation=(math.radians(rx), 0, math.radians(rz)))
    ob = bpy.context.active_object
    ob.name = nm
    ob.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(M[m])
    ob.parent = parent
    return ob


def ball(nm, r, loc, m, parent, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=14, ring_count=10)
    ob = bpy.context.active_object
    ob.name = nm
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(M[m])
    ob.parent = parent
    return ob


# body sits at hip/torso-centre world Z=0.92; ALL child pivots/boxes below use
# TRUE parent-local coords (world = 0.92 + local_z) so limbs no longer stack a
# second +0.92 offset (the bug that lifted arms over the head and floated shoes).
body = pivot("body", (0, 0, 0.92), root)
box("torso", (0.42, 0.26, 0.58), (0, 0, 0.26), "jacket", body)
box("shirt_strip", (0.26, 0.275, 0.16), (0, 0.01, 0.05), "shirt", body)
box("shoulders", (0.50, 0.24, 0.16), (0, 0, 0.56), "jacket", body)
box("collar", (0.26, 0.22, 0.10), (0, 0, 0.65), "jacket", body)
box("belt", (0.42, 0.27, 0.10), (0, 0, 0.00), "shoe", body)
box("backpack", (0.30, 0.14, 0.34), (0, -0.18, 0.30), "jeans", body)
box("pack_strap", (0.10, 0.10, 0.06), (0, 0.14, 0.46), "shoe", body)
box("neck", (0.11, 0.11, 0.10), (0, 0, 0.62), "skin", body)
ball("head", 0.13, (0, 0.01, 0.73), "skin", body)
ball("hair", 0.138, (0, -0.01, 0.78), "hair", body, scale=(1, 1, 0.72))
head = pivot("head_root", (0, 0, 0.63), root)
head.parent = body

for s, tag in ((-1, "L"), (1, "R")):
    a = pivot("arm%s_root" % tag, (s * 0.27, 0, 0.56), root)
    a.parent = body
    box("arm%s_upper" % tag, (0.115, 0.125, 0.34), (0, 0, -0.18), "jacket", a)
    box("arm%s_fore" % tag, (0.105, 0.115, 0.30), (0, 0.015, -0.48), "jacket", a)
    ball("arm%s_hand" % tag, 0.058, (0, 0.02, -0.66), "skin", a)
    l = pivot("leg%s_root" % tag, (s * 0.115, 0, 0.03), root)
    l.parent = body
    box("leg%s_thigh" % tag, (0.165, 0.180, 0.44), (0, 0, -0.22), "jeans", l)
    box("leg%s_shin" % tag, (0.145, 0.160, 0.42), (0, -0.01, -0.62), "jeans", l)
    box("leg%s_shoe" % tag, (0.150, 0.300, 0.09), (0, 0.06, -0.875), "shoe", l)

gun = pivot("gun_root", (-0.02, 0.16, 0.06), root)
gun.parent = body
box("gun_slide", (0.055, 0.215, 0.075), (0, 0, 0), "steel", gun)
box("gun_grip", (0.048, 0.065, 0.135), (0, -0.065, -0.09), "shoe", gun, rx=-12)
print("player objects:", len(scene.objects), "mats:", len(M))
