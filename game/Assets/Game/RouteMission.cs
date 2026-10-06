using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    public class RouteMission : MonoBehaviour
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;
        public int RouteStage;
        public bool RouteComplete;
        public Transform Cache;
        public string Objective;

        GameObject player;
        Camera cam;
        TextMesh hud;
        int lastRestarts;
        bool reachedInVehicle;
        Material tintedMat;

        public static void Install(GameObject player, Camera cam)
        {
            if (!player || !cam) return;
            var host = new GameObject("RouteMission");
            host.transform.SetParent(null, false);
            host.transform.position = Vector3.zero;
            var r = host.AddComponent<RouteMission>();
            r.player = player;
            r.cam = cam;
            r.lastRestarts = ReadInt("Restarts");
            r.BuildHud();
        }

        void BuildHud()
        {
            var go = new GameObject("RouteHud");
            go.transform.SetParent(cam.transform, false);
            go.transform.localPosition = new Vector3(0.62f, -0.50f, 1.6f);
            go.transform.localRotation = Quaternion.identity;
            hud = go.AddComponent<TextMesh>();
            hud.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            hud.fontSize = 30;
            hud.characterSize = 0.009f;
            hud.anchor = TextAnchor.LowerRight;
            hud.alignment = TextAlignment.Right;
            hud.color = new Color(0.45f, 0.95f, 1f);
            hud.text = "";
        }

        void Update()
        {
            int r = ReadInt("Restarts");
            if (r != lastRestarts)
            {
                lastRestarts = r;
                RouteStage = 0; RouteComplete = false;
                Objective = ""; reachedInVehicle = false;
                if (Cache != null) Cache.gameObject.SetActive(false);
                if (hud != null) hud.text = "";
                return;
            }

            if (RouteStage == 0)
            {
                if (ReadStr("Mission") == "complete")
                {
                    RouteStage = 1;
                    Objective = "EAST DEAD-DROP: drive east to the cache and place it";
                    ActivateCache();
                }
                return;
            }

            if (RouteStage == 2)
            {
                if (hud != null)
                    hud.text = "\u2605 EAST DEAD-DROP COMPLETE \u2605\nThis route stage is finished.";
                return;
            }

            var veh = ReadTransform("Vehicle");
            string mode = ReadStr("Mode");
            bool inCar = mode == "vehicle" && veh != null;

            if (inCar)
            {
                float dv = XZDist(veh.position, new Vector3(50f, 0f, 18f));
                if (dv <= 6f) reachedInVehicle = true;
                if (hud != null)
                    hud.text = "EAST DEAD-DROP\nDrive within 6m of cache: " + Mathf.RoundToInt(dv)
                        + "m\nThen press E to exit, walk close, press F";
            }
            else
            {
                if (!reachedInVehicle)
                {
                    if (hud != null)
                        hud.text = "EAST DEAD-DROP\nEnter coupe (E), drive east to (50,18)";
                    return;
                }
                float dp = XZDist(player.transform.position, new Vector3(50f, 0f, 18f));
                if (hud != null)
                    hud.text = "EAST DEAD-DROP\nWalk to cache: " + Mathf.RoundToInt(dp)
                        + "m\nPress F to place (<=1.5m)";
                if (dp <= 1.5f && LoopInput.Pressed(KeyCode.F))
                {
                    RouteStage = 2; RouteComplete = true;
                    Objective = "EAST DEAD-DROP COMPLETE";
                    if (tintedMat != null)
                    {
                        tintedMat.color = Color.green;
                        tintedMat.SetColor("_EmissionColor", Color.green * 0.7f);
                    }
                }
            }
        }

        void ActivateCache()
        {
            if (Cache != null) { Cache.gameObject.SetActive(true); return; }
            var anchor = new GameObject("RouteCache");
            anchor.transform.SetParent(null, false);
            anchor.transform.position = new Vector3(50f, 0.14f, 18f);
            anchor.transform.rotation = Quaternion.identity;
            Cache = anchor.transform;

            Transform src = Find("AlleyDumpster");
            if (src == null) src = Find("dumpster_a");

            if (src != null)
            {
                var c = Instantiate(src, anchor).transform;
                c.localPosition = Vector3.zero;
                c.localRotation = Quaternion.identity;
                c.localScale = src.localScale;
                foreach (var col in c.GetComponentsInChildren<Collider>()) col.enabled = false;
                foreach (var rd in c.GetComponentsInChildren<Renderer>())
                {
                    var m = new Material(rd.sharedMaterial);
                    m.color = new Color(0.15f, 0.82f, 1f);
                    m.EnableKeyword("_EMISSION");
                    m.SetColor("_EmissionColor", new Color(0.05f, 0.45f, 0.65f));
                    rd.sharedMaterial = m;
                    if (tintedMat == null) tintedMat = m;
                }
                var r0 = c.GetComponentInChildren<Renderer>();
                if (r0 != null)
                {
                    var b = r0.bounds;
                    c.localPosition = new Vector3(0f, 0.14f - b.min.y, 0f);
                }
            }
            Cache.gameObject.SetActive(true);
        }

        static Transform Find(string n) { var g = GameObject.Find(n); return g != null ? g.transform : null; }
        static float XZDist(Vector3 a, Vector3 b) => Vector2.Distance(new Vector2(a.x, a.z), new Vector2(b.x, b.z));
        static string ReadStr(string n)
        {
            try { var f = typeof(LoopSignals).GetField(n, St); return f != null ? f.GetValue(null) as string : null; }
            catch { return null; }
        }
        static int ReadInt(string n)
        {
            try { var f = typeof(LoopSignals).GetField(n, St); return f != null ? Convert.ToInt32(f.GetValue(null)) : 0; }
            catch { return 0; }
        }
        static Transform ReadTransform(string n)
        {
            try { var f = typeof(LoopSignals).GetField(n, St); return f != null ? f.GetValue(null) as Transform : null; }
            catch { return null; }
        }
    }
}
