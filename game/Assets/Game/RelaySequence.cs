using UnityEngine;

namespace ChicagoGame
{
    public partial class RelaySequence : MonoBehaviour
    {
        static RelaySequence _inst;
        GameObject player;
        Camera cam;
        RouteMission chapter;
        int lastRestarts;

        public bool Active, AllComplete, Failed;
        public int ActivationCount, ExpectedIndex, WrongOrderCount;
        public float Remaining;
        public string Objective;
        public Transform[] Relays = new Transform[3];

        float armedAt, flashUntil;
        int flashIndex = -1;

        public static void Install(GameObject player, Camera cam)
        {
            var go = new GameObject("RelaySequence");
            _inst = go.AddComponent<RelaySequence>();
            _inst.player = player;
            _inst.cam = cam;
            _inst.chapter = GameObject.Find("RouteMission").GetComponent<RouteMission>();
            _inst.lastRestarts = LoopSignals.Restarts;
            _inst.BuildProps();
            _inst.BuildHud();
            _inst.SetSitesVisible(false);
            _inst.HideHud();
        }

        void Update()
        {
            if (LoopSignals.Restarts != lastRestarts)
            {
                lastRestarts = LoopSignals.Restarts;
                Active = AllComplete = Failed = false;
                ActivationCount = ExpectedIndex = WrongOrderCount = 0;
                Remaining = 0;
                flashIndex = -1;
                flashUntil = 0;
                SetSitesVisible(false);
                HideHud();
                return;
            }

            if (!Active)
            {
                if (chapter.RouteStage == 2 && chapter.RouteComplete)
                {
                    Active = true;
                    armedAt = Time.time;
                    Remaining = 45;
                    SetSitesVisible(true);
                }
                return;
            }

            if (AllComplete || Failed) return;
            Remaining = UnityEngine.Mathf.Max(0, 45 - (Time.time - armedAt));
            if (Remaining <= 0) { Failed = true; return; }

            if (LoopInput.Pressed(KeyCode.F) && LoopSignals.Mode == "foot")
            {
                int hit = -1;
                float px = player.transform.position.x, pz = player.transform.position.z;
                for (int i = 0; i < Relays.Length; i++)
                {
                    if (Relays[i] == null) continue;
                    float dx = Relays[i].position.x - px, dz = Relays[i].position.z - pz;
                    if (dx * dx + dz * dz <= 2.25f) { hit = i; break; }
                }
                if (hit < 0) return;
                if (hit == ExpectedIndex)
                {
                    ActivationCount++;
                    ExpectedIndex++;
                    if (ActivationCount >= 3) AllComplete = true;
                }
                else
                {
                    ActivationCount = 0;
                    ExpectedIndex = 0;
                    WrongOrderCount++;
                    flashIndex = hit;
                    flashUntil = Time.time + 0.3f;
                }
            }
        }

        void LateUpdate()
        {
            PaintSites(Time.time < flashUntil ? flashIndex : -1);
            UpdateHud();
        }
    }
}