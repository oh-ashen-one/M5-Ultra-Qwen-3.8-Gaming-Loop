// Passive external chapter/physics evidence. Never changes input or game state.
using System;
using System.IO;
using System.Linq;
using System.Globalization;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

public static class LoopCounterExfilObservation
{
    [Serializable] public class Value { public string name, type, value; }
    [Serializable] public class Actor {
        public int entityId;
        public string name;
        public float[] position,velocity,capsuleCenter,rootScale;
        public float capsuleRadius,capsuleHeight,horizontalPenetration;
        public bool hasBody,kinematic,colliderEnabled;
        public Value[] state;
        public LoopCounterExfilContacts.Contact[] contacts;
    }
    [Serializable] public class State {
        public bool available;
        public Value[] chapter;
        public Actor[] actors;
    }
    static float[] V(Vector3 v) { return new[]{v.x,v.y,v.z}; }
    static bool Simple(Type t) { return t.IsEnum || t==typeof(string) || t==typeof(bool) || t==typeof(int) || t==typeof(float) || t==typeof(double); }
    static Value[] PublicState(MonoBehaviour component) {
        var values=new List<Value>();var flags=BindingFlags.Public|BindingFlags.Instance|BindingFlags.DeclaredOnly;
        foreach(var field in component.GetType().GetFields(flags).Where(f=>Simple(f.FieldType)))
            values.Add(new Value {name=field.Name,type=field.FieldType.Name,value=Convert.ToString(field.GetValue(component),CultureInfo.InvariantCulture)});
        foreach(var property in component.GetType().GetProperties(flags).Where(p=>p.CanRead && p.GetIndexParameters().Length==0 && Simple(p.PropertyType)))
            values.Add(new Value {name=property.Name,type=property.PropertyType.Name,value=Convert.ToString(property.GetValue(component),CultureInfo.InvariantCulture)});
        return values.OrderBy(v=>v.name).ToArray();
    }
    public static State Capture() {
        var scripts=UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsInactive.Include,FindObjectsSortMode.None);
        var mission=scripts.FirstOrDefault(m=>m && m.GetType().FullName=="ChicagoGame.CounterExfilMission");
        if(!mission)return new State {available=false,actors=new Actor[0]};
        var actors=scripts.Where(m=>m && m.GetType().FullName=="ChicagoGame.CounterExfilRunner").Select(m=>{
            var rb=m.GetComponent<Rigidbody>();var col=m.GetComponent<Collider>();
            var capsule=m.GetComponent<CapsuleCollider>();
            var probe=m.GetComponent<LoopCounterExfilContacts>();
            if(!probe)probe=m.gameObject.AddComponent<LoopCounterExfilContacts>();
            return new Actor {entityId=m.gameObject.GetInstanceID(),name=m.name,position=V(m.transform.position),
                velocity=rb?V(rb.linearVelocity):null,hasBody=rb!=null,kinematic=rb && rb.isKinematic,
                capsuleCenter=capsule?V(capsule.center):null,rootScale=V(m.transform.lossyScale),
                capsuleRadius=capsule?capsule.radius:0,capsuleHeight=capsule?capsule.height:0,
                horizontalPenetration=LoopObservation.HorizontalPenetration(m.transform),
                colliderEnabled=col && col.enabled && col.gameObject.activeInHierarchy,
                state=PublicState(m),contacts=probe.Current()};
        }).ToArray();
        return new State {available=true,chapter=PublicState(mission),actors=actors};
    }
}

public class LoopCounterExfilContacts : MonoBehaviour
{
    [Serializable] public class Contact {
        public string other;
        public int otherId;
        public bool vehicle;
        public float time,separation;
        public float[] point,normal,impulse;
    }
    [Serializable] class Event {
        public string kind,actor;
        public int entityId,frame,otherId;
        public bool otherIsVehicle;
        public float time;
        public Contact[] contacts;
    }
    readonly Dictionary<int,Contact[]> current=new Dictionary<int,Contact[]>();
    string output;
    static float[] V(Vector3 v) { return new[]{v.x,v.y,v.z}; }
    void Awake() {
        var args=Environment.GetCommandLineArgs();int i=Array.IndexOf(args,"--loop-output");
        if(i>=0 && i+1<args.Length)output=Path.Combine(args[i+1],"counter-exfil-contacts.jsonl");
    }
    void Observe(string kind,Collision collision) {
        var other=collision.collider;int id=other.GetInstanceID();
        var records=new List<Contact>();
        foreach(var p in collision.contacts)records.Add(new Contact {other=other.name,otherId=id,
            vehicle=LoopSignals.Vehicle && other.transform.IsChildOf(LoopSignals.Vehicle),
            time=Time.time-LoopRuntime.StartedAt,separation=p.separation,
            point=V(p.point),normal=V(p.normal),impulse=V(collision.impulse)});
        if(kind=="exit")current.Remove(id);else current[id]=records.ToArray();
        if(output!=null)File.AppendAllText(output,JsonUtility.ToJson(new Event {kind=kind,actor=name,
            entityId=gameObject.GetInstanceID(),frame=Time.frameCount,otherId=id,
            otherIsVehicle=LoopSignals.Vehicle && other.transform.IsChildOf(LoopSignals.Vehicle),
            time=Time.time-LoopRuntime.StartedAt,contacts=records.ToArray()})+"\n");
    }
    void OnCollisionEnter(Collision c) { Observe("enter",c); }
    void OnCollisionStay(Collision c) { Observe("stay",c); }
    void OnCollisionExit(Collision c) { Observe("exit",c); }
    public Contact[] Current() { return current.Values.SelectMany(v=>v).ToArray(); }
}
