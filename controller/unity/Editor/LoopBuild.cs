// Original external build harness, never writable by the local builder.
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class LoopBuild
{
    public static void Build()
    {
        try {
            var output = Environment.GetEnvironmentVariable("LOOP_BUILD_OUTPUT");
            if (string.IsNullOrEmpty(output)) throw new Exception("Missing owned build output");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            new GameObject("External loop harness").AddComponent<LoopRuntime>();
            Directory.CreateDirectory("Assets/LoopHarness/Generated");
            EditorSceneManager.SaveScene(scene, "Assets/LoopHarness/Generated/Loop.unity");
            PlayerSettings.companyName = "Original Chicago Loop";
            PlayerSettings.productName = "Chicago Local Slice";
            PlayerSettings.defaultScreenWidth = 960; PlayerSettings.defaultScreenHeight = 540;
            PlayerSettings.runInBackground = true;
            PlayerSettings.SetArchitecture(UnityEditor.Build.NamedBuildTarget.Standalone, 1);
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new [] {"Assets/LoopHarness/Generated/Loop.unity"}, locationPathName=output,
                target=BuildTarget.StandaloneOSX, options=BuildOptions.Development });
            if (report.summary.result != BuildResult.Succeeded) throw new Exception("Build did not succeed: " + report.summary.result);
            LoopCharacterImportObservation.Save(Path.GetDirectoryName(output));
            File.WriteAllText(Path.Combine(Path.GetDirectoryName(output), "build-result.json"),
                "{\"passed\":true,\"unity\":\"" + Application.unityVersion + "\",\"errors\":" + report.summary.totalErrors + "}");
            EditorApplication.Exit(0);
        } catch (Exception error) { Debug.LogException(error); EditorApplication.Exit(2); }
    }
}
