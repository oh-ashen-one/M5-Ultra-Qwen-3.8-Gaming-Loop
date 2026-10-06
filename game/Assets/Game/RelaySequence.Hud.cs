using UnityEngine;
namespace ChicagoGame
{
    public partial class RelaySequence
    {
        TextMesh relayHud;
        Transform relayCard;
        static readonly string[] DIR = { "NORTH", "SOUTH", "NORTHWEST" };

        void BuildHud()
        {
            var go = new GameObject("RelayHud");
            go.transform.SetParent(cam.transform, false);
            go.transform.localPosition = new Vector3(.52f, -.55f, 1.6f);
            go.transform.localRotation = Quaternion.identity;

            var t = new GameObject("Text");
            t.transform.SetParent(go.transform, false);
            relayHud = t.AddComponent<TextMesh>();
            relayHud.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            relayHud.fontSize = 40;
            relayHud.characterSize = .0125f;
            relayHud.anchor = TextAnchor.UpperCenter;
            relayHud.alignment = TextAlignment.Center;
            relayHud.color = new Color(.55f, .8f, .8f);
            relayHud.text = "";

            Transform src = null;
            var hud = GameObject.Find("RouteHud");
            if (hud != null) src = hud.transform.Find("HudCard");
            if (src == null) { var c = GameObject.Find("HudCard"); if (c) src = c.transform; }
            if (src != null)
            {
                var clone = Instantiate(src.gameObject, go.transform);
                clone.transform.localPosition = new Vector3(0f, -.065f, .025f);
                clone.transform.localScale = new Vector3(1.3f, .23f, .01f);
                clone.transform.localRotation = Quaternion.identity;
                var col = clone.GetComponent<Collider>();
                if (col != null) col.enabled = false;
                relayCard = clone.transform;
            }
        }

        void HideHud()
        {
            if (relayHud) relayHud.text = "";
            if (relayCard) relayCard.gameObject.SetActive(false);
            Objective = "";
        }

        void UpdateHud()
        {
            if (!Active) { HideHud(); return; }
            if (relayCard) relayCard.gameObject.SetActive(true);
            if (!relayHud) return;

            string s;
            if (AllComplete) s = "RELAY COMPLETE\nThree relays online";
            else if (Failed) s = "RELAY FAILED\nR to retry";
            else
            {
                int rem = Mathf.CeilToInt(Remaining);
                int i = Mathf.Min(ExpectedIndex, 2);
                float dist = 0f;
                if (Relays[i])
                {
                    float dx = Relays[i].position.x - player.transform.position.x;
                    float dz = Relays[i].position.z - player.transform.position.z;
                    dist = Mathf.Sqrt(dx * dx + dz * dz);
                }
                s = "RELAY " + ActivationCount + "/3  " + rem + "s\n" +
                    (i + 1) + " " + DIR[i] + " " + Mathf.RoundToInt(dist) + "F";
            }
            relayHud.text = s;
            Objective = s;
        }
    }
}