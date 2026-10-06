using UnityEngine;

namespace ChicagoGame
{
    // Adds real physics colliders so grounded walking (CharacterController.Move)
    // is stopped by buildings, piers, bins and pavement-edge fences.
    // Major colliders reuse existing mesh-local bounds (imported transforms
    // preserved); end barriers reuse the original chain-link fence asset.
    public static class WorldColliders
    {
        // Visible walkable pavement top surface: X -1..6, Z -2..30, Y top 0.14.
        const float PX0 = -1f, PX1 = 6f, PZ0 = -2f, PZ1 = 30f;
        const float WALL_H = 3.2f, WALL_T = 0.5f;

        public static void Install(Object[] roots, GameObject fenceSourcePrefab)
        {
            var go = new GameObject("WorldCollision");

            // 1) Major building / pier / bin / party-wall colliders from mesh bounds.
            foreach (var r in roots)
            {
                if (r == null) continue;
                var root = (r as Component) != null ? (r as Component).gameObject : (r as GameObject);
                if (root == null) continue;
                foreach (var mf in root.GetComponentsInChildren<MeshFilter>())
                {
                    if (mf.GetComponent<Collider>() != null) continue;
                    if (!IsMajor(mf.name)) continue;
                    var b = mf.sharedMesh.bounds;
                    var bc = mf.gameObject.AddComponent<BoxCollider>();
                    bc.center = b.center;
                    bc.size = b.size;
                }
            }

            // 2) Bound traversal to the visible pavement with edge barriers.
            AddWall(go, new Vector3(PX0 - WALL_T * 0.5f, WALL_H * 0.5f, (PZ0 + PZ1) * 0.5f),
                    new Vector3(WALL_T, WALL_H, (PZ1 - PZ0)));
            AddWall(go, new Vector3(PX1 + WALL_T * 0.5f, WALL_H * 0.5f, 3.0f),
                    new Vector3(WALL_T, WALL_H, 10.0f));
            AddWall(go, new Vector3(PX1 + WALL_T * 0.5f, WALL_H * 0.5f, 25.0f),
                    new Vector3(WALL_T, WALL_H, 10.0f));
            AddWall(go, new Vector3((PX0 + PX1) * 0.5f, WALL_H * 0.5f, PZ1 + WALL_T * 0.5f),
                    new Vector3((PX1 - PX0) + WALL_T * 2f, WALL_H, WALL_T));
            AddWall(go, new Vector3((PX0 + PX1) * 0.5f, WALL_H * 0.5f, PZ0 - WALL_T * 0.5f),
                    new Vector3((PX1 - PX0) + WALL_T * 2f, WALL_H, WALL_T));

            // 2b) Connected east alley pavement patch (rendered, not invisible),
            // reusing original pavement mesh/material/rotation/thickness.
            float AX0 = 6f, AX1 = 22f, AZ0 = 8f, AZ1 = 20f;
            Transform pv0 = null;
            var pvGo = GameObject.Find("Pavement");
            if (pvGo != null) pv0 = pvGo.transform;
            if (pv0 != null)
            {
                var omf = pv0.GetComponent<MeshFilter>(); var omr = pv0.GetComponent<MeshRenderer>();
                if (omf != null && omr != null)
                {
                    var b = omf.sharedMesh.bounds; var wb = omr.bounds;
                    var ls = new Vector3((AZ1 - AZ0) / b.size.x, (AX1 - AX0) / b.size.y, 0.14f / b.size.z);
                    var ap = new GameObject("AlleyPavement");
                    ap.transform.SetParent(go.transform, false);
                    ap.transform.rotation = pv0.rotation;
                    ap.transform.localScale = ls;
                    ap.transform.position = new Vector3((AX0 + AX1) * 0.5f, 0.14f - wb.size.y * 0.5f, (AZ0 + AZ1) * 0.5f)
                                            - pv0.rotation * Vector3.Scale(b.center, ls);
                    ap.AddComponent<MeshFilter>().sharedMesh = omf.sharedMesh;
                    var rGo = GameObject.Find("road_asphalt");
                    var rR = rGo != null ? rGo.GetComponent<MeshRenderer>() : null;
                    ap.AddComponent<MeshRenderer>().sharedMaterial = rR != null ? rR.sharedMaterial : omr.sharedMaterial;
                    var fl = ap.AddComponent<BoxCollider>(); fl.center = b.center; fl.size = b.size;
                }
            }
            // Bound east (X22) and both Z edges across X6..22; west X6 stays open.
            AddWall(go, new Vector3(AX1 + WALL_T * 0.5f, WALL_H * 0.5f, (AZ0 + AZ1) * 0.5f),
                    new Vector3(WALL_T, WALL_H, AZ1 - AZ0));
            AddWall(go, new Vector3((AX0 + AX1) * 0.5f, WALL_H * 0.5f, AZ1 + WALL_T * 0.5f),
                    new Vector3(AX1 - AX0 + WALL_T * 2f, WALL_H, WALL_T));
            AddWall(go, new Vector3((AX0 + AX1) * 0.5f, WALL_H * 0.5f, AZ0 - WALL_T * 0.5f),
                    new Vector3(AX1 - AX0 + WALL_T * 2f, WALL_H, WALL_T));
            if (fenceSourcePrefab != null)
            {
                PlaceFence(fenceSourcePrefab, go, new Vector3(AX1 - 0.3f, 0f, (AZ0 + AZ1) * 0.5f),
                    Quaternion.Euler(0f, 90f, 0f), new Vector3((AZ1 - AZ0) / 18f, 1f, 1f));
                PlaceFence(fenceSourcePrefab, go, new Vector3((AX0 + AX1) * 0.5f, 0f, AZ1 - 0.3f),
                    Quaternion.identity, new Vector3((AX1 - AX0) / 18f, 1f, 1f));
                PlaceFence(fenceSourcePrefab, go, new Vector3((AX0 + AX1) * 0.5f, 0f, AZ0 + 0.3f),
                    Quaternion.identity, new Vector3((AX1 - AX0) / 18f, 1f, 1f));
            }

            // Hide ONLY original decorative fence mesh crossing the opening X5..6,Z8..20.
            foreach (var r in roots)
            {
                if (r == null) continue;
                var root = (r as Component) != null ? (r as Component).gameObject : (r as GameObject);
                if (root == null) continue;
                foreach (var mr in root.GetComponentsInChildren<MeshRenderer>())
                {
                    if (!mr.name.StartsWith("fence_")) continue;
                    var b = mr.bounds;
                    if (b.center.x >= 5f && b.center.x <= 6f && b.center.z >= 8f && b.center.z <= 20f)
                        mr.enabled = false;
                }
            }

            // Warm-neutral fill over the east alley (golden-hour key light retained)
            // plus a local material tint on the alley pavement so road edge + actor read.
            var l0 = new GameObject("AlleyFill0").AddComponent<Light>();
            l0.transform.SetParent(go.transform, false); l0.transform.position = new Vector3(12f, 4f, 12f);
            l0.type = LightType.Point; l0.color = new Color(1f, 0.85f, 0.70f); l0.range = 20f; l0.intensity = 2.5f; l0.shadows = LightShadows.None;
            var l1 = new GameObject("AlleyFill1").AddComponent<Light>();
            l1.transform.SetParent(go.transform, false); l1.transform.position = new Vector3(19f, 4f, 16f);
            l1.type = LightType.Point; l1.color = new Color(1f, 0.85f, 0.70f); l1.range = 18f; l1.intensity = 3f; l1.shadows = LightShadows.None;
            var apGo = GameObject.Find("AlleyPavement");
            var apMr = apGo != null ? apGo.GetComponent<MeshRenderer>() : null;
            if (apMr != null) { var apMat = new Material(apMr.sharedMaterial); apMat.color = new Color(0.30f, 0.30f, 0.29f, 1f); apMr.material = apMat; }

            // Frame alley entrance with existing props (no new assets).
            {
                var bp = GameObject.Find("bollard01"); var dp = GameObject.Find("dumpster_a");
                var targets = new[] { new Vector2(8f, 8.8f), new Vector2(8f, 19.65f), new Vector2(16f, 9.5f) };
                var srcs = new[] { bp, bp, dp };
                var names = new[] { "AlleyBollardS", "AlleyBollardN", "AlleyDumpster" };
                for (int i = 0; i < 3; i++)
                {
                    if (srcs[i] == null) continue;
                    var inst = Object.Instantiate(srcs[i]); inst.name = names[i];
                    inst.transform.SetParent(go.transform, true);
                    inst.transform.rotation = srcs[i].transform.rotation;
                    inst.transform.localScale = srcs[i].transform.lossyScale;
                    var mn = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
                    var mx = new Vector3(float.MinValue, float.MinValue, float.MinValue);
                    foreach (var rr in inst.GetComponentsInChildren<Renderer>())
                    { var rb = rr.bounds; mn = Vector3.Min(mn, rb.min); mx = Vector3.Max(mx, rb.max); }
                    if (mn.x > mx.x) continue;
                    var cxz = new Vector3((mn.x + mx.x) * 0.5f, mn.y, (mn.z + mx.z) * 0.5f);
                    var delta = new Vector3(targets[i].x - cxz.x, 0.14f - cxz.y, targets[i].y - cxz.z);
                    inst.transform.position += delta;
                }
            }

            {
                var ds = GameObject.Find("door00_panel"); var dmf = ds != null ? ds.GetComponent<MeshFilter>() : null; var dmr = ds != null ? ds.GetComponent<MeshRenderer>() : null;
                if (dmf != null && dmr != null)
                {
                    var dgo = new GameObject("ServiceDoor"); dgo.transform.SetParent(go.transform, false);
                    dgo.transform.localScale = ds.transform.lossyScale;
                    dgo.transform.rotation = Quaternion.Euler(0f, 90f, 0f) * ds.transform.rotation;
                    dgo.AddComponent<MeshFilter>().sharedMesh = dmf.sharedMesh;
                    var dR = dgo.AddComponent<MeshRenderer>(); dR.sharedMaterial = dmr.sharedMaterial;
                    var db = dR.bounds;
                    // Pull the wood panel 0.07m OUTWARD (toward -Z, the alley
                    // interior) from the stone surround centre (Z19.92) so the
                    // solid stone backing no longer hides the wood door face.
                    dgo.transform.position += new Vector3(16f - db.center.x, 0.14f - db.min.y, 19.85f - db.center.z);
                }
            }
            {
                var ds = GameObject.Find("door00_surround"); var dmf = ds != null ? ds.GetComponent<MeshFilter>() : null; var dmr = ds != null ? ds.GetComponent<MeshRenderer>() : null;
                if (dmf != null && dmr != null)
                {
                    var dgo = new GameObject("ServiceDoorSurround"); dgo.transform.SetParent(go.transform, false);
                    dgo.transform.localScale = ds.transform.lossyScale;
                    dgo.transform.rotation = Quaternion.Euler(0f, 90f, 0f) * ds.transform.rotation;
                    dgo.AddComponent<MeshFilter>().sharedMesh = dmf.sharedMesh;
                    var dR = dgo.AddComponent<MeshRenderer>(); dR.sharedMaterial = dmr.sharedMaterial;
                    var db = dR.bounds;
                    dgo.transform.position += new Vector3(16f - db.center.x, 0.14f - db.min.y, 19.92f - db.center.z);
                }
            }
            // 3) Understandable end barriers using the original fence mesh.
            var fw = GameObject.Find("facade_wall");
            if (fw != null)
            {
                var omf = fw.GetComponent<MeshFilter>(); var omr = fw.GetComponent<MeshRenderer>();
                if (omf != null && omr != null)
                {
                    var b = omf.sharedMesh.bounds;
                    var srcRot = fw.transform.rotation;
                    var r90 = Quaternion.Euler(0f, 90f, 0f) * srcRot;
                    var names = new[] { "AlleySouthWall", "AlleyNorthWall", "AlleyEndWall" };
                    var centers = new[] { new Vector3(14f, 4.4f, 7.75f), new Vector3(14f, 4.4f, 20.25f), new Vector3(22.25f, 4.4f, 14f) };
                    var rots = new[] { r90, r90, srcRot };
                    var scales = new[]
                    {
                        new Vector3(16f / b.size.x, 0.5f / b.size.y, 8.8f / b.size.z),
                        new Vector3(16f / b.size.x, 0.5f / b.size.y, 8.8f / b.size.z),
                        new Vector3(12f / b.size.x, 0.5f / b.size.y, 8.8f / b.size.z)
                    };
                    for (int i = 0; i < 3; i++)
                    {
                        var o = new GameObject(names[i]);
                        o.transform.SetParent(go.transform, false);
                        o.transform.rotation = rots[i];
                        o.transform.localScale = scales[i];
                        o.transform.position = centers[i] - rots[i] * Vector3.Scale(b.center, scales[i]);
                        o.AddComponent<MeshFilter>().sharedMesh = omf.sharedMesh;
                        o.AddComponent<MeshRenderer>().sharedMaterial = omr.sharedMaterial;
                        var bc = o.AddComponent<BoxCollider>();
                        bc.center = b.center; bc.size = b.size;
                    }
                }
            }
            if (fenceSourcePrefab != null)
            {
                // North (forward, +Z) end: fence runs across pavement width.
                PlaceFence(fenceSourcePrefab, go,
                    new Vector3((PX0 + PX1) * 0.5f, 0f, PZ1 - 0.3f),
                    Quaternion.identity,
                    new Vector3((PX1 - PX0) / 18f, 1f, 1f));
                // West (-X) end: fence runs along pavement depth.
                PlaceFence(fenceSourcePrefab, go,
                    new Vector3(PX0 + 0.3f, 0f, (PZ0 + PZ1) * 0.5f),
                    Quaternion.Euler(0f, 90f, 0f),
                    new Vector3((PZ1 - PZ0) / 18f, 1f, 1f));
            }
        }

        static bool IsMajor(string nm)
        {
            var n = nm.ToLower();
            if (n.Contains("facade_wall") || n.Contains("facade_base")) return true;
            if (n.Contains("pier_col") || n.Contains("pier_base")) return true;
            if (n.Contains("dumpster") && n.Contains("body")) return true;
            if (n.Contains("alley_wall")) return true;
            return false;
        }

        static void AddWall(GameObject parent, Vector3 pos, Vector3 size)
        {
            var w = new GameObject("Barrier");
            w.transform.SetParent(parent.transform, false);
            w.transform.localPosition = pos;
            var bc = w.AddComponent<BoxCollider>();
            bc.center = Vector3.zero;
            bc.size = size;
        }

        static void PlaceFence(GameObject prefab, GameObject parent, Vector3 pos,
                              Quaternion rot, Vector3 scale)
        {
            var inst = Object.Instantiate(prefab, parent.transform, false);
            // Keep only the fence_run subtree; drop ltrack / alley so this is a clean barrier.
            var keep = FindDeep(inst.transform, "fence");
            foreach (Transform ch in inst.transform)
                if (ch != keep) Object.Destroy(ch.gameObject);

            inst.name = "FenceBarrier";
            inst.transform.localPosition = pos;
            inst.transform.localRotation = rot;
            inst.transform.localScale = scale;

            if (keep != null)
            {
                var bc = keep.gameObject.AddComponent<BoxCollider>();
                FitBox(keep, out var center, out var size);
                bc.center = center;
                bc.size = size;
            }
        }

        static Transform FindDeep(Transform t, string contains)
        {
            foreach (Transform c in t)
            {
                if (c.name.ToLower().Contains(contains)) return c;
                var d = FindDeep(c, contains);
                if (d != null) return d;
            }
            return null;
        }

        // Combined local-space AABB of all child renderers under parent.
        static void FitBox(Transform parent, out Vector3 center, out Vector3 size)
        {
            var min = new Vector3(float.MaxValue, float.MaxValue, float.MaxValue);
            var max = new Vector3(float.MinValue, float.MinValue, float.MinValue);
            foreach (var r in parent.GetComponentsInChildren<Renderer>())
            {
                var mb = r.bounds; // world
                var corners = Corners(mb);
                foreach (var c in corners)
                {
                    var lc = parent.InverseTransformPoint(c);
                    min = Vector3.Min(min, lc);
                    max = Vector3.Max(max, lc);
                }
            }
            if (min.x > max.x) { center = Vector3.zero; size = Vector3.one; return; }
            center = (min + max) * 0.5f;
            size = max - min;
        }

        static Vector3[] Corners(Bounds b)
        {
            var c = b.center; var e = b.extents;
            return new[]
            {
                c + new Vector3(-e.x,-e.y,-e.z), c + new Vector3( e.x,-e.y,-e.z),
                c + new Vector3(-e.x, e.y,-e.z), c + new Vector3( e.x, e.y,-e.z),
                c + new Vector3(-e.x,-e.y, e.z), c + new Vector3( e.x,-e.y, e.z),
                c + new Vector3(-e.x, e.y, e.z), c + new Vector3( e.x, e.y, e.z),
            };
        }
    }
}
