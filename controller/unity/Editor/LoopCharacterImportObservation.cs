// Passive imported-asset evidence; no importer, clip or scene writes.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class LoopCharacterImportObservation
{
    [Serializable] public class Clip {
        public string name; public bool legacy, preview;
        public float length, frameRate; public string wrapMode;
        public int curveCount; public string[] rotationPaths;
    }
    [Serializable] public class Take {
        public string name,takeName; public float firstFrame,lastFrame;
    }
    [Serializable] public class Result {
        public string assetPath,animationType;
        public bool importAnimation;
        public Clip[] clips; public Take[] defaultTakes;
    }
    public static void Save(string buildDirectory) {
        const string path="Assets/Resources/Generated/player/scene.fbx";
        var importer=AssetImporter.GetAtPath(path) as ModelImporter;
        var clips=new List<Clip>();var takes=new List<Take>();
        foreach(var asset in AssetDatabase.LoadAllAssetsAtPath(path)) {
            var clip=asset as AnimationClip;if(!clip) continue;
            var bindings=AnimationUtility.GetCurveBindings(clip);
            var rotations=new HashSet<string>();
            foreach(var binding in bindings)
                if(binding.propertyName.Contains("Rotation") || binding.propertyName.Contains("Euler"))
                    rotations.Add(binding.path);
            var paths=new List<string>(rotations);paths.Sort();
            clips.Add(new Clip {name=clip.name,legacy=clip.legacy,preview=clip.name.StartsWith("__preview__"),
                length=clip.length,frameRate=clip.frameRate,wrapMode=clip.wrapMode.ToString(),
                curveCount=bindings.Length,rotationPaths=paths.ToArray()});
        }
        if(importer)
            foreach(var take in importer.defaultClipAnimations)
                takes.Add(new Take {name=take.name,takeName=take.takeName,
                    firstFrame=take.firstFrame,lastFrame=take.lastFrame});
        File.WriteAllText(Path.Combine(buildDirectory,"character-import.json"),JsonUtility.ToJson(
            new Result {assetPath=path,animationType=importer ? importer.animationType.ToString() : "missing",
                importAnimation=importer && importer.importAnimation,clips=clips.ToArray(),defaultTakes=takes.ToArray()},true));
    }
}
