using System.Collections.Generic;
using UnityEngine;

namespace ChicagoGame
{
    public sealed class PlayerPresentation : MonoBehaviour
    {
        Transform body;
        Transform visual;
        Animation anim;
        string idleClip, walkClip, jogClip;
        string aimIdleClip, aimWalkClip, aimJogClip;
        string baseClip, upperClip;
        float aimWeight, lastShot = -999f;
        Vector3 lastPos;
        bool posValid, wasDead, wasVehicle;
        int lastRestarts = int.MinValue;

        public static void Install(GameObject body)
        {
            if (body == null) return;
            Transform v = FindVisual(body.transform);
            if (v == null) return;
            Animation a = v.GetComponent<Animation>();
            if (a == null) a = v.gameObject.AddComponent<Animation>();
            a.playAutomatically = false;
            a.cullingType = AnimationCullingType.AlwaysAnimate;
            PlayerPresentation p = body.GetComponent<PlayerPresentation>();
            if (p == null) p = body.AddComponent<PlayerPresentation>();
            p.body = body.transform;
            p.visual = v;
            p.anim = a;
            p.Prepare();
        }

        static Transform FindVisual(Transform root)
        {
            var t = root.Find("PlayerVisual");
            if (t != null) return t;
            for (int i = 0; i < root.childCount; ++i)
            {
                var c = FindVisual(root.GetChild(i));
                if (c != null) return c;
            }
            return null;
        }

        void OnEnable()
        {
            baseClip = null; upperClip = null; aimWeight = 0f; posValid = false; lastShot = -999f;
            if (anim != null)
            {
                anim.SetLayerWeight(1, 0f);
                wasDead = DeathAuthority.IsDead;
                anim.enabled = !wasDead;
            }
        }

        void Prepare()
        {
            if (anim == null) return;
            anim.Stop();
            anim.playAutomatically = false;
            var loaded = Resources.LoadAll<AnimationClip>("Generated/player/scene");
            var names = new List<string>();
            for (int i = 0; i < loaded.Length; ++i)
            {
                var c = loaded[i];
                if (c == null || c.length < 0.1f || c.name.StartsWith("__preview__")) continue;
                c.wrapMode = WrapMode.Loop;
                c.legacy = true;
                if (anim.GetClip(c.name) == null) anim.AddClip(c, c.name);
                if (!names.Contains(c.name)) names.Add(c.name);
            }
            idleClip = Resolve(names, "Idle", "idle", "IdlePose", "A_0", "0");
            walkClip = Resolve(names, "Walk", "walk", "Walking", "A_1", "1");
            jogClip = Resolve(names, "Jog", "jog", "Run", "A_2", "2");
            aimIdleClip = Resolve(names, "AimIdle", "Aim_Idle", "aim_idle", "Aim", "Aim_0", "3");
            aimWalkClip = Resolve(names, "AimWalk", "Aim_Walk", "aim_walk", "Aim_1", "4");
            aimJogClip = Resolve(names, "AimJog", "Aim_Jog", "aim_jog", "Aim_2", "5");
            if (string.IsNullOrEmpty(idleClip) && names.Count > 0) idleClip = names[0];
            SetLayer(idleClip, 0); SetLayer(walkClip, 0); SetLayer(jogClip, 0);
            SetLayer(aimIdleClip, 1); SetLayer(aimWalkClip, 1); SetLayer(aimJogClip, 1);
        }

        static string Resolve(List<string> names, params string[] wanted)
        {
            for (int w = 0; w < wanted.Length; ++w)
            {
                string want = Strip(wanted[w]);
                for (int i = 0; i < names.Count; ++i)
                    if (Strip(names[i]) == want) return names[i];
            }
            return null;
        }

        static string Strip(string s)
        {
            if (string.IsNullOrEmpty(s)) return "";
            return s.Replace("_", "").Replace("-", "").Replace(" ", "").ToLowerInvariant();
        }

        void SetLayer(string name, int layer)
        {
            if (string.IsNullOrEmpty(name)) return;
            var s = anim[name];
            if (s != null) s.layer = layer;
        }

        void Fade(string name, int layer, float fade)
        {
            if (string.IsNullOrEmpty(name) || anim.GetClip(name) == null) return;
            var s = anim[name];
            s.layer = layer;
            if (!anim.IsPlaying(name))
                anim.CrossFade(name, Mathf.Max(0.01f, fade), PlayMode.StopSameLayer);
        }

        void Update()
        {
            if (anim == null) return;
            bool dead = DeathAuthority.IsDead;
            string mode = LoopSignals.Mode;
            bool vehicle = mode != null &&
                (mode.IndexOf("Veh", System.StringComparison.OrdinalIgnoreCase) >= 0 ||
                 mode.IndexOf("Drive", System.StringComparison.OrdinalIgnoreCase) >= 0 ||
                 mode.IndexOf("Car", System.StringComparison.OrdinalIgnoreCase) >= 0);

            if (dead)
            {
                if (!wasDead)
                {
                    anim.enabled = false;
                    baseClip = null; upperClip = null; aimWeight = 0f; posValid = false; lastShot = -999f;
                    anim.SetLayerWeight(1, 0f);
                    wasDead = true;
                }
                return;
            }
            if (wasDead)
            {
                wasDead = false;
                anim.enabled = true;
                baseClip = null; upperClip = null; aimWeight = 0f; posValid = false; lastShot = -999f;
            }

            if (vehicle)
            {
                if (!wasVehicle)
                {
                    wasVehicle = true;
                    baseClip = null; upperClip = null; aimWeight = 0f; posValid = false; lastShot = -999f;
                    anim.SetLayerWeight(1, 0f);
                }
                return;
            }
            if (wasVehicle)
            {
                wasVehicle = false;
                baseClip = null; upperClip = null; aimWeight = 0f; posValid = false; lastShot = -999f;
            }

            if (visual == null || !visual.gameObject.activeInHierarchy)
            {
                posValid = false; baseClip = null; upperClip = null; aimWeight = 0f; lastShot = -999f;
                anim.SetLayerWeight(1, 0f);
                return;
            }
            if (string.IsNullOrEmpty(idleClip) && string.IsNullOrEmpty(walkClip) && string.IsNullOrEmpty(jogClip)) return;

            if (LoopSignals.Restarts != lastRestarts)
            {
                lastRestarts = LoopSignals.Restarts;
                anim.Stop();
                baseClip = null; upperClip = null; aimWeight = 0f; posValid = false; lastShot = -999f;
                anim.SetLayerWeight(1, 0f);
            }
            if (body == null) return;

            Vector3 pos = body.position;
            float dt = Time.unscaledDeltaTime;
            float speed = 0f;
            if (posValid && dt > 0.0001f)
            {
                speed = Vector2.Distance(new Vector2(pos.x - lastPos.x, pos.z - lastPos.z), Vector2.zero) / dt;
                if (speed > 18f) speed = 0f;
            }
            lastPos = pos; posValid = true;

            if (LoopInput.Pressed(KeyCode.Mouse0)) lastShot = Time.unscaledTime;
            bool aiming = LoopInput.Held(KeyCode.Mouse1) || Time.unscaledTime - lastShot < 0.45f;
            bool moving = speed > 0.35f;
            bool shift = LoopInput.Held(KeyCode.LeftShift);

            string wantBase = moving ? (shift ? jogClip : walkClip) : idleClip;
            if (!string.IsNullOrEmpty(wantBase) && wantBase != baseClip)
            {
                Fade(wantBase, 0, 0.16f);
                baseClip = wantBase;
            }

            float cycle = moving ? Mathf.Clamp(speed / 3.2f, 0.55f, 1.45f) : 1f;
            if (baseClip == jogClip) cycle *= 0.78f;
            if (cycle < 0.45f) cycle = 0.45f;

            if (!string.IsNullOrEmpty(baseClip))
            {
                var s = anim[baseClip];
                if (s != null) s.speed = cycle;
            }

            aimWeight = Mathf.MoveTowards(aimWeight, aiming ? 1f : 0f, Time.unscaledDeltaTime * 4.5f);
            anim.SetLayerWeight(1, aimWeight);

            if (aimWeight > 0.01f)
            {
                string wantUpper = moving ? (shift ? aimJogClip : aimWalkClip) : aimIdleClip;
                if (!string.IsNullOrEmpty(wantUpper) && wantUpper != upperClip)
                {
                    Fade(wantUpper, 1, 0.16f);
                    upperClip = wantUpper;
                }
                if (!string.IsNullOrEmpty(upperClip))
                {
                    var s = anim[upperClip];
                    if (s != null) s.speed = moving ? cycle : 1f;
                }
            }
        }
    }
}
