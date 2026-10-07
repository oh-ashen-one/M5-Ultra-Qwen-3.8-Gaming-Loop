// Passive observation only: never writes game state, inputs or transforms.
using System;
using System.Linq;
using UnityEngine;

public static class LoopRelayObservation
{
    [Serializable] public class Site {
        public int index, rendererCount, colliderCount;
        public bool exists, active, actorChild, originalMeshReuse;
        public float[] position, boundsCenter, boundsSize, colliderCenter, colliderSize;
        public float[] materialColor;
    }
    [Serializable] public class State {
        public bool present, valid, active, complete, failed;
        public int componentCount, count, expected, wrongOrders;
        public float remaining;
        public string objective;
        public Site[] sites;
        public LoopRouteObservation.Panel hud;
    }
    static float[] Vec(Vector3 v) { return new[]{v.x,v.y,v.z}; }
    public static State Capture()
    {
        var found=UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
            .Where(m=>m.GetType().FullName=="ChicagoGame.RelaySequence").ToArray();
        var s=new State{present=found.Length>0,componentCount=found.Length};
        if(found.Length!=1)return s;
        var m=found[0];var t=m.GetType();
        string[] names={"Active","AllComplete","Failed","ActivationCount","ExpectedIndex","WrongOrderCount","Remaining","Objective","Relays"};
        Type[] types={typeof(bool),typeof(bool),typeof(bool),typeof(int),typeof(int),typeof(int),typeof(float),typeof(string),typeof(Transform[])};
        for(int i=0;i<names.Length;i++)if(t.GetField(names[i])==null || t.GetField(names[i]).FieldType!=types[i])return s;
        s.valid=true;s.active=(bool)t.GetField("Active").GetValue(m);
        s.complete=(bool)t.GetField("AllComplete").GetValue(m);s.failed=(bool)t.GetField("Failed").GetValue(m);
        s.count=(int)t.GetField("ActivationCount").GetValue(m);s.expected=(int)t.GetField("ExpectedIndex").GetValue(m);
        s.wrongOrders=(int)t.GetField("WrongOrderCount").GetValue(m);s.remaining=(float)t.GetField("Remaining").GetValue(m);
        s.objective=(string)t.GetField("Objective").GetValue(m);
        s.hud=LoopRouteObservation.ObservePanel(GameObject.Find("MissionBoard")!=null?"MissionBoard":"RelayHud",Camera.main);
        var roots=t.GetField("Relays").GetValue(m) as Transform[];
        if(roots==null)roots=new Transform[0];
        var original=UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsInactive.Include,FindObjectsSortMode.None)
            .Where(f=>f.sharedMesh!=null && !roots.Any(r=>r!=null && f.transform.IsChildOf(r))).Select(f=>f.sharedMesh).ToHashSet();
        s.sites=roots.Select((root,index)=>{
            var p=new Site{index=index,exists=root!=null};if(root==null)return p;
            p.active=root.gameObject.activeInHierarchy;p.position=Vec(root.position);
            p.actorChild=(LoopSignals.Player!=null && root.IsChildOf(LoopSignals.Player)) ||
                (LoopSignals.Vehicle!=null && root.IsChildOf(LoopSignals.Vehicle));
            var filters=root.GetComponentsInChildren<MeshFilter>(true).Where(f=>f.sharedMesh!=null).ToArray();
            p.originalMeshReuse=filters.Length>0 && filters.All(f=>original.Contains(f.sharedMesh) &&
                !new[]{"Cube","Sphere","Cylinder","Capsule","Plane","Quad"}.Contains(f.sharedMesh.name));
            var renderers=filters.Select(f=>f.GetComponent<Renderer>()).Where(r=>r!=null).ToArray();
            p.rendererCount=renderers.Count(r=>r.enabled && r.gameObject.activeInHierarchy);
            if(renderers.Length>0){
                var b=renderers[0].bounds;foreach(var r in renderers.Skip(1))b.Encapsulate(r.bounds);
                p.boundsCenter=Vec(b.center);p.boundsSize=Vec(b.size);
                var mat=renderers[0].sharedMaterial;
                if(mat!=null && mat.HasProperty("_Color")){var c=mat.color;p.materialColor=new[]{c.r,c.g,c.b,c.a};}
            }
            var cols=root.GetComponentsInChildren<Collider>(true).Where(c=>c.enabled && c.gameObject.activeInHierarchy && !c.isTrigger).ToArray();
            p.colliderCount=cols.Length;
            if(cols.Length>0){var b=cols[0].bounds;foreach(var c in cols.Skip(1))b.Encapsulate(c.bounds);p.colliderCenter=Vec(b.center);p.colliderSize=Vec(b.size);}
            return p;
        }).ToArray();
        return s;
    }
}
