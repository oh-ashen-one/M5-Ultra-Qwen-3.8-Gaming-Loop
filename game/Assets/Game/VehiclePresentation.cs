using UnityEngine;

namespace ChicagoGame
{
    // Visual-only driver proxy. Reads LoopSignals/DeathAuthority, never writes
    // to the physical player, the vehicle transform, camera, colliders or the
    // shared foot Animation. Pure presentation; control authority untouched.
    public sealed class VehiclePresentation : MonoBehaviour
    {
        const float BOARD = 0.8f;      // matches original Board clip length
        const float DOOR = 0.55f;      // left-door bias during entry, metres

        static string Strip(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("_", "").Replace("-", "").Replace(" ", "").ToLowerInvariant();
        }

        static Transform Find(Transform r, string w)
        {
            if (r == null) return null;
            if (Strip(r.name) == Strip(w)) return r;
            for (int i = 0; i < r.childCount; ++i)
            {
                var c = Find(r.GetChild(i), w);
                if (c != null) return c;
            }
            return null;
        }

        // Root transform whose facing axis we retain; never assumed to be +Z.
        Transform body, visRef, hipL, hipR, elbL, elbR, hipAnchor, fwdAnchor;
        GameObject proxy;
        Animation anim;
        Renderer[] guns;

        bool wasVeh, active, hasSpawn;
        int lastRestarts = int.MinValue;
        float board = 1f;
        Vector3 startPos;
        Quaternion startRot;
        float face0Ang;

        public static void Install(GameObject body)
        {
            if (body == null) return;
            var p = body.GetComponent<VehiclePresentation>();
            if (p == null) p = body.AddComponent<VehiclePresentation>();
            p.body = body.transform;
            p.visRef = Find(body.transform, "PlayerVisual");   // exact reference convention
            p.lastRestarts = LoopSignals.Restarts;
        }

        // Build the proxy once by cloning the visible visual subtree. This
        // keeps the imported 270/scale rig and the Animation instance intact
        // without cloning the player or its scripts.
        void EnsureProxy()
        {
            var root = LoopSignals.Vehicle;
            if (proxy != null || visRef == null || root == null) return;
            var clone = Object.Instantiate(visRef.gameObject, root, false);
            clone.name = "DriverVisual";
            proxy = clone;
            anim = clone.GetComponent<Animation>();
            if (anim != null)
            {
                anim.playAutomatically = false;
                anim.cullingType = AnimationCullingType.AlwaysAnimate;
                Configure(anim, "Board", WrapMode.Once);
                Configure(anim, "Drive", WrapMode.Loop);
            }
            hipL = Find(clone.transform, "pivot_hip_l");
            hipR = Find(clone.transform, "pivot_hip_r");
            elbL = Find(clone.transform, "pivot_elbow_l");
            elbR = Find(clone.transform, "pivot_elbow_r");
            var rl = clone.GetComponentsInChildren<Renderer>(true);
            var gl = new System.Collections.Generic.List<Renderer>();
            foreach (var r in rl)
            {
                string n = Strip(r.name);
                if (n == "pistolslide" || n == "pistolgrip") gl.Add(r);
            }
            guns = gl.ToArray();
            SetGuns(false);
            proxy.SetActive(false);
            active = false;
        }

        // Explicit AnimationState wrap: asset wrap alone reset one frame early.
        static void Configure(Animation a, string clip, WrapMode wm)
        {
            if (a == null || string.IsNullOrEmpty(clip)) return;
            var st = a[clip];
            if (st == null)
            {
                var c = Resources.Load<AnimationClip>("Generated/player/scene/" + clip);
                if (c != null && a.GetClip(clip) == null) a.AddClip(c, clip);
                st = a[clip];
                if (st == null) return;
                c.wrapMode = wm;   // Board/Drive are unused by foot, no conflict
            }
            st.wrapMode = wm;
            st.enabled = false;
            st.speed = 1f;
        }

        void SetGuns(bool on)
        {
            if (guns == null) return;
            for (int i = 0; i < guns.Length; ++i) guns[i].enabled = on;
        }

        static bool IsVehicle(string m)
        {
            return !string.IsNullOrEmpty(m) && m.IndexOf("Veh", System.StringComparison.OrdinalIgnoreCase) >= 0;
        }

        void MidWorld(out Vector3 h, out Vector3 e)
        {
            h = Vector3.zero; e = Vector3.zero;
            if (hipL && hipR) h = (hipL.position + hipR.position) * 0.5f;
            if (elbL && elbR) e = (elbL.position + elbR.position) * 0.5f;
        }

        static float Ang(Vector3 v) { return Mathf.Atan2(v.x, v.z); }
        static Vector3 Flat(Vector3 v) { v.y = 0f; return v.sqrMagnitude > 1e-6f ? v.normalized : Vector3.forward; }

        // Resolve a rotation whose measured elbow-forward equals the target dir.
        // Two samples: the rig is rigid under root yaw, so the residual is a
        // single yaw add; no joint posing, no +Z assumption.
        Quaternion AlignTo(Vector3 targetDir)
        {
            var a = Flat(targetDir);
            proxy.rotation = Quaternion.LookRotation(a, Vector3.up);
            if (anim != null) anim.Sample();
            MidWorld(out var h, out var e);
            float need = Ang(a) - Ang(Flat(e - h));
            var r = Quaternion.Euler(0f, need * Mathf.Rad2Deg, 0f) * proxy.rotation;
            proxy.rotation = r;
            return r;
        }

        // Snap hips-mid onto the anchor with rotation r, measured not assumed.
        Vector3 SeatedPos(Quaternion r, Vector3 targetDir)
        {
            MidWorld(out var h, out _);
            Vector3 local = Quaternion.Inverse(r) * (h - proxy.position);
            return hipAnchor.position - r * local;
        }

        void CaptureSpawn()
        {
            proxy.SetActive(true);
            proxy.transform.position = visRef.position;       // exact world pose of visible courier
            proxy.transform.rotation = visRef.rotation;
            startPos = visRef.position;
            startRot = visRef.rotation;
            SetGuns(false);
            if (anim != null)
            {
                anim.Stop();
                if (anim["Board"] != null) anim["Board"].time = 0f;
                anim.Play("Board", PlayMode.StopSameLayer);
                anim.Sample();
            }
            MidWorld(out var h, out var e);
            face0Ang = Ang(Flat(e - h));
            hasSpawn = true;
            board = 0f;
        }

        void Deactivate()
        {
            if (proxy != null) proxy.SetActive(false);
            if (anim != null) anim.Stop();
            active = false;
            hasSpawn = false;
            board = 1f;
        }

        void LateUpdate()
        {
            if (visRef == null) return;
            EnsureProxy();
            if (proxy == null || anim == null) return;

            bool veh = IsVehicle(LoopSignals.Mode);
            bool dead = DeathAuthority.IsDead;
            int rst = LoopSignals.Restarts;

            if (rst != lastRestarts) { lastRestarts = rst; Deactivate(); wasVeh = veh; return; }

            // Freeze on death: never board while dead; keep frozen seated visual.
            if (dead) { wasVeh = veh; return; }

            if (veh && !wasVeh)
            {
                if (hipAnchor == null || fwdAnchor == null)
                {
                    var root = LoopSignals.Vehicle;
                    hipAnchor = Find(root, "driver_hip_anchor");
                    fwdAnchor = Find(root, "driver_forward_anchor");
                }
                if (hipAnchor && fwdAnchor) CaptureSpawn();
                active = veh && hipAnchor && fwdAnchor;
            }
            else if (!veh && wasVeh) Deactivate();
            wasVeh = veh;

            if (!active || !hasSpawn) return;

            // Car body forward from two real world anchors (handles half-turn).
            Vector3 carF = Flat(fwdAnchor.position - hipAnchor.position);
            Vector3 carR = Flat(Vector3.Cross(Vector3.up, carF));   // left-side bias

            if (board < 1f)
            {
                board += Time.deltaTime / BOARD;
                if (board >= 1f)
                {
                    board = 1f;
                    if (anim["Drive"] != null) anim["Drive"].time = 0f;
                    anim.Play("Drive", PlayMode.StopSameLayer);
                }
            }

            float t = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(board));
            float wantAng = Mathf.LerpAngle(face0Ang, Ang(carF), t);
            var r = AlignTo(new Vector3(Mathf.Sin(wantAng), 0f, Mathf.Cos(wantAng)));

            Vector3 seated = SeatedPos(r, carF);
            if (board < 1f)
            {
                // Bias toward the driver-side door while entering, then settle.
                Vector3 door = seated - carR * (DOOR * (1f - t));
                proxy.transform.position = Vector3.Lerp(startPos, door, t);
            }
            else
            {
                proxy.transform.position = seated;
            }
        }
    }
}
