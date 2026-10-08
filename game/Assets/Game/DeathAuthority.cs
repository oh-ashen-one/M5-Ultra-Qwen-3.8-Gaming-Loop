using UnityEngine;

namespace ChicagoGame
{
    // ---------------------------------------------------------------------
    // Single authoritative player-death decision for the whole loop.
    //
    // Every chapter (courier delivery, east dead-drop, relay chain, runner
    // interception) and every input channel (foot stride, car throttle, door
    // boarding, trigger pull) asks THIS component whether the courier is
    // standing, instead of inventing its own failure wording or quietly
    // carrying on. The whole rule set is one shared evaluation:
    //
    //  * Health <= 0 IS death. IsDead reads live LoopSignals.Health on every
    //    call, so the zero-health frame is already lost even when this
    //    component's Update has not run yet: a dead courier can bank no
    //    objective, stride, door or shot, whatever order Unity happens to run
    //    the chapter scripts in.
    //  * Death latches, and ONLY a real LoopSignals.Restarts change - the
    //    ordinary R reset - releases it. There is no positive-health grace:
    //    nothing in this loop heals, so health drifting back above zero with no
    //    R must never resurrect input. The Restarts edge is sampled inside the
    //    decision itself, so a reset that restores health and re-spawns before
    //    this Update resumes play on the very next read instead of stranding
    //    the courier dead for an extra frame.
    //
    // This authority only decides. It never writes health, Restarts, Shots,
    // Hits, PursuitLevel, Mode/Mission, objective completion, input or camera
    // state, and it owns no presentation: the existing MissionBoard renders the
    // failure, so no banner, font, material or primitive is created here.
    // ---------------------------------------------------------------------
    [DefaultExecutionOrder(-40000)]
    public sealed class DeathAuthority : MonoBehaviour
    {
        static DeathAuthority inst;

        bool latched;
        int lastRestarts;
        Transform anchor;
        Camera view;

        // ---- public authority -------------------------------------------------

        /// <summary>
        /// True when the courier may not act: the death latch is set, or live
        /// health is spent. The latch clears only on a real Restarts change.
        /// </summary>
        public static bool IsDead
        {
            get { var d = inst; return d != null ? d.Decide() : LoopSignals.Health <= 0f; }
        }

        public static bool HasAuthority { get { return inst != null; } }

        /// <summary>True once a lethal frame has been latched since the last R.</summary>
        public static bool Latched { get { var d = inst; return d != null && d.latched; } }

        /// <summary>Installation anchors, read-only; this component never moves them.</summary>
        public static Transform Player { get { return inst != null ? inst.anchor : null; } }
        public static Camera View { get { return inst != null ? inst.view : null; } }

        /// <summary>
        /// Called by whoever inflicts lethal damage. Idempotent: it re-runs the
        /// one shared decision and adds no bookkeeping of its own.
        /// </summary>
        public static void ReportDeath() { var d = inst; if (d != null) d.Decide(); }

        /// <summary>Live health, read straight from the signal - no fake default.</summary>
        public static float CurrentHealth() { return LoopSignals.Health; }

        // ---- setup ------------------------------------------------------------

        /// <summary>
        /// Adopt or refresh the singleton. Pure bookkeeping: no scene object,
        /// material or font is created and nothing on the camera is altered.
        /// </summary>
        public static void Install(GameObject player, Camera cam)
        {
            var d = inst;
            if (d == null)
            {
                var go = new GameObject("DeathAuthority");
                go.transform.SetParent(null, false);
                go.transform.position = Vector3.zero;
                go.transform.rotation = Quaternion.identity;
                d = go.AddComponent<DeathAuthority>();   // Awake adopts inst
                if (d == null) return;
            }
            if (d.anchor == null && player != null) d.anchor = player.transform;
            if (d.view == null && cam != null) d.view = cam;
            d.Decide();                    // align the Restarts baseline at once
        }

        void Awake()
        {
            if (inst != null && inst != this) { Destroy(gameObject); return; }
            inst = this;
            lastRestarts = LoopSignals.Restarts;
        }

        void OnDestroy() { if (inst == this) inst = null; }

        // ---- the one decision --------------------------------------------------

        /// <summary>
        /// The single evaluation behind IsDead, ReportDeath and Update, so no
        /// caller can ever get a different answer than the authority itself.
        /// </summary>
        bool Decide()
        {
            int r = LoopSignals.Restarts;
            if (r != lastRestarts)
            {
                // Ordinary R: the same reset that re-spawns the courier, the
                // coupe and every chapter also restores health. This edge is
                // the only thing that ever clears the latch.
                lastRestarts = r;
                latched = false;
            }

            if (LoopSignals.Health <= 0f) latched = true;   // same-frame death
            return latched || LoopSignals.Health <= 0f;
        }

        void Update() { Decide(); }        // keeps the latch warm for readers
    }
}
