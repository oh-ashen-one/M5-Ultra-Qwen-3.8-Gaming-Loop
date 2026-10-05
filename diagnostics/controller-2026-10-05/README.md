# Controller qualification — 2026-10-05

These are disposable controller fixtures, not Chicago gameplay or art-quality results.

- Twelve CPU state/edit/evidence/recovery tests pass, including interrupted-edit preservation and restoration of only the owned game directory after repeated failure.
- Actual macOS sandbox probe allowed an owned write and denied protected reads/writes.
- Native Unity 6000.6.4f1 compiled the original prior Qwen Blender fixture and built an ARM64 macOS app. The Metal player ran for 16.017 seconds, recorded 140 samples and four actual frames, and observed 16.094 m displacement from replayed application input.
- The same app with its movement deliberately disabled exited normally but was rejected: 0 m movement and unchanged captures. A clean exit does not count as a pass. See [exact native receipt](native-green-red.json).
- The updated scoped Blender export passed. Editable Blender sources remain outside Unity Assets; the FBX is imported once.
- A fresh Flash-Next session saw an actual stationary frame plus trusted input/movement observations. It identified the blue sphere and red cube, returned FIX, and explained the missing movement. It also read and changed a scoped note using its exact full-file hash. No builder history was supplied. See [sanitized model receipt](model-tools-critic.json).

![Actual native disposable fixture; not Chicago output](disposable-native-frame.png)

Qualification exposed and corrected scoped preference/cache writes, Darwin IPC paths, excessively long compiler socket paths, redundant Blender auto-import and macOS app-bundle discovery reads. Earlier failed attempts remain private for diagnosis; no failure was relabeled as a passing playthrough. The model guard cleanly stopped one handoff that exceeded engine ownership/capacity, then was explicitly restored after fixing the cause. A native startup crash was diagnosed before relaunch. The final native and model/tool qualifications completed with the separate existing Blender preserved and no positive swap growth reported.

Camera frames and transform traces do not establish HUD, audio, collision completeness, sustained 60fps or a finished game. See the [runbook](../../docs/CONTROLLER-RUNBOOK.md) for limits and recovery commands.
