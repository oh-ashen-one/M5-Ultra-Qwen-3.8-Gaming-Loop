// Passive external chapter observations; no game state or actor movement.
using System;
using System.Linq;
using System.Reflection;
using UnityEngine;

public static class LoopRouteObservation
{
    [Serializable] public class Panel {
        public string name, text;
        public bool visible;
        public float[] textRect, cardRect;
        public float[] captureTextRect, captureCardRect;
    }
    [Serializable] public class State {
        public bool present, valid, complete, cacheExists, cacheActive, actorChild, originalMeshReuse;
        public int componentCount, stage, rendererCount;
        public string objective;
        public float[] cachePosition;
        public string[] meshNames;
        public float[] cacheBoundsCenter, cacheBoundsSize;
        public int emissiveRenderers;
        public Panel[] hudPanels;
        public float liveAspect, captureAspect;
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
        var camera=Camera.main;
        value.liveAspect=camera!=null?camera.aspect:0;
        value.captureAspect=(float)LoopRuntime.CaptureWidth/LoopRuntime.CaptureHeight;
        value.hudPanels=new[]{"RouteHud","MissionHud","HudStatus"}.Select(n=>ObservePanel(n,camera)).ToArray();
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
        var renderers=root.GetComponentsInChildren<Renderer>(true)
            .Where(r=>r.enabled && r.gameObject.activeInHierarchy).ToArray();
        if(renderers.Length>0) {
            var bounds=renderers[0].bounds;
            foreach(var r in renderers.Skip(1))bounds.Encapsulate(r.bounds);
            value.cacheBoundsCenter=new[]{bounds.center.x,bounds.center.y,bounds.center.z};
            value.cacheBoundsSize=new[]{bounds.size.x,bounds.size.y,bounds.size.z};
            value.emissiveRenderers=renderers.Count(r=>r.sharedMaterials.Any(mat=>
                mat!=null && mat.IsKeywordEnabled("_EMISSION") && mat.HasProperty("_EmissionColor") &&
                mat.GetColor("_EmissionColor").maxColorComponent>.05f));
        }
        return value;
    }
    public static Panel ObservePanel(string name,Camera camera)
    {
        var value=new Panel{name=name};var go=GameObject.Find(name);
        if(go==null || camera==null)return value;
        var text=go.GetComponentInChildren<TextMesh>(true);
        var renderer=text!=null?text.GetComponent<Renderer>():go.GetComponent<Renderer>();
        value.text=text!=null?text.text:"";
        value.visible=renderer!=null && renderer.enabled && renderer.gameObject.activeInHierarchy && value.text.Length>0;
        if(renderer!=null) {value.textRect=Rect(renderer,camera);value.captureTextRect=Rect(renderer,camera,true);}
        var card=go.GetComponentsInChildren<Renderer>().FirstOrDefault(r=>r!=renderer && r.enabled);
        if(card!=null) {value.cardRect=Rect(card,camera);value.captureCardRect=Rect(card,camera,true);}
        return value;
    }
    static float[] Rect(Renderer renderer,Camera camera,bool capture=false)
    {
        var b=renderer.localBounds;
        float x0=float.PositiveInfinity,y0=x0,x1=float.NegativeInfinity,y1=x1;
        for(int mask=0;mask<8;mask++) {
            var local=new Vector3((mask&1)==0?b.min.x:b.max.x,(mask&2)==0?b.min.y:b.max.y,(mask&4)==0?b.min.z:b.max.z);
            var p=camera.WorldToViewportPoint(renderer.transform.TransformPoint(local));
            // RenderTexture uses its own aspect. Keep live-window coordinates
            // separately; never change the gameplay camera to measure the PNG.
            if(capture) {
                if(camera.orthographic || camera.usePhysicalProperties)return new float[0];
                p.x=.5f+(p.x-.5f)*camera.aspect/((float)LoopRuntime.CaptureWidth/LoopRuntime.CaptureHeight);
            }
            if(p.z<=0)return new float[0];
            x0=Mathf.Min(x0,p.x);y0=Mathf.Min(y0,p.y);x1=Mathf.Max(x1,p.x);y1=Mathf.Max(y1,p.y);
        }
        return new[]{x0,y0,x1,y1};
    }
}
