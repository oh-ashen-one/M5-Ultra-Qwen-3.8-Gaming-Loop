using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    // ---------------------------------------------------------------------
    // Single authoritative player-death decision for the whole loop.
    //
    // Every chapter (courier delivery, east dead-drop, relay chain, runner
    // interception) and every input channel (foot stride, car throttle, door
    // boarding, trigger pull) asks THIS component whether the courier is
    // standing instead of inventing its own failure wording or quietly
    // carrying on. Rules held here:
    //
    //  * Health <= 0 IS death, and it wins the frame it happens: IsDead reads
    //    live signal health, so a zero-health frame can never be spent on an
    //    objective, a stride, a door or a shot regardless of the order Unity
    //    happens to run the chapter scripts in.
    //  * Death is latched until an ordinary R reset (Restarts change). A later
    //    update order, or a legacy mission that is already "complete", cannot
    //    resurrect input or hand out a new chapter to a dead courier.
    //  * Death never heals, never rewinds a receipt the living player already
    //    earned, never fabricates completion and never erases a more truthful
    //    failure reason (a missing prefab stays a missing prefab).
    //  * One unmistakable failure/reset banner is owned here so the depleted
    //    health state is always visible, on top of whatever the chapters show.
    // ---------------------------------------------------------------------
    [DefaultExecutionOrder(-40000)]
    public class DeathAuthority : MonoBehaviour
    {
        public const string FailLine1 = "HEALTH DEPLETED";
        public const string FailLine2 = "MISSION FAILED";
        public const string FailLine3 = "Press R to reset";
        public const string FailText = FailLine1 + "\n" + FailLine2 + "\n" + FailLine3;

        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;

        // Fallback only: an R reset restores health and bumps Restarts in the
        // same call, so normally the Restarts edge clears the latch instantly.
        const float RESTORE_GRACE = 0.25f;

        static DeathAuthority inst;

        static readonly Vector3 BANNER_POS = new Vector3(0f, 0.33f, 1.6f);

        Transform player;
        Camera cam;
        bool latched;
        float restoreTimer = -1f;
        int lastRestarts;

        GameObject banner;
        TextMesh bannerText;
        Material bannerCardMat;

        // ---- public authority -------------------------------------------------

        /// <True> when the courier may not act: latch set, or live health spent.
        public static bool IsDead
        {
            get
            {
                if (inst != null && inst.latched) return true;
                return CurrentHealth() <= 0f;
            }
        }

        public static bool HasAuthority { get { return inst != null; } }

        public static bool BannerVisible
        {
            get { return inst != null && inst.banner != null && inst.banner.activeSelf; }
        }

        public static float CurrentHealth()
        {
            try { return LoopSignals.Health; }
            catch { return 100f; }   // unreadable signal must not freeze play
        }

        /// <summary>
        /// Called by whoever inflicts lethal damage. Idempotent; it only ever
        /// downgrades the run (never heals, never completes anything).
        /// </summary>
        public static void ReportDeath()
        {
            var d = inst;
            if (d == null) return;
            if (!d.latched && CurrentHealth() <= 0f)
            {
                d.latched = true;
                d.restoreTimer = -1f;
                d.DeclareFailure();
            }
            d.ApplyVisibility();
        }

        // ---- setup ------------------------------------------------------------

        public static void Install(GameObject player, Camera cam)
        {
            if (inst != null) { inst.AttachCamera(cam); return; }
            var go = new GameObject("DeathAuthority");
            go.transform.SetParent(null, false);
            go.transform.position = Vector3.zero;
            go.transform.rotation = Quaternion.identity;
            var d = go.AddComponent<DeathAuthority>();   // Awake adopts inst
            if (d == null) return;
            d.player = player != null ? player.transform : null;
            d.AttachCamera(cam);
            d.lastRestarts = ReadInt("Restarts");
            d.BuildBanner();
        }

        void Awake()
        {
            if (inst != null && inst != this) { Destroy(gameObject); return; }
            inst = this;
            lastRestarts = ReadInt("Restarts");
        }

        void OnDestroy()
        {
            if (inst == this) inst = null;
            if (bannerCardMat != null) Destroy(bannerCardMat);
            bannerCardMat = null;
        }

        void AttachCamera(Camera c)
        {
            if (cam == null && c != null)
            {
                cam = c;
                if (banner == null) BuildBanner();
            }
        }

        void BuildBanner()
        {
            if (banner != null || cam == null) return;

            var go = new GameObject("DeathBanner");
            go.transform.SetParent(cam.transform, false);
            go.transform.localPosition = BANNER_POS;
            go.transform.localRotation = Quaternion.identity;
            go.transform.localScale = Vector3.one;

            // Dark slab behind the type, one slice further from the lens than the
            // glyphs (same construction as the existing mission boards) so the
            // message reads against any street backdrop.
            var card = GameObject.CreatePrimitive(PrimitiveType.Cube);
            card.name = "DeathCard";
            card.transform.SetParent(go.transform, false);
            card.transform.localPosition = new Vector3(0f, -0.175f, 0.025f);
            card.transform.localRotation = Quaternion.identity;
            card.transform.localScale = new Vector3(1.72f, 0.44f, 0.01f);
            var col = card.GetComponent<Collider>();
            if (col != null) Destroy(col);          // never blocks aim or camera

            var rd = card.GetComponent<Renderer>();
            if (rd != null)
            {
                bannerCardMat = new Material(Shader.Find("Standard"))
                {
                    color = new Color(0.045f, 0.012f, 0.016f),
                    hideFlags = HideFlags.HideAndDontSave
                };
                bannerCardMat.EnableKeyword("_EMISSION");
                bannerCardMat.SetColor("_EmissionColor", new Color(0.05f, 0f, 0f));
                rd.sharedMaterial = bannerCardMat;
            }

            bannerText = go.AddComponent<TextMesh>();
            bannerText.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            bannerText.fontSize = 46;
            bannerText.characterSize = 0.0155f;
            bannerText.anchor = TextAnchor.UpperCenter;
            bannerText.alignment = TextAlignment.Center;
            bannerText.color = new Color(1f, 0.26f, 0.2f);
            bannerText.text = FailText;

            banner = go;
            banner.SetActive(false);
        }

        // ---- per-frame authority ---------------------------------------------

        void Update()
        {
            int r = ReadInt("Restarts");
            if (r != lastRestarts)
            {
                // Ordinary R: the same reset that re-spawns the courier, the coupe
                // and every chapter also restores health, so the failure latch and
                // its banner clear here and input-driven play resumes.
                lastRestarts = r;
                latched = false;
                restoreTimer = -1f;
            }

            if (CurrentHealth() <= 0f)
            {
                restoreTimer = -1f;
                if (!latched)
                {
                    latched = true;
                    DeclareFailure();
                }
            }
            else if (latched)
            {
                // Nothing in this loop heals a dead courier except the R reset; if
                // health has genuinely come back, release the latch even when the
                // Restarts edge was missed by script order.
                if (restoreTimer < 0f) restoreTimer = 0f;
                restoreTimer += Time.deltaTime;
                if (restoreTimer >= RESTORE_GRACE)
                {
                    latched = false;
                    restoreTimer = -1f;
                }
            }

            ApplyVisibility();
        }

        void DeclareFailure()
        {
            // Only an unfinished legacy courier mission turns into "failed"
            // because of death. A parcel the living courier actually delivered
            // keeps its completed receipt: no faked rewind of history.
            if (ReadStr("Mission") == "active") Set("Mission", "failed");
            ApplyVisibility();
        }

        void ApplyVisibility()
        {
            bool dead = IsDead;
            if (banner == null) return;
            if (dead && bannerText != null) bannerText.text = FailText;
            if (banner.activeSelf != dead) banner.SetActive(dead);
        }

        // ---- tolerant signal access (mirrors the existing modules) ------------

        static void Set(string name, object value)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            if (f == null && p == null) return;
            var type = f != null ? f.FieldType : p.PropertyType;
            if (type.IsEnum && value != null) value = Enum.Parse(type, value.ToString(), true);
            if (f != null) f.SetValue(null, value);
            else if (p != null && p.CanWrite) p.SetValue(null, value);
        }

        static int ReadInt(string name)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            try
            {
                if (f != null) return Convert.ToInt32(f.GetValue(null));
                if (p != null && p.CanRead) return Convert.ToInt32(p.GetValue(null));
            }
            catch { }
            return 0;
        }

        static string ReadStr(string name)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            try
            {
                if (f != null) return f.GetValue(null) as string;
                if (p != null && p.CanRead) return p.GetValue(null) as string;
            }
            catch { }
            return null;
        }
    }
}
