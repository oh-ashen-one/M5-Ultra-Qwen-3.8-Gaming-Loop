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
        bool _driving;
        float _speed;

        public static void Install(GameObject player, GameObject coupe, Follow follow)
        {
            if (!player || !coupe) return;
            var root = new GameObject("Vehicle");
            root.transform.position = coupe.transform.position;
            root.transform.rotation = Quaternion.Euler(0f, coupe.transform.eulerAngles.y, 0f);
            coupe.transform.SetParent(root.transform, true);
            coupe.transform.rotation = Quaternion.Euler(0f, 180f, 0f) * coupe.transform.rotation;
            var v = root.AddComponent<VehicleInteraction>();
            v._player = player;
            v._cc = player.GetComponent<CharacterController>();
            v._walker = player.GetComponent<Walker>();
            v._follow = follow;
            for (int i = 0; i < player.transform.childCount; i++)
                if (player.transform.GetChild(i).name == "PlayerVisual")
                    v._pv = player.transform.GetChild(i);
        }

        void Update()
        {
            bool e = LoopInput.Pressed(KeyCode.E);
            if (!_driving)
            {
                if (e && Vector3.Distance(_player.transform.position, transform.position) < 2.5f)
                    Enter();
                return;
            }
            float throttle = LoopInput.MoveY;
            float steer = LoopInput.MoveX;
            _speed += throttle * 6f * Time.deltaTime;
            _speed = Mathf.Clamp(_speed, -3f, 8f);
            if (Mathf.Abs(throttle) < 0.01f)
                _speed = Mathf.MoveTowards(_speed, 0f, 3f * Time.deltaTime);
            float turn = 90f * Mathf.Clamp01(Mathf.Abs(_speed) / 4f) * Mathf.Sign(_speed);
            transform.Rotate(0f, steer * turn * Time.deltaTime, 0f);
            Vector3 move = transform.forward * _speed * Time.deltaTime;
            float groundY = transform.position.y;
            if (Physics.Raycast(transform.position + Vector3.up, Vector3.down, out var hit, 3f))
                groundY = hit.point.y;
            move.y = groundY - transform.position.y;
            transform.position += move;
            if (e) Exit();
        }

        void Enter()
        {
            _driving = true; _speed = 0f;
            _walker.enabled = false; _cc.enabled = false;
            if (_pv) _pv.gameObject.SetActive(false);
            _follow.target = transform;
            Set("Vehicle", transform); Set("Mode", "vehicle");
        }

        void Exit()
        {
            _driving = false; _speed = 0f;
            _player.transform.position = transform.position + transform.right * -1.5f + Vector3.up * 0.02f;
            _player.transform.rotation = Quaternion.LookRotation(transform.forward, Vector3.up);
            _walker.enabled = true; _cc.enabled = true;
            if (_pv) _pv.gameObject.SetActive(true);
            _follow.target = _player.transform;
            Set("Vehicle", null); Set("Mode", "foot");
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
