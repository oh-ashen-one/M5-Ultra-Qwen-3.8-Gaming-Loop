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

            // 3) Understandable end barriers using the original fence mesh.
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
