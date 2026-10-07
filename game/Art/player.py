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
    nt = m.node_tree; b = nt.nodes.get('Principled BSDF')
    if b is None:
        b = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = nt.nodes.get('Material Output')
        if out is None:
            out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    cc = (*c, 1.0)
    b.inputs['Base Color'].default_value = cc
    try:
        m.diffuse_color = cc
    except Exception:
        pass
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if n in ('Jacket_Charcoal', 'Jacket_Highlight', 'Jeans_DarkBlue', 'Jeans_Seam'):
        S = 256
        name = n + '_Tex'
        img = bpy.data.images.get(name)
        if img is None or img.size[0] != S or img.size[1] != S:
            if img is not None:
                bpy.data.images.remove(img)
            img = bpy.data.images.new(name, S, S, alpha=False, float_buffer=False)
            try:
                img.colorspace_settings.name = 'sRGB'
            except Exception:
                pass
            try:
                img.generated_width = S
                img.generated_height = S
                img.generated_color = cc
            except Exception:
                pass
            r0 = float(c[0]); g0 = float(c[1]); b0 = float(c[2])
            denim = 'Jeans' in n
            px = [0.0] * (S * S * 4)
            twopi = 6.283185307179586
            for y in range(S):
                yf = (y + 0.5) / S
                yv = yf * twopi
                sy1 = math.sin(yv * 0.73)
                sy2 = math.sin(yv * 2.31)
                wy = abs(math.sin(y * 0.5235987756))
                row = y * S * 4
                for x in range(S):
                    xf = (x + 0.5) / S
                    xv = xf * twopi
                    lo = math.sin(xv * 1.13) * sy1
                    md = math.sin(xv * 3.77) * sy2
                    hi = math.sin(x * 0.41 + y * 0.61) * math.cos(x * 0.73 - y * 0.53)
                    wx = abs(math.sin(x * 0.5235987756))
                    weave = (wx + wy) * 0.5 - 0.5
                    hashv = (math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0
                    grain = hashv - 0.5
                    v = 0.24 * lo + 0.12 * md + 0.08 * hi + 0.10 * weave + 0.06 * grain
                    if denim:
                        rr = r0 + v * 0.021 + max(0.0, v) * 0.006
                        gg = g0 + v * 0.026 + max(0.0, v) * 0.004
                        bb = b0 + v * 0.032
                    else:
                        rr = r0 + v * 0.014 + max(0.0, v) * 0.003
                        gg = g0 + v * 0.014
                        bb = b0 + v * 0.018
                    if rr < 0.0:
                        rr = 0.0
                    elif rr > 1.0:
                        rr = 1.0
                    if gg < 0.0:
                        gg = 0.0
                    elif gg > 1.0:
                        gg = 1.0
                    if bb < 0.0:
                        bb = 0.0
                    elif bb > 1.0:
                        bb = 1.0
                    rr = rr ** 0.4545 if rr > 0.0 else 0.0
                    gg = gg ** 0.4545 if gg > 0.0 else 0.0
                    bb = bb ** 0.4545 if bb > 0.0 else 0.0
                    p = row + x * 4
                    px[p] = rr; px[p + 1] = gg; px[p + 2] = bb; px[p + 3] = 1.0
            try:
                import array
                img.pixels.foreach_set(array.array('f', px))
            except Exception:
                try:
                    img.pixels[:] = px
                except Exception:
                    for i, val in enumerate(px):
                        img.pixels[i] = val
        ti = nt.nodes.new('ShaderNodeTexImage')
        ti.image = img
        ti.location = (-520, 180)
        try:
            ti.extension = 'REPEAT'
            ti.interpolation = 'LINEAR'
        except Exception:
            pass
        try:
            tc = nt.nodes.new('ShaderNodeTexCoord')
            tc.location = (-760, 180)
            nt.links.new(tc.outputs['UV'], ti.inputs['Vector'])
        except Exception:
            pass
        nt.links.new(ti.outputs['Color'], b.inputs['Base Color'])
    return m

M_SKIN  = MAT("Skin_Warm", (0.44, 0.285, 0.205), 0.52)
M_JKT   = MAT("Jacket_Charcoal", (0.072, 0.072, 0.084), 0.86)
M_JKT_HL= MAT("Jacket_Highlight", (0.118, 0.118, 0.132), 0.80)
M_TRIM  = MAT("Trim_JacketDark", (0.026, 0.026, 0.032), 0.68)
M_JEANS = MAT("Jeans_DarkBlue", (0.092, 0.120, 0.196), 0.92)
M_JEANS_HL= MAT("Jeans_Seam", (0.142, 0.172, 0.252), 0.90)
M_SHOE  = MAT("Shoe_Black", (0.028, 0.028, 0.034), 0.48)
M_HAIR  = MAT("Hair_Black", (0.022, 0.018, 0.015), 0.55)
M_PIST  = MAT("Pistol_Steel", (0.085, 0.085, 0.10), 0.35, 0.80)
M_EYE   = MAT("Eye_Dark", (0.014, 0.014, 0.02), 0.40)


def shade_bevel(o, w=0.006, ang=0.70):
    for p in o.data.polygons: p.use_smooth = True
    m = o.modifiers.new("bev", "BEVEL")
    m.width = w; m.segments = 2; m.limit_method = "ANGLE"
    m.angle_limit = ang; m.use_clamp_overlap = True; m.miter_outer = "MITER_ARC"
    try: m.harden_normals = True
    except Exception: pass
    return o

def OBJ(n, bm, mat):
    me = bpy.data.meshes.new(n)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    uvl = me.uv_layers.active
    if uvl is None or len(uvl.data) != len(me.loops):
        if uvl is not None:
            try:
                me.uv_layers.remove(uvl)
            except Exception:
                pass
        uvl = me.uv_layers.new(name='UVMap')
    sc = 5.5
    if mat is not None:
        if 'Jeans' in mat.name:
            sc = 4.5
        elif 'Jacket' in mat.name:
            sc = 6.0
    for p in me.polygons:
        nx = p.normal[0]; ny = p.normal[1]; nz = p.normal[2]
        ax = abs(nx); ay = abs(ny); az = abs(nz)
        if ax >= ay and ax >= az:
            mode = 0
        elif ay >= ax and ay >= az:
            mode = 1
        else:
            mode = 2
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if mode == 0:
                u = co.y; v = co.z
            elif mode == 1:
                u = co.x; v = co.z
            else:
                u = co.x; v = co.y
            uvl.data[li].uv = (u * sc, v * sc)
    o = bpy.data.objects.new(n, me)
    CO.objects.link(o)
    return o

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

# clothed courier body (shaped yoke/shoulder, closed neck+collar, connected trousers/shoes)
# one continuous jacket loft builds volume + trapezius saddle so shoulder is not an open cap
add(LOFT("jkt_torso", [L(0.95,0.150,0.124,2.4,0.82,-0.010), L(1.04,0.162,0.130,2.4,0.84,-0.012),
     L(1.18,0.168,0.134,2.6,0.82,-0.014), L(1.30,0.167,0.132,2.8,0.80,-0.014),
     L(1.40,0.162,0.124,3.0,0.82,-0.012), L(1.46,0.150,0.110,3.2,0.86,-0.010),
     L(1.50,0.088,0.080,2.4,1.0,0.004)], M_JKT, False, False), "spine")
# trapezius saddle fills neck->shoulder dip (no narrow-top / floating shoulder)
add(LOFT("jkt_yoke", [L(1.442,0.152,0.052,2.0,1.0,0.012), L(1.472,0.120,0.054,2.2,1.0,0.010),
     L(1.500,0.072,0.052,2.6,1.0,0.008)], M_JKT, True, False), "spine")
add(LOFT("jkt_hem", [L(0.92,0.168,0.134,2.4,0.82,-0.012), L(0.958,0.178,0.142,2.2,0.80,-0.010),
     L(1.00,0.170,0.136,2.4,0.86,-0.010)], M_TRIM, True, True), "spine")
# restrained jacket collar: tapered, no fat cylinder
add(LOFT("jkt_collar", [L(1.452,0.094,0.086,2.6,1.0,0.010), L(1.498,0.080,0.078,2.6,1.0,0.010),
     L(1.536,0.064,0.064,3.0,1.0,0.006)], M_TRIM, True, False), "spine")
add(BOX("jkt_placket", (0, 0.124, 1.20), (0.014, 0.020, 0.40), M_TRIM), "spine")
for s in (1, -1):
    add(BOX(f"jkt_pocket_{'l' if s>0 else 'r'}", (0.080*s, 0.122, 1.10), (0.052, 0.018, 0.072), M_JKT_HL), "spine")
add(LOFT("neck", [L(1.42,0.062,0.064,2.2,1.0,0.0), L(1.50,0.066,0.066,2.2,1.0,0.0),
     L(1.575,0.060,0.062,2.4,1.0,0.0)], M_SKIN, False, True), "spine")

# head / face : rounded skull + jaw mass + ears, close-fitting hair (no rear plate)
add(SPH("head", (0, 0.005, 1.690), 1.0, M_SKIN, (0.086, 0.100, 0.108)), "head")
add(SPH("jaw", (0, 0.030, 1.638), 1.0, M_SKIN, (0.070, 0.080, 0.060)), "head")
add(SPH("chin", (0, 0.082, 1.612), 1.0, M_SKIN, (0.030, 0.030, 0.026)), "head")
add(SPH("nose", (0, 0.092, 1.672), 1.0, M_SKIN, (0.020, 0.026, 0.034)), "head")
for s in (1, -1):
    add(SPH(f"ear_{'l' if s>0 else 'r'}", (0.084*s, -0.002, 1.686), 1.0, M_SKIN, (0.014, 0.026, 0.040)), "head")
    add(BOX(f"eye_{'l' if s>0 else 'r'}", (0.040*s, 0.088, 1.700), (0.028, 0.010, 0.014), M_EYE), "head")
    add(BOX(f"brow_{'l' if s>0 else 'r'}", (0.040*s, 0.090, 1.724), (0.032, 0.010, 0.010), M_HAIR), "head")
    add(SPH(f"temple_hair_{'l' if s>0 else 'r'}", (0.074*s, 0.026, 1.702), 1.0, M_HAIR, (0.018, 0.040, 0.046)), "head")
add(SPH("hair_cap", (0, -0.012, 1.714), 1.0, M_HAIR, (0.092, 0.106, 0.082)), "head")
add(SPH("hair_back", (0, -0.042, 1.668), 1.0, M_HAIR, (0.084, 0.074, 0.072)), "head")

# arms : rounded delt overlaps yoke+sleeve (closed shoulder) + tapered sleeve/fore + cuff
for key, s in (("l", 1), ("r", -1)):
    add(LOFT(f"sleeve_{key}", [LS(1.518,0.026,0.030,0.098*s,2.2),
        LS(1.500,0.050,0.054,0.128*s,2.4), LS(1.478,0.072,0.076,0.158*s,2.4),
        LS(1.450,0.082,0.082,0.176*s,2.4), LS(1.410,0.078,0.080,0.188*s,2.4),
        LS(1.330,0.073,0.077,0.198*s,2.4), LS(1.260,0.070,0.074,0.202*s,2.4),
        LS(1.180,0.068,0.072,0.202*s,2.5)], M_JKT, True, False, 22, 0.004), key+"sh")
    add(LOFT(f"fold_{key}", [LS(1.20,0.074,0.078,0.202*s,2.4,1.0,0.0),
         LS(1.13,0.077,0.081,0.205*s,2.4,1.0,0.0), LS(1.07,0.072,0.076,0.208*s,2.4,1.0,0.0)], M_JKT_HL, False, False, 18, 0.003), key+"sh")
    add(LOFT(f"fore_{key}", [LS(1.18,0.068,0.072,0.202*s,2.4,1.0,0.0),
         LS(1.06,0.062,0.066,0.212*s,2.4,1.0,0.0), LS(0.95,0.056,0.060,0.220*s,2.6,1.0,0.0)], M_JKT, w=0.004), key+"el")
    add(BOX(f"cuff_{key}", (0.216*s, 0.006, 0.945), (0.066, 0.078, 0.050), M_TRIM), key+"el")
    add(BOX(f"palm_{key}", (0.222*s, 0.012, 0.90), (0.050, 0.084, 0.074), M_SKIN), key+"el")
    add(BOX(f"fingers_{key}", (0.222*s, 0.052, 0.864), (0.046, 0.050, 0.062), M_SKIN), key+"el")
    add(BOX(f"thumb_{key}", (0.198*s, 0.040, 0.894), (0.022, 0.046, 0.026), M_SKIN), key+"el")

# legs : tapered trousers meet a raised shoe collar (no ankle gap), grounded soles
add(LOFT("pants_pelvis", [L(0.84,0.150,0.118,2.4,0.86,-0.006), L(0.95,0.158,0.126,2.5,0.84,-0.010),
     L(1.00,0.152,0.120,2.6,0.82,-0.012)], M_JEANS, True, False), "root")
add(LOFT("belt_waist", [L(0.982,0.160,0.128,2.5,0.82,-0.010), L(1.018,0.162,0.130,2.5,0.82,-0.010)], M_TRIM, True, True), "root")
for key, s in (("l", 1), ("r", -1)):
    add(LOFT(f"thigh_{key}", [LS(0.95,0.100,0.104,0.095*s,2.4,0.86,-0.006),
         LS(0.72,0.092,0.096,0.098*s,2.5,0.84,-0.010), LS(0.50,0.084,0.088,0.100*s,2.6,0.84,-0.012)], M_JEANS, False, True, 22, 0.004), key+"hip")
    add(SPH(f"kneepad_{key}", (0.100*s, 0.052, 0.50), 1.0, M_JEANS, (0.080, 0.058, 0.092)), key+"knee")
    add(LOFT(f"shin_{key}", [LS(0.50,0.080,0.084,0.100*s,2.5,0.86,-0.006),
         LS(0.30,0.070,0.074,0.102*s,2.6,0.86,-0.008), LS(0.11,0.066,0.068,0.105*s,2.8,0.90,-0.006)], M_JEANS, False, True, 22, 0.004), key+"knee")
    add(BOX(f"pantcuff_{key}", (0.105*s, 0.0, 0.118), (0.078, 0.086, 0.050), M_JEANS_HL), key+"knee")
    add(BOX(f"ankle_{key}", (0.105*s, 0.010, 0.085), (0.072, 0.082, 0.050), M_SHOE), key+"knee")
    add(BOX(f"shoe_{key}", (0.105*s, 0.045, 0.048), (0.084, 0.185, 0.048), M_SHOE, 0.012), key+"knee")
    add(BOX(f"toe_{key}", (0.105*s, 0.170, 0.050), (0.080, 0.060, 0.050), M_SHOE, 0.020), key+"knee")

# right-hand handgun carried by the right elbow (rel)
ps = BOX("pistol_slide", (-0.2213, 0.0414, 0.8097), (0.030, 0.20, 0.046), M_PIST, 0.004)
ps.rotation_euler = (-1.555, 0.230, -0.824)
add(ps, "rel")
pg = BOX("pistol_grip", (-0.2442, -0.0161, 0.9238), (0.026, 0.050, 0.10), M_PIST, 0.004)
pg.rotation_euler = (-1.555, 0.230, -0.824)
add(pg, "rel")

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
        ob.keyframe_insert("rotation_euler", index=i, frame=int(f))

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
    "spine":[(145,(0.00,0,0)),(160,(0.02,0,0)),(175,(0.00,0,0))],
    "lsh":[(145,(0.60,0.80,0)),(160,(0.61,0.79,0)),(175,(0.60,0.80,0))],
    "rsh":[(145,(0.80,-0.70,0)),(160,(0.80,-0.69,0)),(175,(0.80,-0.70,0))],
    "lel":[(145,(0.75,0.15,0)),(160,(0.76,0.15,0)),(175,(0.75,0.15,0))],
    "rel":[(145,(0.60,-0.20,0)),(160,(0.61,-0.20,0)),(175,(0.60,-0.20,0))]})

# Board 185..209  (credible crouched entry reaching in, legs already tucking).
# Frame 209 reproduces the EXACT Drive 219 values on every pivot Drive uses,
# including both legs, so the entry no longer snaps into the sit.
play(185, 209, {
    "spine":[(185,(0.70,0,0)),(192,(0.70,0,0)),(199,(0.74,0,0)),(204,(0.76,0,0)),(209,(0.45,0,0))],
    "head":[(185,(0.05,0,0)),(197,(0.05,0.02,0)),(209,(0.0,0.04,0))],
    "lsh":[(185,(1.50,0,0)),(197,(1.32,0,0)),(209,(1.15,0,0))],
    "rsh":[(185,(1.50,0,0)),(197,(1.30,0,0)),(209,(1.10,0,0))],
    "lel":[(185,(0.55,0,0)),(197,(0.75,0,0)),(209,(0.95,0,0))],
    "rel":[(185,(0.55,0,0)),(197,(0.75,0,0)),(209,(0.95,0,0))],
    "lhip":[(185,(0.70,0,0)),(197,(1.20,0,0)),(209,(1.70,0,0))],
    "lknee":[(185,(-0.70,0,0)),(197,(-0.90,0,0)),(209,(-1.10,0,0))],
    "rhip":[(185,(0.50,0,0)),(197,(1.05,0,0)),(209,(1.60,0,0))],
    "rknee":[(185,(-0.50,0,0)),(197,(-0.78,0,0)),(209,(-1.05,0,0))]})

# Drive 219..279  (hips at the fixed anchor: thighs swung up-forward, knees
# deeply bent so the soles tuck inside the footwell above the floor/road, torso
# leaning, forearms bent so the palms meet the wheel's left/right rim, gentle
# sway with loop-continuous endpoints).
play(219, 279, {
    "spine":[(219,(0.45,0,0)),(249,(0.47,0,0)),(279,(0.45,0,0))],
    "head":[(219,(0.0,0.04,0)),(249,(0.0,0.0,0)),(279,(0.0,0.04,0))],
    "lsh":[(219,(1.15,0,0)),(249,(1.17,0,0)),(279,(1.15,0,0))],
    "rsh":[(219,(1.10,0,0)),(249,(1.08,0,0)),(279,(1.10,0,0))],
    "lel":[(219,(0.95,0,0)),(249,(0.97,0,0)),(279,(0.95,0,0))],
    "rel":[(219,(0.95,0,0)),(249,(0.93,0,0)),(279,(0.95,0,0))],
    "lhip":[(219,(1.70,0,0)),(249,(1.72,0,0)),(279,(1.70,0,0))],
    "lknee":[(219,(-1.10,0,0)),(249,(-1.10,0,0)),(279,(-1.10,0,0))],
    "rhip":[(219,(1.60,0,0)),(249,(1.62,0,0)),(279,(1.60,0,0))],
    "rknee":[(219,(-1.05,0,0)),(249,(-1.05,0,0)),(279,(-1.05,0,0))]})

# Pin inter-clip gaps to rest so no state bleeds across a range boundary.
for a, b in [(62,70),(102,110),(136,144),(176,184),(210,218)]:
    pin(a, b)

# Single action per pivot, no NLA tracks, and stable timeline endpoints.
for n in ALLP:
    ob = keys[n]
    if ob.animation_data is None or ob.animation_data.action is None:
        raise RuntimeError("missing action: " + n)

SC.scene.frame_set(1)
print("courier v2 repaired:", len(bpy.data.objects), "objects; clips",
      "1-61 71-101 111-135 145-175 185-209 219-279 @30fps")
