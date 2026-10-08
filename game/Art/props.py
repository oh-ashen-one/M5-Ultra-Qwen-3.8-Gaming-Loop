"""Original Chicago street furniture: L-track steel pier/viaduct, fence,
dumpster, alley props. Pure bpy, no imports. Author: local Qwen builder.
Convention: up = +Z, one module = 14 m of elevated structure along X.
"""
import bpy
import bmesh
import math

NAME = "props"
scene = bpy.context.scene
scene.name = NAME
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


def mat(nm, col, rough=0.8, metal=0.0, emit=None, estr=0.0):
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
    "concrete": mat("p_concrete", (0.340, 0.335, 0.330)),
    "cguyan":   mat("p_concrete grimy", (0.245, 0.240, 0.228)),
    "steel":    mat("p_steel", (0.210, 0.215, 0.225), 0.45, 1.0),
    "rust":     mat("p_rusted steel", (0.270, 0.145, 0.085), 0.75, 0.7),
    "rail":     mat("p_rail steel", (0.430, 0.430, 0.440), 0.35, 1.0),
    "fence":    mat("p_chainlink", (0.400, 0.410, 0.420), 0.5, 1.0),
    "green":    mat("p_dumpster green", (0.075, 0.200, 0.135), 0.70, 0.1),
    "blue":     mat("p_dumpster blue", (0.070, 0.140, 0.300), 0.70, 0.1),
    "tire":     mat("p_tire", (0.030, 0.030, 0.032), 0.95, 0.0),
    "wood":     mat("p_pallet wood", (0.260, 0.175, 0.105)),
    "yellow":   mat("p_bollard yellow", (0.620, 0.450, 0.045), 0.65, 0.1),
    "lamp":     mat("p_lamp glow", (0.9, 0.85, 0.7), 0.3, 0.0, (1.0, 0.86, 0.6), 6.0),
}

for nm in list(M):
    pass


def new(name):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    return o


root = new("props_root")


def box(nm, dims, loc, m, parent=root, rz=0.0):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.els if False else bm.verts:
        v.co.x *= dims[0]
        v.co.y *= dims[1]
        v.co.z *= dims[2]
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nm, me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(M[m])
    ob.location = loc
    ob.rotation_euler[2] = math.radians(rz)
    ob.parent = parent
    return ob


def cyl(nm, r, depth, loc, m, parent=root, rot=(0.0, 0.0, 0.0), verts=14):
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nm, me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(M[m])
    ob.location = loc
    ob.rotation_euler = rot
    ob.parent = parent
    return ob


# ---- elevated L structure: pier bents every 14 m, deck at 9.2 m
L = new("ltrack")
L.parent = root
for i in range(3):
    x = -14.0 + i * 14.0
    pier = new("pier_%02d" % i)
    pier.parent = L
    pier.location = (x, 0, 0)
    box("pier_base%02d" % i, (3.0, 3.0, 0.7), (0, 0, 0.35), "concrete", pier)
    box("pier_colL%02d" % i, (1.05, 1.05, 8.0), (-1.25, 0, 4.4), "cguyan", pier)
    box("pier_colR%02d" % i, (1.05, 1.05, 8.0), (1.25, 0, 4.4), "cguyan", pier)
    box("pier_cap%02d" % i, (4.2, 2.2, 0.55), (0, 0, 8.65), "concrete", pier)
    box("pier_brace%02d" % i, (3.4, 0.32, 0.42), (0, 0, 7.6), "rust", pier)
    for s in (-1, 1):
        box("pier_gus%02d_%d" % (i, s), (0.24, 1.6, 0.24), (s * 1.9, 0, 6.6), "rust", pier)
box("deck_spanA", (14.6, 8.6, 0.85), (-7.0, 0, 9.45), "concrete", L)
box("deck_spanB", (14.6, 8.6, 0.85), (7.0, 0, 9.45), "concrete", L)
box("deck_fasciaA", (14.6, 0.42, 0.9), (-7.0, -4.35, 8.85), "cguyan", L)
box("deck_fasciaB", (14.6, 0.42, 0.9), (7.0, -4.35, 8.85), "cguyan", L)
for i in range(2):
    y = -4.15 + i * 8.3
    box("rail_walk%02d" % i, (28.6, 0.14, 0.10), (0, y, 11.25), "rail", L)
    for j in range(21):
        box("rail_post%02d_%02d" % (i, j), (0.09, 0.09, 1.7), (-14.0 + j * 1.4, y, 10.4), "rail", L)
box("rail_trackbed", (28.6, 4.2, 0.20), (0, 0, 9.98), "cguyan", L)
for y in (-1.0, 1.0):
    box("rail_track%02d" % (0 if y < 0 else 1), (28.6, 0.14, 0.16), (0, y, 10.16), "rail", L)

# ---- chain-link fence run (collision stop) 18 m along X
F = new("fence_run")
F.parent = root
box("fence_rail_top", (18.0, 0.09, 0.09), (0, 0, 2.15), "steel", F)
box("fence_rail_mid", (18.0, 0.08, 0.08), (0, 0, 1.10), "steel", F)
for i in range(10):
    x = -9.0 + i * 2.0
    cyl("fence_post%02d" % i, 0.06, 2.3, (x, 0, 1.15), "steel", F)
    for k in range(11):
        box("fence_mesh%02d_%02d" % (i, k), (0.05, 0.05, 0.16), (x + 0.2 + k * 0.16, 0, 1.95), "fence", F, rz=45)
        box("fence_mesh%02d_b%02d" % (i, k), (0.05, 0.05, 0.16), (x + 0.2 + k * 0.16, 0, 0.85), "fence", F, rz=45)

# ---- alley mouth props
A = new("alley_props")
A.parent = root
for nm, m, x in (("dumpster_a", "green", -2.2), ("dumpster_b", "blue", 2.6)):
    g = new(nm)
    g.parent = A
    g.location = (x, 0, 0)
    box(nm + "_body", (2.4, 1.25, 1.15), (0, 0, 0.62), m, g)
    box(nm + "_lid", (2.45, 1.30, 0.16), (0, -0.05, 1.27), m, g, rz=4)
    box(nm + "_rail", (2.45, 0.08, 0.08), (0, -0.66, 1.05), "steel", g)
    for sx in (-0.9, 0.9):
        cyl(nm + "_wheel_%0.1f" % sx, 0.16, 0.12, (sx, -0.5, 0.16), "tire", g, rot=(0, math.pi / 2, 0))
for i in range(5):
    cyl("tire_stack%02d" % i, 0.42, 0.24, (5.6, 1.2 + (i % 2) * 0.12, 0.13 + i * 0.245), "tire", A,
        rot=(math.pi / 2, 0, 0))
for i in range(3):
    box("pallet%02d" % i, (1.2, 0.9, 0.16), (-5.4 + i * 0.12, 1.1 - i * 0.05, 0.09 + i * 0.17), "wood", A, rz=6 * i)
for i in range(4):
    box("bollard%02d" % i, (0.24, 0.24, 1.05), (7.4 + (i % 2) * 0.9, -1.6 + i * 1.1, 0.52), "yellow", A)
for i in range(6):
    box("trash%02d" % i, (0.34, 0.30, 0.26), (-1.0 + i * 0.7, -0.9 - (i % 3) * 0.35, 0.13), "cguyan", A, rz=25 * i)

# ---- street lamp + hydrant
S = new("street_fixtures")
S.parent = root
cyl("lamp_post", 0.11, 5.6, (4.0, -3.4, 2.8), "steel", S)
box("lamp_arm", (0.12, 1.1, 0.12), (4.0, -2.9, 5.55), "steel", S)
box("lamp_head", (0.42, 0.62, 0.18), (4.0, -2.35, 5.44), "lamp", S)
cyl("hydrant_body", 0.16, 0.9, (-3.6, -3.0, 0.45), "rust", S)
cyl("hydrant_cap", 0.24, 0.14, (-3.6, -3.0, 0.94), "rust", S)
cyl("manhole", 0.42, 0.06, (1.2, -5.6, 0.03), "steel", S)

print("props objects:", len(scene.objects), "mats:", len(M))
