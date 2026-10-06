using UnityEngine;

namespace ChicagoGame
{
    // Connected second street continuing EAST from the alley end (X22).
    // Footprint X22..60, Z8..28, ground top Y0.14. Reuses original
    // pavement / facade_wall / fence meshes, materials and transforms.
    // The old X22 alley boundary becomes an open interior junction; only
    // the new OUTER edges are closed here. All accepted geometry is kept.
    public static class ConnectedStreet
    {
        const float SX0 = 22f, SX1 = 60f, SZ0 = 8f, SZ1 = 28f;
        const float WT = 0.5f, WH = 3.2f, DEPTH = 8.8f;

        public static void Install(GameObject parent, GameObject fenceSrc)
        {
            // --- Pavement patch (rendered, matches alley construction). ---
            var pvGo = GameObject.Find("Pavement");
            var pf = pvGo != null ? pvGo.transform : null;
            if (pf != null)
            {
                var omf = pf.GetComponent<MeshFilter>();
                var omr = pf.GetComponent<MeshRenderer>();
                if (omf != null && omr != null)
                {
                    var b = omf.sharedMesh.bounds; var wb = omr.bounds;
                    var ls = new Vector3((SZ1 - SZ0) / b.size.x, (SX1 - SX0) / b.size.y, 0.14f / b.size.z);
                    var go = new GameObject("StreetPavement");
                    go.transform.SetParent(parent.transform, false);
                    go.transform.rotation = pf.rotation;
                    go.transform.localScale = ls;
                    go.transform.position = new Vector3((SX0 + SX1) * 0.5f, 0.14f - wb.size.y * 0.5f, (SZ0 + SZ1) * 0.5f)
                                            - pf.rotation * Vector3.Scale(b.center, ls);
                    go.AddComponent<MeshFilter>().sharedMesh = omf.sharedMesh;
                    var rGo = GameObject.Find("road_asphalt");
                    var rR = rGo != null ? rGo.GetComponent<MeshRenderer>() : null;
                    var mr = go.AddComponent<MeshRenderer>();
                    mr.sharedMaterial = rR != null ? rR.sharedMaterial : omr.sharedMaterial;
                    var sMat = new Material(mr.sharedMaterial);
                    sMat.color = new Color(0.30f, 0.30f, 0.29f, 1f);
                    mr.material = sMat;
                    var fl = go.AddComponent<BoxCollider>(); fl.center = b.center; fl.size = b.size;
                }
            }

            // --- Visible facade outer walls (+ matching thin colliders). ---
            var fw = GameObject.Find("facade_wall");
            if (fw != null)
            {
                var omf = fw.GetComponent<MeshFilter>();
                var omr = fw.GetComponent<MeshRenderer>();
                if (omf != null && omr != null)
                {
                    var b = omf.sharedMesh.bounds; var srcRot = fw.transform.rotation;
                    var r90 = Quaternion.Euler(0f, 90f, 0f) * srcRot;

                    // South (Z8) and North (Z28) run along X -> rot r90.
                    Facade(parent, "StreetSouthWall", omf.sharedMesh, omr.sharedMaterial, r90,
                        new Vector3((SX0 + SX1) * 0.5f, 4.4f, SZ0 - WT * 0.5f),
                        new Vector3((SX1 - SX0) / b.size.x, 0.5f / b.size.y, DEPTH / b.size.z));
                    Facade(parent, "StreetNorthWall", omf.sharedMesh, omr.sharedMaterial, r90,
                        new Vector3((SX0 + SX1) * 0.5f, 4.4f, SZ1 + WT * 0.5f),
                        new Vector3((SX1 - SX0) / b.size.x, 0.5f / b.size.y, DEPTH / b.size.z));
                    // East (X60) and west-nub (X22, closes Z20..28 above alley) run along Z -> srcRot.
                    Facade(parent, "StreetEastWall", omf.sharedMesh, omr.sharedMaterial, srcRot,
                        new Vector3(SX1 + WT * 0.5f, 4.4f, (SZ0 + SZ1) * 0.5f),
                        new Vector3((SZ1 - SZ0) / b.size.x, 0.5f / b.size.y, DEPTH / b.size.z));
                    Facade(parent, "StreetWestNubWall", omf.sharedMesh, omr.sharedMaterial, srcRot,
                        new Vector3(SX0, 4.4f, (20f + SZ1) * 0.5f),
                        new Vector3((SZ1 - 20f) / b.size.x, 0.5f / b.size.y, DEPTH / b.size.z));
                }
            }

            // --- Thin collision bounds for the new outer edges. ---
            WorldColliders.AddWall(parent, new Vector3((SX0 + SX1) * 0.5f, WH * 0.5f, SZ0 - WT * 0.5f),
                new Vector3((SX1 - SX0) + WT * 2f, WH, WT));
            WorldColliders.AddWall(parent, new Vector3((SX0 + SX1) * 0.5f, WH * 0.5f, SZ1 + WT * 0.5f),
                new Vector3((SX1 - SX0) + WT * 2f, WH, WT));
            WorldColliders.AddWall(parent, new Vector3(SX1 + WT * 0.5f, WH * 0.5f, (SZ0 + SZ1) * 0.5f),
                new Vector3(WT, WH, SZ1 - SZ0));
            WorldColliders.AddWall(parent, new Vector3(SX0, WH * 0.5f, (20f + SZ1) * 0.5f),
                new Vector3(WT, WH, SZ1 - 20f));

            // --- Decorative fence closing the new outer edges. ---
            if (fenceSrc != null)
            {
                WorldColliders.PlaceFence(fenceSrc, parent, new Vector3((SX0 + SX1) * 0.5f, 0f, SZ0 + 0.3f),
                    Quaternion.identity, new Vector3((SX1 - SX0) / 18f, 1f, 1f));
                WorldColliders.PlaceFence(fenceSrc, parent, new Vector3((SX0 + SX1) * 0.5f, 0f, SZ1 - 0.3f),
                    Quaternion.identity, new Vector3((SX1 - SX0) / 18f, 1f, 1f));
                WorldColliders.PlaceFence(fenceSrc, parent, new Vector3(SX1 - 0.3f, 0f, (SZ0 + SZ1) * 0.5f),
                    Quaternion.Euler(0f, 90f, 0f), new Vector3((SZ1 - SZ0) / 18f, 1f, 1f));
                // Interior junction north-outer corner (X22, Z20..28): close the
                // west-nub visually so the X22 opening reads as a passage, not a void.
                WorldColliders.PlaceFence(fenceSrc, parent, new Vector3(SX0 + 0.3f, 0f, (20f + SZ1) * 0.5f),
                    Quaternion.Euler(0f, 90f, 0f), new Vector3((SZ1 - 20f) / 18f, 1f, 1f));
            }

            // --- Warm fill light so the longer street reads (no new art). ---
            AddFill(parent, new Vector3(32f, 4f, 16f), 20f, 2.5f);
            AddFill(parent, new Vector3(50f, 4f, 18f), 20f, 2.5f);
EastStreetDetail.Install(parent);
            EastStreetGround.Install(parent);
        }

        static void Facade(GameObject parent, string nm, Mesh m, Material mat,
                           Quaternion rot, Vector3 center, Vector3 scale)
        {
            var o = new GameObject(nm);
            o.transform.SetParent(parent.transform, false);
            o.transform.rotation = rot;
            o.transform.localScale = scale;
            var b = m.bounds;
            o.transform.position = center - rot * Vector3.Scale(b.center, scale);
            o.AddComponent<MeshFilter>().sharedMesh = m;
            o.AddComponent<MeshRenderer>().sharedMaterial = mat;
            var bc = o.AddComponent<BoxCollider>();
            bc.center = b.center; bc.size = b.size;
        }

        static void AddFill(GameObject parent, Vector3 pos, float range, float inten)
        {
            var l = new GameObject("StreetFill").AddComponent<Light>();
            l.transform.SetParent(parent.transform, false);
            l.transform.position = pos;
            l.type = LightType.Point; l.color = new Color(1f, 0.85f, 0.70f);
            l.range = range; l.intensity = inten; l.shadows = LightShadows.None;
        }
    }
}
