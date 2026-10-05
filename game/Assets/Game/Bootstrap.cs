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

            var rig = new GameObject("MainCamera");
            rig.tag = "MainCamera";
            rig.AddComponent<AudioListener>();
            var cam = rig.AddComponent<Camera>();
            cam.nearClipPlane = 0.1f;
            rig.transform.position = body.transform.position + new Vector3(0f, 3f, -4.5f);
            rig.transform.rotation = Quaternion.Euler(15f, body.transform.eulerAngles.y, 0f);
            rig.AddComponent<Follow>().target = body.transform;

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
        public Vector3 offset = new Vector3(0f, 3f, 4.5f);
        public float damping = 7f;

        void LateUpdate()
        {
            if (target == null) return;
            var want = target.position + Quaternion.Euler(0f, target.eulerAngles.y, 0f) * offset;
            transform.position = Vector3.Lerp(transform.position, want, Mathf.Clamp01(damping * Time.deltaTime));
            transform.LookAt(target.position + Vector3.up * 1.2f);
        }
    }
}
