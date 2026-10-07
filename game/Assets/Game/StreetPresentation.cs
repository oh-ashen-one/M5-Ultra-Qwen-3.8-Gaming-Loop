using UnityEngine;

namespace ChicagoGame
{
    // Visual-only golden-hour backdrop pass. Builds a bounded skyline of
    // distant building assemblies from ORIGINAL exported facade/roof/chimney
    // meshes (no primitives, no IO, no animation, no colliders, no moves of
    // existing objects). Also corrects brick tiling on the long stretched
    // outer walls / road copies and adds restrained per-lot trim tint plus a
    // few warm dusk-lit east-street windows. Gameplay roots, colliders,
    // route openings, anchors, camera, HUD and controllers are untouched.
    public static class StreetPresentation
    {
        static Quaternion basis;
        static Mesh facadeMesh, roofMesh, chimneyMesh;
        static Material facadeMat;

        public static void Install()
        {
            Collect();
            if (facadeMesh == null || facadeMat == null) return;

            var root = new GameObject("SkylineBackdrop");
            // x,z,w,d,h,yaw,fogK,hue  (16 assemblies, behind outer walls only)
            var sp = new float[][]
            {
                new float[]{ 96, 12, 5, 5, 30,180, 0.06f, 0.05f},
                new float[]{112, 22, 6, 6, 46,180, 0.20f, 0.12f},
                new float[]{126, 16, 5, 5, 38,180, 0.34f, 0.02f},
                new float[]{140, 26, 7, 7, 62,180, 0.46f, 0.00f},
                new float[]{150, 12, 4, 4, 26,180, 0.55f, 0.30f},
                new float[]{120, 31, 5, 6, 34,180, 0.30f, 0.18f},
                new float[]{104, 32, 6, 5, 22,180, 0.12f, 0.26f},
                new float[]{  2, 44, 6, 6, 24,  0, 0.18f, 0.10f},
                new float[]{ -4, 52, 5, 5, 30,  0, 0.30f, 0.22f},
                new float[]{  6, 58, 7, 6, 40,  0, 0.40f, 0.02f},
                new float[]{  0, 66, 5, 5, 26,  0, 0.50f, 0.16f},
                new float[]{  8, 74, 6, 6, 34,  0, 0.58f, 0.28f},
                new float[]{ 70, 44, 6, 6, 28,135, 0.22f, 0.12f},
                new float[]{ 82, 52, 5, 5, 22,135, 0.34f, 0.24f},
                new float[]{ 66, 35, 5, 6, 18,135, 0.16f, 0.06f},
                new float[]{ 92, 34, 6, 5, 24,135, 0.40f, 0.32f},
            };
            foreach (var s in sp) Tower(root, s);
            Tiling();
            Detail();
        }

        static void Collect()
        {
            foreach (var mf in Object.FindObjectsOfType<MeshFilter>(false))
            {
                if (mf == null || mf.sharedMesh == null) continue;
                var n = mf.gameObject.name;
                if (facadeMesh == null && n == "facade_wall")
                {
                    facadeMesh = mf.sharedMesh; basis = mf.transform.rotation;
                    var r = mf.GetComponent<MeshRenderer>();
                    if (r != null && r.sharedMaterial != null) facadeMat = r.sharedMaterial;
                }
                else if (roofMesh == null && n == "roof_slab") roofMesh = mf.sharedMesh;
                else if (chimneyMesh == null && n == "chimney") chimneyMesh = mf.sharedMesh;
            }
        }

        static void Tower(GameObject par, float[] s)
        {
            float x = s[0], z = s[1], w = s[2], d = s[3], h = s[4], yaw = s[5], fk = s[6], hue = s[7];
            var asm = new GameObject("Tower");
            asm.transform.SetParent(par.transform, false);
            var rot = Quaternion.Euler(0f, yaw, 0f) * basis;
            var fog = RenderSettings.fogColor;
            var brick = new Color(0.30f, 0.11f, 0.085f);
            var cool = new Color(0.30f, 0.34f, 0.40f);
            var tint = Color.Lerp(Color.Lerp(brick, cool, hue), fog, fk);
            tint = new Color(tint.r * (0.86f + 0.30f * hue), tint.g * (0.86f + 0.30f * hue),
                             tint.b * (0.90f + 0.28f * hue));
            Place(asm, facadeMesh, tint, rot, new Vector3(x, h * 0.5f, z), new Vector3(w, h, d));
            var rT = Color.Lerp(new Color(0.10f, 0.12f, 0.15f), fog, fk);
            if (roofMesh != null)
                Place(asm, roofMesh, rT, rot, new Vector3(x, h + 0.06f, z),
                      new Vector3(w * 1.06f, 0.36f, d * 1.06f));
            if (h > 33f && chimneyMesh != null)
                Place(asm, chimneyMesh, rT, rot, new Vector3(x + w * 0.2f, h + h * 0.07f + 0.3f, z - d * 0.2f),
                      new Vector3(1.1f, h * 0.14f, 1.1f));
        }

        // Proven local->world box mapping (localX->Z, localY->X, localZ->Y),
        // placed so the mesh bounds center lands on ctr. No collider added.
        static void Place(GameObject par, Mesh m, Color col, Quaternion rot, Vector3 ctr, Vector3 wS)
        {
            var b = m.bounds;
            var o = new GameObject("bk");
            o.transform.SetParent(par.transform, false);
            o.transform.rotation = rot;
            var s = new Vector3(wS.z / b.size.x, wS.x / b.size.y, wS.y / b.size.z);
            o.transform.localScale = s;
            o.transform.position = ctr - rot * Vector3.Scale(b.center, s);
            o.AddComponent<MeshFilter>().sharedMesh = m;
            var mr = o.AddComponent<MeshRenderer>();
            var mat = new Material(facadeMat);
            mat.color = col;
            mat.EnableKeyword("_EMISSION");
            mat.SetColor("_EmissionColor", Color.black);
            mr.sharedMaterial = mat;
        }

        // Un-stretch the brick/asphalt on the long scaled outer walls + road
        // copies by matching the tiling to the world bounds, plus a soft warm
        // wall tint. Material-only change; transforms/geometry untouched.
        static void Tiling()
        {
            foreach (var r in Object.FindObjectsOfType<MeshRenderer>(false))
            {
                var n = r.gameObject.name;
                bool wall = n == "StreetSouthWall" || n == "StreetNorthWall" ||
                            n == "StreetEastWall" || n == "StreetWestNubWall";
                bool road = n == "StreetPavement" || n == "road_asphalt";
                if (!wall && !road) continue;
                var om = r.sharedMaterial; if (om == null) continue;
                var m = new Material(om);
                var hor = Mathf.Max(0.01f, Mathf.Max(r.bounds.size.x, r.bounds.size.z));
                var bs = om.mainTextureScale;
                if (road)
                    m.mainTextureScale = new Vector2(Mathf.Max(0.5f, bs.x * hor / 12f),
                                                     Mathf.Max(0.5f, bs.y * hor / 12f));
                else
                    m.mainTextureScale = new Vector2(Mathf.Max(0.5f, bs.x * hor / 12f),
                                                     Mathf.Max(0.3f, bs.y * r.bounds.size.y / 8.8f));
                m.color = new Color(1f, 0.97f, 0.93f, 1f);
                r.material = m;
            }
        }

        // Restrained dusk detail on the east-street rowhouses only: a few
        // warm-lit window panes and a per-lot tint on cornice/base/pier trims.
        static void Detail()
        {
            int i = 0;
            foreach (var r in Object.FindObjectsOfType<MeshRenderer>(false))
            {
                if (r.transform.root == null || r.transform.root.name != "EastStreetDetail") continue;
                var n = r.gameObject.name; var om = r.sharedMaterial; if (om == null) continue;
                float h = Hash(n + i); i++;
                if (n.Contains("_glass"))
                {
                    if (h > 0.46f) continue;
                    var m = new Material(om);
                    float g = 0.03f + 0.11f * h;
                    m.EnableKeyword("_EMISSION");
                    m.SetColor("_EmissionColor", new Color(g, g * 0.80f, g * 0.55f, 1f));
                    r.material = m;
                }
                else if (n.StartsWith("cornice") || n.StartsWith("facade_base") || n.StartsWith("pier"))
                {
                    var m = new Material(om);
                    m.color = new Color(0.92f + 0.16f * h, 0.92f + 0.16f * h, 0.95f + 0.10f * h, 1f);
                    r.material = m;
                }
            }
        }

        static float Hash(string s)
        {
            uint h = 2166136261u;
            foreach (char c in s) { h ^= (uint)c; h *= 16777619u; }
            return ((h >> 8) & 0xFFFFu) / 65535f;
        }
    }
}
