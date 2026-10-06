using UnityEngine;

namespace ChicagoGame
{
    [DefaultExecutionOrder(100)]
    public class InterceptionMission : MonoBehaviour
    {
        public bool Active, Complete, Failed;
        public int Stopped, Escaped, Spawned;
        public string Objective;

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
            if (LoopSignals.Restarts != lastRestarts) { lastRestarts = LoopSignals.Restarts; Cleanup(); return; }
            if (!Active)
            {
                if (relay && relay.AllComplete) { Active = true; armedAt = Time.time; UpdateObj(); }
                return;
            }
            if (!receiptDone)
            {
                Objective = "INTERCEPT RUNNERS 0/3\nMove to aim; Mouse0 fire\nStopped 0 / Escaped 0\nRelay complete | R reset";
                if (Time.time - armedAt < RECEIPT) return;
                receiptDone = true;
            }
            if (Complete || Failed) return;
            if (ReadHealth() <= 0) { Failed = true; FreezeAll(); UpdateObj(); return; }
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
            if (!Active || !receiptDone || Complete || Failed) return;
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
            if (!Active || !receiptDone || Complete || Failed) return;
            for (int i = 0; i < 3; i++)
            {
                if (resolved[i] || agents[i] == null || !agents[i].alive) continue;
                if (bodies[i] != null && bodies[i].position.x >= ESCAPE_X)
                {
                    resolved[i] = true; Escaped++; Failed = true;
                    DisableVis(i); FreezeAll(); UpdateObj(); return;
                }
            }
        }

        void SpawnRunner(int i)
        {
            Spawned++;
            var prefab = Resources.Load<GameObject>("Generated/player/scene");
            if (prefab == null)
            { Failed = true; Objective = "MISSION FAILED\nMissing player prefab\nStopped " + Stopped + " / Escaped " + Escaped + "\nR reset"; return; }
            var go = new GameObject("InterceptRunner" + (i + 1));
            go.transform.localScale = Vector3.one;
            go.transform.rotation = Quaternion.identity;
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
            if (Complete) Objective = "INTERCEPT RUNNERS 3/3\nAll stopped, no escapes\nStopped 3 / Escaped 0\nR reset";
            else if (Failed)
            { string why = Escaped > 0 ? "Runner escaped!" : "Health depleted"; Objective = "MISSION FAILED\n" + why + "\nStopped " + Stopped + " / Escaped " + Escaped + "\nR reset"; }
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
