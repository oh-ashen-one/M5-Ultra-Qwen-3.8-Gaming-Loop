using UnityEngine;
using System.Collections.Generic;

namespace ChicagoGame
{
    // ---------------------------------------------------------------------
    // One westbound exfil runner of the Counter-Exfil chapter.
    //
    // The actor IS the original courier: the same Generated/player/scene mesh,
    // stripped of inherited physics exactly like the existing interception
    // runners, then given one honest solid capsule plus a dynamic rigidbody so
    // the world, the aim ray and the coupe all agree it is real and hittable.
    //
    // Movement is pure physics: a commanded westbound velocity along the one
    // corridor the native survey actually qualified for a westbound capsule
    // ("central-westbound"), gravity left untouched, lateral correction only
    // when a real sweep test says the space is open. No transform traversal, no
    // teleport, no climbing through a barrier.
    //
    // A pin is PROVEN, never assumed: it needs real sustained CONTACT with the
    // courier's own coupe (OnCollisionEnter/Stay/Exit on this body, filtered to
    // that one root) AND real failure to make westward progress while the body
    // is still pressing west. Proximity or a ray alone never qualifies. The
    // uninterrupted hold clock is reset the instant either half is lost, so
    // driving the coupe away releases a live pin on the next step, and nothing
    // about a pin is cached once it lapses.
    //
    // This component never writes health, hp, alive, Restarts, Shots, Hits,
    // Mode, Mission or any signal. hp/alive belong to Combat, which damages any
    // genuinely hit live RivalAgent through its own existing path.
    // ---------------------------------------------------------------------
    public sealed class CounterExfilRunner : MonoBehaviour
    {
        // ---- wired once by CounterExfilMission ----
        public int Slot;
        public string Label = "RUNNER";
        public int StartHp = 3;
        public float DriveSpeed = 1.35f;
        public Transform Coupe;                                   // the player-driven coupe root
        public Vector3 LaneEast = new Vector3(47.605f, 0f, 17.4603f);   // surveyed east/alley crossing
        public Vector3 LaneWest = new Vector3(3.0f, 0f, 16.0057f);      // surveyed west exit crossing

        public RivalAgent Agent;        // real combat identity; never written here
        public Rigidbody Body;

        // ---- qualification constants ----
        const float BlockedRate = 0.30f;     // m/s of real westward travel still counted as "held"
        const float MeasuredTime = 0.5f;     // no verdict from an unmeasured body
        public const float Qualify = 0.8f;   // uninterrupted obstruction needed to qualify a pin

        const float MidEastX = 22.0f;
        const float MidEastZ = 16.5738f;
        const float MidWestX = 6.0f;
        const float MidWestZ = 16.0057f;

        // ---- live physical state, derived only from real physics ----
        float lastContact = -999f;
        float westEma;
        float observed;
        float hold;
        float pinTotal;
        float prevX;
        bool prevValid;
        bool downHandled;
        readonly List<Collider> coupeContacts = new List<Collider>();

        // ---- ordinary public read-only observation ----
        public int Hp { get { return Agent != null ? Mathf.Max(0, Agent.hp) : 0; } }
        public int HpAtStart { get { return StartHp; } }
        public bool Alive { get { return Agent != null && Agent.alive; } }
        public bool Killed { get { return Agent != null && !Agent.alive; } }
        public bool ContactNow
        {
            get
            {
                TrimCoupeContacts();
                return Coupe != null && coupeContacts.Count > 0 && lastContact >= -1f;
            }
        }
        public bool BlockedNow { get { return observed > MeasuredTime && westEma < BlockedRate; } }
        /// <summary>True only while a qualified pin is being maintained right now.</summary>
        public bool Pinned { get { return !DeathAuthority.IsDead && Alive && ContactNow && BlockedNow && hold >= Qualify; } }
        /// <summary>Uninterrupted contact+blocked clock, zeroed on any separation.</summary>
        public float HoldSeconds { get { return hold; } }
        /// <summary>Total seconds this actor has actually spent pin-qualified.</summary>
        public float PinTotal { get { return pinTotal; } }
        public bool EverPinned { get { return pinTotal > 0f; } }
        public float WestSpeed { get { return westEma; } }
        public float X { get { return transform.position.x; } }
        public float Z { get { return transform.position.z; } }

        /// <summary>z of the one validated lane at world x (piecewise survey, no invented offset).</summary>
        public float LaneZ(float x)
        {
            if (x >= LaneEast.x) return LaneEast.z;
            if (x <= LaneWest.x) return LaneWest.z;
            if (x >= MidEastX) return LerpZ(LaneEast.x, LaneEast.z, MidEastX, MidEastZ, x);
            if (x >= MidWestX) return LerpZ(MidEastX, MidEastZ, MidWestX, MidWestZ, x);
            return LerpZ(MidWestX, MidWestZ, LaneWest.x, LaneWest.z, x);
        }

        static float LerpZ(float x0, float z0, float x1, float z1, float x)
        {
            float span = x0 - x1;
            if (Mathf.Abs(span) < 0.0001f) return z0;
            return Mathf.Lerp(z0, z1, (x0 - x) / span);
        }

        /// <summary>Place on the validated lane; gravity settles the rest.</summary>
        public void SetOnLane(float x)
        {
            transform.position = new Vector3(x, 0.30f, LaneZ(x));
            transform.rotation = Quaternion.LookRotation(Vector3.left, Vector3.up);
            prevX = x; prevValid = false;
        }

        /// <summary>
        /// One physics step of the chapter, driven by the mission so a frozen or
        /// dead chapter drives nothing at all. Returns nothing; every observable
        /// is read back afterwards.
        /// </summary>
        public void PhysicsStep(float dt)
        {
            if (Body == null || dt <= 0f) return;

            if (!Alive)
            {
                // Permanently resolved: Combat has already dropped the collider,
                // so a downed body must not keep sailing. One stop, one latch.
                if (!downHandled)
                {
                    downHandled = true;
                    Vector3 d = Body.linearVelocity; d.x = 0f; d.z = 0f;
                    Body.linearVelocity = d;
                    Body.isKinematic = true;
                }
                return;
            }
            if (Body.isKinematic) Body.isKinematic = false;

            Vector3 p = Body.position;

            // Real measured westward travel, not the commanded number.
            float west = prevValid ? (prevX - p.x) / Mathf.Max(1e-4f, dt) : westEma;
            westEma = Mathf.Lerp(westEma, Mathf.Clamp(west, -6f, 6f), 0.3f);
            prevX = p.x; prevValid = true; observed += dt;

            // Keep pressing west every step: the solver, not a script, decides
            // whether the body moves. That is what makes a held body and a
            // shoved body look different from the outside.
            Vector3 vel = Body.linearVelocity;
            vel.x = -DriveSpeed;
            vel.z = 0f;
            float dz = LaneZ(p.x) - p.z;
            if (Mathf.Abs(dz) > 0.35f)
            {
                Vector3 side = dz > 0f ? Vector3.forward : Vector3.back;
                if (!BlockedAlong(side, DriveSpeed * dt * 2f + 0.02f))
                    vel.z = Mathf.Sign(dz) * DriveSpeed * 0.5f;
            }
            Body.linearVelocity = vel;   // vel.y untouched: gravity still owns it

            // ---- pin accounting: contact AND blocked, or the clock restarts ----
            bool held = ContactNow && BlockedNow;
            hold = held ? hold + dt : 0f;
            if (hold >= Qualify) pinTotal += dt;
        }

        /// <summary>Softly cancel the westward drive (chapter over). A living
        /// body stays dynamic - a pinned actor is never left frozen.</summary>
        public void CoastToStop()
        {
            if (Body == null || !Alive || Body.isKinematic) return;
            Vector3 v = Body.linearVelocity; v.x = 0f; v.z = 0f;
            Body.linearVelocity = v;
        }

        void OnCollisionEnter(Collision c) { Touch(c); }
        void OnCollisionStay(Collision c) { Touch(c); }
        void OnCollisionExit(Collision c) { Release(c); }

        void Touch(Collision c)
        {
            if (!Alive) return;
            if (!IsCoupe(c)) return;
            Collider col = c.collider;
            if (col == null) return;

            if (!coupeContacts.Contains(col))
            {
                coupeContacts.Add(col);
                if (coupeContacts.Count == 1) hold = 0f;
            }
            lastContact = Time.time;
        }

        void Release(Collision c)
        {
            if (!IsCoupe(c)) return;
            Collider col = c.collider;
            if (col != null) coupeContacts.Remove(col);

            if (coupeContacts.Count == 0)
            {
                lastContact = -999f;
                hold = 0f;
            }
        }

        void TrimCoupeContacts()
        {
            for (int i = coupeContacts.Count - 1; i >= 0; i--)
            {
                Collider c = coupeContacts[i];
                if (c == null || !c.enabled || !c.gameObject.activeInHierarchy || !IsCoupeCollider(c))
                    coupeContacts.RemoveAt(i);
            }

            if (coupeContacts.Count == 0 && lastContact > -1f)
            {
                lastContact = -999f;
                hold = 0f;
            }
        }
        bool IsCoupe(Collision c)
        {
            if (c == null) return false;
            return IsCoupeCollider(c.collider);
        }

        bool IsCoupeCollider(Collider c)
        {
            if (c == null || Coupe == null) return false;
            var t = c.transform;
            return t == Coupe || t.IsChildOf(Coupe);
        }

        bool BlockedAlong(Vector3 dir, float dist)
        {
            if (Body == null || dist <= 0f || Body.isKinematic) return false;
            var hits = Body.SweepTestAll(dir, dist);
            for (int i = 0; i < hits.Length; i++)
            {
                var h = hits[i];
                if (h.collider == null || h.collider.isTrigger) continue;
                var t = h.transform;
                if (t == transform || t.IsChildOf(transform)) continue;
                if (h.normal.y > 0.5f) continue;          // a floor is not a wall
                return true;
            }
            return false;
        }
    }
}
