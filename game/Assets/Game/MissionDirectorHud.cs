using UnityEngine;
using System.Text.RegularExpressions;
using System.Reflection;
using System.Collections.Generic;

namespace ChicagoGame
{
    [DefaultExecutionOrder(31000)]
    public class MissionDirectorHud : MonoBehaviour
    {
        static MissionDirectorHud _inst;
        GameObject _player; Camera _cam;
        TextMesh _board; Renderer[] _hide; Transform _hudStatus;
        RelaySequence _relay; RouteMission _route; CourierMission _courier;
        InterceptionMission _interception; CounterExfilMission _counter;

        // Board palette, single source of truth. BoardColor is exactly the
        // colour Setup installs the board with, so a released death hands the
        // live or completed chapter copy back in its own original colour;
        // DownColor is the only colour a downed courier is ever shown in, so a
        // health-depleted failure cannot be mistaken for an objective.
        static readonly Color BoardColor = new Color(.95f, .95f, .95f);
        static readonly Color DownColor = new Color(1f, .26f, .22f);

        public static void Install(GameObject player, Camera cam)
        {
            if (_inst != null) return;
            CounterExfilMission.Install(player, cam);
            var go = new GameObject("MissionDirectorHud");
            _inst = go.AddComponent<MissionDirectorHud>();
            _inst._player = player; _inst._cam = cam;
            _inst.Setup();
        }

        void Setup()
        {
            var b = new GameObject("MissionBoard");
            b.transform.SetParent(_cam.transform, false);
            b.transform.localPosition = new Vector3(.50f, .85f, 1.6f);
            b.transform.localRotation = Quaternion.identity;
            _board = b.AddComponent<TextMesh>();
            _board.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            _board.fontSize = 40; _board.characterSize = .0145f;
            _board.anchor = TextAnchor.UpperCenter;
            _board.alignment = TextAlignment.Center;
            _board.color = BoardColor;

            Transform src = null;
            var mh = GameObject.Find("MissionHud");
            if (mh) src = mh.transform.Find("HudCard");
            if (!src) { var c = GameObject.Find("HudCard"); if (c) src = c.transform; }
            if (src)
            {
                var cl = Instantiate(src.gameObject, b.transform);
                cl.name = "BoardCard";
                cl.transform.localPosition = new Vector3(0, -.125f, .025f);
                cl.transform.localScale = new Vector3(1.5f, .36f, .01f);
                cl.transform.localRotation = Quaternion.identity;
                cl.SetActive(true);
                var unlitShader = Resources.Load<Shader>("HudOpaque");
                var boardMat = new Material(unlitShader);
                boardMat.color = new Color(0.06f, 0.07f, 0.085f, 1f);
                foreach (var r in cl.GetComponentsInChildren<Renderer>()) { r.material = boardMat; r.enabled = true; }
                foreach (var col in cl.GetComponentsInChildren<Collider>()) col.enabled = false;
            }

            var list = new List<Renderer>();
            foreach (var n in new[] { "MissionHud", "RouteHud", "RelayHud" })
            { var h = GameObject.Find(n); if (h) list.AddRange(h.GetComponentsInChildren<Renderer>(true)); }
            _hide = list.ToArray();

            var hs = GameObject.Find("HudStatus");
            if (hs) _hudStatus = hs.transform;
            _relay = FindAny<RelaySequence>();
            _route = FindAny<RouteMission>();
            _courier = FindAny<CourierMission>();
        }

        void LateUpdate()
        {
            if (!_hudStatus) { var hs = GameObject.Find("HudStatus"); if (hs) _hudStatus = hs.transform; }
            if (_hudStatus) _hudStatus.localPosition = new Vector3(-1.20f, .85f, 1.6f);
            if (!_relay) _relay = FindAny<RelaySequence>();
            if (!_route) _route = FindAny<RouteMission>();
            if (!_courier) _courier = FindAny<CourierMission>();
            if (!_counter) _counter = FindAny<CounterExfilMission>();

            var _interception = FindAny<InterceptionMission>();

            // Death outranks every board line, live or completed, and is read
            // from the single authority before any chapter is consulted: a
            // courier whose health is spent never keeps reading "PARCEL IN
            // HAND", "DELIVERY COMPLETE" or a live interception objective -
            // he reads the depleted health and the ordinary R retry that
            // releases the latch. A more specific failure a chapter genuinely
            // recorded first is kept ahead of the death line instead of being
            // overwritten by it.
            bool down = DeathAuthority.IsDead;
            string s = down ? DeathBoard(_interception, _counter) : null;

            if (s == null)
            {
                if (_counter != null && _counter.BoardPriority)
                    s = _counter.Objective;
                else if (_counter != null && _counter.Armed)
                {
                    string old = _interception != null ? _interception.Objective : null;
                    string line = _counter.HudLine;
                    if (!string.IsNullOrEmpty(old))
                        s = string.IsNullOrEmpty(line) ? old : old + "\n" + line;
                    else if (!string.IsNullOrEmpty(line))
                        s = line;
                }
                else if (_interception != null && _interception.Active)
                    s = _interception.Objective;
                else if (_relay != null && _relay.Active)
                {
                    string two = _relay.Objective ?? "OBJECTIVE UNAVAILABLE";
                    string foot = "\nDelivery complete / Dead-drop complete";
                    if (_relay.AllComplete) foot += "\nR reset";
                    s = two + foot;
                }
                else if (_route != null && _route.RouteStage >= 1)
                {
                    var rh = GameObject.Find("RouteHud");
                    var rt = rh ? rh.GetComponentInChildren<TextMesh>(true) : null;
                    string two = rt ? rt.text : "";
                    string foot = "\nDELIVERY COMPLETE";
                    s = two + foot;
                }
                else if (_courier != null) s = Courier(_courier);
            }

            _board.text = s ?? "OBJECTIVE UNAVAILABLE";
            // The colour follows the same verdict, so the failure is
            // unmistakable and a released death returns the board to exactly
            // the colour Setup installed.
            _board.color = down ? DownColor : BoardColor;
            foreach (var r in _hide) if (r) r.enabled = false;
        }

        /// <summary>Board copy for a downed courier, chosen before any chapter
        /// is consulted so a health-depleted failure always beats live and
        /// completed chapter text. Built with real line breaks so the TextMesh
        /// actually wraps onto separate lines, and always names the ordinary R
        /// reset - the only event that releases the DeathAuthority latch.
        /// Where a chapter genuinely recorded a more specific failure first
        /// (a runner that really escaped, a relay window that really expired,
        /// the route's own recorded reason) that reason leads and the death
        /// line follows it, so history is reported rather than overwritten;
        /// where no such record exists nothing is invented and only the
        /// depleted health is stated. The chapter consulted most recently -
        /// the counter-exfil, then the interception, then the dead-drop chain,
        /// then the route.</summary>
        string DeathBoard(InterceptionMission im, CounterExfilMission ce)
        {
            string why = ce != null ? ce.FailReason : null;
            if (string.IsNullOrEmpty(why) && im != null) why = im.FailReason;
            if (string.IsNullOrEmpty(why) && _relay != null) why = _relay.FailReason;
            if (string.IsNullOrEmpty(why) && _route != null) why = _route.FailReason;
            if (string.IsNullOrEmpty(why))
                return "COURIER DOWN\nHEALTH DEPLETED\nPRESS R TO RESTART";
            return why + "\nCOURIER DOWN - HEALTH DEPLETED\nPRESS R TO RESTART";
        }

        string Courier(CourierMission cm)
        {
            string m = ReadStr("Mission");
            if (m == "failed") return "MISSION FAILED\nR to retry";
            if (m == "complete") return "DELIVERY COMPLETE\nR to reset";

            bool carry = cm.parcel && cm.parcel.IsChildOf(_player.transform);
            string mode = ReadStr("Mode");
            Transform veh = typeof(LoopSignals).GetField("Vehicle",
                BindingFlags.Static | BindingFlags.Public)?.GetValue(null) as Transform;
            Vector3 me = (mode == "vehicle" && veh) ? veh.position : _player.transform.position;
            me.y = 0; int cd = ParseCd();

            if (!carry)
            {
                Vector3 t = cm.parcel ? cm.parcel.position : Vector3.zero; t.y = 0;
                int d = Mathf.RoundToInt(Vector3.Distance(me, t));
                return "COURIER: grab parcel\n" + d + "m, F grab"
                    + (cd > 0 ? " / " + cd + "s" : "") + "\nWASD move | E car | R reset";
            }
            Vector3 p = cm.padRend ? cm.padRend.transform.position : Vector3.zero; p.y = 0;
            int dd = Mathf.RoundToInt(Vector3.Distance(me, p));
            return "PARCEL IN HAND\n" + dd + "m" + (cd > 0 ? " / " + cd + "s" : "")
                + "\nE car | F deliver | Mouse0 fire\nR reset";
        }

        int ParseCd()
        {
            var mh = GameObject.Find("MissionHud");
            if (!mh) return 0;
            var tm = mh.GetComponentInChildren<TextMesh>(true);
            if (!tm) return 0;
            var mt = Regex.Match(tm.text, @"\[?(\d+)\s*s");
            return mt.Success ? int.Parse(mt.Groups[1].Value) : 0;
        }

        T FindAny<T>() where T : Component
        { var a = FindObjectsOfType<T>(); return a.Length > 0 ? a[0] : null; }

        static string ReadStr(string f)
        {
            var fi = typeof(LoopSignals).GetField(f,
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            return fi != null ? fi.GetValue(null) as string : "";
        }
    }
}
