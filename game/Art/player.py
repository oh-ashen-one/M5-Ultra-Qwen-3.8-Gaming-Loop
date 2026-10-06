"""Original player character (art source). Pure bpy/bmesh, no imports.

Author: local Qwen builder. Convention: up = +Z, forward = +Y.
Anatomical height 1.80 m measured from the foot-sole plane.

EXPORT CONTRACT: the Unity integration shifts the instantiated visual by
Y = -0.79 (localPosition += (0,-0.79,0)). The whole rig is therefore built
lifted by L = 0.79 above player_root: sole-of-foot sits at Z = +0.79, so
after the -0.79 Unity offset the feet land exactly on the controller base
(controller bottom = body.y + 0.025) and the ~1.80 m body fills the 1.75 m
controller. Every pivot/mesh gets ONE parent — no doubled offsets, nothing
is reparented twice.

TRANSFORM CONTRACT (made explicit and consistent here):
  * pivot() places a NAMED PIVOT in WORLD space (matrix_world, world coords
    include the lift L). Pivot-local frames are derived by Blender.
  * mk() interprets its `mw` argument as the object's LOCAL matrix relative
    to its `parent` (matrix_basis, identity parent-inverse). So:
      - head / arm / leg / gun mesh callers pass TRUE parent-local coords
        (e.g. arm hangs down the parent's local -Z).
      - torso / pelvis callers carry readable absolute (world) numbers and
        are routed through mkb(), which converts world -> body-local with
        body.matrix_world.inverted(). The lift L cancels in that subtraction,
        so torso anatomy heights stay exactly as authored.
  * view_layer.update() is called after pivots exist so parent world
    matrices are valid before any world->local conversion.

Named pivots retained for the game pose code:
  player_root  head_root  armL_root  armR_root  legL_root  legR_root
  (plus gun_root under armR_root)
"""
import bpy
import bmesh
import math
from mathutils import Matrix, Euler

NAME = "player"
L = 0.79  # presentation lift so Unity's -0.79 offset grounds the feet.
F = lambda z: z + L
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
    "jacket":  mat("pl_jacket", (0.052, 0.056, 0.066), 0.78),
    "jacket2": mat("pl_jacket2", (0.036, 0.038, 0.046), 0.74),
    "shirt":   mat("pl_shirt", (0.720, 0.718, 0.700), 0.85),
    "jeans":   mat("pl_jeans", (0.075, 0.095, 0.140), 0.88),
    "skin":    mat("pl_skin", (0.330, 0.215, 0.155), 0.62),
    "hair":    mat("pl_hair", (0.030, 0.028, 0.028), 0.70),
    "shoe":    mat("pl_shoe", (0.045, 0.045, 0.050), 0.62),
    "sole":    mat("pl_sole", (0.018, 0.018, 0.020), 0.90),
    "steel":   mat("pl_steel", (0.230, 0.235, 0.250), 0.40, 1.0),
    "gold":    mat("pl_buckle", (0.55, 0.45, 0.18), 0.35, 1.0),
}

I = Matrix.Identity(4)


def T(x, y, z):
    return Matrix.Translation((x, y, z))


def rot(e):
    # Supported mathutils Euler->4x4 rotation API (Matrix.Euler does NOT exist).
    return Euler(tuple(math.radians(a) for a in e), "XYZ").to_matrix().to_4x4()


def pivot(nm, mw, parent=None):
    # World-space placement for named pivots.
    o = bpy.data.objects.new(nm, None)
    scene.collection.objects.link(o)
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    o.matrix_world = mw
    return o


def ellb(r, clip=None):
    def b(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
        for v in bm.verts:
            v.co.x *= r[0]; v.co.y *= r[1]; v.co.z *= r[2]
        if clip:
            zt, yt = clip
            vs = [v for v in bm.verts if v.co.z < zt and v.co.y > yt]
            if vs:
                bmesh.ops.delete(bm, geom=vs, context='VERTS')
    return b


def boxb(d, br=0.0, seg=2):
    def b(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= d[0]; v.co.y *= d[1]; v.co.z *= d[2]
        if br > 0:
            bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                            offset=br, segments=seg, profile=0.5, affect='EDGES')
    return b


def mk(nm, mkey, parent, mw_local, build, smooth=True):
    # mw_local is the LOCAL matrix relative to `parent` (identity parent-inverse);
    # world = parent.matrix_world @ mw_local, so the body is assembled exactly once.
    me = bpy.data.meshes.new(nm)
    bm = bmesh.new()
    build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nm, me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(M[mkey])
    for p in me.polygons:
        p.use_smooth = smooth
    ob.parent = parent
    ob.matrix_basis = mw_local
    return ob


# ---------- pivots (one parent each; body carries the lift) ----------
root = pivot("player_root", I)
body = pivot("body", T(0, 0, F(0.95)), root)
head = pivot("head_root", T(0, 0, F(1.545)), body)
arms, legs = {}, {}
for s, tag in ((-1, "L"), (1, "R")):
    arms[tag] = pivot("arm%s_root" % tag,
                      T(s * 0.262, 0, F(1.47)) @ rot((0, -6 * s, 0)), body)
    legs[tag] = pivot("leg%s_root" % tag, T(s * 0.105, 0, F(0.95)), body)
bpy.context.view_layer.update()

# torso callers carry absolute (world) numbers -> convert to body-local once.
# (The lift L cancels in body.matrix_world.inverted() @ world, so anatomy heights
#  authored below are preserved unchanged.)
BW_INV = body.matrix_world.inverted()
def mkb(nm, mkey, mw_world, build, smooth=True):
    return mk(nm, mkey, body, BW_INV @ mw_world, build, smooth)

# ---------- torso / pelvis ----------
mkb("pelvis", "jeans", T(0, 0, F(0.985)), ellb((0.150, 0.108, 0.118)))
mkb("waist", "jacket", T(0, 0, F(1.18)), ellb((0.148, 0.128, 0.20)))
mkb("chest", "jacket", T(0, 0, F(1.37)), ellb((0.205, 0.138, 0.145)))
mkb("shoulders", "jacket", T(0, 0, F(1.455)), ellb((0.258, 0.132, 0.092)))
mkb("neck", "skin", T(0, 0, F(1.545)), ellb((0.054, 0.052, 0.062)))
mkb("collar", "jacket2", T(0, 0, F(1.525)), ellb((0.086, 0.082, 0.055)))
# shirt V at the neck opening + jacket hem + peeking shirt hem + belt
mkb("shirt_v", "shirt", T(0, 0.112, F(1.40)), boxb((0.085, 0.02, 0.15), 0.012))
mkb("zipper", "steel", T(0, 0.118, F(1.24)), boxb((0.018, 0.014, 0.34), 0.006))
mkb("jacket_hem", "jacket2", T(0, 0, F(1.06)), ellb((0.154, 0.132, 0.05)))
mkb("shirt_hem", "shirt", T(0, 0, F(1.005)), ellb((0.146, 0.120, 0.032)))
mkb("belt", "sole", T(0, 0, F(0.985)), ellb((0.152, 0.124, 0.036)))
mkb("buckle", "gold", T(0, 0.126, F(0.985)), boxb((0.028, 0.014, 0.028), 0.006))

# ---------- head / hair (local to head_root) ----------
mk("skull", "skin", head, T(0, 0, 0.128), ellb((0.093, 0.102, 0.117)))
mk("jaw", "skin", head, T(0, 0.020, 0.078), ellb((0.066, 0.078, 0.058)))
mk("brow", "skin", head, T(0, 0.078, 0.150), ellb((0.062, 0.030, 0.024)))
mk("nose", "skin", head, T(0, 0.100, 0.118), ellb((0.016, 0.022, 0.024)))
mk("earL", "skin", head, T(0.090, -0.008, 0.122), ellb((0.013, 0.030, 0.032)))
mk("earR", "skin", head, T(-0.090, -0.008, 0.122), ellb((0.013, 0.030, 0.032)))
# cap (front-lower verts removed for a short cut) + back/nape mass
mk("hair_cap", "hair", head, T(0, -0.012, 0.148),
   ellb((0.099, 0.106, 0.102), clip=(-0.015, 0.030)))
mk("hair_back", "hair", head, T(0, -0.052, 0.096), ellb((0.090, 0.058, 0.088)))

# ---------- arms (local to armX_root; limb runs down local -Z) ----------
for s, tag in ((-1, "L"), (1, "R")):
    a = arms[tag]
    mk("arm%s_delt" % tag, "jacket", a, T(s * 0.012, 0, -0.005), ellb((0.084, 0.084, 0.092)))
    mk("arm%s_upper" % tag, "jacket", a, T(0, 0.004, -0.165), ellb((0.072, 0.076, 0.160)))
    mk("arm%s_elbow" % tag, "jacket", a, T(0, 0.010, -0.300), ellb((0.060, 0.062, 0.064)))
    mk("arm%s_fore" % tag, "jacket", a, T(0, 0.020, -0.440), ellb((0.055, 0.057, 0.150)))
    mk("arm%s_cuff" % tag, "jacket2", a, T(0, 0.024, -0.565), ellb((0.052, 0.054, 0.034)))
    mk("arm%s_hand" % tag, "skin", a, T(0, 0.030, -0.645), ellb((0.044, 0.060, 0.086)))
    mk("arm%s_thumb" % tag, "skin", a, T(-s * 0.046, 0.042, -0.625),
       ellb((0.018, 0.028, 0.040)))

# ---------- legs + shoes (local to legX_root) ----------
for s, tag in ((-1, "L"), (1, "R")):
    l = legs[tag]
    mk("leg%s_thigh" % tag, "jeans", l, T(0, 0, -0.205), ellb((0.094, 0.102, 0.235)))
    mk("leg%s_knee" % tag, "jeans", l, T(0, 0.004, -0.420), ellb((0.073, 0.076, 0.074)))
    mk("leg%s_shin" % tag, "jeans", l, T(0, -0.006, -0.620), ellb((0.068, 0.071, 0.200)))
    mk("leg%s_cuff" % tag, "jeans", l, T(0, 0, -0.800), ellb((0.058, 0.060, 0.045)))
    mk("leg%s_shoe" % tag, "shoe", l, T(0, 0.058, -0.892), boxb((0.150, 0.300, 0.118), 0.045), False)
    mk("leg%s_sole" % tag, "sole", l, T(0, 0.062, -0.928), boxb((0.160, 0.318, 0.044), 0.016), False)

# ---------- pistol under right hand (gun_root placed in world via pivot) ----------
gun = pivot("gun_root", T(0.293, 0.095, F(0.700)) @ rot((-8, 0, 0)), arms["R"])
bpy.context.view_layer.update()
# gun meshes are local to gun_root:
mk("gun_slide", "steel", gun, T(0, 0.045, 0), boxb((0.028, 0.108, 0.040), 0.010), False)
mk("gun_grip", "shoe", gun, T(0, -0.045, -0.060) @ rot((18, 0, 0)),
   boxb((0.024, 0.034, 0.068), 0.010), False)
mk("gun_trigger", "steel", gun, T(0, -0.010, -0.030), boxb((0.010, 0.030, 0.030), 0.004), False)

bpy.context.view_layer.update()
print("player built:", len(scene.objects), "objects, lift", L)
