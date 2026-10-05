// Trusted capture/input instrumentation. It supplies no game art or mechanics.
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;

[DefaultExecutionOrder(-32000)]
public class LoopInputPump : MonoBehaviour
{
    void Update() { LoopInput.Tick(Time.realtimeSinceStartup - LoopRuntime.StartedAt); }
}

[DefaultExecutionOrder(32000)]
public class LoopRuntime : MonoBehaviour
{
    public static float StartedAt { get; private set; }
    [Serializable] public class Sample {
        public float time, dt, health; public string mode, mission, graphics;
        public float[] player, vehicle; public string[] keys;
        public int frame, shots, hits, pursuit, restarts; public bool camera, hasController, grounded;
        public float[] playerScale, playerUp, playerForward;
    }
    [Serializable] public class ObjectObservation {
        public string name, kind; public float[] position, lossyScale, up, forward, boundsCenter, boundsSize;
        public bool enabled;
    }
    [Serializable] public class SceneObservation { public ObjectObservation[] objects; }
    [Serializable] public class Final { public string capture_id, unity, graphics; public int samples, errors; public float duration; public bool completed; }
    string output, captureId;
    float started, nextSample;
    int samples, errors, captureIndex;
    bool finished;
    bool observedScene;
    static float[] Vec(Vector3 v) { return new [] { v.x, v.y, v.z }; }
    static string Hierarchy(Transform t) { var n=t.name; while(t.parent != null) {t=t.parent;n=t.name+"/"+n;} return n; }
    static ObjectObservation Observe(Component c, string kind, Bounds b) {
        return new ObjectObservation {name=Hierarchy(c.transform), kind=kind, position=Vec(c.transform.position),
            lossyScale=Vec(c.transform.lossyScale), up=Vec(c.transform.up), forward=Vec(c.transform.forward),
            boundsCenter=Vec(b.center), boundsSize=Vec(b.size),
            enabled=c.gameObject.activeInHierarchy && (!(c is Renderer) || ((Renderer)c).enabled)};
    }
    static string Arg(string key) {
        var args = Environment.GetCommandLineArgs();
        var i = Array.IndexOf(args, key); return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
    }
    void Awake()
    {
        Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
        Application.runInBackground = true;
        QualitySettings.vSyncCount = 0; Application.targetFrameRate = 60;
        output = Arg("--loop-output"); captureId = Arg("--loop-capture-id");
        var scenario = Arg("--loop-scenario");
        if (scenario != null) LoopInput.Load(scenario);
        if (output != null) Directory.CreateDirectory(output);
        Application.logMessageReceived += OnLog;
        var type = AppDomain.CurrentDomain.GetAssemblies().Select(a => a.GetType("ChicagoGame.Bootstrap", false)).FirstOrDefault(t => t != null);
        if (type == null) throw new Exception("Required ChicagoGame.Bootstrap.Create() is missing");
        var method = type.GetMethod("Create", BindingFlags.Public | BindingFlags.Static);
        if (method == null) throw new Exception("Required public static Create() is missing");
        method.Invoke(null, null);
        started = Time.realtimeSinceStartup;
        StartedAt = started;
        gameObject.AddComponent<LoopInputPump>();
    }
    void OnLog(string message, string stack, LogType type)
    {
        if (type == LogType.Exception || type == LogType.Error || type == LogType.Assert) {
            errors++;
            if (output != null) File.AppendAllText(Path.Combine(output, "runtime-errors.txt"), message + "\n" + stack + "\n");
        }
    }
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape)) { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }
    }
    static float[] Position(Transform t) { return t == null ? null : new [] {t.position.x, t.position.y, t.position.z}; }
    void LateUpdate()
    {
        if (output == null || finished || LoopInput.Replay == null) return;
        var elapsed = LoopInput.Elapsed;
        if (!observedScene) {
            var renderers=UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)
                .Take(2048).Select(r => Observe(r,"renderer",r.bounds));
            var colliders=UnityEngine.Object.FindObjectsByType<Collider>(FindObjectsSortMode.None)
                .Take(150).Select(c => Observe(c,c.GetType().Name,c.bounds));
            File.WriteAllText(Path.Combine(output,"scene-transforms.json"),JsonUtility.ToJson(
                new SceneObservation {objects=renderers.Concat(colliders).ToArray()},true));
            observedScene=true;
        }
        if (elapsed >= nextSample) {
            nextSample = elapsed + 0.1f;
            var actor=LoopSignals.Player;
            var cc=actor == null ? null : actor.GetComponent<CharacterController>();
            var sample = new Sample {time=elapsed, dt=Time.unscaledDeltaTime, frame=Time.frameCount,
                player=Position(LoopSignals.Player), vehicle=Position(LoopSignals.Vehicle), keys=LoopInput.ActiveKeys,
                mode=LoopSignals.Mode, mission=LoopSignals.Mission, health=LoopSignals.Health,
                shots=LoopSignals.Shots, hits=LoopSignals.Hits, pursuit=LoopSignals.PursuitLevel, restarts=LoopSignals.Restarts,
                camera=Camera.main != null, graphics=SystemInfo.graphicsDeviceType.ToString(),
                hasController=cc != null, grounded=cc != null && cc.isGrounded,
                playerScale=actor == null ? null : Vec(actor.lossyScale),
                playerUp=actor == null ? null : Vec(actor.up),playerForward=actor == null ? null : Vec(actor.forward)};
            File.AppendAllText(Path.Combine(output, "trace.jsonl"), JsonUtility.ToJson(sample) + "\n"); samples++;
        }
        var captures = LoopInput.Replay.captures;
        if (captures != null && captureIndex < captures.Length && elapsed >= captures[captureIndex]) {
            var camera = Camera.main;
            if (camera == null) { errors++; captureIndex++; }
            else {
                // An actual frame of the running candidate, not an editor scene.
                var rt = new RenderTexture(960, 540, 24, RenderTextureFormat.ARGB32);
                var oldTarget = camera.targetTexture; var oldActive = RenderTexture.active;
                camera.targetTexture = rt; camera.Render(); RenderTexture.active = rt;
                var image = new Texture2D(960, 540, TextureFormat.RGB24, false);
                image.ReadPixels(new Rect(0, 0, 960, 540), 0, 0); image.Apply();
                File.WriteAllBytes(Path.Combine(output, "frame-" + captureIndex.ToString("D3") + ".png"), image.EncodeToPNG());
                camera.targetTexture = oldTarget; RenderTexture.active = oldActive; rt.Release();
                Destroy(rt); Destroy(image); captureIndex++;
            }
        }
        if (elapsed >= LoopInput.Replay.duration) {
            finished = true;
            var result = new Final {capture_id=captureId, unity=Application.unityVersion,
                graphics=SystemInfo.graphicsDeviceType.ToString(), samples=samples, errors=errors,
                duration=elapsed, completed=true};
            File.WriteAllText(Path.Combine(output, "runtime-result.json"), JsonUtility.ToJson(result, true));
            Application.Quit(errors == 0 ? 0 : 3);
        }
    }
}
