// External observation only. Never moves actors, deals damage or changes gameplay.
using System;
using System.Linq;
using System.Reflection;
using UnityEngine;

public static class LoopCombatObservation
{
    [Serializable] public class Rival {
        public string name, actor, firstAimCollider, firstAttackCollider;
        public float[] position, actorPosition, renderCenter, renderSize, rootScale, colliderSize;
        public int hp, renderers;
        public bool alive, attackUnobstructed, colliderEnabled;
        public float actorDistance, footDistance, aimDistance;
    }
    static float[] Vec(Vector3 p) { return new [] {p.x,p.y,p.z}; }
    static bool Within(Transform t, Transform root) { return root != null && (t == root || t.IsChildOf(root)); }
    static RaycastHit[] Ordered(Vector3 origin, Vector3 direction, float distance) {
        return Physics.RaycastAll(origin,direction,distance,~0,QueryTriggerInteraction.Ignore)
            .OrderBy(h=>h.distance).ToArray();
    }
    public static Rival[] Capture()
    {
        var actor=LoopSignals.Mode=="vehicle" && LoopSignals.Vehicle != null ? LoopSignals.Vehicle : LoopSignals.Player;
        if (actor == null) return new Rival[0];
        return UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
            .Where(m=>m.GetType().Name=="RivalAgent").Take(8).Select(m=> {
                var t=m.transform;var type=m.GetType();var flags=BindingFlags.Public|BindingFlags.Instance;
                var visual=t.GetComponentsInChildren<Renderer>().Where(r=>r.enabled && r.gameObject.activeInHierarchy).ToArray();
                var bounds=new Bounds(t.position,Vector3.zero);
                for (int i=0;i<visual.Length;i++) { if(i==0) bounds=visual[i].bounds;else bounds.Encapsulate(visual[i].bounds); }
                var collider=t.GetComponent<Collider>();
                var result=new Rival {name=t.name,position=Vec(t.position),actor=actor.name,actorPosition=Vec(actor.position),
                    hp=Convert.ToInt32(type.GetField("hp",flags).GetValue(m)),alive=Convert.ToBoolean(type.GetField("alive",flags).GetValue(m)),
                    renderers=visual.Length,renderCenter=Vec(bounds.center),renderSize=Vec(bounds.size),rootScale=Vec(t.lossyScale),
                    colliderSize=collider != null ? Vec(collider.bounds.size) : null,
                    colliderEnabled=collider != null && collider.enabled && collider.gameObject.activeInHierarchy,
                    actorDistance=Vector3.Distance(actor.position,t.position),
                    footDistance=LoopSignals.Player != null ? Vector3.Distance(LoopSignals.Player.position,t.position) : -1f};
                var origin=t.position+Vector3.up*1.25f;var aim=actor.position+Vector3.up;var delta=aim-origin;
                var attacks=Ordered(origin,delta.normalized,delta.magnitude).Where(h=>!Within(h.transform,t)).ToArray();
                result.firstAttackCollider=attacks.Length>0 ? attacks[0].collider.name : null;
                result.attackUnobstructed=attacks.Length==0 || Within(attacks[0].transform,actor);
                if(Camera.main != null) {
                    var c=Camera.main.transform;
                    var hits=Ordered(c.position,c.forward,60f).Where(h=>!Within(h.transform,LoopSignals.Player) && !Within(h.transform,actor)).ToArray();
                    result.firstAimCollider=hits.Length>0 ? hits[0].collider.name : null;
                    result.aimDistance=hits.Length>0 ? hits[0].distance : -1f;
                }
                return result;
            }).ToArray();
    }
}
