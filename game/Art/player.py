# ORIGINAL clothed courier - art increment 2 (Blender 5.2) local repair
# World: meters, +Z up. Visual built facing +Y with feet at Z=0; presentation
# root lifted to Z=0.79 and statically pre-rotated +pi Z for Unity facing.
# Repairs kept bounded: missing play() helper added; sleeve/forearm/thigh/shin
# lofts are moved to their actual side before world-preserving parenting;
# FX=-1 is repaired to FX=+1 because the root Z half-turn changes world facing,
# not the local Euler semantics. Spine/head are up-Z, so saved forward-intent
# X values are negated to bend toward local +Y. Clip endpoints/gaps are pinned.
import bpy, bmesh, math
from mathutils import Vector

SC = bpy.context
CO = SC.collection
FX = 1.0
UP_Z = {"spine", "head"}

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for ac in list(bpy.data.actions):
    bpy.data.actions.remove(ac, do_unlink=True)
for cl in [c for c in bpy.data.collections if c != CO]:
    bpy.data.collections.remove(cl)

SC.scene.frame_start = 1
SC.scene.frame_end = 279
SC.scene.render.fps = 30

def MAT(n, c, rough=0.8, metal=0.0):
    m = bpy.data.materials.new(n); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*c, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

M_SKIN = MAT("Skin_Warm", (0.42, 0.27, 0.19), 0.55)
M_JKT  = MAT("Jacket_Charcoal", (0.065, 0.065, 0.075), 0.85)
M_TRIM = MAT("Trim_JacketDark", (0.028, 0.028, 0.034), 0.70)
M_JEANS= MAT("Jeans_DarkBlue", (0.055, 0.075, 0.135), 0.90)
M_SHOE = MAT("Shoe_Black", (0.025, 0.025, 0.03), 0.50)
M_HAIR = MAT("Hair_Black", (0.02, 0.016, 0.013), 0.50)
M_PIST = MAT("Pistol_Steel", (0.085, 0.085, 0.10), 0.35, 0.80)
M_EYE  = MAT("Eye_Dark", (0.015, 0.015, 0.02), 0.4)

def shade_bevel(o, w=0.006, ang=0.70):
    for p in o.data.polygons: p.use_smooth = True
    m = o.modifiers.new("bev", "BEVEL")
    m.width = w; m.segments = 2; m.limit_method = "ANGLE"
    m.angle_limit = ang; m.use_clamp_overlap = True; m.miter_outer = "MITER_ARC"
    try: m.harden_normals = True
    except Exception: pass
    return o

def OBJ(n, bm, mat):
    me = bpy.data.meshes.new(n); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(n, me); CO.objects.link(o); return o

def superring(xh, yh, n, seg, yb):
    out = []
    for i in range(seg):
        th = 2*math.pi*i/seg; c = abs(math.cos(th)); s = abs(math.sin(th))
        yv = yh if math.sin(th) >= 0 else yh*yb
        r = ((c/xh)**n + (s/yv)**n) ** (-1.0/n)
        out.append((math.cos(th)*r, math.sin(th)*r))
    return out

def LOFT(n, levels, mat, capT=True, capB=True, seg=22, w=0.006):
    bm = bmesh.new(); rings = []
    for z, xh, yh, q, yb, xs, ys in levels:
        pts = superring(xh, yh, q, seg, yb)
        rings.append([bm.verts.new((x+xs, y+ys, z)) for (x, y) in pts])
    for i in range(len(rings)-1):
        a, b = rings[i], rings[i+1]; k = len(a)
        for j in range(k):
            bm.faces.new((a[j], a[(j+1)%k], b[(j+1)%k], b[j]))
    if capB: bm.faces.new(list(reversed(rings[0])))
    if capT: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return shade_bevel(OBJ(n, bm, mat), w)

def BOX(n, c, sz, mat, w=0.008):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(sz), verts=bm.verts)
    o = OBJ(n, bm, mat); o.location = c; return shade_bevel(o, w)

def SPH(n, c, r, mat, s=None, seg=22):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg//2), radius=r)
    if s: bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    o = OBJ(n, bm, mat); o.location = c; return shade_bevel(o, 0.001)

def EMP(n, loc, size=0.07):
    e = bpy.data.objects.new(n, None)
    e.empty_display_type = "SPHERE"; e.empty_display_size = size
    e.location = loc; CO.objects.link(e); return e

def PAR(o, p):
    o.parent = p; o.matrix_parent_inverse = p.matrix_world.inverted()

root = EMP("player_root", (0, 0, 0), 0.12)
spine = EMP("pivot_spine", (0, 0, 1.0), 0.08)
head = EMP("pivot_head", (0, 0, 1.52))
sh, el, hip, kn = {}, {}, {}, {}
for key, s in (("l", 1), ("r", -1)):
    sh[key]  = EMP(f"pivot_shoulder_{key}", (0.185*s, 0, 1.47))
    el[key]  = EMP(f"pivot_elbow_{key}",    (0.205*s, 0, 1.18))
    hip[key] = EMP(f"pivot_hip_{key}",      (0.095*s, 0, 0.95))
    kn[key]  = EMP(f"pivot_knee_{key}",     (0.100*s, 0, 0.50))
SC.view_layer.update()
for key in ("l", "r"):
    PAR(hip[key], root)
PAR(spine, root)
SC.view_layer.update()
for key in ("l", "r"):
    PAR(sh[key], spine)
PAR(head, spine)
SC.view_layer.update()
for key in ("l", "r"):
    PAR(el[key], sh[key])
    PAR(kn[key], hip[key])
SC.view_layer.update()

def L(z, xh, yh, q=2.4, yb=1.0, ys=0.0, xs=0.0):
    return (z, xh, yh, q, yb, xs, ys)

def LS(z, xh, yh, xs, q=2.4, yb=1.0, ys=0.0):
    return (z, xh, yh, q, yb, xs, ys)

parts = {}
def add(o, key): parts.setdefault(key, []).append(o)

# lofted torso / jacket body (soft-square superellipse, flattened back)
add(LOFT("jkt_torso", [L(1.00,0.148,0.118,2.3,0.92,-0.004), L(1.12,0.158,0.126,2.4,0.86,-0.010),
     L(1.26,0.168,0.132,2.5,0.82,-0.014), L(1.37,0.166,0.128,2.7,0.80,-0.014),
     L(1.46,0.150,0.116,3.2,0.82,-0.012)], M_JKT, False, False), "spine")
add(LOFT("jkt_hem", [L(0.93,0.168,0.132,2.4,0.82,-0.012), L(0.965,0.176,0.140,2.2,0.80,-0.010),
     L(1.00,0.170,0.134,2.4,0.86,-0.010)], M_TRIM, True, True), "spine")
add(LOFT("jkt_collar", [L(1.445,0.076,0.080,2.6,1.0,0.006), L(1.52,0.082,0.086,2.6,1.0,0.012),
     L(1.565,0.060,0.070,3.0,1.06,0.014)], M_TRIM), "spine")
add(BOX("jkt_placket", (0, 0.128, 1.21), (0.014, 0.022, 0.42), M_TRIM), "spine")
for s in (1, -1):
    add(BOX(f"jkt_pocket_{'l' if s>0 else 'r'}", (0.085*s, 0.126, 1.075), (0.055, 0.020, 0.10), M_TRIM), "spine")
add(LOFT("pants_pelvis", [L(0.84,0.150,0.118,2.4,0.86,-0.006), L(0.95,0.156,0.124,2.5,0.84,-0.010),
     L(1.00,0.152,0.120,2.6,0.82,-0.012)], M_JEANS), "root")
add(LOFT("belt_waist", [L(0.982,0.158,0.126,2.5,0.82,-0.010), L(1.016,0.160,0.128,2.5,0.82,-0.010)], M_TRIM), "root")
add(LOFT("neck", [L(1.44,0.058,0.060,2.2), L(1.52,0.060,0.062,2.2)], M_SKIN), "spine")

# head / face (smooth, restrained features)
add(SPH("head", (0, 0, 1.685), 1.0, M_SKIN, (0.088, 0.100, 0.110)), "head")
add(BOX("nose", (0, 0.092, 1.672), (0.030, 0.030, 0.034), M_SKIN), "head")
for s in (1, -1):
    add(BOX(f"eye_{'l' if s>0 else 'r'}", (0.040*s, 0.086, 1.700), (0.030, 0.012, 0.015), M_EYE), "head")
    add(BOX(f"brow_{'l' if s>0 else 'r'}", (0.040*s, 0.088, 1.726), (0.034, 0.012, 0.010), M_HAIR), "head")
add(SPH("hair_cap", (0, -0.008, 1.712), 1.0, M_HAIR, (0.092, 0.104, 0.084)), "head")
add(BOX("hair_back", (0, -0.078, 1.64), (0.15, 0.05, 0.14), M_HAIR), "head")

# arms: lofted sleeve + squared delt read + beveled cuff/hand
# Sleeve and forearm lofts now carry real side X offsets before world-preserving PAR.
for key, s in (("l", 1), ("r", -1)):
    add(BOX(f"delt_{key}", (0.188*s, 0, 1.445), (0.096, 0.112, 0.104), M_JKT, 0.016), key+"sh")
    add(LOFT(f"sleeve_{key}", [
        LS(1.47,0.082,0.086,0.185*s,2.4,1.0,0.0),
        LS(1.32,0.080,0.084,0.195*s,2.4,1.0,0.0),
        LS(1.18,0.076,0.080,0.205*s,2.5,1.0,0.0),
    ], M_JKT, w=0.004), key+"sh")
    add(LOFT(f"fore_{key}", [
        LS(1.18,0.070,0.074,0.205*s,2.4,1.0,0.0),
        LS(1.06,0.066,0.070,0.212*s,2.4,1.0,0.0),
        LS(0.95,0.060,0.064,0.222*s,2.6,1.0,0.0),
    ], M_JKT, w=0.004), key+"el")
    add(BOX(f"cuff_{key}", (0.215*s, 0, 0.95), (0.052, 0.062, 0.052), M_TRIM), key+"el")
    add(BOX(f"palm_{key}", (0.222*s, 0.012, 0.90), (0.050, 0.084, 0.074), M_SKIN), key+"el")
    add(BOX(f"fingers_{key}", (0.222*s, 0.052, 0.864), (0.046, 0.050, 0.062), M_SKIN), key+"el")
    add(BOX(f"thumb_{key}", (0.198*s, 0.040, 0.894), (0.022, 0.046, 0.026), M_SKIN), key+"el")

# legs: lofted tapered trousers, beveled knee pad, pant cuff, shaped shoe
# Thigh and shin lofts now carry real side X offsets before world-preserving PAR.
for key, s in (("l", 1), ("r", -1)):
    add(LOFT(f"thigh_{key}", [
        LS(0.95,0.100,0.104,0.095*s,2.4,0.86,-0.006),
        LS(0.72,0.092,0.096,0.098*s,2.5,0.84,-0.010),
        LS(0.50,0.086,0.090,0.100*s,2.6,0.84,-0.012),
    ], M_JEANS, w=0.004), key+"hip")
    add(BOX(f"kneepad_{key}", (0.100*s, 0.060, 0.50), (0.086, 0.052, 0.096), M_JEANS), key+"knee")
    add(LOFT(f"shin_{key}", [
        LS(0.50,0.082,0.086,0.100*s,2.5,0.86,-0.006),
        LS(0.30,0.072,0.076,0.102*s,2.6,0.86,-0.008),
        LS(0.13,0.062,0.066,0.105*s,2.8,0.88,-0.010),
    ], M_JEANS, w=0.004), key+"knee")
    add(BOX(f"pantcuff_{key}", (0.105*s, 0.0, 0.152), (0.072, 0.080, 0.050), M_JEANS), key+"knee")
    add(BOX(f"shoe_{key}", (0.105*s, 0.052, 0.040), (0.086, 0.20, 0.060), M_SHOE, 0.014), key+"knee")
    add(BOX(f"toe_{key}", (0.105*s, 0.183, 0.046), (0.082, 0.092, 0.062), M_SHOE, 0.022), key+"knee")

# right-hand handgun carried by the right elbow (rel)
add(BOX("pistol_slide", (-0.222, 0.10, 0.90), (0.030, 0.20, 0.046), M_PIST, 0.004), "rel")
add(BOX("pistol_grip", (-0.222, -0.018, 0.846), (0.026, 0.050, 0.10), M_PIST, 0.004), "rel")

SC.view_layer.update()
keys = {"root": root, "spine": spine, "head": head,
        "lsh": sh["l"], "rsh": sh["r"], "lel": el["l"], "rel": el["r"],
        "lhip": hip["l"], "rhip": hip["r"], "lknee": kn["l"], "rknee": kn["r"]}
for k, objs in parts.items():
    for o in objs: PAR(o, keys[k])
SC.view_layer.update()

# Presentation transform. The +pi Z pre-rotation re-aims the visual hierarchy;
# it does not reverse local Euler meaning. Down-Z limbs still bend toward +X
# toward local +Y. Spine/head are up-Z, so UP_Z negates saved forward intent.
root.location = (0.0, 0.0, 0.79)
root.rotation_euler = (0.0, 0.0, math.pi)
SC.view_layer.update()

ALLP = ["spine","head","lsh","rsh","lel","rel","lhip","rhip","lknee","rknee"]
for n in ALLP:
    if n not in keys: raise KeyError(n)
for ob in keys.values():
    ob.animation_data_clear()

def keyrot(n, f, r):
    if n not in keys: raise KeyError(n)
    ob = keys[n]
    if ob.animation_data is None: ob.animation_data_create()
    sx = -1.0 if n in UP_Z else 1.0
    ob.rotation_euler = (FX*sx*float(r[0]), float(r[1]), float(r[2]))
    for i in range(3):
        ob.keyframe_insert("rotation_euler", index=i, frame=int(f), replace=True)

def pin(a, b=None):
    if b is None: b = a
    for n in ALLP:
        keyrot(n, a, (0.0, 0.0, 0.0))
        keyrot(n, b, (0.0, 0.0, 0.0))

def play(a, b, d):
    pin(a, b)
    for n, pts in d.items():
        if n not in keys: raise KeyError(n)
        for f, r in pts:
            keyrot(n, f, r)

# Pin true rest at frame 1, then author the six clips.
pin(1, 1)

# Idle 1..61  (breathing / weight shift / head sway; loop-continuous at rest)
play(1, 61, {"spine":[(16,(0.018,0,0)),(31,(0,0,0)),(46,(-0.012,0,0))],
             "head":[(16,(0.004,0.05,0)),(31,(0.01,0,0)),(46,(-0.004,-0.05,0))],
             "lsh":[(16,(0.02,0,0)),(31,(0,0,0)),(46,(-0.02,0,0))],
             "rsh":[(16,(-0.02,0,0)),(31,(0,0,0)),(46,(0.02,0,0))]})

# Walk 71..101  (one opposing cycle, loop seam preserved)
play(71, 101, {
    "lhip":[(71,(-0.30,0,0)),(79,(0,0,0)),(86,(0.34,0,0)),(93,(0.05,0,0)),(101,(-0.30,0,0))],
    "lknee":[(71,(-0.15,0,0)),(79,(-0.55,0,0)),(86,(-0.05,0,0)),(93,(-0.30,0,0)),(101,(-0.15,0,0))],
    "rhip":[(71,(0.34,0,0)),(79,(0.05,0,0)),(86,(-0.30,0,0)),(93,(0,0,0)),(101,(0.34,0,0))],
    "rknee":[(71,(-0.05,0,0)),(79,(-0.30,0,0)),(86,(-0.15,0,0)),(93,(-0.55,0,0)),(101,(-0.05,0,0))],
    "lsh":[(71,(0.30,0,0)),(79,(0,0,0)),(86,(-0.34,0,0)),(93,(-0.05,0,0)),(101,(0.30,0,0))],
    "rsh":[(71,(-0.34,0,0)),(79,(-0.05,0,0)),(86,(0.30,0,0)),(93,(0,0,0)),(101,(-0.34,0,0))],
    "lel":[(71,(0.30,0,0)),(86,(0.45,0,0)),(101,(0.30,0,0))],
    "rel":[(71,(0.45,0,0)),(86,(0.30,0,0)),(101,(0.45,0,0))],
    "spine":[(71,(0.02,0,0)),(86,(0.02,0,0)),(101,(0.02,0,0))]})

# Jog 111..135  (larger amp / faster cycle, knee clearance)
play(111, 135, {
    "lhip":[(111,(-0.50,0,0)),(117,(0,0,0)),(123,(0.60,0,0)),(129,(0.10,0,0)),(135,(-0.50,0,0))],
    "lknee":[(111,(-0.30,0,0)),(117,(-0.90,0,0)),(123,(-0.05,0,0)),(129,(-0.45,0,0)),(135,(-0.30,0,0))],
    "rhip":[(111,(0.60,0,0)),(117,(0.10,0,0)),(123,(-0.50,0,0)),(129,(0,0,0)),(135,(0.60,0,0))],
    "rknee":[(111,(-0.05,0,0)),(117,(-0.45,0,0)),(123,(-0.30,0,0)),(129,(-0.90,0,0)),(135,(-0.05,0,0))],
    "lsh":[(111,(0.50,0,0)),(117,(0,0,0)),(123,(-0.60,0,0)),(129,(-0.10,0,0)),(135,(0.50,0,0))],
    "rsh":[(111,(-0.60,0,0)),(117,(-0.10,0,0)),(123,(0.50,0,0)),(129,(0,0,0)),(135,(-0.60,0,0))],
    "lel":[(111,(0.90,0,0)),(123,(1.10,0,0)),(135,(0.90,0,0))],
    "rel":[(111,(1.10,0,0)),(123,(0.90,0,0)),(135,(1.10,0,0))],
    "spine":[(111,(0.12,0,0)),(123,(0.12,0,0)),(135,(0.12,0,0))]})

# Aim 145..175  (right weapon toward face/local +Y + left support, restrained breath)
play(145, 175, {
    "spine":[(145,(0.10,0,0)),(160,(0.12,0,0)),(175,(0.10,0,0))],
    "lsh":[(145,(1.30,0,0)),(165,(1.33,0,0)),(175,(1.30,0,0))],
    "rsh":[(145,(1.30,0,0)),(165,(1.32,0,0)),(175,(1.30,0,0))],
    "lel":[(145,(0.45,0,0)),(165,(0.50,0,0)),(175,(0.45,0,0))],
    "rel":[(145,(0.45,0,0)),(165,(0.46,0,0)),(175,(0.45,0,0))]})

# Board 185..209  (lean + right-hand reach into car, staggered feet)
play(185, 209, {
    "spine":[(185,(0.50,0,0)),(197,(0.52,0,0)),(209,(0.50,0,0))],
    "rsh":[(185,(1.55,0,0)),(197,(1.62,0,0)),(209,(1.55,0,0))],
    "rel":[(185,(-0.20,0,0)),(197,(-0.15,0,0)),(209,(-0.20,0,0))],
    "lsh":[(185,(0.80,0,0)),(209,(0.80,0,0))],
    "lhip":[(185,(0.20,0,0)),(209,(0.20,0,0))],
    "lknee":[(185,(-0.25,0,0)),(209,(-0.25,0,0))],
    "rhip":[(185,(-0.10,0,0)),(209,(-0.10,0,0))]})

# Drive 219..279  (seated thighs/shins, hands toward wheel, body sway)
play(219, 279, {
    "spine":[(219,(0.18,0,0)),(249,(0.20,0,0)),(279,(0.18,0,0))],
    "head":[(219,(0,0.03,0)),(249,(0,-0.03,0)),(279,(0,0.03,0))],
    "lsh":[(219,(1.00,0,0)),(249,(1.02,0,0)),(279,(1.00,0,0))],
    "rsh":[(219,(1.00,0,0)),(249,(0.98,0,0)),(279,(1.00,0,0))],
    "lel":[(219,(0.70,0,0)),(249,(0.72,0,0)),(279,(0.70,0,0))],
    "rel":[(219,(0.70,0,0)),(249,(0.68,0,0)),(279,(0.70,0,0))],
    "lhip":[(219,(1.00,0,0)),(279,(1.00,0,0))],
    "lknee":[(219,(-1.00,0,0)),(279,(-1.00,0,0))],
    "rhip":[(219,(0.92,0,0)),(279,(0.92,0,0))],
    "rknee":[(219,(-0.94,0,0)),(279,(-0.94,0,0))]})

# Pin inter-clip gaps to rest so no state bleeds across a range boundary.
for a, b in [(62,70),(102,110),(136,144),(176,184),(210,218)]:
    pin(a, b)

# Single action per pivot, no NLA tracks, and stable timeline endpoints.
for n in ALLP:
    ob = keys[n]
    if ob.animation_data is None or ob.action is None:
        raise RuntimeError("missing action: " + n)
    for fc in ob.action.fcurves:
        fc.extrapolation = 'CONSTANT'

SC.scene.frame_set(1)
print("courier v2 repaired:", len(bpy.data.objects), "objects; clips",
      "1-61 71-101 111-135 145-175 185-209 219-279 @30fps")
