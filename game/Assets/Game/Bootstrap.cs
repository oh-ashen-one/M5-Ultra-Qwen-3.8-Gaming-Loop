using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    public static class Bootstrap
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;

        public static void Create()
        {
            var streetPrefab = Resources.Load<GameObject>("Generated/street/scene");
            var street = streetPrefab != null
                ? UnityEngine.Object.Instantiate(streetPrefab)
                : new GameObject("Street");
            street.name = "Street";
            street.transform.rotation = Quaternion.Euler(0f, 90f, 0f) * street.transform.rotation;
            var streetExt = UnityEngine.Object.Instantiate(street);
            streetExt.name = "Street";
            streetExt.transform.position = new Vector3(-0.9f, 0f, 21f);
            street.transform.position = new Vector3(-0.9f, 0f, 7f);
            Transform sw = null;
            foreach (var r in street.GetComponentsInChildren<MeshRenderer>())
                if (r.name.ToLower().Contains("side")) { sw = r.transform; break; }
            if (sw != null) {
                var smr = sw.GetComponent<MeshRenderer>(); var smf = sw.GetComponent<MeshFilter>();
                var b = smf.sharedMesh.bounds; var wb = smr.bounds;
                var ls = new Vector3(32f / b.size.x, 7f / b.size.y, 0.14f / b.size.z);
                var pv = new GameObject("Pavement");
                pv.transform.rotation = sw.rotation;
                pv.transform.localScale = ls;
                pv.transform.position = new Vector3(2.5f, 0.14f - wb.size.y * 0.5f, 14f) - pv.transform.rotation * Vector3.Scale(b.center, ls);
                pv.AddComponent<MeshFilter>().sharedMesh = smf.sharedMesh;
                pv.AddComponent<MeshRenderer>().sharedMaterial = smr.sharedMaterial;
            }
            static GameObject Coupe() { var p = Resources.Load<GameObject>("Generated/coupe/scene"); return p ? UnityEngine.Object.Instantiate(p) : null; }
            static GameObject Props() { var p = Resources.Load<GameObject>("Generated/props/scene"); return p ? UnityEngine.Object.Instantiate(p) : null; }
            var props = Props(); if (props != null) { props.name = "Props"; props.transform.position = new Vector3(5.5f, 0f, 11f); props.transform.rotation = Quaternion.Euler(0f, 90f, 0f) * props.transform.rotation; }
            var coupe = Coupe(); if (coupe != null) { coupe.name = "Coupe"; coupe.transform.position = new Vector3(3.6f, 0f, 8f); }
            GameObject body = new GameObject("Player");
            body.name = "Player";
            var playerPrefab = Resources.Load<GameObject>("Generated/player/scene");
            if (playerPrefab != null)
            {
                var visual = UnityEngine.Object.Instantiate(playerPrefab, body.transform, true);
                visual.name = "PlayerVisual";
                visual.transform.localPosition += new Vector3(0f, -0.79f, 0f);
            }

            if (street.GetComponentInChildren<Collider>() == null)
            {
                var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
                ground.name = "GroundCollider";
                ground.transform.SetParent(null, false);
                ground.transform.localPosition = new Vector3(0f, -0.36f, 0f);
                ground.transform.localScale = new Vector3(400f, 1f, 400f);
                UnityEngine.Object.Destroy(ground.GetComponent<MeshRenderer>());
            }

            foreach (var c in body.GetComponentsInChildren<Collider>()) UnityEngine.Object.Destroy(c);
            foreach (var r in body.GetComponentsInChildren<Rigidbody>()) UnityEngine.Object.Destroy(r);

            var p = body.transform.position;
            body.transform.position = new Vector3(0f, 0.3f, 1.7f);

            var cc = body.AddComponent<CharacterController>();
            cc.center = new Vector3(0f, 0.9f, 0f);
            cc.height = 1.75f;
            cc.radius = 0.32f;
            cc.skinWidth = 0.02f;
            cc.minMoveDistance = 0f;
            cc.stepOffset = 0.35f;
            cc.slopeLimit = 55f;

            Set("Player", body.transform);
            Set("Mode", "foot");
            body.AddComponent<Walker>();

            var fencePrefab = Resources.Load<GameObject>("Generated/props/scene");
            WorldColliders.Install(new UnityEngine.Object[] { street, streetExt, props }, fencePrefab);

            var rig = new GameObject("MainCamera");
            rig.tag = "MainCamera";
            rig.AddComponent<AudioListener>();
            var cam = rig.AddComponent<Camera>();
            cam.nearClipPlane = 0.1f;
            cam.fieldOfView = 64f;
            rig.transform.position = body.transform.position + new Vector3(0f, 3.1f, -5.2f);
            rig.transform.rotation = Quaternion.Euler(10f, body.transform.eulerAngles.y, 0f);
            var follow = rig.AddComponent<Follow>(); follow.target = body.transform;
            if (coupe != null) VehicleInteraction.Install(body, coupe, follow);
            CourierMission.Install(body, cam);
            Combat.Install(body, cam);
            AudioFX.Install(rig.transform);
            HudStatus.Install(cam);

            // Golden-hour Chicago key light: low warm sun casting long raking
            // shadows across the brick rowhouses, matching the supplied visual
            // target (autumn dusk, sky glow behind the skyline).
            var sun = new GameObject("Directional Light").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1.35f;
            sun.color = new Color(1.0f, 0.82f, 0.60f);
            sun.shadows = LightShadows.Soft;
            sun.shadowStrength = 0.75f;
            // Low elevation (~18 deg) for long shadows; azimuth down the block.
            sun.transform.rotation = Quaternion.Euler(18f, -34f, 0f);

            // Warm hazy dusk fog fades the far skyline into the sky glow so the
            // tiled blocks dissolve like the reference photo instead of hard-
            // ending at the tile boundary.
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogColor = new Color(0.86f, 0.72f, 0.56f);
            RenderSettings.fogDensity = 0.010f;

            // Warm hazy flat ambient so shadowed brick keeps colour and the scene
            // never reads as flat grey. Unity 6 Built-in exposes only ambientLight
            // (Flat) reliably; a warm dusk tone matches the sky glow behind the
            // skyline and lifts the shadow interiors under the rowhouses.
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.46f, 0.42f, 0.40f);
        }

        static void Set(string name, object value)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            if (f == null && p == null) return;
            var type = f != null ? f.FieldType : p.PropertyType;
            if (type == typeof(Transform)) value = (value as Component).transform;
            else if (type == typeof(GameObject)) value = (value as Component).gameObject;
            else if (type.IsEnum) value = Enum.Parse(type, value.ToString(), true);
            if (f != null) f.SetValue(null, value);
            else p.SetValue(null, value);
        }
    }

    public class Walker : MonoBehaviour
    {
        public float speed = 3.2f;
        public float turnSpeed = 540f;
        CharacterController cc;
        float vy;

        void Awake() { cc = GetComponent<CharacterController>(); }

        void Update()
        {
            var dir = new Vector3(LoopInput.MoveX, 0f, LoopInput.MoveY);
            if (dir.sqrMagnitude > 1f) dir.Normalize();

            if (cc.isGrounded && vy < 0f) vy = -2f;
            vy = Mathf.Max(vy - 18f * Time.deltaTime, -25f);

            cc.Move((dir * speed + Vector3.up * vy) * Time.deltaTime);

            if (dir.sqrMagnitude > 0.0001f)
            {
                var want = Quaternion.LookRotation(dir, Vector3.up);
                transform.rotation = Quaternion.RotateTowards(transform.rotation, want, turnSpeed * Time.deltaTime);
            }
        }
    }

    public class Follow : MonoBehaviour
    {
        public Transform target;
        // Third-person BEHIND-the-target rig: negative Z keeps the camera on the
        // courier's back so the forward route (parcel, coupe lane, green pad) is
        // framed ahead instead of shoved to a corner or hidden behind the lens.
        public Vector3 offset = new Vector3(0f, 3.1f, -5.2f);
        public float damping = 8f;
        public float lookAhead = 4.0f;
        public LayerMask collideMask = ~0;

        // Vehicle-mode rig: the chase framing must keep the WHOLE coupe silhouette
        // (roof + both flanks) with margin. When the car hugs a facade the generic
        // cramped path collapses to a waist-height 0.18 m hug and jams the lens into
        // the rear quarter. Vehicle mode therefore keeps a much larger horizontal
        // floor and a high downward pose so the car never fuses with the wall.
        public bool vehicle = false;
        public Vector3 vehicleOffset = new Vector3(0f, 4.3f, -8.2f);
        public float vehicleMinHoriz = 5.6f;
        public float vehicleMinY = 3.6f;

        readonly RaycastHit[] hits = new RaycastHit[16];
        readonly Collider[] near = new Collider[8];
        Renderer[] rend;
        Transform cachedTarget;

        void LateUpdate()
        {
            if (target == null) { rend = null; cachedTarget = null; return; }
            if (target != cachedTarget) { cachedTarget = target; rend = target.GetComponentsInChildren<Renderer>(); }
            var yaw = Quaternion.Euler(0f, target.eulerAngles.y, 0f);

            Vector3 origin = target.position;

            // Real target bounds: used only for the shoulder/overhead pose and the
            // look target, so framing reflects the actual actor, not a distance proxy.
            float top = origin.y, ctr = origin.y; bool have = false;
            if (rend != null)
            {
                foreach (var r in rend)
                {
                    if (r == null) continue;
                    var b = r.bounds;
                    if (!have) { top = b.max.y; ctr = (b.min.y + b.max.y) * 0.5f; have = true; }
                    else { top = Mathf.Max(top, b.max.y); ctr = (ctr + b.center.y) * 0.5f; }
                }
            }
            if (!have) { top = origin.y + 1.8f; ctr = origin.y + 1.0f; }
            float bodyTop = Mathf.Max(0.5f, top - origin.y);

            // Split the rig offset into horizontal (the part that collides with a
            // wall behind) and vertical (the part that keeps a usable height). Scaling
            // the whole normalized direction — the old dir*maxSafe — collapsed Y to the
            // feet when a close wall forced a tiny distance, giving a waist-height view.
            Vector3 activeOffset = vehicle ? vehicleOffset : offset;
            Vector3 fullOff = yaw * activeOffset;
            Vector3 horiz = new Vector3(fullOff.x, 0f, fullOff.z);
            float horizFull = horiz.magnitude;
            if (horizFull < 1e-4f) { transform.position = origin + fullOff; return; }
            Vector3 hdir = horiz / horizFull;

            const float clearance = 0.25f;   // wall surface + near-plane budget
            float camY = activeOffset.y;     // normal height until proven cramped
            float crampHorizFloor = vehicle ? vehicleMinHoriz : 0.18f;
            float crampYFloor = vehicle ? vehicleMinY : 1.35f;

            // Horizontal room measured at head height along the back direction.
            Vector3 probeOrigin = origin + Vector3.up * Mathf.Max(1.0f, bodyTop * 0.9f);
            float hFull = horizFull;
            float hHit = float.PositiveInfinity;
            int n = Physics.RaycastNonAlloc(probeOrigin, hdir, hits, hFull + 0.05f,
                                           collideMask, QueryTriggerInteraction.Ignore);
            for (int i = 0; i < n; i++)
            {
                var t = hits[i].collider ? hits[i].collider.transform : null;
                if (t == target || (t && t.IsChildOf(target))) continue;
                if (hits[i].distance < hHit) hHit = hits[i].distance;
            }

            float hDist = hFull;
            bool cramped = false;
            if (hHit < float.PositiveInfinity)
            {
                float avail = hHit - clearance;
                if (avail < hFull * 0.6f)
                {
                    // Back space is short. For the foot rig we hug the actor (small
                    // floor) but for the coupe we MUST keep the whole silhouette
                    // framed: never let a near facade pull the lens into the car,
                    // instead hold a high wide pose and the vehicle horizontal floor.
                    cramped = true;
                    camY = Mathf.Max(crampYFloor, bodyTop + 0.25f);
                    hDist = Mathf.Max(crampHorizFloor, avail);
                }
                else
                {
                    hDist = Mathf.Min(hFull, avail);
                }
            }

            Vector3 want = origin + hdir * hDist + Vector3.up * camY;
            Vector3 pos = Vector3.Lerp(transform.position, want,
                                       Mathf.Clamp01(damping * Time.deltaTime));

            // Validate the ACTUAL smoothed segment using an above-ground pivot derived
            // from the actor's real visual bounds (chest height) so we never cast or
            // step from a root that sits at or below the floor surface.
            float pivotH = Mathf.Clamp(ctr - origin.y, 0.5f, 1.4f);
            Vector3 pivot = origin + Vector3.up * pivotH;
            Vector3 seg = pos - pivot;
            float segLen = seg.magnitude;
            if (segLen > 0.02f)
            {
                Vector3 sd = seg / segLen;
                if (Physics.Raycast(pivot, sd, out RaycastHit v, segLen,
                                    collideMask, QueryTriggerInteraction.Ignore))
                {
                    var vt = v.collider ? v.collider.transform : null;
                    bool own = vt == target || (vt && vt.IsChildOf(target));
                    if (!own && v.distance < segLen - clearance)
                        pos = pivot + sd * Mathf.Max(0.05f, v.distance - clearance);
                }
            }

            // Final geometry-aware near-plane guard: if the smoothed lens overlaps any
            // foreign collider, step toward the pivot (not raw root) until open.
            // Clamp each step to remaining distance; never push below walkable surface.
            float floorY = origin.y + 0.02f; // approximate floor top from root
            for (int k = 0; k < 5; k++)
            {
                int overlapCount = Physics.OverlapSphereNonAlloc(pos, clearance, near,
                                                                   collideMask, QueryTriggerInteraction.Ignore);
                if (overlapCount == 0) break;

                bool touchingForeign = false;
                for (int i = 0; i < overlapCount; i++)
                {
                    var t = near[i] ? near[i].transform : null;
                    if (t == null || t == target || t.IsChildOf(target)) continue;
                    touchingForeign = true; break;
                }
                if (!touchingForeign) break;

                Vector3 toT = pivot - pos;
                float d = toT.magnitude;
                if (d < 1e-4f) break;

                float step = Mathf.Min(clearance, d);
                Vector3 candidate = pos + toT / d * step;
                candidate.y = Mathf.Max(candidate.y, floorY + 0.08f);
                pos = candidate;
            }
            // Absolute floor guard: camera lens must remain above walkable surface.
            pos.y = Mathf.Max(pos.y, floorY + 0.08f);
            transform.position = pos;

            // Look target: normal pose unchanged. When cramped, aim at the real torso
            // center (bounds) with a short forward lead so the actor stays framed while
            // the route ahead remains on screen — an over-the-shoulder collision pose.
            if (!cramped)
            {
                transform.LookAt(origin + Vector3.up * 1.1f + yaw * Vector3.forward * lookAhead);
            }
            else
            {
                float lookY = Mathf.Clamp(ctr - origin.y, 1.0f, bodyTop);
                transform.LookAt(origin + Vector3.up * lookY + yaw * Vector3.forward * 1.4f);
            }
        }
    }
}
