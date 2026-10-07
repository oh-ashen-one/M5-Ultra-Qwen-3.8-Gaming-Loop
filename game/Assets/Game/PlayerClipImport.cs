#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;

public sealed class PlayerClipImport : AssetPostprocessor
{
    const string Target = "Assets/Resources/Generated/player/scene.fbx";

    static ModelImporterClipAnimation Clip(string name, float first, float last, bool loop, string takeName)
    {
        return new ModelImporterClipAnimation
        {
            name = name,
            takeName = takeName,
            firstFrame = first,
            lastFrame = last,
            loopTime = loop
        };
    }

    bool IsTarget()
    {
        return assetImporter != null && assetImporter.assetPath == Target;
    }

    public new void OnPreprocessModel()
    {
        if (!IsTarget()) return;
        var mi = assetImporter as ModelImporter;
        if (mi == null) return;
        mi.importAnimation = true;
        mi.animationType = ModelImporterAnimationType.Legacy;
    }

    public new void OnPreprocessAnimation()
    {
        if (!IsTarget()) return;
        var mi = assetImporter as ModelImporter;
        if (mi == null) return;

        string take = "Scene";
        var defaults = mi.defaultClipAnimations;
        if (defaults != null)
            foreach (var c in defaults)
                if (!string.IsNullOrEmpty(c.takeName))
                {
                    take = c.takeName;
                    break;
                }

        mi.importAnimation = true;
        mi.animationType = ModelImporterAnimationType.Legacy;
        mi.clipAnimations = new[]
        {
            Clip("Idle", 1f, 61f, true, take),
            Clip("Walk", 71f, 101f, true, take),
            Clip("Jog", 111f, 135f, true, take),
            Clip("Aim", 145f, 175f, true, take),
            Clip("Board", 185f, 209f, false, take),
            Clip("Drive", 219f, 279f, true, take)
        };
    }
}
#endif
