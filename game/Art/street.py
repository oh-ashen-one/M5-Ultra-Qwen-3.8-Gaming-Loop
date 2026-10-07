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
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (col[0], col[1], col[2], 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    img = IMGMAP.get(nm)
    if img and img in bpy.data.images:
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images[img]
        t.location = (-600, 200)
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.location = (-820, 200)
        nt.links.new(uv.outputs["UV"], t.inputs["Vector"])
        tint = TINTMAP.get(nm)
        out = t.outputs["Color"]
        if tint:
            mx = nt.nodes.new("ShaderNodeMixRGB")
            mx.blend_type = "MULTIPLY"
            mx.inputs["Fac"].default_value = 1.0
            mx.inputs["Color2"].default_value = (tint[0], tint[1], tint[2], 1.0)
            mx.location = (-380, 200)
            nt.links.new(t.outputs["Color"], mx.inputs["Color1"])
            out = mx.outputs["Color"]
        nt.links.new(out, b.inputs["Base Color"])
    return m


IMGMAP = {
    "brick": "t_brick", "darkbrick": "t_brick",
    "limestone": "t_stone", "concrete": "t_conc",
    "asphalt": "t_asph", "wood": "t_wood",
}
TINTMAP = {"darkbrick": (0.55, 0.50, 0.50)}
TEX = {
    "brick": (4.0, 1.0), "dkbrick": (4.0, 1.0),
    "stone": (2.0, 2.0), "concrete": (2.0, 2.0),
    "asphalt": (4.0, 4.0), "wood": (1.0, 0.5),
}


def _h(x, y, s):
    n = (x * 73856093) ^ (y * 19349663) ^ (s * 83492791)
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _vn(u, v, N, s):
    fx = u * N; fy = v * N; xi = int(fx); yi = int(fy)
    xf = fx - xi; yf = fy - yi
    x0 = xi % N; x1 = (xi + 1) % N; y0 = yi % N; y1 = (yi + 1) % N
    a = _h(x0, y0, s); b = _h(x1, y0, s); c = _h(x0, y1, s); d = _h(x1, y1, s)
    sx = xf * xf * (3 - 2 * xf); sy = yf * yf * (3 - 2 * yf)
    return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy


def _fb(u, v, N, s, o=2):
    val = 0.0; amp = 1.0; f = N; t = 0.0
    for i in range(o):
        val += amp * _vn(u, v, f, s + i * 17); t += amp; amp *= 0.5; f *= 2
    return val / t


def gen(nm, s, mode):
    N = 512
    if nm in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[nm])
    im = bpy.data.images.new(nm, N, N, alpha=False)
    im.colorspace_settings.name = "sRGB"
    px = [0.0] * (N * N * 4)
    for y in range(N):
        v = y / N; row = y * N
        for x in range(N):
            u = x / N
            if mode == "brick":
                bw = 0.0625; rh = 1 / 12.0; ri = int(v * 12)
                bx = (u - (ri % 2) * 0.5 * bw) % bw; by = v - ri * rh
                mo = bx < 0.013 or bx > bw - 0.013 or by < 0.006 or by > rh - 0.006
                if mo:
                    rr, gg, bb = 0.60, 0.58, 0.54
                else:
                    ti = _h(int(u * 16), ri, s + 3)
                    rr = 0.40 + 0.12 * ti; gg = 0.12 + 0.05 * ti; bb = 0.09 + 0.04 * ti
                    if ti < 0.35:
                        rr *= 0.72; gg *= 0.74; bb *= 0.78
                    n1 = _fb(u, v, 48, s + 5)
                    rr += (n1 - 0.5) * 0.06; gg += (n1 - 0.5) * 0.05; bb += (n1 - 0.5) * 0.04
            elif mode == "stone":
                m1 = _fb(u, v, 8, s + 1); st = _fb(u, v * 0.6, 5, s + 7)
                jr = (v * 6) % 1.0; j = 0.6 if (jr < 0.03 or jr > 0.97) else 1.0
                rr = (0.30 + 0.30 * m1 + 0.05 * st) * j
                gg = (0.28 + 0.30 * m1 + 0.05 * st) * j
                bb = (0.24 + 0.26 * m1 + 0.04 * st) * j
            elif mode == "concrete":
                g = _fb(u, v, 40, s + 2); bl = _fb(u, v, 5, s + 9)
                b0 = 0.33 + 0.10 * (g - 0.5) + 0.06 * (bl - 0.5)
                rr = gg = b0; bb = b0 * 0.98
            elif mode == "asphalt":
                g = _fb(u, v, 90, s + 4); p = _fb(u, v, 6, s + 11)
                b0 = 0.075 + 0.05 * (g - 0.5) + 0.03 * (p - 0.5)
                rr = gg = b0; bb = b0 * 1.06
            else:
                g = _fb(u * 9, v * 1.4, 6, s + 6); b0 = 0.16 + 0.12 * g
                rr = b0; gg = b0 * 0.6; bb = b0 * 0.4
            i = (row + x) * 4
            px[i] = max(0.0, min(1.0, rr)); px[i + 1] = max(0.0, min(1.0, gg))
            px[i + 2] = max(0.0, min(1.0, bb)); px[i + 3] = 1.0
    im.pixels.foreach_set(px)
    return im


gen("t_brick", 11, "brick")
gen("t_stone", 23, "stone")
gen("t_conc", 37, "concrete")
gen("t_asph", 53, "asphalt")
gen("t_wood", 71, "wood")

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
    md = ob.data
    us, vs = TEX.get(m, (1.0, 1.0))
    uv_layer = md.uv_layers.active
    if uv_layer is None:
        uv_layer = md.uv_layers.new(name='UVMap')
    for poly in md.polygons:
        n = poly.normal
        ax = 0
        if abs(n[1]) >= abs(n[0]) and abs(n[1]) >= abs(n[2]):
            ax = 1
        elif abs(n[0]) >= abs(n[2]):
            ax = 0
        else:
            ax = 2
        for li in poly.loop_indices:
            co = md.vertices[md.loops[li].vertex_index].co
            if ax == 1:
                u, v = co[0], co[2]
            elif ax == 0:
                u, v = co[1], co[2]
            else:
                u, v = co[0], co[1]
            uv_layer.data[li].uv = (u / us, v / vs)
    md.update()
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
        # mullion cross: sits proud of the frame so it throws shadow on the glass
        box(t + "_mullV", (0.10, 0.07, 1.74), (x, -0.19, z), "trim")
        box(t + "_mullH", (0.96, 0.07, 0.10), (x, -0.19, z), "trim")

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

# ---- facade relief: projecting piers divide the wall into repeated bays and
#      throw vertical cast shadows; a segmented planter strip anchors the base.
#      All sit within the near-wall sidewalk strip so the route is unobstructed.
for pi, px in enumerate((-6.0, 0.0, 6.0)):
    box("pier%02d" % pi, (0.60, 0.34, H - 0.70), (px, -0.15, (H - 0.70) / 2 + 0.10), "brick")
    box("pier%02d_cap" % pi, (0.74, 0.46, 0.18), (px, -0.20, H - 0.62), "stone")
for pxi, px in enumerate((-5.0, 0.0, 5.0)):
    w = 3.40 if pxi == 1 else 1.70
    box("planter%02d_curb" % pxi, (w, 0.55, 0.46), (px, -0.42, 0.23), "stone")
    box("planter%02d_soil" % pxi, (w - 0.22, 0.40, 0.10), (px, -0.42, 0.46), "wood")

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

# ---- (alley party-wall / gate section REMOVED) ---------------------------
# The alley_slab / alley_wallW,E / copings / gate mesh were present in this
# source but absent from the accepted 102a2095 FBX. Re-export exposed them:
# their first world centers (-3.10, 2.80, 12.85 / 14.95, sizes 11.60x5.60x0.30)
# run ACROSS the accepted route lane and stopped the car at Z~10.55. They are
# removed outright so the accepted X-1..6, Z-2..30 route stays physically open.
# No colliders disabled, no anchors moved, no targeting widened.

# ---- south END-FACE relief (Blender X = -6 plane -> world z ~= 1) ---------
# This is the large blank red gable wall seen at the LEFT of the route (NOT the
# already-windowed front, whose mullions/pier trims did not read in-frame).
# Repeated recessed window bays, projecting brick pilasters, a stone base band
# and a cornice cap divide the slab with strong cast-shadow relief. Everything
# protrudes toward -BlenderX (world z < 1) and spans world x <= -1.2, so the
# playable pavement / route (x -1..6) is never obstructed; original facade_wall
# and facade_base geometry is left intact.
EF = -6.0
box("ef_base", (0.30, D, 1.05), (EF - 0.12, D / 2, 0.52), "stone")
box("ef_cornice_bed", (0.34, D, 0.24), (EF - 0.15, D / 2, H - 0.50), "stone")
box("ef_cornice", (0.52, D, 0.40), (EF - 0.24, D / 2, H - 0.18), "stone")
for pi, py in enumerate((0.40, 2.30, 4.10, 5.90, D - 0.40)):
    box("ef_pil%d" % pi, (0.24, 0.50, H - 1.30), (EF - 0.10, py, (H - 1.30) / 2 + 1.05), "brick")
    box("ef_pil%d_cap" % pi, (0.34, 0.66, 0.16), (EF - 0.15, py, H - 0.70), "stone")
# mid-height stone belt course reads as a horizontal datum at visible height
box("ef_belt", (0.30, D, 0.26), (EF - 0.14, D / 2, 4.20), "stone")
# full-depth repeated bay rhythm: four window bays stacked over two floors
for ei, ey in enumerate((1.35, 3.20, 4.95, 6.75)):
    for ri, ez in enumerate((2.85, 5.55)):
        t = "ef_win%d_%d" % (ri, ei)
        box(t + "_frame", (0.16, 1.05, 1.55), (EF - 0.07, ey, ez), "trim")
        box(t + "_glass", (0.08, 0.78, 1.30), (EF - 0.11, ey, ez), "glass")
        box(t + "_sill",   (0.36, 1.26, 0.14), (EF - 0.17, ey, ez - 0.86), "stone")
        box(t + "_lintel", (0.26, 1.16, 0.24), (EF - 0.12, ey, ez + 0.92), "stone")
        box(t + "_mullV",  (0.07, 0.09, 1.30), (EF - 0.14, ey, ez), "trim")

M["leaf"] = mat("foliage", (0.13, 0.17, 0.07), 0.9)
IMGMAP["foliage"] = ""

for k, dx in enumerate((-5.4, 5.4)):
    box("surf_pipe%02d" % k, (0.12, 0.12, 8.2), (dx, -0.16, 4.0), "steel")
    box("surf_elbow%02d" % k, (0.12, 0.40, 0.12), (dx, -0.30, 8.1), "steel")
    box("surf_drain%02d" % k, (0.22, 0.30, 0.10), (dx, -0.30, 0.12), "steel")

for k, dx in enumerate((-2.2, 2.2)):
    box("surf_meter%02d" % k, (0.34, 0.16, 0.50), (dx, -0.16, 1.50), "steel")

for k, dx in enumerate((-3.0, 3.0)):
    box("surf_vent%02d" % k, (0.50, 0.28, 0.34), (dx, -0.16, 7.40), "steel")

for k, dx in enumerate((-4.5, -1.5)):
    for kk, zz in enumerate((4.55, 6.75)):
        box("surf_shutL%d_%d" % (k, kk), (0.16, 0.06, 1.90), (dx - 0.78, -0.16, zz), "wood")
        box("surf_shutR%d_%d" % (k, kk), (0.16, 0.06, 1.90), (dx + 0.78, -0.16, zz), "wood")

for k, (px, pz) in enumerate(((-5.0, 0.62), (0.0, 0.62), (5.0, 0.62))):
    bpy.ops.mesh.primitive_icosphere_add(subdivisions=1, radius=0.28, location=(px, -0.42, pz))
    bo = bpy.context.active_object
    bo.name = "surf_bush%02d" % k
    bo.scale = (1.4, 1.0, 0.9)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bo.data.materials.clear()
    bo.data.materials.append(M["leaf"])
    bo.parent = root

print("street module objects:", len(scene.objects), "mats:", len(M))
