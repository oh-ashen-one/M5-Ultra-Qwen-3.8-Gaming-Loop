// External read-only native clearance survey. No actor movement or scene edits.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;

public class LoopCounterExfilSurvey : MonoBehaviour
{
    [Serializable] public class Point {
        public float[] position;
        public string ground;
        public float groundY;
        public string[] renderedSupport, capsuleOverlaps, coupeOverlaps;
    }
    [Serializable] public class Segment {
        public float[] from, to;
        public string[] capsuleHits, coupeHits;
    }
    [Serializable] public class Route {
        public string name;
        public Point[] points;
        public Segment[] segments;
        public bool capsuleClear, coupeClear, groundedAndRendered;
    }
    [Serializable] public class Survey {
        public string scope, utc;
        public float time, health, runnerRadius, runnerHeight, coupeHorizontalMargin;
        public float[] player, vehicle, actualBoxCenter, actualBoxSize, actualBoxScale;
        public Route[] routes;
    }
    bool saved;
    static float[] V(Vector3 v) { return new[]{v.x,v.y,v.z}; }
    static string Name(Transform t) { var s=t.name; while(t.parent) {t=t.parent;s=t.name+"/"+s;} return s; }
    static bool Actor(Collider c) {
        return (LoopSignals.Player && c.transform.IsChildOf(LoopSignals.Player)) ||
            (LoopSignals.Vehicle && c.transform.IsChildOf(LoopSignals.Vehicle));
    }
    static string[] Names(IEnumerable<Collider> hits) {
        return hits.Where(c=>c && !Actor(c)).Select(c=>Name(c.transform)).Distinct().OrderBy(s=>s).ToArray();
    }
    static string[] Hits(RaycastHit[] hits) { return Names(hits.Select(h=>h.collider)); }
    static bool Ground(Vector3 p, out RaycastHit hit) {
        var hits=Physics.RaycastAll(p+Vector3.up*3,Vector3.down,6,~0,QueryTriggerInteraction.Ignore)
            .Where(h=>!Actor(h.collider) && h.normal.y>.9f).OrderBy(h=>h.distance).ToArray();
        hit=hits.Length>0?hits[0]:default(RaycastHit);return hits.Length>0;
    }
    Route Check(string name, Vector3[] nodes, BoxCollider box, Renderer[] surfaces) {
        var points=new List<Point>();var segments=new List<Segment>();
        Vector3 scale=box.transform.lossyScale;
        Vector3 half=Vector3.Scale(box.size,scale)*.5f+new Vector3(.2f,0,.2f);
        Vector3 localCenter=Vector3.Scale(box.center,scale);
        float bottom=localCenter.y-half.y;
        for(int i=0;i<nodes.Length-1;i++) {
            Vector3 delta=nodes[i+1]-nodes[i];delta.y=0;
            int count=Mathf.CeilToInt(delta.magnitude/.5f);
            Quaternion orientation=Quaternion.LookRotation(delta.normalized,Vector3.up);
            Vector3 previous=Vector3.zero;bool previousGround=false;
            for(int n=0;n<=count;n++) {
                var p=Vector3.Lerp(nodes[i],nodes[i+1],n/(float)count);
                bool ground=Ground(p,out var hit);float y=ground?hit.point.y:0;
                // The capsule rests 2cm above measured support. The actual body
                // rests 1cm above support; only its horizontal margin is enlarged.
                var low=new Vector3(p.x,y+.40f,p.z);var high=low+Vector3.up*1.14f;
                var root=new Vector3(p.x,y-bottom+.01f,p.z);
                var center=root+orientation*localCenter;
                var support=surfaces.Where(r=>r.enabled && r.gameObject.activeInHierarchy &&
                    r.bounds.size.y<.6f && Mathf.Abs(r.bounds.max.y-y)<.25f &&
                    r.bounds.min.x<=p.x-.38f && r.bounds.max.x>=p.x+.38f &&
                    r.bounds.min.z<=p.z-.38f && r.bounds.max.z>=p.z+.38f)
                    .Select(r=>Name(r.transform)).Distinct().OrderBy(s=>s).ToArray();
                points.Add(new Point {position=V(p),ground=ground?Name(hit.transform):null,groundY=y,
                    renderedSupport=support,
                    capsuleOverlaps=Names(Physics.OverlapCapsule(low,high,.38f,~0,QueryTriggerInteraction.Ignore)),
                    coupeOverlaps=Names(Physics.OverlapBox(center,half,orientation,~0,QueryTriggerInteraction.Ignore))});
                if(n>0 && ground && previousGround) {
                    var step=p-previous;step.y=0;var d=step.normalized;float length=step.magnitude;
                    var oldLow=new Vector3(previous.x,y+.40f,previous.z);
                    var oldRoot=new Vector3(previous.x,y-bottom+.01f,previous.z);
                    segments.Add(new Segment {from=V(previous),to=V(p),
                        capsuleHits=Hits(Physics.CapsuleCastAll(oldLow,oldLow+Vector3.up*1.14f,.38f,d,length,~0,QueryTriggerInteraction.Ignore)),
                        coupeHits=Hits(Physics.BoxCastAll(oldRoot+orientation*localCenter,half,d,orientation,length,~0,QueryTriggerInteraction.Ignore))});
                }
                previous=p;previousGround=ground;
            }
        }
        return new Route {name=name,points=points.ToArray(),segments=segments.ToArray(),
            groundedAndRendered=points.All(p=>p.ground!=null && p.renderedSupport.Length>0),
            capsuleClear=points.All(p=>p.capsuleOverlaps.Length==0)&&segments.All(s=>s.capsuleHits.Length==0),
            coupeClear=points.All(p=>p.coupeOverlaps.Length==0)&&segments.All(s=>s.coupeHits.Length==0)};
    }
    void LateUpdate() {
        if(saved || LoopInput.Elapsed<77f)return;
        if(!LoopSignals.Vehicle || !LoopSignals.Player)throw new Exception("Survey requires actual player and coupe");
        var box=LoopSignals.Vehicle.GetComponent<BoxCollider>();
        if(!box)throw new Exception("Survey requires the actual coupe BoxCollider");
        var renderers=UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None);
        var start=LoopSignals.Vehicle.position;
        var routes=new List<Route>();
        routes.Add(Check("central-westbound",new[]{start,new Vector3(22,0,16.5738f),new Vector3(6,0,16.0057f),new Vector3(3,0,16.0057f)},box,renderers));
        foreach(float z in new[]{10f,15f,19f})routes.Add(Check("candidate-z"+z,new[]{new Vector3(47.6f,0,z),new Vector3(3,0,z)},box,renderers));
        routes.Add(Check("handoff-foot-retrieval",new[]{LoopSignals.Player.position,start},box,renderers));
        var value=new Survey {scope="Read-only westbound overlap and swept geometry preflight; actor roots excluded, other obstacles retained. Render support uses thin renderer world bounds, not triangle coverage. Not an input-driven driving or incident PASS.",
            utc=DateTime.UtcNow.ToString("O"),time=LoopInput.Elapsed,health=LoopSignals.Health,
            runnerRadius=.38f,runnerHeight=1.9f,coupeHorizontalMargin=.2f,
            player=V(LoopSignals.Player.position),vehicle=V(start),actualBoxCenter=V(box.center),actualBoxSize=V(box.size),actualBoxScale=V(box.transform.lossyScale),routes=routes.ToArray()};
        var args=Environment.GetCommandLineArgs();int a=Array.IndexOf(args,"--loop-output");
        if(a<0 || a+1>=args.Length)throw new Exception("Survey output missing");
        File.WriteAllText(Path.Combine(args[a+1],"counter-exfil-survey.json"),JsonUtility.ToJson(value,true));saved=true;
    }
}
