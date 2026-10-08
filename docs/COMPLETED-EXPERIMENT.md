# Completed experiment report

The development experiment is closed. Its outcome is a rough original native Unity game with verified mechanical milestones, incomplete final presentation and unresolved physical input in the standalone walkthrough.

## Method and accepted mechanics

Local Qwen used exact source retrieval, mediated edits, serial roles, original Blender authoring, native rendering, immutable acceptance checks and known-good checkpoints. Cloud Codex supplied controller/acceptance infrastructure, supervision and disclosed recovery. The approximately 90% local gameplay-coding target was not independently measured. Compilation, grep matches, token counts and time alone did not establish playability.

Accepted fallback `de0b3360fa7d7a1722aa981ee4dbf3a1c223ccd7` passed real shooting, maintained physical coupe obstruction and foot completion, escape/contact/reset negatives, ten declared death boundaries and ten prior gameplay regressions. Its verified new route completed at 114.433 seconds; the 124-second replay included reset behavior. This was scoped prototype acceptance, not the intended ten-minute final experience.

Later passes added original character/clothing/rig/animation, coupe cabin/driver presentation, street surfaces/facade detail, HUD backing and lighting. Native tests examined motion, fit, materials/UV, wheel facing, parcel contact and map coverage. Visible presentation remained coarse.

Lighting `c31e737aa547dcbbd5a3ad134f4963a1f9ff9cc1` and the lowered original parcel were kept. Changing the sun direction also shifts the procedural skybox sun disc; claims that the sky was entirely unchanged were incorrect. The parcel still crowds the reticle. A short silent fixed-clock clip is not real-time performance proof.

## Rejected experiments and exact rollback

Brick source `0270d7e120698e6d6f66298170b3cd1be5c708bc` exported to `3058f8dae7771175f3bd53a538b3d054e215e4bc`. The original brick PNG outputs changed while other canonical textures, UV and manifest data were preserved. An initial gate rejected newly added passive geometry-observation metadata. A separate qualification explicitly accounted for that metadata and required native geometry/material/tangent/slot equality. A fresh local critic rejected the visual merit. Exact original-byte restoration produced `35a62880b9d9c7e27f687e78419a99ad47533a39` and matching native pixels.

Asphalt source `dde97107a7e10253120ba9a816603b85320192a4` exported to `b9d55637f7ccb9ec98a973af85bb860a2f711d6f`. A broad PNG-directory count gate failed because three pre-existing legacy files remained outside the six-image canonical manifest. A separate qualification checked all six canonical images, all three protected legacy files and passive export metadata. Nothing was deleted simply to make the count green.

The asphalt candidate passed native preservation checks but failed local visual review. The critic's zero-pixel-variation claim was false: startup, carry and street views changed 9,504, 1,909 and 119,538 RGB pixels. Their mean absolute channel differences were approximately 0.02635, 0.00255 and 0.29070 on the 0–255 scale. Pixel changes did not demonstrate useful visual benefit, and two rejected passes do not prove a universal mathematical limit on albedo shading. The original reviews and failures were preserved separately from factual corrections.

The controller mechanically restored recorded original source/export bytes and removed only newly added passive metadata absent from the baseline. No cloud art redesign was introduced. Rejected commits remain in the game branch's history.

## Final restored verification

Final source: `c4f43907e2bf8eeceb86274dc9c984c029f154fa`.

Recorded prior source: `35a62880b9d9c7e27f687e78419a99ad47533a39`.

Their complete game trees match. Native build SHA-256: `3a6113539f34c2baee9271e54a783c995801acb8137908a89917751586b275e0`.

An actual 18-second carry/contact check and 125-second map replay passed. Imported geometry, images, materials, slots and tangents matched, as did all 1,402 lighting observations. Three actual 960×540 camera-rendered PNGs exactly matched the kept baseline:

| View | Game time | Capture completed, UTC | PNG SHA-256 |
| --- | --- | --- | --- |
| Startup | 0.5 s | 2026-10-08 06:21:04.213939 | `156066f1f43a8a65bd692982db3c613c887d76c6834df836cc602ee94cc32cb4` |
| Parcel carry | 14.5 s | 2026-10-08 06:21:21.428137 | `18e0158a60c947e78b2847dae87e1fc69ba6fbd30586729e3654f6febea88cbd` |
| Street | 44 s | 2026-10-08 06:22:33.603155 | `dab11c92458c1c7032c1199b98c9cba27bb248f3392e8b1a8f54b345d98a097d` |

Raw media is not included. A failed-mission timeout banner on the map tour is not a successful mission-ending receipt. These tests verify current restoration, not a fresh rerun of every historical adverse case.

Before the fixed cap, the run was paused and its recorded model/controller/task-scoped engine processes had stopped. Other workloads were untouched; the accepted fallback and failure history remained preserved.

## Standalone window and input test

The owner requested a manual walkthrough and personal recording. A separate project copy preserved the verified source. A window-settings-only build enabled resizing, windowed mode and a 1280×720 starting size. Compilation succeeded, protected gameplay/art/scene hashes matched, and the player log recorded successful resizing. No Editor UI was required for play.

The owner reported unresponsive keyboard and mouse. The exited player's log showed no startup/input exception. Legacy Input Manager was selected; the no-replay path delegates to Unity's real `Input.GetKey`/`Input.GetKeyDown`. A normal macOS LaunchServices relaunch did not establish a fix.

A passive diagnostic observed only known game controls, focus, health, position, shot/reset counters and pointer position for 180 seconds. It reported focus but no control events, no shots and no reset; the stationary player eventually died. This cannot distinguish missing input delivery from an absent physical-input test and does not establish a root cause. No confirming physical R/W/left-click result was received before publication. Manual input remains unresolved.

[The window helper and diagnostic](../tools/manual-play/README.md) are cloud-authored infrastructure. Original gameplay code/art was preserved. Free mouse-look was not implemented; the camera follows the player.

## Lessons and remaining work

- Bind native results to source/build/time/hash; distinguish preservation from visible improvement.
- Preserve red gates and qualify diagnosed metadata issues separately.
- Keep exact rollback available and correct factual critic errors against measured pixels.
- Test physical controls separately from automated replay before declaring human play ready.
- Character/car/surface/animation/camera/audio quality and varied ten-minute pacing remain unfinished.

This is the saved outcome of a completed experiment, with limitations retained. Public material excludes private chat, raw model reasoning, credentials, routing, private machine paths, raw internal reports and native media.
