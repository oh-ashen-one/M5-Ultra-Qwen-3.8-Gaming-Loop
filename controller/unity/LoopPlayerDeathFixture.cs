// External negative diagnostic: inject health=0 once, before game Update, at a
// declared ordinary-input boundary. Never moves actors or completes objectives.
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;

[DefaultExecutionOrder(-31900)]
public class LoopPlayerDeathFixture : MonoBehaviour
{
    [Serializable] public class State {
        public int courierStage, routeStage, relayCount, relayExpected, stopped, spawned, escaped;
        public bool carrying, routeComplete, relayActive, relayComplete, relayFailed;
        public bool interceptionActive, interceptionComplete, interceptionFailed;
    }
    [Serializable] public class Injection {
        public string caseName, utc, mode, mission;
        public float time, healthBefore, healthAfter;
        public int frame, restarts, shots;
        public string[] keys;
        public float[] player, vehicle;
        public State before;
        public LoopCounterExfilObservation.State counterBefore;
    }
    static readonly BindingFlags Fields = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    bool injected;
    string output;
    void Awake() {
        var args = Environment.GetCommandLineArgs(); int i = Array.IndexOf(args, "--loop-output");
        if (i >= 0 && i + 1 < args.Length) output = args[i + 1];
    }
    static T Read<T>(MonoBehaviour component, string field, T fallback = default(T)) {
        if (component == null) return fallback;
        var member = component.GetType().GetField(field, Fields);
        return member != null && member.GetValue(component) is T value ? value : fallback;
    }
    public static State Capture() {
        if (LoopInput.Replay == null || LoopInput.Replay.fixture != "player-death") return null;
        var all = UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None);
        Func<string, MonoBehaviour> find = name => all.FirstOrDefault(m => m.GetType().FullName == "ChicagoGame." + name);
        var courier = find("CourierMission"); var route = find("RouteMission");
        var relay = find("RelaySequence"); var intercept = find("InterceptionMission");
        if (!courier || !route || !relay || !intercept) throw new Exception("Death diagnostic needs all installed chapters");
        var parcel = Read<Transform>(courier, "parcel");
        return new State {
            courierStage=Read(courier,"stage",-1), carrying=parcel && LoopSignals.Player && parcel.IsChildOf(LoopSignals.Player),
            routeStage=Read(route,"RouteStage",-1), routeComplete=Read<bool>(route,"RouteComplete"),
            relayCount=Read(relay,"ActivationCount",-1), relayExpected=Read(relay,"ExpectedIndex",-1),
            relayActive=Read<bool>(relay,"Active"), relayComplete=Read<bool>(relay,"AllComplete"), relayFailed=Read<bool>(relay,"Failed"),
            stopped=Read(intercept,"Stopped",-1), spawned=Read(intercept,"Spawned",-1), escaped=Read(intercept,"Escaped",-1),
            interceptionActive=Read<bool>(intercept,"Active"), interceptionComplete=Read<bool>(intercept,"Complete"),
            interceptionFailed=Read<bool>(intercept,"Failed")
        };
    }
    static float[] Position(Transform value) { return value ? new[]{value.position.x,value.position.y,value.position.z} : null; }
    void Update() {
        var scenario = LoopInput.Replay;
        if (injected || scenario == null || scenario.fixture != "player-death" || LoopInput.Elapsed < scenario.death_at) return;
        if (!string.IsNullOrEmpty(scenario.death_key)) {
            if (!Enum.TryParse<KeyCode>(scenario.death_key, out var key)) throw new Exception("Invalid death diagnostic input edge");
            if (!LoopInput.Pressed(key)) return;
        }
        if (LoopSignals.Restarts != 0 || LoopSignals.Health <= 0 || output == null)
            throw new Exception("Death fixture needs a living original run at the declared boundary");
        var evidence = new Injection { caseName=scenario.death_case, utc=DateTime.UtcNow.ToString("O"),
            time=LoopInput.Elapsed, frame=Time.frameCount, healthBefore=LoopSignals.Health,
            mode=LoopSignals.Mode, mission=LoopSignals.Mission, restarts=LoopSignals.Restarts,
            shots=LoopSignals.Shots, keys=LoopInput.ActiveKeys, player=Position(LoopSignals.Player),
            vehicle=Position(LoopSignals.Vehicle), before=Capture(), counterBefore=LoopCounterExfilObservation.Capture() };
        LoopSignals.Health = 0;
        evidence.healthAfter = LoopSignals.Health;
        injected = true;
        File.WriteAllText(Path.Combine(output,"death-injection.json"), JsonUtility.ToJson(evidence, true));
    }
}
