using UnityEngine;

namespace ChicagoGame
{
    [DefaultExecutionOrder(100)]
    public class InterceptionMission : MonoBehaviour
    {
        public bool Active, Complete, Failed;
        public int Stopped, Escaped, Spawned;
        public string Objective;

        // ---- death integration (InterceptionMission) ------------------------
        // DeathAuthority owns the single death decision; this chapter only
        // freezes, reports and refuses to arm, receive, spawn, score or
        // complete. FailReason keeps a genuine failure this chapter recorded
        // first - a runner that really crossed the line, a missing prefab - so
        // a lethal hit that lands afterwards reports that more specific reason
        // instead of overwriting history. Nothing here writes health,
        // Restarts, shots or input.
        public string FailReason;
        string objectiveBeforeDeath;
        bool deathHeld;

        /// <summary>True while the courier is down: the freeze the physics and
        /// late-presentation paths must both honour, even in a frame where this
        /// file's Update has not run yet.</summary>
        bool Down { get { return deathHeld || DeathAuthority.IsDead; } }

        static InterceptionMission _inst;
        GameObject player; Camera cam; RelaySequence relay;
        int lastRestarts;
        float armedAt; bool receiptDone;
        GameObject[] runners = new GameObject[3];
        RivalAgent[] agents = new RivalAgent[3];
        Rigidbody[] bodies = new Rigidbody[3];
        bool[] resolved = new bool[3];

        const float ESCAPE_X = 58f, RUN_SPEED = 1.6f, RECEIPT = 3f;
        static readonly Vector3[] SPAWN = {
            new Vector3(24, .2f, 22), new Vector3(24, .2f, 18), new Vector3(24, .2f, 14)
        };
        static readonly float[] STAGGER = { 0f, 6f, 12f };

        public static void Install(GameObject player, Camera cam)
        {
            var go = new GameObject("InterceptionMission");
            _inst = go.AddComponent<InterceptionMission>();
            _inst.player = player; _inst.cam = cam;
            _inst.relay = Object.FindObjectOfType<RelaySequence>();
            _inst.lastRestarts = LoopSignals.Restarts;
        }

        void Update()
        {
            if (LoopSignals.Restarts != lastRestarts)
            {
                // Ordinary R is the only event that ever releases the
                // DeathAuthority latch, so the same edge has to clear this
                // chapter's own freeze and destroy every temporary runner: a
                // fresh loop inherits neither a held board nor a downed
                // courier's frozen escort.
                lastRestarts = LoopSignals.Restarts;
                Cleanup();
                return;
            }

            // Death outranks the whole interception, read before anything can
            // be armable: while the courier is down the finished relay cannot
            // activate this chapter, the receipt is not banked, no runner
            // spawns, no stop or completion is scored and no escape is
            // recorded. Genuine earlier receipts - stops, an escape really
            // clocked, Spawned, an earned Complete - stay exactly as he left
            // them; only the visible objective reports the failure.
            if (DeathAuthority.IsDead) { HoldForDeath(); return; }
            ReleaseDeath();

            if (!Active)
            {
                if (relay && relay.AllComplete) { Active = true; armedAt = Time.time; UpdateObj(); }
                return;
            }
            if (!receiptDone)
            {
                Objective = "INTERCEPT RUNNERS 0/3\nMove to aim; Mouse0 fire\nStopped 0 / Escaped 0\nRelay complete | R reset";
                if (Time.time - armedAt < RECEIPT) return;
            }
            if (Complete || Failed) return;
            // Second live read of the same authority: a lethal hit landing
            // inside this very frame, after the gate above, banks neither the
            // receipt nor a stop, spawn or completion. Death wins
            // simultaneous objective input. Healthy pacing is untouched -
            // the receipt still closes on the same RECEIPT deadline.
            if (DeathAuthority.IsDead) { HoldForDeath(); return; }
            receiptDone = true;
            for (int i = 0; i < 3; i++)
                if (runners[i] == null && Time.time - armedAt >= RECEIPT + STAGGER[i]) SpawnRunner(i);
            for (int i = 0; i < 3; i++)
            {
                if (resolved[i] || agents[i] == null) continue;
                if (!agents[i].alive && agents[i].hp <= 0)
                { resolved[i] = true; Stopped++; FreezeBody(i); }
            }
            if (Stopped >= 3 && Escaped == 0) { Complete = true; FreezeAll(); }
            UpdateObj();
        }

        void FixedUpdate()
        {
            // Physics honours the freeze: a downed courier drives no runner,
            // so nothing can crawl across the line inside a fixed step that no
            // Update ever adjudicated. The Restarts edge ends the hold.
            if (!Active || !receiptDone || Complete || Failed || Down) return;
            for (int i = 0; i < 3; i++)
            {
                if (resolved[i] || bodies[i] == null) continue;
                var rb = bodies[i];
                float dist = RUN_SPEED * Time.fixedDeltaTime;
                var hits = rb.SweepTestAll(Vector3.right, dist);
                bool blocked = false;
                foreach (var h in hits)
                {
                    if (h.transform.root == rb.transform.root) continue;
                    if (h.normal.y > 0.5f) continue;
                    blocked = true; break;
                }
                Vector3 vel = rb.linearVelocity;
                vel.x = blocked ? 0f : RUN_SPEED;
                rb.linearVelocity = vel;
            }
        }

        void LateUpdate()
        {
            // Late adjudication answers to the same authority: a runner that
            // reaches the line while the courier is already down banks no
            // escape, no failure and no visibility change. The genuine
            // Stopped / Escaped counters from before the lethal frame are
            // untouched, and the ordinary R reset is what clears the hold.
            if (!Active || !receiptDone || Complete || Failed || Down) return;
            for (int i = 0; i < 3; i++)
            {
                if (resolved[i] || agents[i] == null || !agents[i].alive) continue;
                if (bodies[i] != null && bodies[i].position.x >= ESCAPE_X)
                {
                    resolved[i] = true; Escaped++; Failed = true;
                    // The chapter's own genuine failure, recorded at the exact
                    // frame this runner really crossed, so a lethal hit that
                    // lands afterwards reports this more specific reason
                    // instead of erasing it.
                    if (string.IsNullOrEmpty(FailReason)) FailReason = "RUNNER ESCAPED";
                    DisableVis(i); FreezeAll(); UpdateObj(); return;
                }
            }
        }

        void SpawnRunner(int i)
        {
            Spawned++;
            var prefab = Resources.Load<GameObject>("Generated/player/scene");
            if (prefab == null)
            { Failed = true; if (string.IsNullOrEmpty(FailReason)) FailReason = "MISSING PLAYER PREFAB"; Objective = "MISSION FAILED\nMissing player prefab\nStopped " + Stopped + " / Escaped " + Escaped + "\nR reset"; return; }
            var go = new GameObject("InterceptRunner" + (i + 1));
            go.transform.localScale = Vector3.one;
            go.transform.rotation = Quaternion.LookRotation(Vector3.right, Vector3.up);
            var child = Instantiate(prefab, go.transform);
            child.transform.localPosition = new Vector3(child.transform.localPosition.x, -0.79f, child.transform.localPosition.z);
            go.transform.position = SPAWN[i];
            foreach (var r in go.GetComponentsInChildren<Rigidbody>()) Destroy(r);
            foreach (var c in go.GetComponentsInChildren<Collider>()) Destroy(c);
            var col = go.AddComponent<CapsuleCollider>();
            col.center = new Vector3(0, .95f, 0); col.height = 1.9f; col.radius = .38f;
            var rb = go.AddComponent<Rigidbody>();
            rb.mass = 80f; rb.useGravity = true; rb.drag = 0f;
            rb.constraints = RigidbodyConstraints.FreezeRotation;
            rb.collisionDetectionMode = CollisionDetectionMode.Continuous;
            foreach (var rd in go.GetComponentsInChildren<Renderer>())
            {
                var m = new Material(Shader.Find("Standard"));
                m.color = new Color(.30f, .36f, .32f);
                rd.sharedMaterial = m;
            }
            var ag = go.AddComponent<RivalAgent>(); ag.hp = 3; ag.alive = true;
            runners[i] = go; agents[i] = ag; bodies[i] = rb;
        }

        void FreezeBody(int i)
        {
            if (bodies[i] == null) return;
            bodies[i].linearVelocity = Vector3.zero;
            bodies[i].angularVelocity = Vector3.zero;
            bodies[i].isKinematic = true;
        }
        void FreezeAll() { for (int i = 0; i < 3; i++) FreezeBody(i); }
        void DisableVis(int i)
        {
            if (!runners[i]) return;
            foreach (var r in runners[i].GetComponentsInChildren<Renderer>()) r.enabled = false;
            var c = runners[i].GetComponent<Collider>(); if (c) c.enabled = false;
        }
        void UpdateObj()
        {
            if (Complete) Objective = "INTERCEPTION COMPLETE\nAll stopped, no escapes\nStopped 3 / Escaped 0\nRelay complete | R reset";
            else if (Failed)
            { string why = Escaped > 0 ? "Runner escaped!" : "Health depleted"; Objective = "INTERCEPTION FAILED\n" + why + "\nStopped " + Stopped + " / Escaped " + Escaped + "\nRelay complete | R reset"; }
            else Objective = "INTERCEPT RUNNERS " + Stopped + "/3\nMove to aim; Mouse0 fire\nStopped " + Stopped + " / Escaped " + Escaped + "\nRelay complete | R reset";
        }
        void Cleanup()
        {
            Active = Complete = Failed = false; Stopped = Escaped = Spawned = 0;
            receiptDone = false; Objective = null;
            for (int i = 0; i < 3; i++)
            { if (runners[i]) Destroy(runners[i]); runners[i] = null; agents[i] = null; bodies[i] = null; resolved[i] = false; }
        }
        float ReadHealth() { return LoopSignals.Health; }
    }
}
