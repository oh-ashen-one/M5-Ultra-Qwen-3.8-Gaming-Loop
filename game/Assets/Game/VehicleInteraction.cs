using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    public class VehicleInteraction : MonoBehaviour
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;

        GameObject _player;
        Transform _pv;
        Walker _walker;
        CharacterController _cc;
        Follow _follow;
        Rigidbody _rb;
        BoxCollider _body;
        bool _driving;
        float _speed;

        static readonly Vector3 PlayerResetPos = new Vector3(0f, 0.3f, 1.7f);
        static readonly Vector3 CarResetPos = new Vector3(3.6f, 0f, 8f);
        static readonly Quaternion CarResetRot = Quaternion.identity;

        const float VEHICLE_LENGTH = 4.5f;
        const float VEHICLE_WIDTH = 1.9f;
        const float VEHICLE_HEIGHT = 1.4f;

        public static void Install(GameObject player, GameObject coupe, Follow follow)
        {
            if (!player || !coupe) return;
            var root = new GameObject("Vehicle");
            root.transform.position = coupe.transform.position;
            root.transform.rotation = Quaternion.Euler(0f, coupe.transform.eulerAngles.y, 0f);
            coupe.transform.SetParent(root.transform, true);
            coupe.transform.rotation = Quaternion.Euler(0f, 180f, 0f) * coupe.transform.rotation;

            // Strip any colliders/rigidbodies carried by the visual coupe mesh.
            // Child colliders at ground level penetrate the pavement and the
            // physics solver zeroes the body velocity every step, so held
            // throttle only produces ~0.2m of creep. The single upright root
            // box below is the only physical vehicle collider.
            foreach (var c in coupe.GetComponentsInChildren<Collider>())
                UnityEngine.Object.Destroy(c);
            foreach (var r in coupe.GetComponentsInChildren<Rigidbody>())
                UnityEngine.Object.Destroy(r);

            // Body collider: bottom lifted above pavement top (~0.14) so the body
            // never starts ground-penetrating (friction lock under throttle).
            var boxCol = root.AddComponent<BoxCollider>();
            boxCol.center = new Vector3(0f, 0.75f, 0f);
            boxCol.size = new Vector3(VEHICLE_WIDTH - 0.1f, 1.2f, VEHICLE_LENGTH - 0.2f);
            var pm = new PhysicsMaterial("VehicleLowFriction");
            pm.dynamicFriction = 0.05f;
            pm.staticFriction = 0.05f;
            pm.frictionCombine = PhysicsMaterialCombine.Minimum;
            pm.bounciness = 0f;
            boxCol.material = pm;

            var rb = root.AddComponent<Rigidbody>();
            rb.mass = 1200f;
            rb.drag = 0.6f;
            rb.angularDrag = 50f;
            rb.useGravity = true;
            rb.isKinematic = false;
            rb.interpolation = RigidbodyInterpolation.Interpolate;
            rb.constraints = RigidbodyConstraints.FreezeRotationX | RigidbodyConstraints.FreezeRotationZ;

            var v = root.AddComponent<VehicleInteraction>();
            v._player = player;
            v._rb = rb;
            v._body = root.GetComponent<BoxCollider>();
            v._cc = player.GetComponent<CharacterController>();
            v._walker = player.GetComponent<Walker>();
            v._follow = follow;
            for (int i = 0; i < player.transform.childCount; i++)
                if (player.transform.GetChild(i).name == "PlayerVisual")
                    v._pv = player.transform.GetChild(i);

            // Always register vehicle root even on foot so reset is observable
            Set("Vehicle", root.transform);
        }

        void Start()
        {
            // Let gravity settle vehicle onto ground at start
            _rb.linearVelocity = Vector3.zero;
        }

        float _throttle;
        float _steer;

        void Update()
        {
            bool e = LoopInput.Pressed(KeyCode.E);
            bool r = LoopInput.Pressed(KeyCode.R);

            if (r)
            {
                DoReset();
                return;
            }

            if (!_driving)
            {
                if (e && Vector3.Distance(_player.transform.position, transform.position) < 2.5f)
                    Enter();
                return;
            }

            _throttle = LoopInput.MoveY;
            _steer = LoopInput.MoveX;

            if (e) Exit();
        }

        void FixedUpdate()
        {
            if (!_driving) return;

            float throttle = _throttle;
            float steer = _steer;

            Vector3 fwd = transform.forward;
            fwd.y = 0f;
            fwd.Normalize();

            // Forward motion via direct velocity (bypasses friction lock)
            float maxSpeed = 12f;
            float accel = 18f;
            float fwdSpeed = Vector3.Dot(_rb.linearVelocity, fwd);

            float newSpeed;
            if (Mathf.Abs(throttle) > 0.01f)
            {
                float target = throttle * maxSpeed;
                float step = accel * Time.fixedDeltaTime;
                if (Mathf.Abs(target) > Mathf.Abs(fwdSpeed))
                    newSpeed = fwdSpeed + Mathf.Sign(target) * step;
                else
                    newSpeed = target;
                if (Mathf.Abs(newSpeed) > maxSpeed)
                    newSpeed = Mathf.Sign(newSpeed) * maxSpeed;
            }
            else
            {
                float decel = 5f * Time.fixedDeltaTime;
                if (Mathf.Abs(fwdSpeed) <= decel) newSpeed = 0f;
                else newSpeed = fwdSpeed - Mathf.Sign(fwdSpeed) * decel;
            }

            // Reconstruct velocity: forward axis only + preserve vertical
            _rb.linearVelocity = fwd * newSpeed + Vector3.up * _rb.linearVelocity.y;

            // Steering: yaw angular velocity
            float turnRate = steer * 90f * Mathf.Clamp01(Mathf.Abs(newSpeed) / 4f)
                             * Mathf.Sign(newSpeed + 0.001f);
            _rb.angularVelocity = new Vector3(0f, turnRate, 0f);

            // Ground: prevent falling through only; do NOT push upward
            if (transform.position.y <= 0f && _rb.linearVelocity.y < 0f)
            {
                var v = _rb.linearVelocity;
                v.y = 0f;
                _rb.linearVelocity = v;
            }
        }

        void Enter()
        {
            _driving = true;
            _speed = 0f;
            _walker.enabled = false;
            _cc.enabled = false;
            if (_pv) _pv.gameObject.SetActive(false);
            _follow.target = transform;
            Set("Mode", "vehicle");
        }

        void Exit()
        {
            _driving = false;
            _speed = 0f;
            _rb.linearVelocity = Vector3.zero;

            Vector3 exitPos = transform.position + transform.right * -1.5f + Vector3.up * 0.3f;
            _player.transform.position = exitPos;
            _player.transform.rotation = Quaternion.LookRotation(transform.forward, Vector3.up);
            _walker.enabled = true;
            _cc.enabled = true;
            if (_pv) _pv.gameObject.SetActive(true);
            _follow.target = _player.transform;
            Set("Mode", "foot");
        }

        void DoReset()
        {
            // Reset driving state
            _speed = 0f;
            _driving = false;

            // Reset car: stop physics, teleport, sync
            _rb.linearVelocity = Vector3.zero;
            _rb.angularVelocity = Vector3.zero;
            _rb.position = CarResetPos;
            _rb.rotation = CarResetRot;
            transform.position = CarResetPos;
            transform.rotation = CarResetRot;

            // Disable player controllers before teleport
            if (_cc != null) _cc.enabled = false;
            if (_walker != null) _walker.enabled = false;
            if (_pv) _pv.gameObject.SetActive(true);

            // Teleport player
            _player.transform.position = PlayerResetPos;
            _player.transform.rotation = Quaternion.identity;

            // Force physics to acknowledge new positions BEFORE re-enabling CC
            Physics.SyncTransforms();

            // Re-enable controllers - they seed from current (correct) position
            if (_cc != null) _cc.enabled = true;
            if (_walker != null) _walker.enabled = true;

            _follow.target = _player.transform;
            Set("Mode", "foot");
            Set("Vehicle", transform);
            Set("Health", 100);

            // Increment restart count only on this real reset.
            int current = 0;
            var f = typeof(LoopSignals).GetField("Restarts", St);
            var p = typeof(LoopSignals).GetProperty("Restarts", St);
            if (f != null) current = (int)f.GetValue(null);
            else if (p != null) current = (int)p.GetValue(null);
            Set("Restarts", current + 1);
        }

        bool GroundRaycast(Vector3 from, out RaycastHit hit)
        {
            Ray ray = new Ray(from + Vector3.up * 1.5f, Vector3.down);
            float remaining = 6f;
            hit = default;
            for (int i = 0; i < 4; i++)
            {
                if (!Physics.Raycast(ray, out RaycastHit h, remaining, ~0, QueryTriggerInteraction.Ignore))
                    return false;
                if (h.transform.root == transform)
                {
                    float advance = (ray.origin - (h.point + Vector3.down * 0.005f)).magnitude;
                    ray.origin = h.point - Vector3.up * 0.005f;
                    remaining -= advance + 0.01f;
                    if (remaining <= 0f) return false;
                    continue;
                }
                hit = h;
                return true;
            }
            return false;
        }

        static void Set(string n, object val)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(n, St); var p = t.GetProperty(n, St);
            if (f == null && p == null) return;
            var type = f != null ? f.FieldType : p.PropertyType;
            if (type == typeof(Transform) && val is Component c) val = c.transform;
            else if (type.IsEnum && val != null) val = Enum.Parse(type, val.ToString(), true);
            if (f != null) f.SetValue(null, val); else p.SetValue(null, val);
        }
    }
}
