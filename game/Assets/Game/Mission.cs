using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    // Rough connected Chicago courier mission built from the existing
    // street/player/coupe/props. This microtask installs only the world
    // content (parcel + destination pad + beacon + on-camera HUD) and the
    // geometry-derived lane probe that guarantees a car-clear route down the
    // block. Interaction (F grab/deliver), Mode-gating and restart respawn
    // are added in the following microtask.
    public class CourierMission : MonoBehaviour
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;

        // Walkable pavement: X -1..6, Z -2..30, top surface Y 0.14.
        const float PAV_TOP = 0.14f;

        public Transform player;
        public Camera cam;
        public Transform parcel;
        // Fixed world-space root for objectives. CourierMission itself lives on
        // the player, so parenting world props to this.transform would drag them
        // along as the courier walks. This no-parent root keeps the parcel, drop
        // pad and beacon anchored to the block.
        Transform missionRoot;
        public Renderer padRend;
        public Renderer beaconRend;
        public Transform beacon;
        public float laneX = 3.8f;

        TextMesh hud;

        Color padColor;
        Color beaconColor;

        // Deterministic candidate lanes tried from centre-west outward.
        static readonly float[] Lanes = { 2.2f, 3.8f, 0.6f, 5.0f };

        public static void Install(GameObject player, Camera cam)
        {
            if (!player || !cam) return;
            // Host the mission on its OWN stationary, unparented world object so
            // that any transform-relative parenting (respawn, reset) anchors to a
            // fixed block location instead of dragging props along with the courier.
            var host = new GameObject("CourierMission");
            host.transform.position = Vector3.zero;
            host.transform.rotation = Quaternion.identity;
            host.transform.SetParent(null, false);
            var m = host.AddComponent<CourierMission>();
            m.player = player.transform;
            m.cam = cam;
            m.Build();
        }

        void Build()
        {
            // Deterministic lane aligned with the parked coupe (X=3.6) so the
            // parcel, pad and beacon all sit directly on the drivable centreline
            // of the block. ProbeLane stays available but we pin the value so the
            // objective/destination geometry is reproducible for a route test.
            laneX = 3.6f;

            // Stationary world root: the objective, destination and beacon must
            // stay fixed on the block regardless of the courier's transform.
            var root = new GameObject("MissionRoot");
            root.transform.position = Vector3.zero;
            missionRoot = root.transform;

            // ---- Objective parcel: bright yellow bobbing/spinning cube ----
            parcel = GameObject.CreatePrimitive(PrimitiveType.Cube).transform;
            parcel.name = "Parcel";
            parcel.SetParent(missionRoot, false);
            parcel.position = new Vector3(laneX, 0.45f, 3.2f);
            parcel.localScale = new Vector3(0.4f, 0.4f, 0.4f);
            var pcol = parcel.GetComponent<Collider>();
            if (pcol != null) Destroy(pcol);
            Paint(parcel.GetComponent<Renderer>(),
                  new Color(1f, 0.85f, 0.05f), new Color(1f, 0.75f, 0.0f));

            // ---- Destination pad: flat green cylinder ----
            var pad = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            pad.name = "DropPad";
            pad.transform.SetParent(missionRoot, false);
            pad.transform.position = new Vector3(laneX, PAV_TOP + 0.01f, 27.5f);
            pad.transform.localScale = new Vector3(3.6f, 0.02f, 3.6f); // r = 1.8, thin
            var padCol = pad.GetComponent<Collider>();
            if (padCol != null) Destroy(padCol);
            padRend = pad.GetComponent<Renderer>();
            padColor = new Color(0.1f, 0.85f, 0.3f);
            Paint(padRend, padColor, padColor * 0.4f);

            // ---- Beacon column: translucent tall light shaft over the pad ----
            var beaconGo = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            beaconGo.name = "Beacon";
            beaconGo.transform.SetParent(missionRoot, false);
            beaconGo.transform.position = new Vector3(laneX, PAV_TOP + 3.5f, 27.5f);
            beaconGo.transform.localScale = new Vector3(1.1f, 3.5f, 1.1f); // 7 m tall
            var bcol = beaconGo.GetComponent<Collider>();
            if (bcol != null) Destroy(bcol);
            beacon = beaconGo.transform;
            beaconRend = beaconGo.GetComponent<Renderer>();
            beaconColor = new Color(0.2f, 1f, 0.4f, 0.28f);
            Paint(beaconRend, beaconColor, beaconColor);
            SetTransparent(beaconRend, 0.28f);

            BuildHud();

            Set("Mission", "active");
        }

        // Sweep a car-sized box down the block; return the first lane whose
        // corridor (Z 12 -> 28, past the coupe) is free of world colliders.
        float ProbeLane()
        {
            Vector3 half = new Vector3(0.9f, 0.6f, 2.15f); // matches coupe box
            var hits = new RaycastHit[8];
            foreach (var lx in Lanes)
            {
                var origin = new Vector3(lx, 0.75f, 12f);
                int n = Physics.BoxCastNonAlloc(origin, half, Vector3.forward,
                                               hits, Quaternion.identity, 16f,
                                               ~0, QueryTriggerInteraction.Ignore);
                if (n == 0) return lx;
            }
            return Lanes[0];
        }

        void BuildHud()
        {
            var go = new GameObject("MissionHud");
            go.transform.SetParent(cam.transform, false);
            go.transform.localPosition = new Vector3(0f, 0.70f, 1.6f);
            go.transform.localRotation = Quaternion.identity;

            // Black backing card 0.2 m further from the lens than the text.
            var card = GameObject.CreatePrimitive(PrimitiveType.Cube);
            card.name = "HudCard";
            card.transform.SetParent(go.transform, false);
            card.transform.localPosition = new Vector3(0f, -0.16f, 0.2f);
            card.transform.localScale = new Vector3(1.7f, 0.28f, 0.01f);
            Destroy(card.GetComponent<Collider>());
            Paint(card.GetComponent<Renderer>(), Color.black, Color.black);

            var tm = go.AddComponent<TextMesh>();
            tm.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            tm.fontSize = 40;
            tm.characterSize = 0.008f;
            tm.anchor = TextAnchor.UpperCenter;
            tm.alignment = TextAlignment.Center;
            tm.color = Color.white;
            hud = tm;
            RefreshHud();
        }

        void RefreshHud()
        {
            if (hud == null) return;
            if (stage == 2)
            {
                hud.text =
                    "\u2605 DELIVERY COMPLETE \u2605\n" +
                    "The parcel has been delivered.\n" +
                    "R to reset";
                return;
            }

            // stage is the real integer: 0=uncollected, 1=carrying, 2=delivered.
            // While driving, display the vehicle's actual position; otherwise the
            // courier's own position. Never claim "in hand" before stage==1.
            Transform veh = typeof(LoopSignals).GetField("Vehicle", St)
                               .GetValue(null) as Transform;
            bool driving = ReadStr("Mode") == "vehicle" && veh != null;
            Vector3 me = driving
                ? veh.position
                : (player != null ? player.position : Vector3.zero);
            me.y = 0f;

            if (stage == 0)
            {
                Vector3 target = parcel != null ? parcel.position : Vector3.zero;
                target.y = 0f;
                int d = Mathf.RoundToInt(Vector3.Distance(me, target));
                hud.text =
                    "COURIER: grab the YELLOW parcel\n" +
                    "OBJECTIVE: reach the parcel  (" + d + " m)\n" +
                    "WASD move   E enter/exit coupe   F grab/deliver   R reset";
            }
            else // stage 1 – carrying
            {
                Vector3 pad = beacon != null ? beacon.position : Vector3.zero;
                pad.y = 0f;
                int d = Mathf.RoundToInt(Vector3.Distance(me, pad));
                hud.text =
                    "COURIER: parcel in hand\n" +
                    "OBJECTIVE: drive to the GREEN pad  (" + d + " m)\n" +
                    "WASD move   E enter/exit coupe   F deliver   R reset";
            }
        }

        // ---- mission stage state ----
        int stage;           // 0=parcel on ground, 1=carrying, 2=delivered(latched)
        int lastRestarts;
        Vector3 padPos;

        void Start()
        {
            lastRestarts = ReadInt("Restarts");
            padPos = new Vector3(laneX, PAV_TOP, 27.5f);
        }

        void Update()
        {
            // Detect R reset via Restarts counter change.
            int r = ReadInt("Restarts");
            if (r != lastRestarts)
            {
                lastRestarts = r;
                Respawn();
            }

            // Animate parcel when in world.
            if (stage == 0 && parcel != null)
            {
                parcel.Rotate(Vector3.up, 90f * Time.deltaTime, Space.World);
                parcel.position += Vector3.up *
                    (Mathf.Sin(Time.time * 3f) * 0.0025f);
            }

            // F interaction.
            if (LoopInput.Pressed(KeyCode.F))
            {
                if (stage == 0 && parcel != null)
                {
                    float dp = Vector3.Distance(
                        new Vector3(player.position.x, 0f, player.position.z),
                        new Vector3(parcel.position.x, 0f, parcel.position.z));
                    if (dp <= 1.5f)
                    {
                        stage = 1;
                        parcel.SetParent(player, false);
                        parcel.localPosition = new Vector3(0.35f, 1.05f, 0.45f);
                        parcel.localScale = new Vector3(0.4f, 0.4f, 0.4f);
                    }
                }
                else if (stage == 1)
                {
                    string mode = ReadStr("Mode");
                    if (mode == "vehicle")
                    {
                        Transform veh = typeof(LoopSignals).GetField("Vehicle", St).GetValue(null) as Transform;
                        if (veh != null)
                        {
                            float dz = Vector2.Distance(
                                new Vector2(veh.position.x, veh.position.z),
                                new Vector2(padPos.x, padPos.z));
                            if (dz <= 2.6f)
                            {
                                stage = 2;
                                if (parcel != null) Destroy(parcel.gameObject);
                                parcel = null;
                                if (padRend != null)
                                {
                                    var m = padRend.sharedMaterial;
                                    if (m != null) { m.color = Color.green; m.SetColor("_EmissionColor", Color.green); }
                                }
                                if (beaconRend != null)
                                {
                                    var m = beaconRend.sharedMaterial;
                                    if (m != null) { m.color = Color.green; m.SetColor("_EmissionColor", Color.green); m.SetFloat("_Mode", 0); }
                                }
                                if (beacon != null)
                                    beacon.localScale *= 1.8f;
                                Set("MissionComplete", true);
                                Set("Mission", "complete");
                            }
                        }
                    }
                }
            }

            RefreshHud();
        }

        void Respawn()
        {
            stage = 0;
            Set("MissionComplete", false);
            Set("Mission", "active");

            if (parcel == null)
            {
                var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                go.name = "Parcel";
                go.transform.SetParent(transform, false);
                go.transform.position = new Vector3(laneX, 0.45f, 3.2f);
                go.transform.localScale = new Vector3(0.4f, 0.4f, 0.4f);
                var col = go.GetComponent<Collider>();
                if (col != null) Destroy(col);
                Paint(go.GetComponent<Renderer>(),
                      new Color(1f, 0.85f, 0.05f), new Color(1f, 0.75f, 0.0f));
                parcel = go.transform;
            }
            else
            {
                parcel.SetParent(transform, false);
                parcel.position = new Vector3(laneX, 0.45f, 3.2f);
                parcel.localScale = new Vector3(0.4f, 0.4f, 0.4f);
            }

            if (padRend != null)
            {
                var m = padRend.sharedMaterial;
                if (m != null) { m.color = padColor; m.SetColor("_EmissionColor", padColor * 0.4f); }
            }
            if (beaconRend != null)
            {
                var m = beaconRend.sharedMaterial;
                if (m != null)
                {
                    m.color = beaconColor;
                    m.SetColor("_EmissionColor", beaconColor);
                    m.SetFloat("_Mode", 3f);
                    m.EnableKeyword("_ALPHABLEND_ON");
                    m.DisableKeyword("_ALPHAPREMULTIPLY_ON");
                    m.renderQueue = 3000;
                    var c = m.color; c.a = 0.28f; m.color = c;
                }
            }
            if (beacon != null)
                beacon.localScale = new Vector3(1.1f, 3.5f, 1.1f);
        }

        // ---- material helpers ----
        static void Paint(Renderer r, Color albedo, Color emissive)
        {
            if (r == null) return;
            var mat = new Material(Shader.Find("Standard"));
            mat.color = albedo;
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", emissive);
            r.sharedMaterial = mat;
        }

        static void SetTransparent(Renderer r, float alpha)
        {
            if (r == null) return;
            var mat = r.sharedMaterial;
            if (mat == null) return;
            mat.SetFloat("_Mode", 3f);
            mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            mat.SetInt("_ZWrite", 0);
            mat.DisableKeyword("_ALPHATEST_ON");
            mat.EnableKeyword("_ALPHABLEND_ON");
            mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            mat.renderQueue = 3000;
            var c = mat.color; c.a = alpha; mat.color = c;
        }

        // ---- tolerant signal writers (never throw if a member is absent) ----
        static void Set(string name, object value)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            if (f == null && p == null) return;
            var type = f != null ? f.FieldType : p.PropertyType;
            if (type == typeof(Transform) && value is Component c) value = c.transform;
            else if (type.IsEnum && value != null) value = Enum.Parse(type, value.ToString(), true);
            if (f != null) f.SetValue(null, value);
            else if (p != null && p.CanWrite) p.SetValue(null, value);
        }

        // ---- tolerant signal readers (never throw if a member is absent) ----
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
