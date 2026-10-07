// Cloud-authored disposable input fixture. Never copied into the real game.
using System;
using System.Linq;
using UnityEngine;
namespace ChicagoGame {
    public static class Bootstrap {
        public static void Create() {
            var source=Resources.Load<GameObject>("Generated/smoke/scene");
            if(source==null) throw new Exception("Original local-Qwen FBX not found");
            var scene=UnityEngine.Object.Instantiate(source);
            var sphere=scene.GetComponentsInChildren<Transform>().First(t=>t.name=="BlueSphere");
            sphere.gameObject.AddComponent<FixtureMotion>();
            LoopSignals.Player=sphere;
            var camera=new GameObject("Fixture camera").AddComponent<Camera>();
            camera.tag="MainCamera";camera.gameObject.AddComponent<AudioListener>();
            camera.transform.position=new Vector3(0,8,-14);camera.transform.LookAt(new Vector3(0,0,3));
            camera.orthographic=true;camera.orthographicSize=8;
            camera.backgroundColor=new Color(0.1f,0.15f,0.2f);
            var light=new GameObject("Fixture light").AddComponent<Light>();
            light.type=LightType.Directional;light.intensity=1.4f;light.transform.rotation=Quaternion.Euler(45,-25,0);
            RenderSettings.ambientLight=new Color(0.4f,0.4f,0.4f);
        }
    }
    public class FixtureMotion:MonoBehaviour {
        void Update() {
            if(!Environment.GetCommandLineArgs().Contains("--fixture-stationary"))
                transform.position+=new Vector3(LoopInput.MoveX,0,LoopInput.MoveY)*2*Time.deltaTime;
        }
    }
}
