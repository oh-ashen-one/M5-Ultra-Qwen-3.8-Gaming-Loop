using UnityEngine;

namespace ChicagoGame
{
    // Enhances the existing east street (X22..60, Z8..28) with sidewalks,
    // curbs, lane dashes and a darker road tint. All geometry uses the
    // original Pavement mesh via the proven ConnectedStreet local-to-world
    // mapping (localX->worldZ, localY->worldX, localZ->worldY).
    public static class EastStreetGround
    {
        public static void Install(GameObject parent)
        {
            var pv = GameObject.Find("Pavement");
            if (pv == null) return;
            var omf = pv.GetComponent<MeshFilter>();
            var omr = pv.GetComponent<MeshRenderer>();
            if (omf == null || omr == null || omf.sharedMesh == null) return;

            var mesh = omf.sharedMesh;
            var srcRot = pv.transform.rotation;
            var b = mesh.bounds;

            // --- Dark road tint on existing StreetPavement renderer only ---
            var sp = GameObject.Find("StreetPavement");
            if (sp != null)
            {
                var spr = sp.GetComponent<MeshRenderer>();
                if (spr != null)
                {
                    var dm = new Material(spr.sharedMaterial);
                    dm.color = new Color(0.085f, 0.085f, 0.095f);
                    dm.EnableKeyword("_EMISSION");
                    dm.SetColor("_EmissionColor", Color.black);
                    spr.material = dm;
                }
            }

            // --- Root (identity) ---
            var root = new GameObject("EastStreetGround");
            root.transform.SetParent(parent.transform, false);

            // Material copies — muted concrete, no glow
            var swMat = Mat(omr.sharedMaterial, new Color(0.36f, 0.35f, 0.32f));
            var crMat = Mat(omr.sharedMaterial, new Color(0.43f, 0.41f, 0.36f));

            // Sidewalks — tops at Y 0.20 (6 cm above road top 0.14)
            Box(root, "SidewalkSouth", mesh, srcRot, swMat,
                new Vector3(41f, 0.17f, 9f), new Vector3(38f, 0.06f, 2f), b, true);
            Box(root, "SidewalkNorth", mesh, srcRot, swMat,
                new Vector3(41f, 0.17f, 27f), new Vector3(38f, 0.06f, 2f), b, true);

            // Curb edges — same top Y 0.20
            Box(root, "CurbSouth", mesh, srcRot, crMat,
                new Vector3(41f, 0.17f, 10f), new Vector3(38f, 0.06f, 0.12f), b, true);
            Box(root, "CurbNorth", mesh, srcRot, crMat,
                new Vector3(41f, 0.17f, 26f), new Vector3(38f, 0.06f, 0.12f), b, true);

            // --- Lane dashes: 9 renderer-only thin strips, no colliders ---
            var dashMat = MatFind("road_dash00");
            if (dashMat == null)
                dashMat = Mat(omr.sharedMaterial, new Color(0.55f, 0.53f, 0.45f));
            else
            {
                var dc = new Material(dashMat);
                dc.EnableKeyword("_EMISSION");
                dc.SetColor("_EmissionColor", Color.black);
                dashMat = dc;
            }

            for (int i = 0; i < 9; i++)
                Box(root, "LaneDash" + i.ToString("D2"), mesh, srcRot, dashMat,
                    new Vector3(26f + 4f * i, 0.142f, 18f),
                    new Vector3(2.4f, 0.002f, 0.10f), b, false);
        }

        // Place one box using the proven ConnectedStreet mapping.
        // Mapping: scale=(wSize.z/b.x, wSize.x/b.y, wSize.y/b.z),
        //          pos   = center - rot * Scale(b.center, scale)
        static void Box(GameObject par, string nm, Mesh m, Quaternion rot,
            Material mat, Vector3 ctr, Vector3 wS, Bounds b, bool col)
        {
            var s = new Vector3(wS.z / b.size.x, wS.x / b.size.y, wS.y / b.size.z);
            var o = new GameObject(nm);
            o.transform.SetParent(par.transform, false);
            o.transform.rotation = rot;
            o.transform.localScale = s;
            o.transform.position = ctr - rot * Vector3.Scale(b.center, s);
            o.AddComponent<MeshFilter>().sharedMesh = m;
            o.AddComponent<MeshRenderer>().sharedMaterial = mat;
            if (col) { var c = o.AddComponent<BoxCollider>(); c.center = b.center; c.size = b.size; }
        }

        static Material Mat(Material src, Color c)
        {
            var m = new Material(src);
            m.color = c;
            m.EnableKeyword("_EMISSION");
            m.SetColor("_EmissionColor", Color.black);
            return m;
        }

        static Material MatFind(string nm)
        {
            var go = GameObject.Find(nm);
            if (go == null) return null;
            var r = go.GetComponent<MeshRenderer>();
            return r != null ? r.sharedMaterial : null;
        }
    }
}
