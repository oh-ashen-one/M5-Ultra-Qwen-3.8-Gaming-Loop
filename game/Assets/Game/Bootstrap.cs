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

        // Scratch buffer for the multi-hit back-probe so we can skip the courier's
        // own capsule and react only to architecture along the view ray.
        readonly RaycastHit[] hits = new RaycastHit[16];

        void LateUpdate()
        {
            if (target == null) return;
            var yaw = Quaternion.Euler(0f, target.eulerAngles.y, 0f);

            // Rig direction is the unobstructed behind-the-back pose. The ray runs
            // from the target origin along that direction, so the camera sits at
            // target + dir*dist. Walls are kept in front of the lens by stopping
            // short of the first foreign hit.
            Vector3 dir = yaw * offset;
            float full = dir.magnitude;
            if (full < 1e-4f) return;
            dir /= full;
            Vector3 origin = target.position;

            // clearance covers both the wall surface and the camera near plane, so
            // the lens never pokes through nor clips the near plane.
            const float clearance = 0.22f;
            float maxSafe = full;

            // Walk all hits along the rig ray and ignore the courier's own colliders;
            // the nearest foreign surface bounds how far back we may go.
            int n = Physics.RaycastNonAlloc(origin, dir, hits, full + 0.05f,
                                           collideMask, QueryTriggerInteraction.Ignore);
            float hitDist = float.PositiveInfinity;
            for (int i = 0; i < n; i++)
            {
                var t = hits[i].collider ? hits[i].collider.transform : null;
                if (t == target || (t && t.IsChildOf(target))) continue;
                if (hits[i].distance < hitDist) hitDist = hits[i].distance;
            }
            // Geometry-safe clamp: never exceed available space. With a wall at 0.65 m
            // this yields ~0.43 m (in front of the wall); it has NO floor that could
            // jump past a close hit the way Max(1.4, hit-0.45) did.
            if (hitDist < float.PositiveInfinity)
                maxSafe = Mathf.Min(full, Mathf.Max(0.05f, hitDist - clearance));

            Vector3 want = origin + dir * maxSafe;
            // Pulled well inside the rig means architecture is touching the lens:
            // this is pure collision response, and we frame the actor accordingly.
            bool cramped = maxSafe < full * 0.55f;

            Vector3 pos = Vector3.Lerp(transform.position, want,
                                       Mathf.Clamp01(damping * Time.deltaTime));

            // Geometry-safe FINAL smoothed pose: re-verify along the actual smoothed
            // ray so an interpolated frame between two safe points can never settle
            // past a wall that the endpoint had already cleared.
            float d = Vector3.Dot(pos - origin, dir);
            if (d > 0.01f && Physics.Raycast(origin, dir, out RaycastHit v, d,
                                             collideMask, QueryTriggerInteraction.Ignore))
            {
                var vt = v.collider ? v.collider.transform : null;
                bool own = vt == target || (vt && vt.IsChildOf(target));
                if (!own && v.distance < d - 0.02f)
                    pos = origin + dir * Mathf.Max(0.05f, v.distance - clearance);
            }
            transform.position = pos;

            // Look down the route normally. When cramped, the back-ray has met a wall
            // ahead of the rig, so pushing look-ahead would aim into that wall; we
            // instead look straight at the courier's torso to keep the actor framed
            // and visible. (Framing is tied to the actual target, not to a fake
            // endpoint-distance visibility proxy.)
            float la = cramped ? 0f : lookAhead;
            float hy = cramped ? 1.0f : 1.1f;
            transform.LookAt(target.position + Vector3.up * hy + yaw * Vector3.forward * la);
        }
    }
}
