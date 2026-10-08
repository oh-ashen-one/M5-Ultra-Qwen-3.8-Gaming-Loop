using System.Collections.Generic;
using UnityEngine;

namespace ChicagoGame {
public sealed class VehiclePresentation : MonoBehaviour {
    const float BOARD = 0.8f;
    const float OPEN_DEG = 62f;
    const string RES = "Generated/player/scene";

    static string Strip(string s) { return string.IsNullOrEmpty(s) ? "" : s.Replace("_", "").Replace("-", "").Replace(" ", "").ToLowerInvariant(); }
    static Transform Find(Transform r, string w) { if (r == null) return null; if (Strip(r.name) == Strip(w)) return r; for (int i = 0; i < r.childCount; ++i) { var c = Find(r.GetChild(i), w); if (c != null) return c; } return null; }

    Transform body, visRef, hipL, hipR, hipAnchor, fwdAnchor, proxy, vehicle, doorHinge, missingDoorRoot;
    Animation anim; Renderer[] guns; string boardClip, driveClip;
    bool hasBasis, active, hasSpawn, frozen, clipsKnown, touchedDoor;
    Quaternion visualBasis = Quaternion.identity, startRot = Quaternion.identity, initialYaw = Quaternion.identity, doorRestRot = Quaternion.identity;
    Vector3 visualScale = Vector3.one, startLocal = Vector3.zero;
    int lastRestarts = int.MinValue; float board = 1f; float doorSign = 1f; Vector3[] path = new Vector3[7];

    public static void Install(GameObject body) {
        if (body == null) return;
        var p = body.GetComponent<VehiclePresentation>(); if (p == null) p = body.AddComponent<VehiclePresentation>();
        p.body = body.transform; p.visRef = Find(body.transform, "PlayerVisual"); p.lastRestarts = LoopSignals.Restarts;
        FinishSurfaces(LoopSignals.Vehicle);
    }

static void FinishSurfaces(Transform root) {
    if (root == null) return;
    var rs = root.GetComponentsInChildren<Renderer>(true);
    if (rs == null || rs.Length == 0) return;
    var clones = new Dictionary<Material, Material>();
    for (int i = 0; i < rs.Length; ++i) {
        var r = rs[i]; if (r == null) continue;
        var shared = r.sharedMaterials;
        if (shared == null || shared.Length == 0) continue;
        var owned = new Material[shared.Length];
        for (int k = 0; k < shared.Length; ++k) owned[k] = shared[k];
        bool dirty = false;
        for (int j = 0; j < shared.Length; ++j) {
            var src = shared[j]; if (src == null) continue;
            string n = Strip(src.name);
            bool d2 = n.StartsWith("coupepaintdark");
            bool p1 = !d2 && n.StartsWith("coupepaint");
            bool trim = n.StartsWith("coupotrim");
            bool rim = n.StartsWith("couperim");
            bool chrome = n.StartsWith("coupechrome");
            bool lamp = n.StartsWith("coupelamp");
            bool tail = n.StartsWith("coupetail");
            if (!(d2 || p1 || trim || rim || chrome || lamp || tail)) continue;
            Material cl;
            if (!clones.TryGetValue(src, out cl) || cl == null) {
                cl = new Material(src);
                cl.name = src.name;
                clones[src] = cl;
            }
            Color c;
            float met, g;
            if (p1) { c = new Color(0.030f, 0.130f, 0.620f, 1f); met = 0.30f; g = 0.72f; }
            else if (d2) { c = new Color(0.016f, 0.075f, 0.380f, 1f); met = 0.30f; g = 0.68f; }
            else if (rim) { c = new Color(0.520f, 0.530f, 0.550f, 1f); met = 0.70f; g = 0.45f; }
            else if (chrome) { c = new Color(0.750f, 0.760f, 0.780f, 1f); met = 0.70f; g = 0.55f; }
            else if (trim) { c = new Color(0.020f, 0.022f, 0.026f, 1f); met = 0.10f; g = 0.28f; }
            else if (lamp) { c = new Color(0.900f, 0.900f, 0.850f, 1f); met = 0f; g = 0.50f; }
            else { c = new Color(0.450f, 0.020f, 0.020f, 1f); met = 0f; g = 0.40f; }
            cl.SetColor("_Color", c);
            if (cl.HasProperty("_Metallic")) cl.SetFloat("_Metallic", met);
            if (cl.HasProperty("_Glossiness")) cl.SetFloat("_Glossiness", g);
            owned[j] = cl; dirty = true;
        }
        if (dirty) r.sharedMaterials = owned;
    }
    clones.Clear();
}

    void EnsureProxy() {
        if (!hasBasis && visRef != null && body != null) { visualBasis = Quaternion.Inverse(body.rotation) * visRef.rotation; visualScale = visRef.localScale; hasBasis = true; }
        var root = LoopSignals.Vehicle;
        if (proxy != null) { if (root != null && proxy.parent != root) proxy.SetParent(root, false); if (anim != null) anim.cullingType = AnimationCullingType.AlwaysAnimate; return; }
        if (visRef == null || root == null) return;
        var clone = Instantiate(visRef.gameObject, root, false); clone.name = "DriverVisual"; proxy = clone.transform;
        anim = clone.GetComponent<Animation>(); if (anim == null) anim = clone.AddComponent<Animation>();
        anim.playAutomatically = false; anim.cullingType = AnimationCullingType.AlwaysAnimate;
        clipsKnown = ResolveDriverClips(); ConfigureDriver();
        hipL = Find(clone.transform, "pivot_hip_l"); hipR = Find(clone.transform, "pivot_hip_r");
        var g = new List<Renderer>(); foreach (var r in clone.GetComponentsInChildren<Renderer>(true)) { string n = Strip(r.name); if (n == "pistolslide" || n == "pistolgrip") g.Add(r); }
        guns = g.ToArray(); SetGuns(false); proxy.gameObject.SetActive(false); vehicle = root; active = false;
    }

    bool ResolveDriverClips() {
        if (anim == null) return false; boardClip = null; driveClip = null;
        var loaded = Resources.LoadAll<AnimationClip>(RES);
        if (loaded != null) foreach (var c in loaded) { if (c == null || c.length < 0.1f || c.name.StartsWith("__preview__")) continue; string n = Strip(c.name);
            if (boardClip == null && n == "board") { if (anim.GetClip(c.name) == null) anim.AddClip(c, c.name); boardClip = c.name; }
            else if (driveClip == null && n == "drive") { if (anim.GetClip(c.name) == null) anim.AddClip(c, c.name); driveClip = c.name; }
        }
        if (boardClip == null || driveClip == null) foreach (AnimationState st in anim) { if (st == null || st.clip == null) continue; string n = Strip(st.clip.name); if (boardClip == null && n == "board") boardClip = st.name; if (driveClip == null && n == "drive") driveClip = st.name; }
        return !string.IsNullOrEmpty(boardClip) && !string.IsNullOrEmpty(driveClip);
    }

    void ConfigureDriver() {
        if (anim == null) return; anim.enabled = true; anim.playAutomatically = false;
        foreach (AnimationState st in anim) { if (st == null) continue; string n = st.clip != null ? Strip(st.clip.name) : ""; bool driver = (boardClip != null && st.name == boardClip) || (driveClip != null && st.name == driveClip) || n == "board" || n == "drive";
            st.speed = 1f; st.enabled = false; st.weight = driver ? 1f : 0f; if (n == "board") st.wrapMode = WrapMode.Once; else if (n == "drive") st.wrapMode = WrapMode.Loop;
        }
        ConfigureState(boardClip, WrapMode.Once); ConfigureState(driveClip, WrapMode.Loop); anim.animatePhysics = false; anim.Stop();
    }

    void ConfigureState(string clip, WrapMode wm) { if (anim == null || string.IsNullOrEmpty(clip)) return; var st = anim[clip]; if (st == null) return; st.layer = 0; st.weight = 1f; st.speed = 1f; st.wrapMode = wm; st.enabled = false; }
    void SetGuns(bool on) { if (guns == null) return; for (int i = 0; i < guns.Length; ++i) if (guns[i] != null) guns[i].enabled = on; }
    static bool IsVehicle(string m) { return !string.IsNullOrEmpty(m) && m.IndexOf("Veh", System.StringComparison.OrdinalIgnoreCase) >= 0; }
    Vector3 HipsLocal() { return hipL && hipR && proxy ? (proxy.InverseTransformPoint(hipL.position) + proxy.InverseTransformPoint(hipR.position)) * 0.5f : Vector3.zero; }
    static Vector3 Flat(Vector3 v) { v.y = 0f; return v.sqrMagnitude > 1e-6f ? v.normalized : Vector3.forward; }
    void EnsureAnchors() { if (vehicle == null) return; if (hipAnchor == null) hipAnchor = Find(vehicle, "driver_hip_anchor"); if (fwdAnchor == null) fwdAnchor = Find(vehicle, "driver_forward_anchor"); }

    bool EnsureDoor(Transform root) {
        if (root == null) return false; if (doorHinge != null) return true; if (missingDoorRoot == root) return false;
        var d = Find(root, "driver_door_hinge"); if (d == null) { missingDoorRoot = root; return false; }
        doorHinge = d; doorRestRot = doorHinge.localRotation; return true;
    }

    float VehicleScale() { if (hipAnchor != null && fwdAnchor != null) { float d = Vector3.Distance(hipAnchor.position, fwdAnchor.position); if (d > 1e-4f) return Mathf.Max(0.05f, d / 0.6f); } return 1f; }
    Vector3 Curve(Vector3 a, Vector3 b, Vector3 c, Vector3 d, float u) { float u2 = u * u, u3 = u2 * u; return 0.5f * ((2f * b) + (-a + c) * u + (2f * a - 5f * b + 4f * c - d) * u2 + (-a + 3f * b - 3f * c + d) * u3); }

    Vector3 BoardPoint(float t, Vector3 seated) {
    Vector3 start = vehicle.TransformPoint(startLocal); if (t <= 0f) return start; if (t >= 1f) return seated;
    Vector3 hip = hipAnchor.position, f = Flat(fwdAnchor.position - hip), r = Flat(Vector3.Cross(Vector3.up, f)), l = -r, s = Vector3.zero; float sc = VehicleScale();
    float mf = Vector3.Dot(start - hip, f) / sc, ml = Vector3.Dot(start - hip, l) / sc;
    path[0] = start;
    path[1] = hip + f * (Mathf.Clamp(mf - 0.25f, -3.25f, -2.25f) * sc) + l * (Mathf.Clamp(ml, 1.22f, 1.62f) * sc);
    path[2] = hip + f * (-1.02f * sc) + l * (1.15f * sc);
    path[3] = hip + f * (-0.03f * sc) + l * (1.07f * sc);
    path[4] = hip + f * (-0.15f * sc) + l * (0.93f * sc);
    path[5] = Vector3.Lerp(hip + f * (-0.11f * sc) + l * (0.17f * sc), seated, 0.35f);
    path[6] = seated;
    float y0 = start.y, y1 = seated.y;
    for (int k = 1; k < 6; k++) { float frac = k / 6f; Vector3 p = path[k]; p.y = Mathf.Lerp(y0, y1, frac); path[k] = p; }
    int i = (int)(t * 6f); if (i < 0) i = 0; if (i > 5) i = 5; float u = t * 6f - i;
    return Curve(path[Mathf.Max(0, i - 1)], path[i], path[Mathf.Min(6, i + 1)], path[Mathf.Min(6, i + 2)], u);
}

    float ComputeDoorSign(Vector3 f, Vector3 r) {
        if (doorHinge == null || hipAnchor == null) return 1f;
        Vector3 doorOut = Vector3.Dot(r, doorHinge.position - hipAnchor.position) <= 0f ? -r : r;
        Vector3 off = doorHinge.childCount > 0 ? doorHinge.GetChild(0).position - doorHinge.position : doorHinge.forward * 0.1f;
        if (off.sqrMagnitude < 1e-6f) off = doorHinge.right * 0.1f;
        return Vector3.Dot(Vector3.Cross(Vector3.up, off), doorOut) < 0f ? -1f : 1f;
    }
    void SetDoor(float deg) {
        if (doorHinge == null) return;
        Vector3 up = doorHinge.parent != null ? doorHinge.parent.InverseTransformDirection(Vector3.up) : Vector3.up;
        if (up.sqrMagnitude < 1e-6f) up = Vector3.up; up.Normalize();
        doorHinge.localRotation = Quaternion.AngleAxis(deg, up) * doorRestRot;
    }

    void ResetDoor() { if (doorHinge != null && touchedDoor) doorHinge.localRotation = doorRestRot; }
    void UpdateDoor(float t) {
        if (!active || !touchedDoor || doorHinge == null) return;
        float open = Mathf.SmoothStep(0f, 1f, t / 0.28f);
        if (t > 0.68f) open *= 1f - Mathf.SmoothStep(0f, 1f, (t - 0.68f) / 0.32f);
        SetDoor(doorSign * OPEN_DEG * Mathf.Clamp01(open));
    }

    void PlayDriver(string clip, bool begin) {
        if (anim == null || string.IsNullOrEmpty(clip)) return; var st = anim[clip]; if (st == null) return;
        anim.enabled = true; anim.playAutomatically = false;
        if (!string.IsNullOrEmpty(boardClip) && boardClip != clip) { var b = anim[boardClip]; if (b != null) b.enabled = false; }
        if (!string.IsNullOrEmpty(driveClip) && driveClip != clip) { var d = anim[driveClip]; if (d != null) d.enabled = false; }
        st.enabled = true; st.weight = 1f; st.speed = 1f; anim.Play(clip, PlayMode.StopSameLayer);
        if (begin) st.time = 0f; else if (board < 1f && st.clip != null && st.clip.length > 0.001f) { float d = clip == boardClip && st.clip.length > 0.1f ? st.clip.length : BOARD; st.time = Mathf.Min(board * d, st.clip.length - 0.001f); } else st.time = 0f;
        st.enabled = true; st.weight = 1f; anim.Sample();
    }

    void CaptureSpawn() {
        if (proxy == null || anim == null || visRef == null || body == null || vehicle == null || doorHinge == null) return;
        if (!hasBasis) { visualBasis = Quaternion.Inverse(body.rotation) * visRef.rotation; visualScale = visRef.localScale; hasBasis = true; }
        if (proxy.parent != vehicle) proxy.SetParent(vehicle, false); proxy.gameObject.SetActive(true); proxy.localScale = visualScale;
        Vector3 f = Flat(fwdAnchor.position - hipAnchor.position), r = Flat(Vector3.Cross(Vector3.up, f));
        startRot = visRef.rotation; initialYaw = Quaternion.LookRotation(f, Vector3.up); proxy.rotation = startRot; proxy.position = visRef.position; startLocal = vehicle.InverseTransformPoint(visRef.position);
        doorSign = ComputeDoorSign(f, r); touchedDoor = true; SetDoor(0f); SetGuns(false);
        anim.enabled = true; anim.playAutomatically = false; anim.Stop(); board = 0f; frozen = false; clipsKnown = ResolveDriverClips() || clipsKnown; ConfigureDriver(); hasSpawn = true; active = true; PlayDriver(boardClip, true);
    }

    void Freeze() { if (!active || proxy == null || anim == null || frozen) return; anim.Sample(); anim.enabled = false; frozen = true; }

    void Restore() {
        if (!frozen || proxy == null || anim == null) return; frozen = false; if (active && !proxy.gameObject.activeSelf) proxy.gameObject.SetActive(true);
        anim.enabled = true; anim.playAutomatically = false; if (active && hasSpawn) { string clip = board < 1f ? boardClip : driveClip; if (!string.IsNullOrEmpty(clip)) PlayDriver(clip, false); }
    }

    void Deactivate() {
        if (proxy != null) proxy.gameObject.SetActive(false); if (anim != null) { anim.Stop(); anim.enabled = true; }
        if (touchedDoor) ResetDoor();
        active = false; hasSpawn = false; frozen = false; board = 1f; vehicle = null; hipAnchor = null; fwdAnchor = null; doorHinge = null; touchedDoor = false;
    }

    void LateUpdate() {
        if (visRef == null) return; EnsureProxy(); if (proxy == null || anim == null || body == null) return;
        var root = LoopSignals.Vehicle; bool veh = IsVehicle(LoopSignals.Mode); bool dead = DeathAuthority.IsDead; int rst = LoopSignals.Restarts;
        if (rst != lastRestarts) { lastRestarts = rst; Deactivate(); return; }
        if (dead) { if (active && !veh) Deactivate(); else Freeze(); return; }
        if (frozen) Restore();
        if (veh) {
            if (root == null) { if (active) Deactivate(); return; }
            if (vehicle != null && vehicle != root) { Deactivate(); return; }
            vehicle = root; if (proxy.parent != vehicle) proxy.SetParent(vehicle, false); EnsureAnchors();
            if (!active) { if (doorHinge == null) EnsureDoor(root); if (clipsKnown && hipAnchor != null && fwdAnchor != null && hipL != null && hipR != null && doorHinge != null) CaptureSpawn(); }
        } else if (active) Deactivate();
        if (!active || !hasSpawn) return;
        if (vehicle == null || hipAnchor == null || fwdAnchor == null || hipL == null || hipR == null || doorHinge == null) { Deactivate(); return; }
        Vector3 f = Flat(fwdAnchor.position - hipAnchor.position), r = Flat(Vector3.Cross(Vector3.up, f));
        if (board < 1f) { float prev = board; board += Time.deltaTime / BOARD; bool ended = prev < 1f && board >= 1f; if (board >= 1f) board = 1f; if (ended) PlayDriver(driveClip, false); }
        float t = board, smooth = Mathf.SmoothStep(0f, 1f, t);
        Quaternion currentYaw = Quaternion.LookRotation(f, Vector3.up), startWorld = currentYaw * Quaternion.Inverse(initialYaw) * startRot, target = currentYaw * visualBasis;
        Quaternion rot = board < 1f ? Quaternion.Slerp(startWorld, target, smooth) : target;
        proxy.rotation = rot; anim.Sample(); Vector3 seated = hipAnchor.position - proxy.TransformVector(HipsLocal());
        proxy.position = board < 1f ? BoardPoint(t, seated) : seated; UpdateDoor(t);
    }
}
}
