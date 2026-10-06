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
                // Forgiving, readable boarding: treat the car's horizontal
                // footprint (half-length + a doorway band) as the interaction
                // zone. The prior 1.0 m ClosestPoint gate failed whenever the
                // collider box sat behind a parked-car shoulder, so a player
                // standing right next to the door was still locked out and the
                // drive leg never started.
                if (e && NearCar(_player.transform.position))
                    Enter();
                return;
            }

            // Driving: physics-based swept movement
            float throttle = LoopInput.MoveY;
            float steer = LoopInput.MoveX;

            _speed += throttle * 6f * Time.deltaTime;
            _speed = Mathf.Clamp(_speed, -3f, 8f);
            if (Mathf.Abs(throttle) < 0.01f)
                _speed = Mathf.MoveTowards(_speed, 0f, 4f * Time.deltaTime);

            // Steering: set Y rotation via physics
            float turn = 90f * Mathf.Clamp01(Mathf.Abs(_speed) / 4f) * Mathf.Sign(_speed);
            float newYaw = transform.eulerAngles.y + steer * turn * Time.deltaTime;
            Quaternion rot = Quaternion.Euler(0f, newYaw, 0f);
            _rb.MoveRotation(rot);

            // Desired velocity in car forward (horizontal only)
            Vector3 forward = rot * Vector3.forward;
            forward.y = 0f;
            Vector3 targetVel = forward * _speed;
            targetVel.y = _rb.linearVelocity.y;

            // No artificial speed-kill: rely on the collider/wall contact and
            // real drag to stop the car under held throttle.
            _rb.linearVelocity = targetVel;

            // Ground snap: raycast down skipping own collider
            if (GroundRaycast(transform.position, out var hit))
            {
                float groundY = hit.point.y;
                float diff = groundY - transform.position.y;
                if (diff > 0.02f && diff < 0.5f)
                {
                    Vector3 vel = _rb.linearVelocity;
                    vel.y = diff / Time.deltaTime;
                    _rb.linearVelocity = vel;
                }
            }

            if (e) Exit();
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
            // Reset car state
            _rb.linearVelocity = Vector3.zero;
            _rb.angularVelocity = Vector3.zero;
            _speed = 0f;
            _driving = false;
            transform.position = CarResetPos;
            transform.rotation = CarResetRot;
            _rb.position = CarResetPos;
            _rb.rotation = CarResetRot;

            // An ENABLED CharacterController clamps its own transform, so a
            // direct position write is silently ignored. Disable it (and the
            // Walker that drives it) before teleporting, then re-enable so the
            // controller re-seeds from the spawn point and gravity settles it.
            if (_cc != null) _cc.enabled = false;
            if (_walker != null) _walker.enabled = false;

            _player.transform.position = PlayerResetPos;
            _player.transform.rotation = Quaternion.identity;

            if (_pv) _pv.gameObject.SetActive(true);
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

        bool NearCar(Vector3 p)
        {
            // Horizontal footprint test: local half extents of the body box plus
            // a ~1.1 m boarding band. Rotation-aware so it still works after the
            // car has been driven and left at an angle. The prior 1.0 m
            // ClosestPoint gate rejected a player standing at the door because
            // the parked-coupe shoulder pushed the collider's nearest point out
            // of reach, so the drive leg never began.
            Vector3 local = transform.InverseTransformPoint(p);
            float hx = VEHICLE_WIDTH * 0.5f + 1.1f;
            float hz = VEHICLE_LENGTH * 0.5f + 1.1f;
            return Mathf.Abs(local.x) <= hx && Mathf.Abs(local.z) <= hz;
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
