# ORIGINAL clothed courier - first art increment (Blender 5.2)
# World: meters, +Z up, +Y forward. player_root at Z=0.79; foot soles at Z=0
# (soles sit 0.79 under root; Unity subtracts 0.79 from instantiated localY).
# Pivot bend axes: POSITIVE rotation about local +X swings limb forward(+Y).
# Shoulder/elbow/hip/knee are empties; mesh parts overlap pivots so bends
# stay covered by cloth. Parenting done exactly once via matrix_parent_inverse.
import bpy, bmesh
from mathutils import Vector
SC = bpy.context
CO = SC.collection
for ob in list(SC.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes): bpy.data.meshes.remove(me)
for cl in [c for c in bpy.data.collections if c != CO]: bpy.data.collections.remove(cl)

def MAT(n, c, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(n); m.use_nodes = True
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
    me = bpy.data.meshes.new(n); bm.to_mesh(me); bm.free()
    me.materials.append(m)
    o = bpy.data.objects.new(n, me); CO.objects.link(o); return o
def BALL(n, c, r, m, s=None, seg=12):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg,
        v_segments=max(6, seg // 2), radius=r)
    if s: bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    o = OBJ(n, bm, m); o.location = c; return o
def BOX(n, c, sz, m, s=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(sz), verts=bm.verts)
    if s: bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    o = OBJ(n, bm, m); o.location = c; return o
def TUBE(n, a, b, r0, r1, m, sx=1.0, sy=1.0, seg=12):
    a, b = Vector(a), Vector(b); d = b - a
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True,
        cap_tris=False, segments=seg, radius1=r0, radius2=r1, depth=d.length)
    if sx != 1.0 or sy != 1.0: bmesh.ops.scale(bm, vec=(sx, sy, 1), verts=bm.verts)
    o = OBJ(n, bm, m); o.location = (a + b) / 2
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return o
def CAPS(n, a, b, r, m):
    o = TUBE(n, a, b, r, r, m); BALL(n + "_a", a, r, m); BALL(n + "_b", b, r, m)
def EMP(n, loc, size=0.07):
    e = bpy.data.objects.new(n, None); e.empty_display_type = "SPHERE"
    e.empty_display_size = size; e.location = loc; CO.objects.link(e); return e
def PAR(o, p):
    o.parent = p; o.matrix_parent_inverse = p.matrix_world.inverted()

# ---- hierarchy: root -> shoulders -> elbows, hips -> knees, head ---------
root = EMP("player_root", (0, 0, 0.79), 0.12)
sh = {}; el = {}; hip = {}; kn = {}
for sgn, s in (("l", 1), ("r", -1)):
    sh[s] = EMP(f"pivot_shoulder_{s}", (0.195 * s, 0, 1.47))   # +X rot: arm fwd / +Y
    el[s] = EMP(f"pivot_elbow_{s}",   (0.215 * s, 0, 1.17))
    hip[s]= EMP(f"pivot_hip_{s}",     (0.095 * s, 0, 0.95))   # +X rot: thigh fwd
    kn[s] = EMP(f"pivot_knee_{s}",    (0.095 * s, 0, 0.50))   # -X rot: shin back
head = EMP("pivot_head", (0, 0, 1.52))                          # +X rot: nod fwd
SC.view_layer.update()
for s in ("l", "r"):
    PAR(sh[s], root); PAR(el[s], sh[s]); PAR(hip[s], root); PAR(kn[s], hip[s])
PAR(head, root)

# ---- torso: continuous jacket (collar+cuffs+hem trim), overlapped joints --
parts = {}
def add(o, key): parts.setdefault(key, []).append(o)
add(TUBE("jkt_torso", (0,0,0.97), (0,0,1.50), 0.165, 0.185, M_JKT, 1.15, 0.72), "root")
add(TUBE("jkt_collar",(0,0.005,1.48),(0,0.015,1.575),0.095,0.070,M_TRIM,1.1,0.9),"root")
add(TUBE("jkt_hem",  (0,0,0.945),(0,0,1.01),0.185,0.172,M_TRIM,1.18,0.75), "root")
add(TUBE("pant_pelvis",(0,0,0.86),(0,0,1.00),0.165,0.18,M_JEANS,1.15,0.72), "root")
add(TUBE("belt_waist", (0,0,0.975),(0,0,1.015),0.185,0.178,M_TRIM,1.2,0.78), "root")
add(TUBE("neck", (0,0,1.47),(0,0,1.60), 0.062, 0.058, M_SKIN), "head")
add(BALL("head", (0,0,1.69), 0.105, M_SKIN, (0.95, 1.08, 1.15)), "head")
add(BOX("nose", (0, 0.108, 1.665), (0.032, 0.03, 0.034), M_SKIN), "head")
add(BALL("hair_top", (0, -0.01, 1.722), 0.113, M_HAIR, (1.0, 1.05, 0.92)), "head")
add(BOX("hair_back", (0, -0.075, 1.64), (0.17, 0.06, 0.13), M_HAIR), "head")

for sgn, s in (("l", 1), ("r", -1)):
    sA = (0.195 * s, 0, 1.47); sE = (0.215 * s, 0, 1.17); sW = (0.232 * s, 0, 0.93)
    add(BALL(f"jkt_delt_{sgn}", sA, 0.105, M_JKT, (1.05, 1.0, 0.95)), sgn + "sh")
    add(TUBE(f"jkt_sleeve_{sgn}", sA, sE, 0.086, 0.080, M_JKT), sgn + "sh")
    add(BALL(f"jkt_delt_cap_{sgn}", sE, 0.080, M_JKT), sgn + "sh")
    add(TUBE(f"jkt_fore_{sgn}", sE, sW, 0.073, 0.066, M_JKT), sgn + "el")
    add(BALL(f"jkt_cuff_{sgn}", (0.230*s, 0, 0.905), 0.070, M_TRIM), sgn + "el")
    add(BALL(f"hand_{sgn}_w", sW, 0.058, M_SKIN), sgn + "el")
    add(BOX(f"hand_{sgn}", (0.234*s, 0.012, 0.852), (0.058, 0.10, 0.115), M_SKIN), sgn + "el")
    add(BOX(f"thumb_{sgn}", (0.205*s, 0.058, 0.882), (0.028, 0.055, 0.032), M_SKIN), sgn + "el")
    hA = (0.095*s, 0, 0.95); hK = (0.095*s, 0, 0.50); hAn = (0.100*s, 0, 0.11)
    add(BALL(f"pant_hip_{sgn}", hA, 0.116, M_JEANS), sgn + "hip")
    add(TUBE(f"pant_thigh_{sgn}", hA, hK, 0.102, 0.092, M_JEANS), sgn + "hip")
    add(BALL(f"pant_knee_{sgn}", hK, 0.09, M_JEANS), sgn + "knee")
    add(TUBE(f"pant_shin_{sgn}", hK, hAn, 0.084, 0.07, M_JEANS), sgn + "knee")
    add(BALL(f"pant_ankle_{sgn}", hAn, 0.072, M_JEANS), sgn + "knee")
    add(BOX(f"shoe_{sgn}", (0.10*s, 0.05, 0.046), (0.115, 0.30, 0.09), M_SHOE), sgn + "knee")
    add(BOX(f"toe_{sgn}", (0.10*s, 0.205, 0.040), (0.108, 0.10, 0.078), M_SHOE), sgn + "knee")

# right-hand original pistol (follows forearm for later aim articulation)
add(BOX("pistol_slide", (0.234, 0.10, 0.845), (0.032, 0.21, 0.05), M_PIST), "rel")
add(BOX("pistol_grip",  (0.232, -0.025, 0.76), (0.028, 0.055, 0.115), M_PIST), "rel")

# ---- parent every mesh part exactly once, preserving world position ------
keys = {"root": root, "head": head,
        "lsh": sh["l"], "lel": el["l"], "rsh": sh["r"], "rel": el["r"],
        "lhip": hip["l"], "lknee": kn["l"], "rhip": hip["r"], "rknee": kn["r"]}
for key, objs in parts.items():
    for o in objs: PAR(o, keys[key])
SC.view_layer.update()
print("courier v1 built:", len(SC.data.objects), "objects")
