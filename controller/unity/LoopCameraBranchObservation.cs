// Passive disposable-build diagnostics. No transforms, colliders or game state are changed.
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public static class LoopCameraBranchObservation
{
    [Serializable] public class Phase {
        public string name; public float[] position;
        public bool cramped; public float top, camY, horizontalHit, horizontalDistance;
    }
    [Serializable] public class TargetBound {
        public string name; public float[] min,max;
        public bool containsCamera,expandedContainsCamera,horizontalOverlap;
        public float cameraDistance;
    }
    [Serializable] public class Snapshot {
        public int frame; public Phase[] phases; public bool segmentPulled,targetLifted;
        public string segmentCollider,targetLiftRenderer; public float segmentHitDistance,nearClip;
        public TargetBound[] targetBounds;
    }
    static int frame=-1;
    static readonly List<Phase> phases=new List<Phase>();
    static bool segmentPulled,targetLifted;
    static string segmentCollider,targetLiftRenderer;
    static float segmentHitDistance;
    static float[] Vec(Vector3 p) { return new [] {p.x,p.y,p.z}; }
    public static void Record(string name,Vector3 pos,bool cramped,float top,float camY,float hit,float dist) {
        if(frame!=Time.frameCount) {
            frame=Time.frameCount;phases.Clear();segmentPulled=false;targetLifted=false;
            segmentCollider="";targetLiftRenderer="";segmentHitDistance=-1;
        }
        phases.Add(new Phase {name=name,position=Vec(pos),cramped=cramped,top=top,camY=camY,
            horizontalHit=float.IsInfinity(hit)?-1:hit,horizontalDistance=dist});
    }
    public static void Segment(string collider,float distance) {
        segmentPulled=true;segmentCollider=collider;segmentHitDistance=distance;
    }
    public static void Lift(string renderer) {targetLifted=true;targetLiftRenderer=renderer;}
    public static Snapshot Capture(Transform actor,Camera camera) {
        if(frame!=Time.frameCount || phases.Count==0)return null;
        var pos=camera.transform.position;
        return new Snapshot {frame=frame,phases=phases.ToArray(),segmentPulled=segmentPulled,
            targetLifted=targetLifted,segmentCollider=segmentCollider,targetLiftRenderer=targetLiftRenderer,
            segmentHitDistance=segmentHitDistance,nearClip=camera.nearClipPlane,
            targetBounds=actor.GetComponentsInChildren<Renderer>().Where(r=>r.enabled && r.gameObject.activeInHierarchy
                && r.GetComponent<TextMesh>()==null).Select(r=>{
                    var b=r.bounds;var expanded=b;expanded.Expand(.25f);
                    return new TargetBound {name=r.name,min=Vec(b.min),max=Vec(b.max),
                        containsCamera=b.Contains(pos),expandedContainsCamera=expanded.Contains(pos),
                        horizontalOverlap=pos.x>=expanded.min.x && pos.x<=expanded.max.x
                            && pos.z>=expanded.min.z && pos.z<=expanded.max.z,
                        cameraDistance=Vector3.Distance(pos,b.ClosestPoint(pos))};
                }).ToArray()};
    }
}
