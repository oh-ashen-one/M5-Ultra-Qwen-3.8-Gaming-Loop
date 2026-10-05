using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    // Camera-child status panel that renders inside Camera.Render (NOT OnGUI).
    // Shows Health and Wanted (PursuitLevel) read directly from the real
    // LoopSignals written by the mission + combat systems. Kept as a separate
    // top-left card so the existing centred objective/controls/retry card in
    // CourierMission is left untouched.
    public class HudStatus : MonoBehaviour
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;
        TextMesh tm;
        Renderer cardRend;
        Transform barFill;          // scales horizontally with Health/100
        TextMesh money;             // cash readout (matches reference top-right)
        int lastHp = -1, lastWanted = -1;
        const float BAR_W = 0.50f;  // full-width bar in camera-space units

        public static void Install(Camera cam)
        {
            if (!cam) return;
            var go = new GameObject("HudStatus");
            go.transform.SetParent(cam.transform, false);
            go.transform.localPosition = new Vector3(-0.86f, 0.80f, 1.6f);
            go.transform.localRotation = Quaternion.identity;
            go.AddComponent<HudStatus>();
        }

        void Awake()
        {
            var card = GameObject.CreatePrimitive(PrimitiveType.Cube);
            card.name = "StatusCard";
            card.transform.SetParent(transform, false);
            card.transform.localPosition = new Vector3(0.42f, -0.045f, 0.03f);
            card.transform.localScale = new Vector3(0.92f, 0.15f, 0.01f);
            var col = card.GetComponent<Collider>();
            if (col != null) Destroy(col);
            var mat = new Material(Shader.Find("Standard"));
            mat.color = new Color(0f, 0f, 0f, 0.72f);
            card.GetComponent<Renderer>().sharedMaterial = mat;
            cardRend = card.GetComponent<Renderer>();

            tm = gameObject.AddComponent<TextMesh>();
            tm.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            tm.fontSize = 34;
            tm.characterSize = 0.011f;
            tm.anchor = TextAnchor.UpperLeft;
            tm.alignment = TextAlignment.Left;
            tm.color = Color.white;
            Refresh();
        }

        void LateUpdate()
        {
            if (tm != null) Refresh();
        }

        void Refresh()
        {
            int hp = ReadInt("Health");
            int w = ReadInt("PursuitLevel");
            if (hp == lastHp && w == lastWanted) return;
            lastHp = hp; lastWanted = w;

            string stars = "";
            for (int i = 0; i < 3; i++) stars += i < w ? " *" : " .";

            tm.text = "HEALTH " + hp + "\nWANTED" + stars;
            tm.color = hp > 60 ? new Color(0.55f, 1f, 0.55f)
                     : hp > 25 ? new Color(1f, 0.85f, 0.3f)
                               : new Color(1f, 0.35f, 0.3f);
        }

        static int ReadInt(string name)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            try
            {
                if (f != null) return Convert.ToInt32(f.GetValue(null));
                if (p != null && p.CanRead) return Convert.ToInt32(p.GetValue(null));
            }
            catch { }
            return 0;
        }
    }
}
