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

        public static void Install(GameObject player, Camera cam)
        {
            if (_inst != null) return;
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
            _board.color = new Color(.95f, .95f, .95f);

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
                var unlitShader = Shader.Find("Unlit/Color");
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

            string s = null;
            if (_relay != null && _relay.Active)
            {
                string two = _relay.Objective ?? "OBJECTIVE UNAVAILABLE";
                string foot = "\nDelivery complete / Dead-drop complete";
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

            _board.text = s ?? "OBJECTIVE UNAVAILABLE";
            foreach (var r in _hide) if (r) r.enabled = false;
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
