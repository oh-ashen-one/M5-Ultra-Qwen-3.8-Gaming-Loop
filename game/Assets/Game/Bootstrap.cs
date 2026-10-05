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

            var sun = new GameObject("Directional Light").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1.1f;
            sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
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

        void LateUpdate()
        {
            if (target == null) return;
            var yaw = Quaternion.Euler(0f, target.eulerAngles.y, 0f);
            var want = target.position + yaw * offset;
            transform.position = Vector3.Lerp(transform.position, want, Mathf.Clamp01(damping * Time.deltaTime));
            // Aim slightly down the route so the horizon sits high and the
            // destination (green pad / parcel) reads in the upper-centre frame
            // while the hood stays near the bottom edge.
            var look = target.position + Vector3.up * 1.1f + yaw * Vector3.forward * lookAhead;
            transform.LookAt(look);
        }
    }
}
