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

        // ---- death integration (RouteMission) -------------------------------
        // DeathAuthority owns the single decision; this chapter only freezes,
        // reports and refuses to advance. FailReason carries a more specific
        // pre-existing failure (a genuine timeout or interception recorded by
        // the run) so the existing MissionBoard can show that reason instead of
        // generic wording. Nothing here ever writes health, Restarts or input.
        public string FailReason;
        string objectiveBeforeDeath;
        bool deathHeld;

        // Board palette, single source of truth. HudColor is exactly the cyan
        // BuildHud installs the route board with, so ReleaseDeath hands the
        // healthy chapter back in its own original colour rather than a
        // hand-typed approximation that could drift; DownColor is the only
        // colour a downed courier is ever shown in.
        static readonly Color HudColor = new Color(0.45f, 0.95f, 1f);
        static readonly Color DownColor = new Color(1f, 0.26f, 0.22f);

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

        Transform missionHud;
        Vector3 hudScale0 = Vector3.one;
        Vector3 missionPos0 = Vector3.zero;
        bool missionCached;
        Transform card;

        Transform missionCard;
        Vector3 mcPos0 = Vector3.zero;
        Vector3 mcScale0 = Vector3.one;
        bool mcCached;

        Transform hudStatus;
        Vector3 hsPos0 = Vector3.zero;
        Vector3 hsScale0 = Vector3.one;
        bool hsCached;

        void BuildHud()
        {
            var go = new GameObject("RouteHud");
            go.transform.SetParent(cam.transform, false);
            go.transform.localPosition = new Vector3(0.52f, 0.85f, 1.6f);
            go.transform.localRotation = Quaternion.identity;
            hud = go.AddComponent<TextMesh>();
            hud.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            hud.fontSize = 40;
            hud.characterSize = 0.0175f;
            hud.anchor = TextAnchor.UpperCenter;
            hud.alignment = TextAlignment.Center;
            hud.color = HudColor;
            hud.text = "";

            var mh = GameObject.Find("MissionHud");
            if (mh != null)
            {
                missionHud = mh.transform;
                missionPos0 = mh.transform.localPosition;
                hudScale0 = mh.transform.localScale;
                missionCached = true;
                Transform mc = mh.transform.Find("HudCard");
                if (mc != null)
                {
                    missionCard = mc;
                    mcPos0 = mc.localPosition;
                    mcScale0 = mc.localScale;
                    mcCached = true;
                }
            }

            Transform c = Find("HudCard");
            if (c != null)
            {
                var clone = Instantiate(c.gameObject, go.transform);
                card = clone.transform;
                card.localPosition = new Vector3(0f, -0.06f, 0.025f);
                card.localRotation = Quaternion.identity;
                card.localScale = new Vector3(1.40f, 0.23f, 0.01f);
                var col = card.GetComponent<Collider>(); if (col != null) col.enabled = false;
            }
            if (card != null) card.gameObject.SetActive(false);
        }

        void LateUpdate()
        {
            if (hud == null) return;
            bool chapter = RouteStage >= 1;

            if (hudStatus == null)
            {
                var hs = GameObject.Find("HudStatus");
                if (hs != null)
                {
                    hudStatus = hs.transform;
                    hsPos0 = hs.transform.localPosition;
                    hsScale0 = hs.transform.localScale;
                    hsCached = true;
                }
            }

            if (missionCached)
            {
                if (chapter)
                {
                    missionHud.localPosition = new Vector3(-0.68f, -0.70f, 1.6f);
                    missionHud.localScale = hudScale0 * 0.9f;
                }
                else
                {
                    missionHud.localPosition = missionPos0;
                    missionHud.localScale = hudScale0;
                }
            }

            if (mcCached)
            {
                if (chapter)
                {
                    missionCard.localPosition = new Vector3(0f, -0.075f, 0.025f);
                    missionCard.localScale = new Vector3(1.20f, 0.24f, 0.01f);
                }
                else
                {
                    missionCard.localPosition = mcPos0;
                    missionCard.localScale = mcScale0;
                }
            }

            if (hsCached)
            {
                if (chapter) hudStatus.localPosition = new Vector3(-1.20f, 0.85f, 1.6f);
                else hudStatus.localPosition = hsPos0;
                hudStatus.localScale = hsScale0;
            }

            if (card != null) card.gameObject.SetActive(chapter && hud.text.Length > 0);

            if (tintedMat != null)
            {
                if (RouteStage == 1)
                {
                    tintedMat.color = new Color(0.10f, 0.50f, 0.48f);
                    tintedMat.SetColor("_EmissionColor", new Color(0.015f, 0.10f, 0.09f));
                }
                else if (RouteStage == 2)
                {
                    tintedMat.color = new Color(0.12f, 0.48f, 0.18f);
                    tintedMat.SetColor("_EmissionColor", new Color(0.015f, 0.08f, 0.02f));
                }
            }

            if (!chapter) return;

            if (RouteStage == 2)
            {
                hud.text = "\u2605 EAST DEAD-DROP COMPLETE \u2605\nChapter complete";
                return;
            }

            var veh = ReadTransform("Vehicle");
            string mode = ReadStr("Mode");
            bool inCar = mode == "vehicle" && veh != null;
            Vector3 tgt = Cache != null ? Cache.position : new Vector3(50f, 0f, 18f);

            if (inCar)
            {
                int d = Mathf.RoundToInt(XZDist(veh.position, tgt));
                hud.text = "EAST DEAD-DROP\nDrive to cache (" + d + "m)  E to exit";
            }
            else if (reachedInVehicle)
            {
                int d = Mathf.RoundToInt(XZDist(player.transform.position, tgt));
                hud.text = "EAST DEAD-DROP\nWalk to cache (" + d + "m)  F to place";
            }
            else
            {
                hud.text = "EAST DEAD-DROP\nEnter the coupe (E)";
            }
        }
        void Update()
        {
            int r = ReadInt("Restarts");
            if (r != lastRestarts)
            {
                // Ordinary R is the only thing that re-opens this chapter: it
                // clears the stage, the cache, the board text and this file's
                // death report, on the very same Restarts edge that releases
                // the DeathAuthority latch. A dead courier can always be reset.
                lastRestarts = r;
                RouteStage = 0; RouteComplete = false;
                Objective = ""; reachedInVehicle = false;
                FailReason = null;
                deathHeld = false;
                objectiveBeforeDeath = null;
                if (Cache != null) Cache.gameObject.SetActive(false);
                if (hud != null) hud.text = "";
                return;
            }

            // Death outranks every route input, including a same-frame F at the
            // cache: while the courier is down the dead-drop cannot activate,
            // cannot be re-entered and cannot be banked. Anything genuinely
            // banked before that lethal frame stays exactly as it was.
            if (DeathAuthority.IsDead) { HoldForDeath(); return; }
            ReleaseDeath();

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
                    // Second live read of the authority: if this frame's lethal
                    // hit lands after the check above, the drop still is not
                    // banked. Death wins simultaneous objective input.
                    if (DeathAuthority.IsDead) { HoldForDeath(); return; }
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

        // ---- death hold -----------------------------------------------------
        // Freeze the chapter without rewriting it. RouteStage, RouteComplete,
        // reachedInVehicle and an already-placed cache stay exactly as the
        // courier left them; only the visible objective text reports the
        // failure, and only an ordinary R (the Restarts edge above) clears it.
        void HoldForDeath()
        {
            if (!deathHeld)
            {
                deathHeld = true;
                objectiveBeforeDeath = Objective;
            }
            Objective = FailureText();
            if (hud != null) { hud.text = FailureText(); hud.color = DownColor; }
        }

        void ReleaseDeath()
        {
            if (!deathHeld) return;
            deathHeld = false;
            Objective = objectiveBeforeDeath;
            objectiveBeforeDeath = null;
            if (hud != null) hud.color = HudColor;
        }

        /// <summary>Board copy for a downed courier. A more specific
        /// pre-existing failure reason is kept ahead of it, but the depleted
        /// health and the R reset are always named.</summary>
        string FailureText()
        {
            if (!string.IsNullOrEmpty(FailReason))
                return FailReason + "\\nHEALTH DEPLETED - PRESS R";
            return "COURIER DOWN\\nHEALTH DEPLETED - PRESS R";
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
                var c = Instantiate(src, anchor.transform).transform;
                c.localPosition = Vector3.zero;
                c.localRotation = Quaternion.identity;
                c.localScale = src.localScale;
                foreach (var col in c.GetComponentsInChildren<Collider>()) col.enabled = false;

                foreach (var rd in c.GetComponentsInChildren<Renderer>())
                {
                    var m = new Material(rd.sharedMaterial);
                    string rn = rd.name.ToLower();
                    if (rn.Contains("wheel"))
                    {
                        m.color = new Color(0.07f, 0.07f, 0.08f);
                        m.DisableKeyword("_EMISSION");
                        m.SetColor("_EmissionColor", Color.black);
                    }
                    else if (rn.Contains("rail"))
                    {
                        m.color = new Color(0.12f, 0.50f, 0.55f);
                        m.EnableKeyword("_EMISSION");
                        m.SetColor("_EmissionColor", new Color(0.03f, 0.32f, 0.36f));
                        tintedMat = m;
                    }
                    else
                    {
                        m.color = new Color(0.13f, 0.21f, 0.23f);
                        m.DisableKeyword("_EMISSION");
                        m.SetColor("_EmissionColor", Color.black);
                    }
                    rd.sharedMaterial = m;
                }
                // Aggregate bounds of all cloned renderers
                Bounds agg = new Bounds(c.position, Vector3.zero);
                foreach (var rd in c.GetComponentsInChildren<Renderer>())
                    agg.Encapsulate(rd.bounds);
                // World offset: center X/Z -> anchor X/Z, min Y -> anchor.y
                Vector3 aPos = anchor.transform.position;
                Vector3 delta = new Vector3(
                    aPos.x - agg.center.x,
                    aPos.y - agg.min.y,
                    aPos.z - agg.center.z);
                c.position += delta;
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
