using UnityEngine;
namespace ChicagoGame
{
    public partial class RelaySequence
    {
        Renderer[][] siteRend = new Renderer[3][];
        Material[][] siteMat;
        TextMesh[] labels = new TextMesh[3];

        void BuildProps()
        {
            Vector3[] pos = { new Vector3(53,.2f,27), new Vector3(41,.2f,9), new Vector3(29,.2f,27) };
            GameObject src = GameObject.Find("AlleyDumpster") ?? GameObject.Find("dumpster_a");
            Font f = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            siteMat = new Material[3][];
            for (int i = 0; i < 3; i++)
            {
                var root = new GameObject("RelaySite" + (i + 1));
                root.transform.position = pos[i];
                Relays[i] = root.transform;
                siteRend[i] = new Renderer[0];
                if (src != null)
                {
                    var clone = Object.Instantiate(src);
                    clone.transform.SetParent(root.transform, true);
                    var mrs = clone.GetComponentsInChildren<MeshRenderer>();
                    if (mrs.Length > 0)
                    {
                        Bounds b = mrs[0].bounds;
                        foreach (var r in mrs) b.Encapsulate(r.bounds);
                        float s = 1f / Mathf.Max(b.size.x, b.size.y, b.size.z);
                        clone.transform.localScale *= s;
                        mrs = clone.GetComponentsInChildren<MeshRenderer>();
                        b = mrs[0].bounds;
                        foreach (var r in mrs) b.Encapsulate(r.bounds);
                        float ox = pos[i].x - b.center.x;
                        float oz = pos[i].z - b.center.z;
                        float oy = pos[i].y - b.min.y;
                        clone.transform.localPosition += new Vector3(ox, oy, oz);
                    }
                    foreach (var c in clone.GetComponentsInChildren<Collider>()) c.enabled = false;
                    siteRend[i] = clone.GetComponentsInChildren<Renderer>();
                }
                var mats = new Material[siteRend[i].Length];
                for (int m = 0; m < mats.Length; m++)
                    mats[m] = siteRend[i][m] ? new Material(siteRend[i][m].sharedMaterial) : null;
                siteMat[i] = mats;
                for (int m = 0; m < siteRend[i].Length && m < mats.Length; m++)
                    if (siteRend[i][m] && mats[m]) siteRend[i][m].sharedMaterial = mats[m];
                if (siteRend[i].Length > 0)
                {
                    Bounds b = siteRend[i][0].bounds;
                    foreach (var r in siteRend[i]) if (r) b.Encapsulate(r.bounds);
                    var col = root.AddComponent<BoxCollider>();
                    col.center = root.transform.InverseTransformPoint(b.center);
                    col.size = b.size;
                }
                var lo = new GameObject("Label" + (i + 1));
                lo.transform.SetParent(root.transform, false);
                lo.transform.localPosition = new Vector3(0, 1.2f, 0);
                var tm = lo.AddComponent<TextMesh>();
                tm.text = (i + 1).ToString();
                tm.characterSize = 0.12f;
                tm.fontSize = 64;
                tm.font = f;
                tm.alignment = TextAlignment.Center;
                tm.anchor = TextAnchor.MiddleCenter;
                labels[i] = tm;
            }
        }

        void SetSitesVisible(bool value)
        {
            for (int i = 0; i < 3; i++)
                if (Relays[i] != null) Relays[i].gameObject.SetActive(value);
        }

        void PaintSites(int flash)
        {
            Color charcoal = new Color(0.22f, 0.22f, 0.24f);
            Color teal = new Color(0f, 0.55f, 0.55f);
            Color green = new Color(0.2f, 0.68f, 0.2f);
            Color red = new Color(0.72f, 0.12f, 0.12f);
            for (int i = 0; i < 3; i++)
            {
                Color c = charcoal;
                if (Failed) c = red;
                else if (i == flash) c = red;
                else if (AllComplete) c = green;
                else if (i < ExpectedIndex) c = green;
                else if (i == ExpectedIndex) c = teal;
                if (siteMat != null && siteMat[i] != null)
                    foreach (var m in siteMat[i])
                    {
                        if (!m) continue;
                        m.color = c;
                        if (m.HasProperty("_EmissionColor"))
                            m.SetColor("_EmissionColor", Color.black);
                    }
                if (labels[i] && cam)
                    labels[i].transform.rotation = Quaternion.LookRotation(
                        labels[i].transform.position - cam.transform.position);
            }
        }
    }
}
