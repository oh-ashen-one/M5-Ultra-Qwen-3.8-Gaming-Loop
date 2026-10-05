"""Original Chicago two-flat / greystone street facade module (art source).

Author: local Qwen builder. All geometry authored here with bpy, no imports.
Pivot: street_root at (0,0,0) = front face of building at sidewalk grade.
Convention: facade front plane at y=0, building body extends to +y, street at -y.
Module width 12 m (one two-flat lot), depth 8 m, height 8.8 m (2 floors + cornice).
"""
import bpy

NAME = "street"
scene = bpy.context.scene
scene.name = NAME
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


def mat(nm, col, rough=0.85, metal=0.0):
    m = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M = {
    "brick":    mat("brick", (0.300, 0.110, 0.085)),
    "dkbrick":  mat("darkbrick", (0.180, 0.092, 0.072)),
    "stone":    mat("limestone", (0.540, 0.520, 0.465)),
    "trim":     mat("window_trim", (0.080, 0.090, 0.100)),
    "glass":    mat("window_glass", (0.035, 0.055, 0.080), 0.15),
    "steel":    mat("steel", (0.260, 0.270, 0.290), 0.45, 1.0),
    "concrete": mat("concrete", (0.355, 0.350, 0.345)),
    "wood":     mat("wood", (0.200, 0.115, 0.070)),
}

root = bpy.data.objects.new("street_root", None)
scene.collection.objects.link(root)
W, D, H = 12.0, 8.0, 8.8


def box(nm, dims, loc, m, rx=0.0, rz=0.0, parent=root):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=(rx, 0.0, rz))
    ob = bpy.context.active_object
    ob.name = nm
    ob.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.clear()
    ob.data.materials.append(M[m])
    ob.parent = parent
    return ob


box("facade_wall", (W, D, H), (0, D / 2, H / 2), "brick")
box("facade_base", (W + 0.10, 0.32, 1.05), (0, -0.06, 0.52), "stone")
box("facade_belt", (W + 0.06, 0.22, 0.30), (0, -0.09, 3.30), "stone")
box("cornice_bed", (W + 0.20, 0.34, 0.26), (0, -0.14, H - 0.22), "stone")
box("cornice", (W + 0.60, 0.62, 0.44), (0, -0.28, H + 0.10), "stone")
box("roof_slab", (W - 0.30, D - 0.30, 0.22), (0, D / 2, H - 0.02), "concrete")
box("chimney", (0.90, 0.90, 1.80), (3.60, 5.60, H + 0.70), "dkbrick")
for i in range(19):
    box("dentil%02d" % i, (0.30, 0.34, 0.20), (-W / 2 + 0.35 + i * 0.65, -0.16, H - 0.42), "stone")

BAYS = (-4.5, -1.5, 1.5, 4.5)
for r, z in enumerate((2.10, 4.55, 6.75)):
    for i, x in enumerate(BAYS):
        t = "win%d_%d" % (r, i)
        box(t + "_frame", (1.28, 0.18, 2.05), (x, -0.07, z), "trim")
        box(t + "_glass", (1.00, 0.08, 1.78), (x, -0.12, z), "glass")
        box(t + "_sill", (1.56, 0.38, 0.14), (x, -0.17, z - 1.08), "stone")
        box(t + "_lintel", (1.50, 0.24, 0.26), (x, -0.10, z + 1.16), "stone")

for j, x in enumerate((-3.0, 3.0)):
    box("door%02d_surround" % j, (1.46, 0.22, 2.58), (x, -0.09, 1.29), "stone")
    box("door%02d_panel" % j, (1.06, 0.10, 2.10), (x, -0.16, 1.06), "wood")
    box("door%02d_transom" % j, (1.06, 0.08, 0.40), (x, -0.16, 2.42), "glass")
    for i in range(3):
        h = 0.17 * (i + 1)
        box("stoop%02d_step%d" % (j, i), (1.90, 0.38, h), (x, -0.90 + 0.38 * i, h / 2), "stone")
    box("stoop%02d_cheekL" % j, (0.26, 1.15, 0.95), (x - 1.00, -0.60, 0.48), "stone")
    box("stoop%02d_cheekR" % j, (0.26, 1.15, 0.95), (x + 1.00, -0.60, 0.48), "stone")
    box("stoop%02d_postL" % j, (0.08, 0.08, 1.00), (x - 1.00, -1.10, 1.00), "steel")
    box("stoop%02d_postR" % j, (0.08, 0.08, 1.00), (x + 1.00, -1.10, 1.00), "steel")

for bi, x in enumerate((-4.5, -1.5)):
    for k, z in enumerate((3.70, 6.00)):
        p = "fireesc%d_%d" % (bi, k)
        box(p + "_plat", (1.60, 1.05, 0.09), (x, 0.52, z), "steel")
        box(p + "_railtop", (1.60, 0.07, 0.07), (x, 0.98, z + 0.95), "steel")
        for s in range(5):
            box(p + "_bal%d" % s, (0.05, 0.05, 0.90), (x - 0.72 + s * 0.36, 0.98, z + 0.50), "steel")
        box(p + "_bracket", (0.10, 1.00, 0.10), (x, 0.50, z - 0.34), "steel", rx=0.35)
        box(p + "_ladder", (0.50, 0.07, 1.90), (x, 0.58, z - 0.95), "steel", rx=0.45)

box("sidewalk", (W + 2.0, 3.20, 0.14), (0, -1.70, 0.07), "concrete")
box("curb", (W + 2.0, 0.22, 0.18), (0, -3.32, 0.09), "concrete")

M["asphalt"] = mat("asphalt", (0.085, 0.085, 0.090), 0.95)
M["paint"] = mat("road paint", (0.620, 0.520, 0.110), 0.70)
M["grate"] = mat("storm grate", (0.230, 0.235, 0.240), 0.60, 1.0)
M["chain"] = mat("chain link", (0.420, 0.430, 0.440), 0.50, 1.0)

# ---- drivable street surface, painted centre line, storm grate -----------
box("road_asphalt", (W + 2.0, 11.00, 0.12), (0, -9.05, -0.01), "asphalt")
for i in range(6):
    box("road_dash%02d" % i, (2.40, 0.16, 0.03), (-5.5 + i * 2.2, -9.0, 0.06), "paint")
box("storm_grate", (0.92, 0.70, 0.05), (4.40, -3.80, 0.055), "grate")
for i in range(6):
    box("grate_bar%02d" % i, (0.82, 0.05, 0.06), (4.40, -4.10 + i * 0.12, 0.080), "grate")

# ---- alley mouth: paved gap between lots, brick party walls, closed gate --
box("alley_slab", (1.80, 11.60, 0.12), (6.90, 2.20, -0.01), "asphalt")
box("alley_wallW", (0.30, 11.60, 5.60), (5.85, 2.20, 2.80), "dkbrick")
box("alley_wallE", (0.30, 11.60, 5.60), (7.95, 2.20, 2.80), "dkbrick")
box("alley_copingW", (0.44, 11.60, 0.16), (5.85, 2.20, 5.68), "stone")
box("alley_copingE", (0.44, 11.60, 0.16), (7.95, 2.20, 5.68), "stone")

gate = bpy.data.objects.new("alley_gate", None)
scene.collection.objects.link(gate)
gate.parent = root
box("gate_post_L", (0.13, 0.13, 2.30), (5.98, -1.60, 1.15), "steel", parent=gate)
box("gate_post_R", (0.13, 0.13, 2.30), (7.82, -1.60, 1.15), "steel", parent=gate)
box("gate_rail_top", (2.00, 0.10, 0.10), (6.90, -1.60, 2.22), "steel", parent=gate)
box("gate_rail_bot", (2.00, 0.09, 0.09), (6.90, -1.60, 0.22), "steel", parent=gate)
for i in range(13):
    box("gate_wireV%02d" % i, (0.045, 0.045, 2.00), (6.05 + i * 0.142, -1.60, 1.22), "chain", parent=gate)
for i in range(7):
    for k in (-1, 1):
        box("gate_wireD%02d_%d" % (i, k), (0.05, 0.05, 0.60),
            (6.12 + i * 0.26, -1.60, 1.22), "chain", parent=gate, rz=0.785398 * k)

print("street module objects:", len(scene.objects), "mats:", len(M))
