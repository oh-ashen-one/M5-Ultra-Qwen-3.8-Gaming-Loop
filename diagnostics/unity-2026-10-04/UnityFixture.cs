// Cloud-authored connector fixture, not game code. Geometry/materials come from
// the unchanged local-Qwen Blender scene in connector-2026-10-05.
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class UnityFixture
{
    [Serializable] public class Evidence
    {
        public string stage, unity, graphics;
        public int meshes, materials, vertices, width, height;
        public string[] objects;
        public bool passed;
    }
    static GameObject LoadAsset(bool import = false)
    {
        if (import)
            AssetDatabase.ImportAsset("Assets/Original/scene.fbx", ImportAssetOptions.ForceSynchronousImport);
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Original/scene.fbx");
        if (asset == null) throw new Exception("FBX did not import as a GameObject");
        var root = (GameObject)PrefabUtility.InstantiatePrefab(asset);
        if (root.GetComponentsInChildren<MeshFilter>().Length != 3)
            throw new Exception("Expected three original Qwen mesh objects");
        foreach (var expected in new [] { "RedCube", "BlueSphere", "GroundPlane" })
            if (!root.GetComponentsInChildren<Transform>().Any(t => t.name == expected))
                throw new Exception("Missing original object: " + expected);
        return root;
    }
    static Evidence Describe(GameObject root, string stage)
    {
        var meshes = root.GetComponentsInChildren<MeshFilter>();
        var materials = root.GetComponentsInChildren<Renderer>().SelectMany(r => r.sharedMaterials).Distinct().ToArray();
        if (materials.Length != 3 || materials.Any(m => m == null))
            throw new Exception("Expected three imported materials");
        return new Evidence { stage = stage, unity = Application.unityVersion,
            graphics = SystemInfo.graphicsDeviceType.ToString(), meshes = meshes.Length,
            materials = materials.Length, vertices = meshes.Sum(m => m.sharedMesh.vertexCount),
            objects = meshes.Select(m => m.name).OrderBy(n => n).ToArray(), passed = true };
    }
    static void Write(Evidence e)
    {
        Directory.CreateDirectory("Evidence");
        File.WriteAllText("Evidence/" + e.stage + ".json", JsonUtility.ToJson(e, true));
        Debug.Log("[Fixture] " + e.stage + " PASS");
    }
    public static void ImportAndCheck()
    {
        try
        {
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = LoadAsset(true);
            Write(Describe(root, "import-compile"));
        }
        catch (Exception e) { Debug.LogError("[Fixture] " + e.Message); EditorApplication.Exit(2); }
    }
    public static void Render()
    {
        try
        {
            if (SystemInfo.graphicsDeviceType != GraphicsDeviceType.Metal)
                throw new Exception("Expected actual Metal rendering");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = LoadAsset();
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.4f, 0.4f, 0.4f);
            var light = new GameObject("Diagnostic light").AddComponent<Light>();
            light.type = LightType.Directional; light.intensity = 1.1f;
            light.transform.rotation = Quaternion.Euler(45, -25, 0);
            var camera = new GameObject("Diagnostic camera").AddComponent<Camera>();
            camera.transform.position = new Vector3(0, 4, -8);
            camera.transform.LookAt(new Vector3(0, 0.8f, 0));
            camera.orthographic = true; camera.orthographicSize = 3.5f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.16f, 0.18f, 0.21f);
            camera.nearClipPlane = 0.1f; camera.farClipPlane = 100;
            var target = new RenderTexture(512, 512, 24, RenderTextureFormat.ARGB32);
            camera.targetTexture = target;
            camera.Render();
            RenderTexture.active = target;
            var image = new Texture2D(512, 512, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, 512, 512), 0, 0); image.Apply();
            Directory.CreateDirectory("Evidence");
            File.WriteAllBytes("Evidence/unity-frame.png", image.EncodeToPNG());
            camera.targetTexture = null; RenderTexture.active = null; target.Release();
            var evidence = Describe(root, "render"); evidence.width = 512; evidence.height = 512;
            Write(evidence);
        }
        catch (Exception e) { Debug.LogError("[Fixture] " + e.Message); EditorApplication.Exit(3); }
    }
}
