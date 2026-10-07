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
                new float[]{ -14, 40, 7, 6, 16,  0, 0.16f, 0.20f},
                new float[]{  -4, 41, 8, 6, 20,  0, 0.14f, 0.08f},
                new float[]{   6, 40, 7, 6, 15,  0, 0.15f, 0.26f},
                new float[]{  15, 42, 8, 7, 22,  0, 0.18f, 0.12f},
                new float[]{ -16, 58, 9, 9, 38,  0, 0.40f, 0.02f},
                new float[]{  -2, 66, 10,10, 52,  0, 0.46f, 0.00f},
                new float[]{  12, 60, 8, 8, 30,  0, 0.42f, 0.18f},
                new float[]{  22, 72, 9, 9, 44,  0, 0.52f, 0.10f},
                new float[]{  72, 10, 8, 7, 18, 90, 0.16f, 0.10f},
                new float[]{  73, 20, 7, 6, 22, 90, 0.14f, 0.24f},
                new float[]{  72, 30, 8, 7, 16, 90, 0.15f, 0.06f},
                new float[]{  74, 40, 9, 7, 24, 90, 0.18f, 0.30f},
                new float[]{  92, 14, 9, 9, 40,135, 0.40f, 0.12f},
                new float[]{ 104, 26,10,10, 58,135, 0.46f, 0.02f},
                new float[]{  90, 40, 8, 8, 32,135, 0.44f, 0.22f},
                new float[]{ 112, 48, 9, 9, 48,135, 0.52f, 0.32f},
            };
            foreach (var s in sp) Tower(root, s);
            // Two bounded visual-only ground slabs from the ORIGINAL facade mesh via
            // the proven Place mapping (rot = basis, so wS.x->X, wS.y->Y, wS.z->Z).
            // 0.24 m thick, top 0.21 m. North X-18..22 / Z33.5..81.5 (bounds Z>=32),
            // East X64..156 / Z4..60 (bounds X>=64); both outside playable
            // X-1..6/Z-2..30, alley X6..22/Z8..20, east X22..60/Z8..28. Asphalt is a
            // read-only lookup, cloned onto the two NEW renderers only.
            Material asphaltMat = null;
            foreach (var r in Object.FindObjectsOfType<MeshRenderer>(false))
            {
                if (r == null || r.gameObject.name != "road_asphalt") continue;
                var om = r.sharedMaterial;
                if (om != null && om.mainTexture != null) { asphaltMat = om; break; }
            }
            Place(root, facadeMesh, new Color(0.2f, 0.195f, 0.19f), basis,
                  new Vector3(2f, 0.09f, 57.5f), new Vector3(40f, 0.24f, 48f));
            var north = root.transform.GetChild(root.transform.childCount - 1);
            north.name = "FarGroundNorth";
            var nR = north.GetComponent<MeshRenderer>();
            if (nR != null && asphaltMat != null)
            {
                var nm = new Material(asphaltMat);
                var nb = asphaltMat.mainTextureScale;
                nm.mainTextureScale = new Vector2(Mathf.Max(0.5f, nb.x * 2f), Mathf.Max(0.5f, nb.y * 40f / 24f));
                nm.color = new Color(0.74f, 0.72f, 0.69f, 1f);
                if (nm.HasProperty("_Metallic")) nm.SetFloat("_Metallic", 0f);
                if (nm.HasProperty("_Glossiness")) nm.SetFloat("_Glossiness", 0.08f);
                if (nm.HasProperty("_EmissionColor")) nm.SetColor("_EmissionColor", Color.black);
                nR.sharedMaterial = nm;
            }
            Place(root, facadeMesh, new Color(0.2f, 0.195f, 0.19f), basis,
                  new Vector3(110f, 0.09f, 32f), new Vector3(92f, 0.24f, 56f));
            var east = root.transform.GetChild(root.transform.childCount - 1);
            east.name = "FarGroundEast";
            var eR = east.GetComponent<MeshRenderer>();
            if (eR != null && asphaltMat != null)
            {
                var em = new Material(asphaltMat);
                var eb = asphaltMat.mainTextureScale;
                em.mainTextureScale = new Vector2(Mathf.Max(0.5f, eb.x * 92f / 24f), Mathf.Max(0.5f, eb.y * 56f / 24f));
                em.color = new Color(0.74f, 0.72f, 0.69f, 1f);
                if (em.HasProperty("_Metallic")) em.SetFloat("_Metallic", 0f);
                if (em.HasProperty("_Glossiness")) em.SetFloat("_Glossiness", 0.08f);
                if (em.HasProperty("_EmissionColor")) em.SetColor("_EmissionColor", Color.black);
                eR.sharedMaterial = em;
            }
            Tiling();
            Detail();
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = new Color(0.82f, 0.71f, 0.58f, 1f);
            RenderSettings.fogStartDistance = 62f;
            RenderSettings.fogEndDistance = 230f;
            RenderSettings.fogDensity = 0.0045f;
            RenderSettings.ambientLight = new Color(0.42f, 0.41f, 0.40f, 1f);
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
            float hs = Hash(x + "," + z);
            var brick = new Color(0.30f, 0.11f, 0.085f);
            var cool = new Color(0.30f, 0.34f, 0.40f);
            var tint = Color.Lerp(Color.Lerp(brick, cool, hue), fog, fk);
            tint = new Color(tint.r * (0.86f + 0.30f * hue), tint.g * (0.86f + 0.30f * hue),
                             tint.b * (0.90f + 0.28f * hue));
            // Ground context: a thin pavement apron plus a dark plinth so each
            // tower meets the street instead of floating over bare ground.
            // Both sit on Y0, same proven Place mapping, no terrain, no collider.
            var grit = Color.Lerp(new Color(0.23f, 0.21f, 0.19f), fog, Mathf.Min(0.92f, fk + 0.30f));
            Place(asm, facadeMesh, grit, rot, new Vector3(x, 0.07f, z),
                  new Vector3(w + 2.4f + 1.6f * hs, 0.14f, d + 2.4f + 1.6f * hs));
            var plinth = Color.Lerp(new Color(0.15f, 0.13f, 0.12f), fog, fk * 0.80f);
            Place(asm, facadeMesh, plinth, rot, new Vector3(x, 0.66f, z),
                  new Vector3(w + 0.5f, 1.32f, d + 0.5f));
            Place(asm, facadeMesh, tint, rot, new Vector3(x, h * 0.5f, z), new Vector3(w, h, d));
            // Bounded window/spandrel bands: barely overscaled thin slabs of the
            // ORIGINAL facade mesh read as shadowed window strips. Band count is
            // capped so no assembly exceeds 9 renderers.
            var band = Color.Lerp(new Color(0.055f, 0.055f, 0.075f), fog, fk * 0.55f);
            int n = h > 30f ? 2 : 1;
            for (int i = 0; i < n; i++)
            {
                float y = h * (0.40f + 0.27f * i + 0.05f * hs);
                Place(asm, facadeMesh, band, rot, new Vector3(x, y, z),
                      new Vector3(w + 0.16f, Mathf.Clamp(h * 0.11f, 0.9f, 2.6f), d + 0.16f));
            }
            // Cornice band under the parapet gives the silhouette a stone cap.
            var stone = Color.Lerp(new Color(0.60f, 0.56f, 0.50f), fog, fk);
            Place(asm, facadeMesh, stone, rot, new Vector3(x, h - 0.55f, z),
                  new Vector3(w + 0.34f, 0.70f, d + 0.34f));
            var rT = Color.Lerp(new Color(0.10f, 0.12f, 0.15f), fog, fk);
            if (roofMesh != null)
                Place(asm, roofMesh, rT, rot, new Vector3(x, h + 0.06f, z),
                      new Vector3(w * 1.06f, 0.36f, d * 1.06f));
            // Rooftop variation on the taller blocks: one setback penthouse and
            // the original chimney mesh, both resting on the roof slab.
            if (h > 33f)
            {
                float ch = Mathf.Clamp(h * 0.09f, 1.4f, 4.5f);
                Place(asm, facadeMesh, Color.Lerp(tint, Color.black, 0.22f), rot,
                      new Vector3(x - w * 0.10f, h + 0.24f + ch * 0.5f, z + d * 0.08f),
                      new Vector3(w * 0.46f, ch, d * 0.46f));
                if (chimneyMesh != null)
                    Place(asm, chimneyMesh, rT, rot, new Vector3(x + w * 0.2f, h + h * 0.07f + 0.3f, z - d * 0.2f),
                          new Vector3(1.1f, h * 0.14f, 1.1f));
            }
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
            // Restrained, deterministic surface pass over the ORIGINAL Street and
            // EastStreetDetail renderers only. Each material is copied from that
            // renderer's own image-backed Standard material, so every facade/road
            // image binding, mesh, UV set, transform and culling state stays as
            // exported; nothing is added, moved, hidden, re-scaled or cleared. Only
            // the colour multiply, metallic and smoothness are nudged (matte brick,
            // matte asphalt, no specular sheen, no saturation lift) and a minority
            // of window panes gain a faint warm interior response while the rest
            // read as dark recesses. Seeds are read-only: original name plus the
            // quantised world bounds centre, never written back to any transform.
            foreach (var r in Object.FindObjectsOfType<MeshRenderer>(false))
            {
                var root = r.transform.root; if (root == null) continue;
                var rn = root.name;
                if (rn != "Street" && rn != "EastStreetDetail") continue;
                var om = r.sharedMaterial; if (om == null) continue;
                var n = r.gameObject.name; var b = r.bounds;

                bool pave = n == "StreetPavement" || n == "road_asphalt" ||
                            n == "StreetSouthWall" || n == "StreetNorthWall" ||
                            n == "StreetEastWall" || n == "StreetWestNubWall";
                bool glass = (n.Contains("glass") || n.Contains("window")) &&
                             om.HasProperty("_EmissionColor");
                bool trim = n.StartsWith("cornice") || n.StartsWith("facade_base") ||
                            n.StartsWith("pier") || n.StartsWith("sill") ||
                            n.StartsWith("lintel") || n.StartsWith("stoop");
                bool roof = n.StartsWith("roof") || n.StartsWith("chimney") ||
                            n.StartsWith("parapet") || n.StartsWith("bulkhead");
                bool brick = n.StartsWith("facade") || n.Contains("brick");
                if (!pave && !glass && !trim && !roof && !brick) continue;

                int lx = Mathf.RoundToInt(b.center.x * 0.5f);
                int lz = Mathf.RoundToInt(b.center.z * 0.5f);
                float lot = Hash(rn + "L" + lx + "," + lz);   // lot identity
                float h = Hash(n + lx + "," + lz);            // per-element

                var m = new Material(om);
                if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", glass ? 0.05f : 0f);
                if (m.HasProperty("_Glossiness"))
                    m.SetFloat("_Glossiness",
                        glass ? 0.26f + 0.18f * h :
                        roof ? 0.05f + 0.06f * h :
                        pave ? 0.07f + 0.05f * lot :
                               0.10f + 0.10f * lot);

                if (!pave)
                {
                    Color c = m.color;
                    if (glass)
                    {
                        float dim = 0.60f + 0.18f * lot;      // recessed, not mirrored
                        c = new Color(c.r * dim, c.g * dim, c.b * (dim + 0.08f), c.a);
                        bool lit = h > 0.74f;                 // few panes only
                        float g = lit ? 0.020f + 0.038f * lot : 0f;
                        m.SetColor("_EmissionColor", new Color(g, g * 0.86f, g * 0.62f, 1f));
                        if (lit) m.EnableKeyword("_EMISSION"); else m.DisableKeyword("_EMISSION");
                    }
                    else if (trim)
                    {
                        float k = 0.88f + 0.14f * lot;        // stone lintels / piers
                        c = new Color(c.r * k, c.g * k * 0.99f, c.b * (k * 1.02f), c.a);
                    }
                    else if (roof)
                    {
                        float k = 0.74f + 0.12f * lot;        // tar roofs, soot stacks
                        c = new Color(c.r * k, c.g * k * 0.99f, c.b * k, c.a);
                    }
                    else
                    {
                        float k = 0.93f + 0.12f * lot;        // per-lot exposure
                        float w = 0.015f + 0.045f * lot;      // brownstone / grey drift
                        c = new Color(c.r * (k + w), c.g * k, c.b * (k - w * 0.7f), c.a);
                    }
                    m.color = c;
                }
                r.material = m;
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
