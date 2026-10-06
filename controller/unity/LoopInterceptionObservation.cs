// External passive state/physics observation; never changes actors or outcomes.
using System;
using System.Linq;
using UnityEngine;

public static class LoopInterceptionObservation
{
    [Serializable] public class Target {
        public string name, groundCollider;
        public bool alive, colliderEnabled, dynamicBody, gravity;
        public int hp, renderers;
        public float[] position, velocity;
        public float footGap;
    }
    [Serializable] public class State {
        public bool present, valid, active, complete, failed;
        public int componentCount, stopped, escaped, spawned;
        public string objective;
        public Target[] targets;
    }
    static float[] Vec(Vector3 v) { return new[]{v.x,v.y,v.z}; }
    public static State Capture()
    {
        var all=UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None);
        var found=all.Where(m=>m.GetType().FullName=="ChicagoGame.InterceptionMission").ToArray();
        var s=new State{present=found.Length>0,componentCount=found.Length};
        if(found.Length!=1)return s;
        var m=found[0];var t=m.GetType();
        string[] names={"Active","Complete","Failed","Stopped","Escaped","Spawned","Objective"};
        Type[] types={typeof(bool),typeof(bool),typeof(bool),typeof(int),typeof(int),typeof(int),typeof(string)};
        for(int i=0;i<names.Length;i++)if(t.GetField(names[i])==null || t.GetField(names[i]).FieldType!=types[i])return s;
        s.valid=true;s.active=(bool)t.GetField("Active").GetValue(m);
        s.complete=(bool)t.GetField("Complete").GetValue(m);s.failed=(bool)t.GetField("Failed").GetValue(m);
        s.stopped=(int)t.GetField("Stopped").GetValue(m);s.escaped=(int)t.GetField("Escaped").GetValue(m);
        s.spawned=(int)t.GetField("Spawned").GetValue(m);s.objective=(string)t.GetField("Objective").GetValue(m);
        s.targets=all.Where(a=>a.GetType().FullName=="ChicagoGame.RivalAgent" && a.name.StartsWith("InterceptRunner"))
            .Select(a=>{
                var b=a.GetComponent<Rigidbody>();var c=a.GetComponent<Collider>();
                var v=new Target{name=a.name,position=Vec(a.transform.position),
                    hp=(int)a.GetType().GetField("hp").GetValue(a),alive=(bool)a.GetType().GetField("alive").GetValue(a),
                    colliderEnabled=c!=null && c.enabled, dynamicBody=b!=null && !b.isKinematic,
                    gravity=b!=null && b.useGravity,velocity=b!=null?Vec(b.linearVelocity):null,
                    renderers=a.GetComponentsInChildren<Renderer>().Count(r=>r.enabled && r.gameObject.activeInHierarchy),footGap=999};
                if(c!=null && c.enabled){
                    var h=Physics.RaycastAll(c.bounds.center,Vector3.down,3f,~0,QueryTriggerInteraction.Ignore)
                        .Where(x=>x.transform!=a.transform && !x.transform.IsChildOf(a.transform)).OrderBy(x=>x.distance).ToArray();
                    if(h.Length>0){v.groundCollider=h[0].collider.name;v.footGap=c.bounds.min.y-h[0].point.y;}
                }
                return v;
            }).ToArray();
        return s;
    }
}
