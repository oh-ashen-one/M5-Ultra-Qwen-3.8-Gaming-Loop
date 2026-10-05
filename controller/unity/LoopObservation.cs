// Original external observation only: never moves actors or forces game state.
using System;
using System.Linq;
using UnityEngine;

public static class LoopObservation
{
    [Serializable] public class MissionObject {
        public string name, hierarchy;
        public float[] position;
        public bool playerChild;
    }
    public static MissionObject[] MissionObjects(Transform player)
    {
        return UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)
            .Where(r => r.enabled && (r.name == "Parcel" || r.name == "DropPad" || r.name == "Beacon"))
            .Take(12).Select(r => {
                var t = r.transform; var p = t.position; var path = t.name;
                for (var parent = t.parent; parent != null; parent = parent.parent) path = parent.name + "/" + path;
                return new MissionObject {name=t.name, hierarchy=path, position=new [] {p.x,p.y,p.z},
                    playerChild=player != null && t.IsChildOf(player)};
            }).ToArray();
    }
    static readonly float[] audio = new float[256];
    public static bool HasCollider(Transform root)
    {
        return root != null && root.GetComponentsInChildren<Collider>().Any(c => c.enabled && !c.isTrigger);
    }
    public static float HorizontalPenetration(Transform root)
    {
        if (root == null) return 0f;
        float worst = 0f;
        foreach (var own in root.GetComponentsInChildren<Collider>())
        {
            if (!own.enabled || own.isTrigger) continue;
            var b = own.bounds;
            foreach (var other in Physics.OverlapBox(b.center, b.extents, Quaternion.identity, ~0, QueryTriggerInteraction.Ignore))
            {
                if (other == own || other.transform.IsChildOf(root)) continue;
                Vector3 direction; float distance;
                if (Physics.ComputePenetration(own, own.transform.position, own.transform.rotation,
                    other, other.transform.position, other.transform.rotation, out direction, out distance)
                    && Mathf.Abs(direction.y) < .5f) worst = Mathf.Max(worst, distance);
            }
        }
        return worst;
    }
    public static string[] VisibleText()
    {
        return UnityEngine.Object.FindObjectsByType<TextMesh>(FindObjectsSortMode.None)
            .Where(t => t.gameObject.activeInHierarchy && t.GetComponent<Renderer>() != null
                && t.GetComponent<Renderer>().enabled && !String.IsNullOrWhiteSpace(t.text))
            .Take(30).Select(t => t.text).ToArray();
    }
    public static float AudioRms()
    {
        if (!UnityEngine.Object.FindObjectsByType<AudioSource>(FindObjectsSortMode.None).Any(s => s.isPlaying)) return 0f;
        AudioListener.GetOutputData(audio, 0);
        float sum=0f; foreach (float value in audio) sum += value*value;
        return Mathf.Sqrt(sum/audio.Length);
    }
}
