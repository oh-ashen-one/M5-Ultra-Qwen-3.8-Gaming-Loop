using System.Collections.Generic;
using UnityEngine;

namespace ChicagoGame {
public sealed class VehiclePresentation : MonoBehaviour {
    const float BOARD = 0.8f;
    const float DOOR = 0.55f;
    const string RES = "Generated/player/scene";

    static string Strip(string s) { return string.IsNullOrEmpty(s) ? "" : s.Replace("_", "").Replace("-", "").Replace(" ", "").ToLowerInvariant(); }
    static Transform Find(Transform r, string w) { if (r == null) return null; if (Strip(r.name) == Strip(w)) return r; for (int i = 0; i < r.childCount; ++i) { var c = Find(r.GetChild(i), w); if (c != null) return c; } return null; }

    Transform body, visRef, hipL, hipR, hipAnchor, fwdAnchor, proxy, vehicle;
    Animation anim; Renderer[] guns; string boardClip, driveClip;
    Quaternion visualBasis = Quaternion.identity; Vector3 visualScale = Vector3.one;
    bool hasBasis, active, hasSpawn, frozen, clipsKnown;
    int lastRestarts = int.MinValue; float board = 1f; Vector3 startLocal; Quaternion startRot = Quaternion.identity;

    public static void Install(GameObject body) {
        if (body == null) return;
        var p = body.GetComponent<VehiclePresentation>(); if (p == null) p = body.AddComponent<VehiclePresentation>();
        p.body = body.transform; p.visRef = Find(body.transform, "PlayerVisual"); p.lastRestarts = LoopSignals.Restarts;
    }

    void EnsureProxy() {
        if (!hasBasis && visRef != null && body != null) { visualBasis = Quaternion.Inverse(body.rotation) * visRef.rotation; visualScale = visRef.localScale; hasBasis = true; }
        var root = LoopSignals.Vehicle; if (proxy != null) { if (root != null && proxy.parent != root) proxy.SetParent(root, false); return; }
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
        ConfigureState(boardClip, WrapMode.Once); ConfigureState(driveClip, WrapMode.Loop); anim.Stop();
    }
    void ConfigureState(string clip, WrapMode wm) { if (anim == null || string.IsNullOrEmpty(clip)) return; var st = anim[clip]; if (st == null) return; st.layer = 0; st.weight = 1f; st.speed = 1f; st.wrapMode = wm; st.enabled = false; }
    void SetGuns(bool on) { if (guns == null) return; for (int i = 0; i < guns.Length; ++i) guns[i].enabled = on; }
    static bool IsVehicle(string m) { return !string.IsNullOrEmpty(m) && m.IndexOf("Veh", System.StringComparison.OrdinalIgnoreCase) >= 0; }
    Vector3 HipsLocal() { return hipL && hipR && proxy ? (proxy.InverseTransformPoint(hipL.position) + proxy.InverseTransformPoint(hipR.position)) * 0.5f : Vector3.zero; }
    static Vector3 Flat(Vector3 v) { v.y = 0f; return v.sqrMagnitude > 1e-6f ? v.normalized : Vector3.forward; }
    void EnsureAnchors() { if (vehicle == null) return; if (hipAnchor == null) hipAnchor = Find(vehicle, "driver_hip_anchor"); if (fwdAnchor == null) fwdAnchor = Find(vehicle, "driver_forward_anchor"); }

    void PlayDriver(string clip, bool begin) {
        if (anim == null || string.IsNullOrEmpty(clip)) return; var st = anim[clip]; if (st == null) return;
        anim.enabled = true; anim.playAutomatically = false;
        if (!string.IsNullOrEmpty(boardClip) && boardClip != clip) { var b = anim[boardClip]; if (b != null) b.enabled = false; }
        if (!string.IsNullOrEmpty(driveClip) && driveClip != clip) { var d = anim[driveClip]; if (d != null) d.enabled = false; }
        st.enabled = true; st.weight = 1f; st.speed = 1f; anim.Play(clip, PlayMode.StopSameLayer);
        if (begin) st.time = 0f; else if (board < 1f && st.clip != null && st.clip.length > 0.001f) { float d = clip == boardClip && st.clip.length > 0.1f ? st.clip.length : BOARD; st.time = Mathf.Min(board * d, st.clip.length - 0.001f); } else if (!begin) st.time = 0f;
        st.enabled = true; st.weight = 1f; anim.Sample();
    }

    void CaptureSpawn() {
        if (proxy == null || anim == null || visRef == null || body == null || vehicle == null) return;
        if (!hasBasis) { visualBasis = Quaternion.Inverse(body.rotation) * visRef.rotation; visualScale = visRef.localScale; hasBasis = true; }
        if (proxy.parent != vehicle) proxy.SetParent(vehicle, false); proxy.gameObject.SetActive(true); proxy.localScale = visualScale;
        startRot = visRef.rotation; proxy.rotation = startRot; proxy.position = visRef.position; startLocal = vehicle.InverseTransformPoint(visRef.position);
        SetGuns(false); anim.enabled = true; anim.playAutomatically = false; anim.Stop(); board = 0f; frozen = false;
        clipsKnown = ResolveDriverClips() || clipsKnown; ConfigureDriver(); hasSpawn = true; active = true; PlayDriver(boardClip, true);
    }

    void Freeze() { if (!active || proxy == null || anim == null || frozen) return; anim.Sample(); anim.enabled = false; frozen = true; }
    void Restore() {
        if (!frozen || proxy == null || anim == null) return; frozen = false; if (active && !proxy.gameObject.activeSelf) proxy.gameObject.SetActive(true);
        anim.enabled = true; anim.playAutomatically = false; if (active && hasSpawn) { string clip = board < 1f ? boardClip : driveClip; if (!string.IsNullOrEmpty(clip)) PlayDriver(clip, false); }
    }
    void Deactivate() {
        if (proxy != null) proxy.gameObject.SetActive(false); if (anim != null) { anim.Stop(); anim.enabled = true; }
        active = false; hasSpawn = false; frozen = false; board = 1f; vehicle = null; hipAnchor = null; fwdAnchor = null;
    }

    void LateUpdate() {
        if (visRef == null) return; EnsureProxy(); if (proxy == null || anim == null || body == null) return;
        var root = LoopSignals.Vehicle; bool veh = IsVehicle(LoopSignals.Mode); bool dead = DeathAuthority.IsDead; int rst = LoopSignals.Restarts;
        if (rst != lastRestarts) { lastRestarts = rst; Deactivate(); return; }
        if (dead) { if (active && !veh) Deactivate(); else Freeze(); return; }
        if (frozen) Restore();
        if (veh) {
            if (root == null) { if (active) Deactivate(); return; }
            if (vehicle != null && vehicle != root) Deactivate(); vehicle = root;
            if (proxy.parent != vehicle) proxy.SetParent(vehicle, false); EnsureAnchors();
            if (!active) { if (clipsKnown && hipAnchor != null && fwdAnchor != null && hipL != null && hipR != null) CaptureSpawn(); }
            else if (hipAnchor == null || fwdAnchor == null) { hipAnchor = fwdAnchor = null; EnsureAnchors(); if (hipAnchor == null || fwdAnchor == null) { Deactivate(); return; } }
        } else if (active) Deactivate();
        if (!active || !hasSpawn) return;
        if (vehicle == null || hipAnchor == null || fwdAnchor == null || hipL == null || hipR == null) { Deactivate(); return; }
        Vector3 carF = Flat(fwdAnchor.position - hipAnchor.position); Vector3 carR = Flat(Vector3.Cross(Vector3.up, carF));
        if (board < 1f) { var bs = anim[boardClip]; float d = bs != null && bs.clip != null && bs.clip.length > 0.1f ? bs.clip.length : BOARD; board += Time.deltaTime / d; if (board >= 1f) { board = 1f; PlayDriver(driveClip, false); } }
        float t = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(board)); Quaternion target = Quaternion.LookRotation(carF, Vector3.up) * visualBasis;
        Quaternion rot = board < 1f ? Quaternion.Slerp(startRot, target, t) : target; proxy.rotation = rot; anim.Sample();
        Vector3 localH = HipsLocal(); proxy.rotation = rot; Vector3 seated = hipAnchor.position - proxy.TransformVector(localH);
        if (board < 1f) { Vector3 enterStart = vehicle.TransformPoint(startLocal); proxy.position = Vector3.Lerp(enterStart, seated - carR * (DOOR * (1f - t)), t); } else proxy.position = seated;
    }
} }
