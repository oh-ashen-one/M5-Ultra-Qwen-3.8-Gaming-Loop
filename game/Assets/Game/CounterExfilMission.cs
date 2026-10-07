using UnityEngine;

namespace ChicagoGame
{
    // ---------------------------------------------------------------------
    // Counter-Exfil: the westbound half of the same incident.
    //
    // Dormant until the OLD interception closes cleanly (three stopped, no
    // escape). Then Armed: the courier is handed off on foot about 20 m from
    // his own coupe, left exactly where the old mission drove it, with 28
    // health and whatever is left of the old encounter standing where the
    // player left it. The measured healthy handoff had the ORIGINAL rival
    // already down, so nothing here assumes that rival is live, revives it or
    // adds pressure during the retrieval - he walks back with the ordinary
    // Walker and boards with the ordinary E.
    //
    // Explicit F while seated AND stationary starts Active and exactly three
    // runners: a 6 HP lead and two 3 HP stragglers, all built from the original
    // player prefab, all genuinely solid and hittable by the existing Combat
    // aim ray. They flee west along the one corridor the native survey
    // qualified for a westbound capsule AND for the real coupe box
    // ("central-westbound", zero static overlaps, zero swept hits). That survey
    // route is PIECEWISE, and the lane follows its surveyed waypoints in order:
    // 47.605/17.4603 -> 22/16.5738 -> 6/16.0057 -> 3/16.0057. A straight
    // endpoint-to-endpoint interpolation is NOT that path, so it is not used.
    // The z10/z15/z19 candidates are NOT qualified - dumpsters,
    // piers, the alley north wall and a barrier sit on them - and the old
    // eastbound interception evidence proves nothing about westbound travel, so
    // no distinct lateral lanes are invented: all three share the single
    // validated lane, separated lengthwise.
    //
    // Resolution is only ever real: a kill is a real bullet through the existing
    // Combat hit path, counted once, permanent; a pin is sustained real coupe
    // contact plus genuinely blocked westward travel (see CounterExfilRunner).
    // An unresolved runner that really crosses the validated west exit fails the
    // chapter with that runner named. Complete needs all three killed or
    // currently pinned, no escape, and the living courier walking the west exit.
    //
    // DeathAuthority owns the single death verdict and gates arming, launching,
    // spawning, driving, pin clocks, escapes, scoring and the board. The
    // ordinary Restarts edge destroys every actor, timer and pin and hands the
    // run back. Nothing here writes Health, Restarts, Shots, Hits, Mode or
    // Mission, and the ordinary ending and R stay available if the player never
    // presses F.
    // ---------------------------------------------------------------------
    [DefaultExecutionOrder(120)]
    public sealed class CounterExfilMission : MonoBehaviour
    {
        static CounterExfilMission _inst;

        GameObject _player;
        InterceptionMission _old;
        int lastRestarts;

        bool armed, active, receiptDone, complete, failed;
        bool driving, spawnedAll;
        string objective, failReason;
        float activatedAt, activeTime;
        bool deathHeld; string objectiveBeforeDeath;

        // Real on-foot east->west crossing evidence. Sampled on every live frame
        // while the chapter is Active - settled or not - and only ever from a
        // living courier on foot: standing beyond the line never counts, only an
        // unbroken chain of foot samples that starts east of it and ends west of
        // it does. Any vehicle frame (boarding, being driven, an E exit), any
        // death hold and the ordinary R reset wipe the chain and its timestamps.
        bool footEastOfExit;   // a live foot sample really seen east of the line
        bool crossedWest;      // a later, contiguous foot sample really west of it
        bool footValid;        // the previous foot sample belongs to this chain
        Vector3 lastFoot;      // that previous sample, for the step-distance guard
        float crossedAt, settledAt;

        readonly CounterExfilRunner[] _runners = new CounterExfilRunner[3];
        readonly GameObject[] _actors = new GameObject[3];
        readonly bool[] _killed = new bool[3];
        readonly bool[] _escaped = new bool[3];
        int killedCount, escapedCount;

        Vector3 seatAnchor; float seatAnchorTime;

        const float RECEIPT = 1.5f;            // this chapter's own readout
        // The validated west exit IS the surveyed central corridor's own west
        // end (x 3.0, z 16.0057). The accepted band is that route's own
        // physical half-width - coupe half-width 0.9 m plus a courier capsule
        // radius 0.32 m plus a small margin - so a wide unqualified side street
        // can never satisfy the exit.
        const float EXIT_X = 3.2f, EXIT_Z = 16.0057f, EXIT_HALF_Z = 1.5f;
        const float CROSS_ARM = 0.6f;          // seen this far east before crossing
        const float MAX_FOOT_STEP = 0.5f;      // < CROSS_ARM: no lone sample may jump the line
        const float LANE_EAST_X = 47.0f, LANE_WEST_X = 8.0f;
        const float MAX_SEAT_SPEED = 0.25f, STILL_TIME = 0.30f;
        // The surveyed piecewise central corridor, ordered east -> west: the
        // lane follows these exact waypoints. A straight endpoint-to-endpoint
        // interpolation is NOT the surveyed path and is not used.
        static readonly Vector3[] LanePath = {
            new Vector3(47.605f, 0f, 17.4603f),
            new Vector3(22f,     0f, 16.5738f),
            new Vector3(6f,      0f, 16.0057f),
            new Vector3(3f,      0f, 16.0057f)
        };
        static readonly Vector3 LaneEast = LanePath[0];
        static readonly Vector3 LaneWest = LanePath[LanePath.Length - 1];
        static readonly float[] BACK = { 11.0f, 8.0f, 5.2f };     // lengthwise separation, one lane
        static readonly int[] HP = { 6, 3, 3 };
        static readonly float[] SPEED = { 1.7f, 1.35f, 1.35f };
        static readonly string[] LABEL = { "LEAD RUNNER", "RUNNER 2", "RUNNER 3" };
        static readonly Color[] TINT = {
            new Color(0.46f, 0.23f, 0.15f), new Color(0.30f, 0.34f, 0.30f), new Color(0.23f, 0.30f, 0.37f)
        };

        // ---- ordinary public read-only observation ----
        public bool Dormant { get { return !armed; } }
        public bool Armed { get { return armed && !active; } }
        public bool Active { get { return active; } }
        public bool Complete { get { return complete; } }
        public bool Failed { get { return failed; } }
        /// <summary>True only once this chapter owns the board; Armed keeps the
        /// old interception ending on screen and merely appends to it.</summary>
        public bool BoardPriority { get { return active; } }
        /// <summary>One compact line the director may append to the OLD ending
        /// while this chapter is only Armed, so the small board is never asked
        /// to carry two full objectives at once.</summary>
        public string HudLine
        {
            get
            {
                if (!armed || active) return null;
                int d = CoupeDistance;
                return d < 0
                    ? "EXFIL ARMED | coupe unavailable"
                    : "EXFIL ARMED coupe " + d + "m | E board, F launch";
            }
        }
        public string Objective { get { return objective; } }
        public string FailReason { get { return failReason; } }
        public CounterExfilRunner Lead { get { return _runners[0]; } }
        public CounterExfilRunner Second { get { return _runners[1]; } }
        public CounterExfilRunner Third { get { return _runners[2]; } }
        public int SpawnedCount { get { int n = 0; for (int i = 0; i < 3; i++) if (_runners[i] != null) n++; return n; } }
        public int KilledCount { get { return killedCount; } }
        public int EscapedCount { get { return escapedCount; } }
        public int PinnedNow { get { int n = 0; for (int i = 0; i < 3; i++) if (_runners[i] != null && _runners[i].Pinned) n++; return n; } }
        /// <summary>Gameplay seconds since launch; frozen at the verdict, so it
        /// never counts load, test or reset time.</summary>
        public float ActiveTime { get { return activeTime; } }
        public float ReceiptLeft { get { return active && !receiptDone ? Mathf.Max(0f, RECEIPT - (float)(Time.time - activatedAt)) : 0f; } }
        public int CoupeDistance { get { var v = LoopSignals.Vehicle; if (v == null) return -1; Vector3 a = Me(); Vector3 b = v.position; a.y = b.y = 0f; return Mathf.RoundToInt(Vector3.Distance(a, b)); } }
        public int ExitDistance { get { Vector3 a = Me(); return Mathf.RoundToInt(Mathf.Abs(a.x - EXIT_X)); } }

        Vector3 Me()
        {
            if (LoopSignals.Mode == "vehicle" && LoopSignals.Vehicle != null) return LoopSignals.Vehicle.position;
            return _player != null ? _player.transform.position : Vector3.zero;
        }

        public static void Install(GameObject player, Camera cam)
        {
            if (_inst != null) return;
            var go = new GameObject("CounterExfilMission");
            go.transform.position = Vector3.zero;
            _inst = go.AddComponent<CounterExfilMission>();
            _inst._player = player;
            _inst._old = Object.FindObjectOfType<InterceptionMission>();
        }

        void Awake() { lastRestarts = LoopSignals.Restarts; }
        void OnDestroy() { if (_inst == this) _inst = null; }

        bool Down { get { return deathHeld || DeathAuthority.IsDead; } }

        void Update()
        {
            if (LoopSignals.Restarts != lastRestarts)
            {
                lastRestarts = LoopSignals.Restarts;
                Cleanup();
                return;
            }
            if (_old == null) _old = Object.FindObjectOfType<InterceptionMission>();
            SampleSeat();

            // Death outranks the chapter before anything can be armed, launched,
            // spawned, driven, pinned, scored or completed.
            if (DeathAuthority.IsDead) { HoldForDeath(); return; }
            ReleaseDeath();

            if (!armed)
            {
                if (_old != null && _old.Complete && !_old.Failed && _old.Escaped == 0 && _old.Stopped >= 3)
                { armed = true; objective = null; }
                return;
            }
            if (!active) { if (LoopInput.Pressed(KeyCode.F) && SeatedStill()) Begin(); return; }
            if (complete || failed) return;

            if (!receiptDone)
            {
                if (Time.time - activatedAt >= RECEIPT) { receiptDone = true; driving = true; SpawnAll(); }
                return;
            }
            // Second read of the same authority: a lethal hit landing inside this
            // frame banks no kill, no escape and no completion.
            if (DeathAuthority.IsDead) { HoldForDeath(); return; }

            activeTime += Time.deltaTime;

            for (int i = 0; i < 3; i++)
            {
                var r = _runners[i];
                if (r == null || _killed[i] || !r.Killed) continue;
                _killed[i] = true; killedCount++;            // permanent, counted once
            }
            for (int i = 0; i < 3; i++)
            {
                var r = _runners[i];
                if (r == null || _killed[i] || _escaped[i]) continue;
                if (r.X <= EXIT_X && !r.Pinned) { RecordEscape(i); return; }
            }
            // Resolution clock first, so a kill landing this frame is already
            // counted when the crossing sample asks whether the run is settled.
            if (Settled()) { if (settledAt <= 0f) settledAt = Time.time; } else settledAt = 0f;
            SampleFoot();
            if (spawnedAll && escapedCount == 0 && Settled() && FootCrossedExit())
            {
                complete = true; StopDrive();
            }
        }

        void FixedUpdate()
        {
            if (!active || !receiptDone || !driving || complete || failed || Down) return;
            float dt = Time.fixedDeltaTime;
            for (int i = 0; i < 3; i++) if (_runners[i] != null) _runners[i].PhysicsStep(dt);
        }

        void LateUpdate() { UpdateBoard(); }

        void Begin()
        {
            active = true; activatedAt = Time.time; activeTime = 0f;
            ClearCrossing(); settledAt = 0f;    // a fresh launch walks its own exit
        }

        void SpawnAll()
        {
            var coupe = LoopSignals.Vehicle;
            float carX = coupe != null ? coupe.position.x : LaneEast.x;
            var prefab = Resources.Load<GameObject>("Generated/player/scene");
            float prevX = float.MaxValue;
            for (int i = 0; i < 3; i++)
            {
                float x = Mathf.Clamp(carX - BACK[i], LANE_WEST_X, LANE_EAST_X);
                if (i > 0) x = Mathf.Clamp(Mathf.Max(x, prevX + 2.5f), LANE_WEST_X, LANE_EAST_X);
                prevX = x;
                SpawnOne(i, prefab, x);
            }
            spawnedAll = SpawnedCount >= 3;
            if (!spawnedAll)
            {
                failed = true;
                if (string.IsNullOrEmpty(failReason)) failReason = "MISSING PLAYER PREFAB";
            }
        }

        void SpawnOne(int i, GameObject prefab, float x)
        {
            if (prefab == null) return;
            var go = new GameObject("CounterExfilRunner" + (i + 1));
            go.transform.localScale = Vector3.one;
            var vis = Object.Instantiate(prefab, go.transform);
            vis.transform.localPosition = new Vector3(vis.transform.localPosition.x, -0.79f, vis.transform.localPosition.z);
            foreach (var r in go.GetComponentsInChildren<Rigidbody>()) Destroy(r);
            foreach (var c in go.GetComponentsInChildren<Collider>()) Destroy(c);

            var col = go.AddComponent<CapsuleCollider>();
            col.center = new Vector3(0f, 0.95f, 0f); col.height = 1.9f; col.radius = 0.38f;
            var rb = go.AddComponent<Rigidbody>();
            rb.mass = 80f; rb.useGravity = true; rb.drag = 0f;
            rb.constraints = RigidbodyConstraints.FreezeRotation;
            rb.collisionDetectionMode = CollisionDetectionMode.Continuous;
            foreach (var rd in go.GetComponentsInChildren<Renderer>())
            {
                var m = new Material(Shader.Find("Standard"));
                m.color = TINT[i];
                rd.sharedMaterial = m;
            }
            var ag = go.AddComponent<RivalAgent>();
            ag.hp = HP[i]; ag.alive = true;

            var run = go.AddComponent<CounterExfilRunner>();
            run.Slot = i; run.Label = LABEL[i]; run.StartHp = HP[i];
            run.DriveSpeed = SPEED[i];
            run.Coupe = LoopSignals.Vehicle;               // the real coupe root, nothing else
            run.LaneEast = LaneEast; run.LaneWest = LaneWest;
            run.Agent = ag; run.Body = rb;
            run.SetOnLane(x);

            _actors[i] = go; _runners[i] = run;
        }

        void RecordEscape(int i)
        {
            _escaped[i] = true; escapedCount++;
            failed = true; driving = false;
            // Named, genuine, recorded at the frame the crossing really happened,
            // so a lethal hit afterwards reports this instead of overwriting it.
            failReason = LABEL[i] + " REACHED THE WEST EXIT";
            StopDrive();
        }

        bool Settled()
        {
            for (int i = 0; i < 3; i++)
                if (_runners[i] == null || !(_killed[i] || _runners[i].Pinned)) return false;
            return true;
        }

        // ---- the real crossing ----
        // One live on-foot sample of the validated central exit, taken every
        // frame the chapter is Active, settled or not, so the east leg of the
        // walk is already on record before the last runner drops. A non-foot
        // frame - boarding, riding, or an E exit dropped beside the line - wipes
        // the whole chain, so nothing but walking east to west can produce it.
        void SampleFoot()
        {
            if (LoopSignals.Mode != "foot" || _player == null || Down) { ClearCrossing(); return; }
            Vector3 p = _player.transform.position;
            Vector3 prev = lastFoot;
            bool stepped = footValid && Vector3.Distance(p, prev) <= MAX_FOOT_STEP;

            // Capture first, then make this the only previous foot sample. A torn
            // chain starts over, but it cannot carry an older east or west claim.
            footValid = true;
            lastFoot = p;

            if (!stepped)
            {
                footEastOfExit = false;
                crossedWest = false;
                crossedAt = 0f;
                return;
            }

            // Only the surveyed central corridor's own physical width counts.
            if (Mathf.Abs(p.z - EXIT_Z) > EXIT_HALF_Z)
            {
                footEastOfExit = false;
                crossedWest = false;
                crossedAt = 0f;
                return;
            }

            if (p.x >= EXIT_X + CROSS_ARM)
            {
                footEastOfExit = true;
                crossedWest = false;
                crossedAt = 0f;
                return;
            }

            // Still on the east side of the exact plane. Keep an earlier central
            // east leg, but never keep a west claim while not west.
            if (p.x >= EXIT_X)
            {
                crossedWest = false;
                crossedAt = 0f;
                return;
            }

            if (stepped && footEastOfExit && prev.x > EXIT_X && p.x < EXIT_X && Settled())
            {
                crossedWest = true;
                crossedAt = Time.time;
                return;
            }

            // West without one continuous, central, settled east-to-west step is
            // just loitering (or an E/teleport/early run): re-arm from the east.
            footEastOfExit = false;
            crossedWest = false;
            crossedAt = 0f;
        }
        void ClearCrossing()
        {
            footEastOfExit = false; crossedWest = false; footValid = false; crossedAt = 0f;
        }

        bool FootCrossedExit()
        {
            if (!crossedWest || LoopSignals.Mode != "foot" || _player == null || Down) return false;
            Vector3 p = _player.transform.position;
            return p.x <= EXIT_X && Mathf.Abs(p.z - EXIT_Z) <= EXIT_HALF_Z;
        }

        void SampleSeat()
        {
            var v = LoopSignals.Vehicle;
            if (v == null) { seatAnchorTime = 0f; return; }
            float step = Vector3.Distance(v.position, seatAnchor);
            if (seatAnchorTime <= 0f || step > 0.25f) { seatAnchor = v.position; seatAnchorTime = Time.time; }
        }

        bool SeatedStill()
        {
            if (LoopSignals.Mode != "vehicle") return false;
            var v = LoopSignals.Vehicle;
            if (v == null) return false;
            var rb = v.GetComponent<Rigidbody>();
            float sp = rb != null ? rb.linearVelocity.magnitude : 0f;
            return sp <= MAX_SEAT_SPEED && seatAnchorTime > 0f && Time.time - seatAnchorTime >= STILL_TIME;
        }

        void StopDrive()
        {
            driving = false;
            for (int i = 0; i < 3; i++) if (_runners[i] != null) _runners[i].CoastToStop();
        }

        // ---- board ----
        void UpdateBoard()
        {
            if (Down) { objective = DeathBoardText(); return; }
            if (failed)
            {
                objective = "COUNTER-EXFIL FAILED\n" + (string.IsNullOrEmpty(failReason) ? "RUNNERS GOT CLEAR" : failReason)
                    + "\nDOWN " + killedCount + " / HELD " + PinnedNow + " / RAN " + escapedCount + "\nR to retry";
                return;
            }
            if (complete)
            {
                objective = "COUNTER-EXFIL COMPLETE\nNO RUNNER REACHED THE WEST EXIT\nDOWN " + killedCount
                    + " / HELD " + PinnedNow + " in " + activeTime.ToString("0") + "s\nR to reset";
                return;
            }
            if (!armed) { objective = null; return; }
            if (!active)
            {
                int d = CoupeDistance;
                objective = d < 0
                    ? "COUNTER-EXFIL ARMED\nCOUPE UNAVAILABLE\nR to reset"
                    : "COUNTER-EXFIL ARMED\nWALK BACK TO THE COUPE " + d + "m\nE board, F to launch\nNo help arriving";
                return;
            }
            if (!receiptDone)
            {
                objective = "COUNTER-EXFIL\nEXFIL RUNNERS WESTBOUND IN " + ReceiptLeft.ToString("0.0")
                    + "s\nLEAD 6 HP, TWO 3 HP\nBlock them west with the coupe";
                return;
            }
            objective = "COUNTER-EXFIL ACTIVE " + activeTime.ToString("0") + "s\nDOWN " + killedCount
                + "/3  HELD " + PinnedNow + "  RAN " + escapedCount + "\n" + RunnerLine()
                + "  EXIT " + ExitDistance + "m\nMouse0 fire | cut west | walk exit";
        }

        string RunnerLine()
        {
            var s = "";
            for (int i = 0; i < 3; i++)
            {
                var r = _runners[i];
                if (r == null) { s += (i == 0 ? "" : " | ") + "--"; continue; }
                s += (i == 0 ? "" : " | ") + (i == 0 ? "L " : i == 1 ? "R2 " : "R3 ")
                     + (r.Killed ? "DOWN" : r.Hp + "/" + r.HpAtStart)
                     + (r.Pinned ? " PIN" : r.HoldSeconds > 0.05f ? " h" + r.HoldSeconds.ToString("0.0") : "");
            }
            return s;
        }

        string DeathBoardText()
        {
            if (!string.IsNullOrEmpty(failReason))
                return failReason + "\nCOURIER DOWN - HEALTH DEPLETED\nPRESS R TO RESTART";
            return "COURIER DOWN\nHEALTH DEPLETED\nPRESS R TO RESTART";
        }

        // ---- death hold: freeze without rewriting history ----
        void HoldForDeath()
        {
            if (!deathHeld)
            {
                deathHeld = true;
                objectiveBeforeDeath = objective;
                if (active && !complete) failed = true;   // a launched chapter dies with him
                StopDrive();                              // no posthumous pin, escape or score
            }
            objective = DeathBoardText();
        }

        void ReleaseDeath()
        {
            if (!deathHeld) return;
            deathHeld = false;
            objective = objectiveBeforeDeath;
            objectiveBeforeDeath = null;
        }

        void Cleanup()
        {
            armed = active = receiptDone = complete = failed = driving = spawnedAll = false;
            killedCount = escapedCount = 0;
            activeTime = 0f; activatedAt = 0f;
            objective = null; failReason = null;
            deathHeld = false; objectiveBeforeDeath = null;
            seatAnchorTime = 0f;
            ClearCrossing(); settledAt = 0f;      // R leaves no crossing evidence behind
            for (int i = 0; i < 3; i++)
            {
                if (_actors[i]) Destroy(_actors[i]);
                _actors[i] = null; _runners[i] = null; _killed[i] = false; _escaped[i] = false;
            }
        }
    }
}
