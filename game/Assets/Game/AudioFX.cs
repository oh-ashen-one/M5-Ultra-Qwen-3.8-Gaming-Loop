using System;
using System.Reflection;
using UnityEngine;

namespace ChicagoGame
{
    // Original procedural audio. Nothing is downloaded: every clip is built at
    // runtime from generated samples and played through real AudioSources under
    // the camera's AudioListener. Cues are driven ONLY by reading real gameplay
    // signals (Shots/Hits/Health/Mission/PursuitLevel/Mode/Vehicle/Player) that
    // the mission + combat systems already write from actual events, plus the
    // player's and vehicle's measured motion. No replay detection, no object
    // moving, no invented signal.
    public class AudioFX : MonoBehaviour
    {
        static readonly BindingFlags St = BindingFlags.Public | BindingFlags.Static;
        static AudioFX I;

        const int SR = 44100;

        // Deterministic LCG so a rebuilt run always sounds identical.
        uint seed = 0x1234abcd;
        float Rand()
        {
            seed = seed * 1664525u + 1013904223u;
            return (seed >> 8) / 16777216f;
        }

        AudioClip foot, gun, hit, hurt, cueStart, cueWin, cueFail, wantedUp;
        AudioSource oneShot, engine;
        Transform engineRig;

        public static void Install(Transform rig)
        {
            if (rig == null) return;
            var host = new GameObject("AudioFX");
            host.transform.SetParent(rig, false);
            host.transform.localPosition = Vector3.zero;
            I = host.AddComponent<AudioFX>();
            I.Build();
        }

        void Build()
        {
            AudioListener al = GetComponentInParent<AudioListener>();
            if (al == null) gameObject.AddComponent<AudioListener>();

            oneShot = gameObject.AddComponent<AudioSource>();
            oneShot.playOnAwake = false;
            oneShot.spatialBlend = 0f;      // HUD/UI-like: fully 2D at the ear
            oneShot.rolloffMode = AudioRolloffMode.Linear;

            engine = gameObject.AddComponent<AudioSource>();
            engine.playOnAwake = false;
            engine.spatialBlend = 0f;
            engine.loop = true;
            engine.volume = 0f;

            float e;
            foot       = Make(0.16f, i => Footstep(i, out e));
            gun        = Make(0.22f, i => Gunshot(i));
            hit        = Make(0.09f, i => Blip(i, 1200f, 0.02f));
            hurt       = Make(0.18f, i => Sweep(i, 420f, 170f, 40f));
            cueStart   = Make(0.34f, i => ToneSeq(i, new[] { 392f, 523f }, 0.17f));
            cueWin     = Make(0.54f, i => ToneSeq(i, new[] { 523f, 659f, 784f }, 0.18f));
            cueFail    = Make(0.60f, i => Sweep(i, 380f, 120f, 6f));
            wantedUp   = Make(0.20f, i => ToneSeq(i, new[] { 880f, 660f }, 0.10f));
            engine.clip = Make(0.60f, i => EngineLoop(i));
            engine.Play();

            AudioListener.volume = 1f;
        }

        // ---- one-shot triggers, level-balanced ----
        public static void FootstepWheeled() { if (I) I.Play(I.foot, 0.32f, 0.85f + I.Rand() * 0.3f); }
        public static void Gunshot()         { if (I) I.Play(I.gun, 0.5f, 0.95f + I.Rand() * 0.12f); }
        public static void HitConfirm()      { if (I) I.Play(I.hit, 0.42f, 1f); }
        public static void Hurt()            { if (I) I.Play(I.hurt, 0.55f, 1f); }
        public static void MissionStart()    { if (I) I.Play(I.cueStart, 0.5f, 1f); }
        public static void MissionWin()      { if (I) I.Play(I.cueWin, 0.6f, 1f); }
        public static void MissionFail()     { if (I) I.Play(I.cueFail, 0.6f, 1f); }
        public static void WantedUp()        { if (I) I.Play(I.wantedUp, 0.4f, 1f); }

        void Play(AudioClip c, float vol, float pitch)
        {
            if (c == null || oneShot == null) return;
            oneShot.pitch = Mathf.Clamp(pitch, 0.5f, 2f);
            oneShot.PlayOneShot(c, vol);
        }

        // ---- polling of real signals ----
        int lastShots, lastHits, lastHealth, lastPursuit;
        string lastMission;
        Vector3 lastPlayer, lastVeh;
        float footAccum;
        bool primed;

        void Update()
        {
            int shots = ReadInt("Shots");
            int hits = ReadInt("Hits");
            int hp = ReadInt("Health");
            int pursuit = ReadInt("PursuitLevel");
            string mission = ReadStr("Mission");
            string mode = ReadStr("Mode");

            if (!primed)
            {
                lastShots = shots; lastHits = hits; lastHealth = hp;
                lastPursuit = pursuit; lastMission = mission; primed = true;
                if (mission == "active") MissionStart();
            }

            if (shots > lastShots) Gunshot();
            if (hits > lastHits) HitConfirm();
            if (hp < lastHealth && lastHealth > 0) Hurt();
            if (pursuit > lastPursuit && pursuit > 0) WantedUp();
            if (mission != lastMission)
            {
                if (mission == "complete") MissionWin();
                else if (mission == "failed") MissionFail();
                else if (mission == "active" && lastMission != null) MissionStart();
                lastMission = mission;
            }
            lastShots = shots; lastHits = hits; lastHealth = hp; lastPursuit = pursuit;

            // ---- footsteps: measured on-foot travel ----
            Vector3 p = LoopSignals.Player ? LoopSignals.Player.position : lastPlayer;
            if (mode == "foot")
            {
                float dh = Vector3.Distance(new Vector3(p.x, 0f, p.z),
                                            new Vector3(lastPlayer.x, 0f, lastPlayer.z));
                if (dh < 0.6f) footAccum += dh;   // ignore teleports/resets
                if (footAccum >= 1.15f) { FootstepWheeled(); footAccum = 0f; }
            }
            lastPlayer = p;

            // ---- engine: measured vehicle speed ----
            Vector3 v = LoopSignals.Vehicle ? LoopSignals.Vehicle.position : lastVeh;
            float vspeed = Vector3.Distance(new Vector3(v.x, 0f, v.z),
                                            new Vector3(lastVeh.x, 0f, lastVeh.z)) / Mathf.Max(1e-4f, Time.deltaTime);
            lastVeh = v;
            bool driving = mode == "vehicle";
            float spd = Mathf.Clamp(vspeed / 8f, 0f, 1f);
            float wantVol = driving ? 0.08f + spd * 0.14f : 0f;
            float wantPitch = 0.65f + spd * 0.9f;
            if (engine != null)
            {
                engine.volume = Mathf.Lerp(engine.volume, wantVol, 0.12f);
                engine.pitch = Mathf.Lerp(engine.pitch, wantPitch, 0.1f);
            }
        }

        // ---- sample generators ----
        AudioClip Make(float dur, Func<int, float> gen)
        {
            int n = Mathf.Max(1, Mathf.RoundToInt(dur * SR));
            var clip = AudioClip.Create("fx", n, 1, SR, false);
            var data = new float[n];
            for (int i = 0; i < n; i++) data[i] = Mathf.Clamp(gen(i), -1f, 1f);
            clip.SetData(data, 0);
            return clip;
        }

        float Footstep(int i, out float e)
        {
            float t = i / (float)SR;
            e = Mathf.Exp(-t * 26f);
            float body = Mathf.Sin(2f * Mathf.PI * 88f * t);
            float knock = Mathf.Sin(2f * Mathf.PI * 240f * t) * 0.4f;
            float noise = (Rand() * 2f - 1f) * 0.4f;
            return e * (0.6f * body + 0.3f * knock + 0.35f * noise);
        }

        float Gunshot(int i)
        {
            float t = i / (float)SR;
            float env = Mathf.Exp(-t * 22f);
            float boom = Mathf.Sin(2f * Mathf.PI * 62f * t) * 0.6f;
            float crack = (Rand() * 2f - 1f);
            // brief high sizzle that decays faster than the body
            float sizzle = (Rand() * 2f - 1f) * Mathf.Exp(-t * 60f);
            return env * (0.45f * crack + 0.6f * boom) + sizzle * 0.4f;
        }

        float Blip(int i, float freq, float decay)
        {
            float t = i / (float)SR;
            float env = Mathf.Exp(-t / decay);
            return env * Mathf.Sin(2f * Mathf.PI * freq * t);
        }

        float Sweep(int i, float f0, float f1, float decay)
        {
            float t = i / (float)SR;
            float span = 1f / SR;
            float f = Mathf.Lerp(f0, f1, t);
            float env = Mathf.Exp(-t * decay);
            // integrate instantaneous frequency for a smooth glide
            float phase = 2f * Mathf.PI * (f0 * t + (f1 - f0) * 0.5f * t * t);
            float noise = (Rand() * 2f - 1f) * 0.15f;
            return env * (Mathf.Sin(phase) + noise);
        }

        float ToneSeq(int i, float[] freqs, float seg)
        {
            float t = i / (float)SR;
            int s = Mathf.Min(freqs.Length - 1, Mathf.FloorToInt(t / seg));
            float local = t - s * seg;
            float env = Mathf.Exp(-local * 8f);
            return env * Mathf.Sin(2f * Mathf.PI * freqs[s] * t) * 0.8f;
        }

        float EngineLoop(int i)
        {
            // 0.6 s window: harmonics chosen so each completes an integer number
            // of cycles (70*0.6=42, 105*0.6=63, 140*0.6=84) -> seamless loop.
            float t = i / (float)SR;
            float s = Mathf.Sin(2f * Mathf.PI * 70f * t) * 0.5f
                    + Mathf.Sin(2f * Mathf.PI * 105f * t) * 0.22f
                    + Mathf.Sin(2f * Mathf.PI * 140f * t) * 0.16f;
            float rumble = (Rand() * 2f - 1f) * 0.08f;
            return (s + rumble) * 0.6f;
        }

        // ---- tolerant readers (never throw if a member is absent) ----
        static int ReadInt(string name)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            try
            {
                if (f != null) return Convert.ToInt32(f.GetValue(null));
                if (p != null && p.CanRead) return Convert.ToInt32(p.GetValue(null));
            }
            catch { }
            return 0;
        }

        static string ReadStr(string name)
        {
            var t = typeof(LoopSignals);
            var f = t.GetField(name, St);
            var p = t.GetProperty(name, St);
            try
            {
                if (f != null) return f.GetValue(null) as string;
                if (p != null && p.CanRead) return p.GetValue(null) as string;
            }
            catch { }
            return null;
        }
    }
}
