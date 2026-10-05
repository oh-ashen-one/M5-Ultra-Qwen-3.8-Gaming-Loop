// Original cloud-authored controller infrastructure; not gameplay authorship.
using System;
using System.IO;
using System.Linq;
using UnityEngine;

public static class LoopInput
{
    [Serializable] public class Step { public float start, end; public string[] keys; }
    [Serializable] public class Scenario { public string id; public float duration; public Step[] steps; public float[] captures; }
    public static Scenario Replay { get; private set; }
    public static float Elapsed { get; internal set; }
    static bool previousLoaded;
    static string[] previous = new string[0];
    static string[] current = new string[0];
    public static void Load(string path) { Replay = JsonUtility.FromJson<Scenario>(File.ReadAllText(path)); }
    internal static void Tick(float elapsed)
    {
        Elapsed = elapsed;
        previous = current;
        current = Replay == null ? new string[0] : Replay.steps.Where(s => elapsed >= s.start && elapsed < s.end)
            .SelectMany(s => s.keys).Distinct().ToArray();
        previousLoaded = true;
    }
    public static bool Held(KeyCode key) { return Replay == null ? Input.GetKey(key) : current.Contains(key.ToString()); }
    public static bool Pressed(KeyCode key) { return Replay == null ? Input.GetKeyDown(key) : previousLoaded && current.Contains(key.ToString()) && !previous.Contains(key.ToString()); }
    public static float MoveX { get { return (Held(KeyCode.D) ? 1 : 0) - (Held(KeyCode.A) ? 1 : 0); } }
    public static float MoveY { get { return (Held(KeyCode.W) ? 1 : 0) - (Held(KeyCode.S) ? 1 : 0); } }
    public static string[] ActiveKeys { get { return current; } }
}

// Game code registers the actual objects/state it uses. The harness observes
// transforms during runtime; it never moves game actors or forces success.
public static class LoopSignals
{
    public static Transform Player, Vehicle;
    public static string Mode = "foot", Mission = "not_started";
    public static float Health = 100;
    public static int Shots, Hits, PursuitLevel, Restarts;
}
