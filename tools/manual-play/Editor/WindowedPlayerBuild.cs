// Cloud-authored standalone presentation/diagnostic infrastructure; original material, MIT.
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
public static class WindowedPlayerBuild {
 public static void Build() {
  try {
   PlayerSettings.resizableWindow = true;
   PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
   PlayerSettings.defaultScreenWidth = 1280;
   PlayerSettings.defaultScreenHeight = 720;
   var output = Environment.GetEnvironmentVariable("WALKTHROUGH_PLAYER_OUTPUT");
   var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
    scenes = new[] {"Assets/LoopHarness/Generated/Loop.unity"},
    locationPathName = output, target = BuildTarget.StandaloneOSX,
    options = BuildOptions.Development
   });
   if(report.summary.result != BuildResult.Succeeded) throw new Exception("Windowed player build failed: " + report.summary.result);
   File.WriteAllText(Path.Combine(Path.GetDirectoryName(output),"build-success.json"),"{\"passed\":true,\"resizableWindow\":true,\"fullscreen\":false}");
   EditorApplication.Exit(0);
  } catch(Exception e) { Debug.LogException(e); EditorApplication.Exit(2); }
 }
}
