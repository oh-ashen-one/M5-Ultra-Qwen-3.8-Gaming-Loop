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
            var street = Instantiate(Resources.Load<GameObject>("Generated/street/scene"));
            street.name = "Street";
            var body = Instantiate(Resources.Load<GameObject>("Generated/player/scene"));
            body.name = "Player";

            Set("Player", body.transform);
            Set("Mode", "foot");

            var cam = new GameObject("MainCamera");
            cam.tag = "MainCamera";
            cam.AddComponent<AudioListener>();
            cam.AddComponent<Camera>();
            cam.transform.position = new Vector3(0f, 5f, -10f);
            cam.transform.rotation = Quaternion.Euler(15f, 0f, 0f);

            var sun = new GameObject("Directional Light").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1.1f;
            sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            if (street.GetComponentInChildren<Collider>() == null)
            {
                var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
                ground.name = "GroundCollider";
                ground.transform.SetParent(street.transform, false);
                ground.transform.localPosition = Vector3.down * 0.5f;
                ground.transform.localScale = new Vector3(400f, 1f, 400f);
                UnityEngine.Object.Destroy(ground.GetComponent<MeshRenderer>());
            }
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
}
