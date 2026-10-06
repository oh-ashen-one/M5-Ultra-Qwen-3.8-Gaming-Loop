// Passive external chapter observations; no game state or actor movement.
using System;
using System.Linq;
using System.Reflection;
using UnityEngine;

public static class LoopRouteObservation
{
    [Serializable] public class State {
        public bool present, valid, complete, cacheExists, cacheActive, actorChild, originalMeshReuse;
        public int componentCount, stage, rendererCount;
        public string objective;
        public float[] cachePosition;
        public string[] meshNames;
    }
    public static State Capture()
    {
        var all=UnityEngine.Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None)
            .Where(m=>m.GetType().FullName=="ChicagoGame.RouteMission").ToArray();
        var value=new State {present=all.Length>0,componentCount=all.Length};
        if(all.Length!=1)return value;
        var m=all[0];var type=m.GetType();
        var stage=type.GetField("RouteStage");var complete=type.GetField("RouteComplete");
        var cache=type.GetField("Cache");var objective=type.GetField("Objective");
        value.valid=stage!=null && stage.FieldType==typeof(int) &&
            complete!=null && complete.FieldType==typeof(bool) &&
            cache!=null && cache.FieldType==typeof(Transform) &&
            objective!=null && objective.FieldType==typeof(string);
        if(!value.valid)return value;
        value.stage=(int)stage.GetValue(m);value.complete=(bool)complete.GetValue(m);
        value.objective=(string)objective.GetValue(m);
        var root=cache.GetValue(m) as Transform;
        value.cacheExists=root!=null;
        if(root==null)return value;
        value.cacheActive=root.gameObject.activeInHierarchy;
        value.cachePosition=new[]{root.position.x,root.position.y,root.position.z};
        value.actorChild=(LoopSignals.Player!=null && root.IsChildOf(LoopSignals.Player)) ||
            (LoopSignals.Vehicle!=null && root.IsChildOf(LoopSignals.Vehicle));
        var filters=root.GetComponentsInChildren<MeshFilter>(true)
            .Where(f=>f.sharedMesh!=null && f.GetComponent<Renderer>()!=null).ToArray();
        var others=UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsInactive.Include,FindObjectsSortMode.None)
            .Where(f=>!f.transform.IsChildOf(root) && f.sharedMesh!=null).ToArray();
        value.meshNames=filters.Select(f=>f.sharedMesh.name).ToArray();
        value.rendererCount=root.GetComponentsInChildren<Renderer>(true)
            .Count(r=>r.enabled && r.gameObject.activeInHierarchy);
        value.originalMeshReuse=filters.Length>0 && filters.All(f=>
            !new[]{"Cube","Cylinder","Sphere","Capsule","Plane","Quad"}.Contains(f.sharedMesh.name) &&
            others.Any(o=>o.sharedMesh==f.sharedMesh));
        return value;
    }
}

