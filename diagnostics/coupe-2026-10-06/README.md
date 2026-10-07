# Coupe silhouette milestone

**Accepted at 2026-10-06 03:12:50.834806 UTC:** local-Qwen source `27cbe3e0addd7348656b6d740595c60ec2d7ab89`, playable checkpoint `d269dc43ac66c39afca4cb98ea53f9e7ed36806f`, qualification `q0048-8e962e4d`. The previous camera checkpoint `e38b0681046fb39cab7f8ec182495903729b5ae6` remains preserved.

At the identical 3.2-second spawn view, the coupe now has more exposed dark wheels, changed wheel openings and a revised body/cabin silhouette. This is a bounded improvement to the existing original asset. The car still consists of crude forms; it does not approach final reference quality. At 15.5 seconds the driving view remains tight against the building, with little road visible, an intrusive green objective disk and a vertical shape in the lower frame. The character, surroundings and horizon remain unfinished.

Only `Art/coupe.py`, its editable Blender source, FBX and export provenance changed. Qwen originally saved the script without exporting it, and the provenance guard correctly paused the queue. A single export-only local-Qwen step completed that exact saved script without reauthoring it. No failed Blender action was replayed. The script SHA-256 remains `9630f574cc8107be2e986e6f5718fe1c92b72f552841b7932e27f1ef0ff408f6`.

Build **`bef84b0466cfa65a12c8acababfc517ae5f46182b12fc4782901a675027b39e4`** passes the unchanged 52-second ordinary-input route and all ten current-source regressions: walking, world collision, vehicle/reset, courier, failure/retry, foot/wall/driving combat, deliberate misses and near-cover aim. The actual target, post and disk stay aligned at X1/Z26 across 503 route samples. Timeout occurs at 30.08 s, reset at 32.03 s, retry pickup at 39.43 s and delivery at 46.33 s. The fresh local critic returned **PASS for coupe silhouette only**.

| Actual native image | Replay time | Capture write time, UTC | Source/build |
| --- | --- | --- | --- |
| Before spawn, existing accepted camera image | 3.2 s | 2026-10-06 02:34:30.525437 | `eeb07c0` / `c55e3e01` |
| Improved coupe spawn | 3.2 s | 2026-10-06 03:02:56.085128 | `27cbe3e` / `bef84b04` |
| Improved coupe driving view | 15.5 s | 2026-10-06 03:03:10.821864 | `27cbe3e` / `bef84b04` |

Times come from the native PNG write timestamps recorded on the M5, not Library upload times. Both new PNGs are confirmed in private Library; the comparison reuses the already saved before-spawn image. The previously delivered camera driving pair is not duplicated.

The critic recommends further camera framing work. Its lane relocation and prop-removal suggestions are not automatic change authority: preserve the accepted physical route, boarding rules and fixed objective anchors, and identify any obstructing geometry before changing it. A bounded representative driving/near-wall check is appropriate; this milestone does not establish complete camera polish. See the [exact native results and attributed local review](native-qualification.json).

At **03:15 UTC**, the same owner continues **q0049-292d36be**, with local Qwen editing a vehicle-camera setup in `Bootstrap.cs`. Those working edits are unverified. There is one queue owner, one healthy resident model and the existing publisher. Original task-7 counts **6/1**, diagnosis history and the **2026-10-08 06:33:12 UTC** hard cap remain unchanged. Final art, audio, performance and connected ten-minute pacing are still unaccepted.

Game C# and Blender art are local-Qwen work. Export/acceptance infrastructure, this evidence record and the disclosed image spot review are cloud supervision. The unchanged controller suite has **156 passing CPU tests on both Macs**.
