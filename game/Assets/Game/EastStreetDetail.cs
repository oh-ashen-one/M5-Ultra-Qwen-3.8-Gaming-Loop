using UnityEngine;

namespace ChicagoGame
{
    public static class EastStreetDetail
    {
        public static void Install(GameObject parent)
        {
            var street = GameObject.Find("Street");
            if (street == null) return;
            var srcPos = street.transform.position;
            var renderers = street.GetComponentsInChildren<MeshRenderer>();

            var root = new GameObject("EastStreetDetail");
            root.transform.SetParent(parent.transform, false);

            var assemblies = new (string n, float x, float z, float yaw)[]
            {
                ("South-0", 28.5f,  8f, -90f),
                ("South-1", 41f,    8f, -90f),
                ("South-2", 53.5f,  8f, -90f),
                ("North-0", 28.5f, 28f,  90f),
                ("North-1", 41f,   28f,  90f),
                ("North-2", 53.5f, 28f,  90f),
                ("East-0",  60f,   18f, 180f),
            };

            foreach (var a in assemblies)
            {
                var asm = new GameObject(a.n);
                asm.transform.SetParent(root.transform, false);
                asm.transform.position = new Vector3(a.x, 0f, a.z);
                var yaw = Quaternion.Euler(0f, a.yaw, 0f);

                foreach (var r in renderers)
                {
                    if (!Include(r.gameObject.name)) continue;
                    var mf = r.GetComponent<MeshFilter>();
                    if (mf == null || mf.sharedMesh == null) continue;
                    var mats = r.sharedMaterials;
                    if (mats == null || mats.Length == 0 || mats[0] == null) continue;

                    var go = new GameObject(r.gameObject.name);
                    go.transform.SetParent(asm.transform, false);
                    go.transform.position = new Vector3(a.x, 0f, a.z)
                                          + yaw * (r.transform.position - srcPos);
                    go.transform.rotation = yaw * r.transform.rotation;
                    go.transform.localScale = r.transform.lossyScale;
                    go.AddComponent<MeshFilter>().sharedMesh = mf.sharedMesh;
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterials = mats;
                }
            }
        }

        static bool Include(string n)
        {
            bool m = n == "facade_base" || n == "facade_belt"
                  || n == "cornice_bed" || n == "cornice"
                  || n.StartsWith("win") || n.StartsWith("door")
                  || n.StartsWith("pier") || n.StartsWith("dentil");
            if (!m) return false;
            if (n.Contains("facade_wall") || n.Contains("ef_")
             || n.Contains("roof") || n.Contains("chimney")
             || n.Contains("stoop") || n.Contains("planter")
             || n.Contains("fireesc")) return false;
            return true;
        }
    }
}
