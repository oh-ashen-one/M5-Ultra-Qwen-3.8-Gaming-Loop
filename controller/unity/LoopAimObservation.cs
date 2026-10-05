// External per-shot evidence. Does not move, aim, damage, or draw gameplay objects.
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEngine;

[DefaultExecutionOrder(-31000)]
public class LoopAimObservation : MonoBehaviour
{
    [Serializable] public class Target {
        public string name;
        public int hpBefore, hpAfter;
        public float[] position, renderCenter, renderSize, viewportMin, viewportMax;
        public bool colliderRayHit, visualBoundsRayHit, viewportContainsCenter, firstRayTarget;
        public float colliderRayDistance;
        [NonSerialized] public MonoBehaviour instance;
    }
    [Serializable] public class Shot {
        public int frame, shotsBefore, shotsAfter, hitsBefore, hitsAfter, restarts;
        public float time;
        public string mode, firstRayCollider;
        public string[] keys, originOverlaps085;
        public float[] cameraPosition, cameraForward;
        public Target[] targets;
    }
    Shot before;
    string output;
    static float[] Vec(Vector3 v) { return new [] {v.x,v.y,v.z}; }
    static bool Within(Transform t,Transform root) {return root!=null && (t==root || t.IsChildOf(root));}
    static int Hp(MonoBehaviour m) {return Convert.ToInt32(m.GetType().GetField("hp",BindingFlags.Public|BindingFlags.Instance).GetValue(m));}
    void Awake() {
        var args=Environment.GetCommandLineArgs();int i=Array.IndexOf(args,"--loop-output");
        if(i>=0 && i+1<args.Length)output=args[i+1];
    }
    void Update() {
        before=null;
        var cam=Camera.main;
        if(output==null || LoopInput.Replay==null || cam==null) return;
        var actor=LoopSignals.Mode=="vehicle" ? LoopSignals.Vehicle : LoopSignals.Player;
        var ray=new Ray(cam.transform.position,cam.transform.forward);
        var hits=Physics.RaycastAll(ray,60f,~0,QueryTriggerInteraction.Ignore)
            .Where(h=>!Within(h.transform,LoopSignals.Player) && !Within(h.transform,actor))
            .OrderBy(h=>h.distance).ToArray();
        var first=hits.Length>0 ? hits[0].collider : null;
        var targets=UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
            .Where(m=>m.GetType().Name=="RivalAgent").Take(8).Select(m=>{
                var renderers=m.GetComponentsInChildren<Renderer>().Where(x=>x.enabled && x.gameObject.activeInHierarchy).ToArray();
                var b=new Bounds(m.transform.position,Vector3.zero);
                for(int j=0;j<renderers.Length;j++){if(j==0)b=renderers[j].bounds;else b.Encapsulate(renderers[j].bounds);}
                Vector3 lo=new Vector3(float.MaxValue,float.MaxValue,float.MaxValue);
                Vector3 hi=new Vector3(float.MinValue,float.MinValue,float.MinValue);
                for(int j=0;j<8;j++){
                    var v=cam.WorldToViewportPoint(new Vector3((j&1)==0?b.min.x:b.max.x,(j&2)==0?b.min.y:b.max.y,(j&4)==0?b.min.z:b.max.z));
                    lo=Vector3.Min(lo,v);hi=Vector3.Max(hi,v);
                }
                var collider=m.GetComponent<Collider>();RaycastHit hit=default(RaycastHit);
                bool intersects=collider!=null && collider.Raycast(ray,out hit,60f);
                return new Target {instance=m,name=m.name,hpBefore=Hp(m),hpAfter=Hp(m),position=Vec(m.transform.position),
                    renderCenter=Vec(b.center),renderSize=Vec(b.size),viewportMin=Vec(lo),viewportMax=Vec(hi),
                    colliderRayHit=intersects,colliderRayDistance=intersects?hit.distance:-1f,
                    visualBoundsRayHit=renderers.Length>0 && b.IntersectRay(ray),
                    viewportContainsCenter=lo.z>0 && lo.x<=.5f && hi.x>=.5f && lo.y<=.5f && hi.y>=.5f,
                    firstRayTarget=first!=null && Within(first.transform,m.transform)};
            }).ToArray();
        before=new Shot {frame=Time.frameCount,time=LoopInput.Elapsed,keys=LoopInput.ActiveKeys,mode=LoopSignals.Mode,
            shotsBefore=LoopSignals.Shots,hitsBefore=LoopSignals.Hits,restarts=LoopSignals.Restarts,
            cameraPosition=Vec(ray.origin),cameraForward=Vec(ray.direction),targets=targets,
            firstRayCollider=first!=null?first.name:null,
            originOverlaps085=Physics.OverlapSphere(ray.origin,.85f,~0,QueryTriggerInteraction.Ignore)
                .Where(c=>!Within(c.transform,LoopSignals.Player) && !Within(c.transform,actor)).Select(c=>c.name).Distinct().ToArray()};
    }
    void LateUpdate() {
        if(before==null || LoopSignals.Restarts!=before.restarts || LoopSignals.Shots<=before.shotsBefore)return;
        before.shotsAfter=LoopSignals.Shots;before.hitsAfter=LoopSignals.Hits;
        foreach(var t in before.targets)if(t.instance!=null)t.hpAfter=Hp(t.instance);
        File.AppendAllText(Path.Combine(output,"aim-shots.jsonl"),JsonUtility.ToJson(before)+"\n");
    }
}
