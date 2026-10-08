# Resizable standalone player and manual-input diagnostic

These are original cloud-authored presentation/diagnostic helpers. They do not change the local-Qwen gameplay or art. Their core source compiled in the owner's isolated walkthrough copy with Unity 6000.6.4f1. The public fresh-clone recipe below has not been requalified; physical keyboard/mouse operation remains unresolved.

## Prepare the bootstrap

Install and license the matching macOS Apple Silicon Unity editor separately. From the repository root, copy the existing public harness into the Unity project. The first build creates its bootstrap scene; the second enables the requested window settings.

```sh
mkdir -p game/Assets/LoopHarness build
cp -R controller/unity/. game/Assets/LoopHarness/

UNITY_EDITOR="/Applications/Unity/Hub/Editor/6000.6.4f1/Unity.app/Contents/MacOS/Unity"

LOOP_BUILD_OUTPUT="$PWD/build/BootstrapPlayer.app" \
  "$UNITY_EDITOR" -batchmode -nographics -projectPath "$PWD/game" \
  -refreshImportMode InProcess -executeMethod LoopBuild.Build \
  -logFile "$PWD/build/bootstrap-build.log"

cp tools/manual-play/Editor/WindowedPlayerBuild.cs game/Assets/LoopHarness/Editor/

WALKTHROUGH_PLAYER_OUTPUT="$PWD/build/ChicagoWalkthrough.app" \
  "$UNITY_EDITOR" -batchmode -nographics -projectPath "$PWD/game" \
  -refreshImportMode InProcess -executeMethod WindowedPlayerBuild.Build \
  -logFile "$PWD/build/windowed-build.log"

open -n build/ChicagoWalkthrough.app --args \
  -screen-fullscreen 0 -screen-width 1280 -screen-height 720
```

Close an Editor already using that project before a CLI build. This recipe uses its existing scenes/assets; it does not invoke local inference, Blender generation, asset exports, automatic replay or a benchmark. Window settings are resizable, windowed and initially 1280×720. Build outputs are local and untracked.

## Optional input diagnosis

To include the passive monitor, copy `ManualInputTrace.cs` into `game/Assets`, rebuild the windowed player, and launch with a log argument:

```sh
cp tools/manual-play/ManualInputTrace.cs game/Assets/
# Repeat the WindowedPlayerBuild.Build command above.
open -n build/ChicagoWalkthrough.app --args \
  -screen-fullscreen 0 --manual-input-log "$PWD/build/manual-input.jsonl"
```

The monitor activates only when that argument is supplied. For at most 180 seconds, it samples WASD/R/E/F/mouse-button states, focus, pointer position, actual player position/health and shot/reset counters. It does not record arbitrary text input, move actors, heal the player or fabricate successful input. The log stays local.

Test real R/W/left-click input while the window has focus. Automated scenario input must not be substituted for this test. The completed experiment did not establish a manual-input fix; see [the report](../../docs/COMPLETED-EXPERIMENT.md).
