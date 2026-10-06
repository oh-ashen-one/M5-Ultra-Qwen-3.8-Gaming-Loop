// External observation only. Never moves camera/actors or changes game outcomes.
using System;
using System.Linq;
using System.Reflection;
using UnityEngine;

public static class LoopCameraObservation
{
    [Serializable] public class Observation {
        public bool available, probeHit, legacyEndpointCrowding, cameraInsideFixture,
            fixtureBetweenTargetAndCamera, nearPlaneTouchesFixture;
        public string target, phase, probeCollider;
        public float[] cameraPosition, cameraForward, targetPosition, pivot, desiredDirection,
            targetViewportMin, targetViewportMax;
        public float desiredDistance, probeDistance, cameraDistance, fixtureHitDistance;
        public int targetSamples, inFrameSamples, unobstructedSamples;
        public string targetRole;
        public int expectedRendererCount,cachedRendererCount;
        public bool rendererCacheMatchesTarget;
        public string[] cameraInsideForeignColliders;
        public LoopCameraBranchObservation.Snapshot branchTrace;
    }
    static float[] Vec(Vector3 p) { return new[] {p.x,p.y,p.z}; }
    public static MonoBehaviour Follow() {
        return UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
            .FirstOrDefault(m=>m.GetType().FullName=="ChicagoGame.Follow");
    }
    public static bool Rig(out Transform target,out Vector3 offset) {
        target=null;offset=Vector3.zero;var f=Follow();if(f==null)return false;
        var t=f.GetType().GetField("target");var o=f.GetType().GetField("offset");
        if(t==null || o==null)return false;
        target=t.GetValue(f) as Transform;offset=(Vector3)o.GetValue(f);
        return target!=null && offset.magnitude>.1f;
    }
    static bool Inside(Collider c,Vector3 p) { return (c.ClosestPoint(p)-p).sqrMagnitude<.00000001f; }
    public static Observation Capture() {
        var result=new Observation {phase=LoopCameraFixture.Phase};var camera=Camera.main;
        Transform actor;Vector3 offset;if(camera==null || !Rig(out actor,out offset))return result;
        result.available=true;result.target=actor.name;result.targetPosition=Vec(actor.position);
        result.targetRole=actor==LoopSignals.Vehicle?"vehicle":actor==LoopSignals.Player?"foot":"other";
        var follow=Follow();var cached=follow.GetType().GetField("rend",BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic)?.GetValue(follow) as Renderer[];
        var expected=actor.GetComponentsInChildren<Renderer>();
        result.expectedRendererCount=expected.Length;result.cachedRendererCount=cached==null?0:cached.Count(r=>r!=null);
        result.rendererCacheMatchesTarget=cached!=null && expected.Length>0 && expected.Length==result.cachedRendererCount
            && expected.All(r=>cached.Any(c=>c==r));
        result.cameraPosition=Vec(camera.transform.position);result.cameraForward=Vec(camera.transform.forward);
        result.branchTrace=LoopCameraBranchObservation.Capture(actor,camera);
        result.cameraInsideForeignColliders=Physics.OverlapSphere(camera.transform.position,.01f,~0,QueryTriggerInteraction.Ignore)
            .Where(c=>c.transform!=actor && !c.transform.IsChildOf(actor) && Inside(c,camera.transform.position))
            .Select(c=>c.name).Distinct().ToArray();
        var pivot=actor.position+Vector3.up*1.25f;
        var desired=Quaternion.Euler(0,actor.eulerAngles.y,0)*offset;var full=desired.magnitude;
        var dir=desired/full;result.pivot=Vec(pivot);result.desiredDirection=Vec(dir);result.desiredDistance=full;
        result.cameraDistance=Vector3.Distance(pivot,camera.transform.position);
        RaycastHit probe;result.probeHit=Physics.Raycast(pivot,dir,out probe,full,~0,QueryTriggerInteraction.Ignore);
        result.probeDistance=result.probeHit?probe.distance:-1;
        result.probeCollider=result.probeHit?probe.collider.name:"";
        // This records the old expression for comparison, not an inferred live local variable.
        result.legacyEndpointCrowding=result.probeHit && full-probe.distance<1.5f;
        var wall=LoopCameraFixture.Wall;
        if(wall!=null && wall.enabled && wall.gameObject.activeInHierarchy) {
            result.cameraInsideFixture=Inside(wall,camera.transform.position);
            var line=camera.transform.position-pivot;RaycastHit hit;
            result.fixtureBetweenTargetAndCamera=wall.Raycast(new Ray(pivot,line.normalized),out hit,line.magnitude);
            result.fixtureHitDistance=result.fixtureBetweenTargetAndCamera?hit.distance:-1;
            var local=new Vector3[4];camera.CalculateFrustumCorners(new Rect(0,0,1,1),camera.nearClipPlane,
                Camera.MonoOrStereoscopicEye.Mono,local);
            var corners=local.Select(v=>camera.transform.TransformPoint(v)).ToArray();
            for(int i=0;i<4;i++) {
                var edge=corners[(i+1)%4]-corners[i];
                if(Inside(wall,corners[i]) || wall.Raycast(new Ray(corners[i],edge.normalized),out hit,edge.magnitude))
                    result.nearPlaneTouchesFixture=true;
            }
        }
        var renderers=actor.GetComponentsInChildren<Renderer>().Where(r=>r.enabled && r.gameObject.activeInHierarchy
            && r.GetComponent<TextMesh>()==null).ToArray();
        if(renderers.Length==0)return result;
        var bounds=renderers[0].bounds;foreach(var r in renderers.Skip(1))bounds.Encapsulate(r.bounds);
        var points=new Vector3[9];points[0]=bounds.center;
        for(int i=0;i<8;i++)points[i+1]=bounds.center+Vector3.Scale(bounds.extents,
            new Vector3((i&1)==0?-1:1,(i&2)==0?-1:1,(i&4)==0?-1:1));
        var min=new Vector3(float.PositiveInfinity,float.PositiveInfinity,float.PositiveInfinity);
        var max=new Vector3(float.NegativeInfinity,float.NegativeInfinity,float.NegativeInfinity);
        foreach(var p in points) {
            var vp=camera.WorldToViewportPoint(p);min=Vector3.Min(min,vp);max=Vector3.Max(max,vp);result.targetSamples++;
            if(vp.z<=camera.nearClipPlane || vp.x<0 || vp.x>1 || vp.y<0 || vp.y>1)continue;
            result.inFrameSamples++;var ray=p-camera.transform.position;
            var hits=Physics.RaycastAll(camera.transform.position,ray.normalized,ray.magnitude,~0,QueryTriggerInteraction.Ignore)
                .OrderBy(h=>h.distance).ToArray();
            if(hits.Length==0 || hits[0].transform==actor || hits[0].transform.IsChildOf(actor))result.unobstructedSamples++;
        }
        result.targetViewportMin=Vec(min);result.targetViewportMax=Vec(max);return result;
    }
}
