// Passive external physics observation. Never changes gameplay or physics settings.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;

public class LoopVehicleObservation : MonoBehaviour
{
    [Serializable] public class Contact {
        public string collider, kind;
        public float time, separation, otherMass;
        public bool otherHasBody, otherKinematic;
        public float[] point, normal, impulse, boundsCenter, boundsSize;
    }
    [Serializable] public class State {
        public bool available;
        public float yaw, throttle, steering, commandedSpeed;
        public float[] forward, velocity, angularVelocity;
        public Contact[] contacts;
    }
    readonly Dictionary<Collider,Contact[]> contacts = new Dictionary<Collider,Contact[]>();
    static float[] V(Vector3 v) { return new [] {v.x,v.y,v.z}; }
    static string Name(Transform t) { var n=t.name; while(t.parent!=null) {t=t.parent;n=t.name+"/"+n;} return n; }
    void Observe(Collision collision) {
        var other=collision.collider; var body=other.attachedRigidbody;
        var records=new List<Contact>();
        for(int i=0;i<Mathf.Min(collision.contactCount,16);i++) {
            var p=collision.GetContact(i);
            records.Add(new Contact {collider=Name(other.transform),kind=other.GetType().Name,
                time=Time.time-LoopRuntime.StartedAt,separation=p.separation,
                point=V(p.point),normal=V(p.normal),impulse=V(collision.impulse),
                boundsCenter=V(other.bounds.center),boundsSize=V(other.bounds.size),
                otherHasBody=body!=null,otherKinematic=body!=null&&body.isKinematic,
                otherMass=body==null?0:body.mass});
        }
        contacts[other]=records.ToArray();
    }
    void OnCollisionEnter(Collision c) { Observe(c); }
    void OnCollisionStay(Collision c) { Observe(c); }
    void OnCollisionExit(Collision c) { contacts.Remove(c.collider); }
    public static State Capture() {
        var root=LoopSignals.Vehicle;
        if(root==null)return new State {available=false};
        var rb=root.GetComponent<Rigidbody>();
        var probe=root.GetComponent<LoopVehicleObservation>();
        if(probe==null)probe=root.gameObject.AddComponent<LoopVehicleObservation>();
        var driver=root.GetComponents<MonoBehaviour>().FirstOrDefault(x=>x.GetType().FullName=="ChicagoGame.VehicleInteraction");
        var field=driver==null?null:driver.GetType().GetField("_speed",BindingFlags.Instance|BindingFlags.NonPublic);
        return new State {available=rb!=null,yaw=root.eulerAngles.y,forward=V(root.forward),
            velocity=rb==null?null:V(rb.linearVelocity),angularVelocity=rb==null?null:V(rb.angularVelocity),
            throttle=LoopInput.MoveY,steering=LoopInput.MoveX,
            commandedSpeed=field==null?0:(float)field.GetValue(driver),
            contacts=probe.contacts.Values.SelectMany(x=>x).Take(64).ToArray()};
    }
}
