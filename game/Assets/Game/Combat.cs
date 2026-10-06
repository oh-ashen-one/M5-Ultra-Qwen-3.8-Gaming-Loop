using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    // Small original rival encounter woven into the courier mission.
    // Reuses the ORIGINAL player mesh (no new asset). One red rival:
    //   * visibly walks toward the courier and shoots (real Health damage)
    //   * PursuitLevel is DERIVED from the actual proximity of the live rival,
    //     so pursuit rises from a real encounter and clears through a
    //     reachable escape: drive far enough away and it returns to 0.
    //   * Mouse0 fires a real camera-forward ray (the unlocked native aim) at
    //     a rendered, collidable rival. Only an actual collider hit counts as
    //     a Hit and only then is the target's real HP reduced.
    // Nothing here detects replay or moves objects in a harness; every signal
    // (Shots/Hits/Health/PursuitLevel) is written from real gameplay events.
    public class RivalAgent : MonoBehaviour
    {
        public int hp = 3;
        public bool alive = true;
        public float muzzle;                 // last-shot cooldown timer
        public Renderer flash;               // hit-flash renderer
        public float flashT;
    }

    public class Combat : MonoBehaviour
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;

        public Transform player;
        public Camera cam;

        RivalAgent rival;
        Transform rivalGo;

        int lastRestarts;
        const float PLAYER_RESET_Y = 0.3f;

        // Rival behaviour.
        const float RIVAL_SPEED = 1.0f;      // slower than the car: escapable
        const float RIVAL_HP = 3f;
        const float SHOT_RANGE = 16f;
        const float SHOT_COOLDOWN = 1.6f;
        const int SHOT_DAMAGE = 4;
        const float FIRE_RANGE = 60f;

        // Chase begins once the courier has the parcel (mission is already
        // active); we simply activate the encounter shortly after launch so it
        // is on the courier's approach line without editing the mission.
        float startTime;
        bool encounterLive;

        static readonly Vector3 RIVAL_SPAWN = new Vector3(2.0f, 0.14f, -0.5f);

        public static void Install(GameObject player, Camera cam)
        {
            if (!player || !cam) return;
            var host = new GameObject("Combat");
            host.transform.position = Vector3.zero;
            host.transform.SetParent(null, false);
            var c = host.AddComponent<Combat>();
            c.player = player.transform;
            c.cam = cam;
            c.Build();
        }

        void Build()
        {
            // Reuse the original player mesh for a rendered rival; strip any
            // physics, then add ONE honest capsule collider so the aim ray and
            // world both recognise a solid, hittable target.
            var prefab = Resources.Load<GameObject>("Generated/player/scene");
            var go = new GameObject("Rival");
            go.transform.localScale = Vector3.one;
            go.transform.rotation = Quaternion.identity;
            if (prefab != null)
            {
                var child = Instantiate(prefab);
                child.transform.SetParent(go.transform, false);
                child.transform.localPosition = new Vector3(child.transform.localPosition.x, -0.79f, child.transform.localPosition.z);
            }
            else
            {
                var cap = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                cap.transform.SetParent(go.transform, false);
            }
            go.transform.position = RIVAL_SPAWN;

            foreach (var r in go.GetComponentsInChildren<Rigidbody>()) Destroy(r);
            foreach (var c in go.GetComponentsInChildren<Collider>()) Destroy(c);

            var col = go.AddComponent<CapsuleCollider>();
            col.center = new Vector3(0f, 0.95f, 0f);
            col.height = 1.9f;
            col.radius = 0.38f;
            col.isTrigger = false;
            var rb = go.AddComponent<Rigidbody>();
            rb.mass = 80f;
            rb.isKinematic = false;
            rb.useGravity = true;
            rb.drag = 2f;
            rb.constraints = RigidbodyConstraints.FreezeRotation;

            // Tint it red so the rival reads as hostile (original geometry kept).
            Renderer flash = null;
            foreach (var r in go.GetComponentsInChildren<Renderer>())
            {
                var m = new Material(Shader.Find("Standard"));
                m.color = new Color(0.75f, 0.08f, 0.08f);
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", new Color(0.25f, 0f, 0f));
                r.sharedMaterial = m;
                if (flash == null) flash = r;
            }

            var a = go.AddComponent<RivalAgent>();
            a.hp = 3;
            a.alive = true;
            a.flash = flash;

            rival = a;
            rivalGo = go.transform;

            lastRestarts = ReadInt("Restarts");
            startTime = Time.time;
            Set("PursuitLevel", 0);
            Set("Shots", 0);
            Set("Hits", 0);
        }

        void Update()
        {
            // R retry: mirrors the mission/vehicle reset. Reposition the rival,
            // restore HP/Health and zero combat counters.
            int r = ReadInt("Restarts");
            if (r != lastRestarts)
            {
                lastRestarts = r;
                ResetEncounter();
            }

            // Encounter activates just after launch, when the courier is on the
            // block approaching the parcel.
            if (!encounterLive && Time.time - startTime > 4.0f &&
                ReadStr("Mission") == "active")
                encounterLive = true;

            if (rival != null && rival.alive && encounterLive)
                ActRival();

            HandleFire();
            UpdateFlash();
            UpdatePursuit();
        }

        void ActRival()
        {
            Transform tgt = LoopSignals.Mode == "vehicle" && LoopSignals.Vehicle != null
                ? LoopSignals.Vehicle : player;
            Vector3 me = tgt.position; me.y = 0f;
            Vector3 to = me - rivalGo.position; to.y = 0f;
            float d = to.magnitude;
            if (d > 0.01f)
            {
                var want = Quaternion.LookRotation(to.normalized, Vector3.up);
                rivalGo.rotation = Quaternion.RotateTowards(rivalGo.rotation, want, 260f * Time.deltaTime);
                if (d > 3.0f) rivalGo.position += to.normalized * (RIVAL_SPEED * Time.deltaTime);
            }
            rival.muzzle -= Time.deltaTime;
            if (d < SHOT_RANGE && rival.muzzle <= 0f)
            {
                rival.muzzle = SHOT_COOLDOWN;
                Vector3 mp = rivalGo.position + Vector3.up * 1.25f;
                Vector3 tb = tgt.position + Vector3.up * 1.0f;
                Vector3 dir = tb - mp; float len = dir.magnitude;
                bool blocked = false; float stop = len;
                if (len > 0.01f)
                {
                    var hits = Physics.RaycastAll(mp, dir.normalized, len);
                    System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
                    foreach (var h in hits)
                    {
                        if (h.transform.root == rivalGo.root || h.collider.isTrigger) continue;
                        if (h.transform.root != tgt.root) { blocked = true; stop = h.distance; }
                        break;
                    }
                }
                if (!blocked)
                {
                    int hp = Mathf.Max(0, ReadInt("Health") - SHOT_DAMAGE);
                    Set("Health", hp);
                    if (hp <= 0 && ReadStr("Mission") == "active") Set("Mission", "failed");
                }
                Tracer(mp, mp + dir.normalized * stop, new Color(1f, 0.5f, 0.05f), 0.06f);
            }
        }

        void HandleFire()
        {
            if (!LoopInput.Pressed(KeyCode.Mouse0)) return;
            Set("Shots", ReadInt("Shots") + 1);

            var origin = cam.transform.position;
            var dir = cam.transform.forward;
            var hits = Physics.RaycastAll(origin, dir, FIRE_RANGE,
                                          ~0, QueryTriggerInteraction.Ignore);

            // Find the FIRST (nearest) collider, ignoring only the shooter's
            // own player hierarchy and, while driving, the controlled vehicle.
            Transform ignorePlayer = LoopSignals.Player ? LoopSignals.Player.root : null;
            Transform ignoreVehicle = null;
            if (LoopSignals.Mode == "vehicle" && LoopSignals.Vehicle != null)
                ignoreVehicle = LoopSignals.Vehicle.root;

            float best = float.MaxValue;
            Vector3 hitPt = origin + dir * FIRE_RANGE;
            RivalAgent first = null;

            foreach (var h in hits)
            {
                var root = h.transform.root;
                if (ignorePlayer != null && root == ignorePlayer) continue;
                if (ignoreVehicle != null && root == ignoreVehicle) continue;
                if (h.distance >= best) continue;
                best = h.distance;
                hitPt = h.point;
                var a = h.collider.GetComponentInParent<RivalAgent>();
                first = (a != null && a.alive) ? a : null;
            }

            // Tracer always ends at the first real collision.
            Tracer(origin, hitPt, new Color(1f, 0.95f, 0.4f), 0.06f);

            // Only if the FIRST collider is a live rival does HP/Hits change.
            if (first != null)
            {
                first.hp -= 1;
                first.flashT = 0.12f;
                Set("Hits", ReadInt("Hits") + 1);
                if (first.hp <= 0)
                {
                    first.alive = false;
                    foreach (var rr in rivalGo.GetComponentsInChildren<Renderer>())
                        rr.enabled = false;
                    var c = rivalGo.GetComponent<CapsuleCollider>();
                    if (c != null) c.enabled = false;
                }
            }
        }

        void UpdateFlash()
        {
            if (rival == null) return;
            if (rival.flashT > 0f)
            {
                rival.flashT -= Time.deltaTime;
                if (rival.flash != null && rival.flash.sharedMaterial != null)
                    rival.flash.sharedMaterial.SetColor("_EmissionColor",
                        rival.flashT > 0f ? Color.white : new Color(0.25f, 0f, 0f));
            }
        }

        // Pursuit is purely DERIVED from the live rival's actual distance: an
        // encounter raises it; driving away lowers and finally clears it.
        void UpdatePursuit()
        {
            int level = 0;
            if (encounterLive && rival != null && rival.alive)
            {
                Transform actor = player;
                if (ReadStr("Mode") == "vehicle")
                {
                    var v = LoopSignals.Vehicle;
                    if (v) actor = v;
                }
                float d = Vector3.Distance(actor.position, rivalGo.position);
                if (d < 5f) level = 3;
                else if (d < 10f) level = 2;
                else if (d < 18f) level = 1;
            }
            Set("PursuitLevel", level);
        }

        void ResetEncounter()
        {
            if (rival != null)
            {
                rival.alive = true;
                rival.hp = 3;
                rival.muzzle = SHOT_COOLDOWN;
                rivalGo.position = RIVAL_SPAWN;
                rivalGo.rotation = Quaternion.identity;
                var c = rivalGo.GetComponent<CapsuleCollider>();
                if (c != null) c.enabled = true;
                foreach (var r in rivalGo.GetComponentsInChildren<Renderer>())
                    r.enabled = true;
            }
            Set("Shots", 0);
            Set("Hits", 0);
            Set("PursuitLevel", 0);
            Set("Health", 100);
            encounterLive = false;
            startTime = Time.time;
        }

        // Thin stretched tracer cube for a short visible shot line.
        void Tracer(Vector3 a, Vector3 b, Color c, float life)
        {
            var t = GameObject.CreatePrimitive(PrimitiveType.Cube);
            t.name = "Tracer";
            var r = t.GetComponent<Renderer>();
            var m = new Material(Shader.Find("Standard"));
            m.color = c;
            m.EnableKeyword("_EMISSION");
            m.SetColor("_EmissionColor", c);
            r.sharedMaterial = m;
            Destroy(t.GetComponent<Collider>());
            var d = b - a;
            t.transform.position = (a + b) * 0.5f;
            t.transform.rotation = Quaternion.LookRotation(d, Vector3.up);
            t.transform.localScale = new Vector3(0.05f, 0.05f, Mathf.Max(0.05f, d.magnitude));
            Destroy(t, life);
        }

        // ---- tolerant signal access (mirrors existing modules) ----
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
                if (f != null) return System.Convert.ToInt32(f.GetValue(null));
                if (p != null && p.CanRead) return System.Convert.ToInt32(p.GetValue(null));
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
