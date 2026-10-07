# ORIGINAL clothed courier - first art increment (Blender 5.2)
# World: meters, +Z up, +Y forward. Build with presentation root at Z=0;
# local foot soles sit at Z=0. Parent once, then lift player_root to Z=0.79.
# Evaluated world soles are near +0.79 and crown near 2.6m. Unity unchanged.
# Pivot bend axes: POSITIVE rotation about local +X swings limb forward(+Y).
# Shoulder/elbow/hip/knee are empties; mesh parts overlap pivots so bends
# stay covered by cloth. Parenting done exactly once via matrix_parent_inverse.
import bpy, bmesh
from mathutils import Vector

SC = bpy.context
CO = SC.collection

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for cl in [c for c in bpy.data.collections if c != CO]:
    bpy.data.collections.remove(cl)

def MAT(n, c, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*c, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

M_SKIN = MAT("Skin_Warm", (0.42, 0.27, 0.19), 0.55)
M_JKT  = MAT("Jacket_Charcoal", (0.065, 0.065, 0.075), 0.85)
M_TRIM = MAT("Trim_JacketDark", (0.028, 0.028, 0.034), 0.7)
M_JEANS= MAT("Jeans_DarkBlue", (0.055, 0.075, 0.135), 0.9)
M_SHOE = MAT("Shoe_Black", (0.025, 0.025, 0.03), 0.5)
M_HAIR = MAT("Hair_Black", (0.02, 0.016, 0.013), 0.5)
M_PIST = MAT("Pistol_Steel", (0.085, 0.085, 0.1), 0.35, 0.8)

def OBJ(n, bm, m):
    me = bpy.data.meshes.new(n)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(n, me)
    CO.objects.link(o)
    return o

def BALL(n, c, r, m, s=None, seg=12):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg,
        v_segments=max(6, seg // 2), radius=r)
    if s:
        bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    o = OBJ(n, bm, m)
    o.location = c
    return o

def BOX(n, c, sz, m, s=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(sz), verts=bm.verts)
    if s:
        bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    o = OBJ(n, bm, m)
    o.location = c
    return o

def TUBE(n, a, b, r0, r1, m, sx=1.0, sy=1.0, seg=12):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
        segments=seg, radius1=r0, radius2=r1, depth=d.length)
    if sx != 1.0 or sy != 1.0:
        bmesh.ops.scale(bm, vec=Vector((sx, sy, 1.0)), verts=bm.verts)
    o = OBJ(n, bm, m)
    o.location = (a + b) / 2
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return o

def CAPS(n, a, b, r, m):
    o = TUBE(n, a, b, r, r, m)
    BALL(n + "_a", a, r, m)
    BALL(n + "_b", b, r, m)
    return o

def EMP(n, loc, size=0.07):
    e = bpy.data.objects.new(n, None)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = size
    e.location = loc
    CO.objects.link(e)
    return e

def PAR(o, p):
    o.parent = p
    o.matrix_parent_inverse = p.matrix_world.inverted()

root = EMP("player_root", (0.0, 0.0, 0.0), 0.12)
sh = {}
el = {}
hip = {}
kn = {}

for key, side in (("l", 1), ("r", -1)):
    sh[key]  = EMP(f"pivot_shoulder_{key}", (0.195 * side, 0.0, 1.47))
    el[key]  = EMP(f"pivot_elbow_{key}",    (0.215 * side, 0.0, 1.17))
    hip[key] = EMP(f"pivot_hip_{key}",      (0.095 * side, 0.0, 0.95))
    kn[key]  = EMP(f"pivot_knee_{key}",     (0.095 * side, 0.0, 0.50))

head = EMP("pivot_head", (0.0, 0.0, 1.52))

SC.view_layer.update()

for key in ("l", "r"):
    PAR(sh[key], root)
    PAR(hip[key], root)
PAR(head, root)

SC.view_layer.update()

for key in ("l", "r"):
    PAR(el[key], sh[key])
    PAR(kn[key], hip[key])

SC.view_layer.update()

parts = {}
def add(o, key):
    parts.setdefault(key, []).append(o)

add(TUBE("jkt_torso", (0,0,0.97), (0,0,1.50), 0.165, 0.185, M_JKT, 1.15, 0.72), "root")
add(TUBE("jkt_collar",(0,0.005,1.48),(0,0.015,1.575),0.095,0.070,M_TRIM,1.1,0.9), "root")
add(TUBE("jkt_hem",  (0,0,0.945),(0,0,1.01),0.185,0.172,M_TRIM,1.18,0.75), "root")
add(TUBE("pant_pelvis",(0,0,0.86),(0,0,1.00),0.165,0.18,M_JEANS,1.15,0.72), "root")
add(TUBE("belt_waist", (0,0,0.975),(0,0,1.015),0.185,0.178,M_TRIM,1.2,0.78), "root")
add(TUBE("neck", (0,0,1.47),(0,0,1.60), 0.062, 0.058, M_SKIN), "head")
add(BALL("head", (0,0,1.69), 0.105, M_SKIN, (0.95, 1.08, 1.15)), "head")
add(BOX("nose", (0, 0.108, 1.665), (0.032, 0.03, 0.034), M_SKIN), "head")
add(BALL("hair_top", (0, -0.01, 1.722), 0.113, M_HAIR, (1.0, 1.05, 0.92)), "head")
add(BOX("hair_back", (0, -0.075, 1.64), (0.17, 0.06, 0.13), M_HAIR), "head")

for key, side in (("l", 1), ("r", -1)):
    sA = (0.195 * side, 0.0, 1.47)
    sE = (0.215 * side, 0.0, 1.17)
    sW = (0.232 * side, 0.0, 0.93)
    add(BALL(f"jkt_delt_{key}", sA, 0.105, M_JKT, (1.05, 1.0, 0.95)), key + "sh")
    add(TUBE(f"jkt_sleeve_{key}", sA, sE, 0.086, 0.080, M_JKT), key + "sh")
    add(BALL(f"jkt_delt_cap_{key}", sE, 0.080, M_JKT), key + "sh")
    add(TUBE(f"jkt_fore_{key}", sE, sW, 0.073, 0.066, M_JKT), key + "el")
    add(BALL(f"jkt_cuff_{key}", (0.230 * side, 0.0, 0.905), 0.070, M_TRIM), key + "el")
    add(BALL(f"hand_{key}_w", sW, 0.058, M_SKIN), key + "el")
    add(BOX(f"hand_{key}", (0.234 * side, 0.012, 0.852), (0.058, 0.10, 0.115), M_SKIN), key + "el")
    add(BOX(f"thumb_{key}", (0.205 * side, 0.058, 0.882), (0.028, 0.055, 0.032), M_SKIN), key + "el")
    hA = (0.095 * side, 0.0, 0.95)
    hK = (0.095 * side, 0.0, 0.50)
    hAn = (0.100 * side, 0.0, 0.11)
    add(BALL(f"pant_hip_{key}", hA, 0.116, M_JEANS), key + "hip")
    add(TUBE(f"pant_thigh_{key}", hA, hK, 0.102, 0.092, M_JEANS), key + "hip")
    add(BALL(f"pant_knee_{key}", hK, 0.09, M_JEANS), key + "knee")
    add(TUBE(f"pant_shin_{key}", hK, hAn, 0.084, 0.07, M_JEANS), key + "knee")
    add(BALL(f"pant_ankle_{key}", hAn, 0.072, M_JEANS), key + "knee")
    add(BOX(f"shoe_{key}", (0.10 * side, 0.05, 0.046), (0.115, 0.30, 0.09), M_SHOE), key + "knee")
    add(BOX(f"toe_{key}", (0.10 * side, 0.205, 0.040), (0.108, 0.10, 0.078), M_SHOE), key + "knee")

# Right-hand pistol mirrors the right forearm (-X) and is carried by rel.
add(BOX("pistol_slide", (-0.234, 0.10, 0.845), (0.032, 0.21, 0.05), M_PIST), "rel")
add(BOX("pistol_grip",  (-0.232, -0.025, 0.76), (0.028, 0.055, 0.115), M_PIST), "rel")

SC.view_layer.update()

keys = {
    "root": root,
    "head": head,
    "lsh": sh["l"], "lel": el["l"],
    "rsh": sh["r"], "rel": el["r"],
    "lhip": hip["l"], "lknee": kn["l"],
    "rhip": hip["r"], "rknee": kn["r"]
}

for key, objs in parts.items():
    for o in objs:
        PAR(o, keys[key])

SC.view_layer.update()

# Presentation lift only: evaluated mesh soles become near +0.79.
root.location = (0.0, 0.0, 0.79)
SC.view_layer.update()

print("courier v1 built:", len(bpy.data.objects), "objects")
