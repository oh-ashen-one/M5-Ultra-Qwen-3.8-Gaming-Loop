// Passive external evidence only: no pose, actor, input or gameplay writes.
using System;
using System.Collections.Generic;
using UnityEngine;

public static class LoopCharacterObservation
{
    [Serializable] public class Joint {
        public string path;
        public bool active;
        public float[] localPosition, localRotation, worldPosition, screenPosition;
    }
    [Serializable] public class Visual {
        public string path;
        public bool active;
        public int rendererCount, visibleRendererCount;
        public float[] worldPosition, boundsCenter, boundsSize;
        public Joint[] joints;
        public Clip[] clips;
    }
    [Serializable] public class Clip {
        public string componentPath, name;
        public bool playing, enabled;
        public float time, normalizedTime, length, speed, weight;
    }
    [Serializable] public class State {
        public float controllerHeight, controllerRadius;
        public float[] controllerCenter;
        public Visual[] visuals;
    }
    static float[] V(Vector3 v) { return new [] {v.x,v.y,v.z}; }
    static string PathOf(Transform t) {
        string p=t.name;
        while(t.parent!=null) {t=t.parent;p=t.name+"/"+p;}
        return p;
    }
    static Visual Observe(Transform root) {
        var nodes=new List<Joint>();
        var camera=Camera.main;
        foreach(var t in root.GetComponentsInChildren<Transform>(true)) {
            // Exported empty pivots and bones carry articulation. Include the
            // visual root, but omit mesh-only leaves from the motion sample.
            if(t!=root && t.GetComponent<Renderer>()!=null && t.childCount==0) continue;
            var q=t.localRotation;
            nodes.Add(new Joint {path=PathOf(t),active=t.gameObject.activeInHierarchy,
                localPosition=V(t.localPosition),localRotation=new [] {q.x,q.y,q.z,q.w},
                worldPosition=V(t.position),screenPosition=camera ? V(camera.WorldToViewportPoint(t.position)) : null});
        }
        var renderers=root.GetComponentsInChildren<Renderer>(true);
        var clips=new List<Clip>();
        foreach(var animation in root.GetComponentsInChildren<Animation>(true))
            foreach(AnimationState state in animation)
                clips.Add(new Clip {componentPath=PathOf(animation.transform),name=state.name,
                    playing=animation.IsPlaying(state.name),enabled=state.enabled,time=state.time,
                    normalizedTime=state.normalizedTime,length=state.length,speed=state.speed,weight=state.weight});
        Bounds bounds=new Bounds(root.position,Vector3.zero);
        bool any=false;int visible=0;
        foreach(var r in renderers) {
            if(!r.enabled || !r.gameObject.activeInHierarchy) continue;
            visible++;
            if(!any) {bounds=r.bounds;any=true;} else bounds.Encapsulate(r.bounds);
        }
        return new Visual {path=PathOf(root),active=root.gameObject.activeInHierarchy,
            rendererCount=renderers.Length,visibleRendererCount=visible,worldPosition=V(root.position),
            boundsCenter=V(bounds.center),boundsSize=V(bounds.size),joints=nodes.ToArray(),clips=clips.ToArray()};
    }
    public static State Capture() {
        var result=new State();var visuals=new List<Visual>();
        var player=LoopSignals.Player;
        if(player) {
            var controller=player.GetComponent<CharacterController>();
            if(controller) {
                result.controllerHeight=controller.height;result.controllerRadius=controller.radius;
                result.controllerCenter=V(controller.center);
            }
            foreach(var child in player.GetComponentsInChildren<Transform>(true))
                if(child.name=="PlayerVisual") visuals.Add(Observe(child));
        }
        // A local-authored presentation component may expose a separate seated
        // visual. Observe it if present; never create or enable one here.
        if(LoopSignals.Vehicle)
            foreach(var child in LoopSignals.Vehicle.GetComponentsInChildren<Transform>(true))
                if(child.name=="DriverVisual") visuals.Add(Observe(child));
        result.visuals=visuals.ToArray();return result;
    }
}
