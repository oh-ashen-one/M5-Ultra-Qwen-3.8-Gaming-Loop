# Courier mission recovery evidence

**Latest candidate, verified 16:49 UTC:** `035e5c4` changes camera framing only and compiles natively. Its [newly proposed replay failed](latest-camera-failed-route.json): it dropped the lateral approach, never picked up the parcel or entered the car, and vehicle displacement was only 0.168 m. The newest actual capture is **16:45:18.870 UTC**, replay t=16 s, build `57dc6ef4d37a2080809c9c9ffb2a378045aaa4c3ce005108fe56eadfcb3f4ce8`. It is a failed/WIP frame, not accepted gameplay. The native image and receipt are available through the existing private artifact route.

The prior `60831ed` mechanical PASS below was followed by a fresh visual **FIX** for small text and the misaligned opaque HUD panel. The critic also lacked an ending frame because the controller selected only start/middle/end despite having captured completion. A tested state-based selector now chooses actual uncollected, carrying, complete, reset and failure frames when present; it is staged for the next safe controller reload. Existing native evidence is immutable. The active owner continues the current local repair; mission failure/retry and later subfeatures have not been reached.

**Native mission and regressions PASS, 16:32 UTC.** Local-Qwen candidate `60831eded5ae1793fcd9170ed57ed6b3f63302b8` compiles and executes the connected mission. The [native gate](pickup-delivery-reset-pass.json) records fixed objectives, walk-away at 4.633 s, return at 7.033 s, F pickup at 7.433 s, F vehicle delivery at 14.350 s and grounded R reset at 17.133 s. All four observed HUD states pass. Vehicle displacement is 17.382 m. Walking, world-collision and vehicle/reset regressions each pass. This is a mechanical result; fresh scoped visual review and promotion are separate.

The last whole-HUD request exhausted 8,192 output tokens without saving. Narrowing to seven exact one-line local-Qwen edits resolved it: all seven saved between 16:28:49 and 16:29:12 UTC; the separate replay submission then used 392 output tokens and 9.66 seconds. The real 2.6 m distance gate is unchanged. The destination is now a stationary west loading bay at X1/Z26 on the existing pavement, with its actual renderer position used for proximity. Parcel location, accepted vehicle physics and spawn are preserved.

Ten original native captures accompany build `c357ee59200e048815adeb6be24fd61e1c0a3d610f15fb1d67d6343a6cb37b93`. The completion frame was captured at **16:29:57.883 UTC** (replay 15.2 s) and reset frame at **16:30:01.447 UTC** (replay 18.5 s). Unchanged PNGs and a matching SHA-256 receipt were retrieved through the existing private artifact route. Actual pixel review confirms correct text facing and state changes, but text is small and the backing sits below it. The game still uses rough development geometry, a large primitive beacon and unfinished car/camera composition. These remain visual defects, not final-quality acceptance.

The stopped attempt never submitted `finish_task`: `summary`, `duration`, `input_steps`, and `captures` were all absent. Its partial source `bf1ab69` and known playable vehicle/reset milestone `479c138` remain preserved. Recovery code is on the existing controller task branch; gameplay edits remain authored by local Qwen.

| Saved local change | Commit | UTC |
| --- | --- | --- |
| Six GameObject/Transform API corrections | `8e4f997` | 15:34:01 |
| Delivery proximity uses the actual vehicle | `632a27d` | 15:34:36 |
| Initial objective/ending presentation | `1dcbfd2` | 15:35:11 |
| Complete integer-stage mapping and controlled-actor HUD position | `bf11d0a` | 16:03:59 checkpoint |

The first replay-only request reached its output limit without a tool call. A separate serialization-only request then submitted the supplied fixture at 15:42:27 UTC. Structural validation passed before native execution; this was not a claim that the route timings would work.

The first native run compiled and rendered eight frames, but failed pickup and delivery. Its external trace jumped from 3.213 to 5.142 seconds around an image capture, skipping the entire S4..4.6 interval. That evidence remains unchanged. The subsequent harness uses fixed 60 Hz simulation time for automated input and records wall duration separately; ordinary human input remains unchanged. No performance claim is made.

The [next native gate](pickup-pass-delivery-fail.json), on local candidate `d3a7f74`, records fixed parcel/pad/beacon anchoring, walking away at 4.533 seconds, returning at 8.15 seconds, and pickup at 8.667 seconds. S input was actually observed in 25 samples. The run covered 16 simulation seconds and 20.575 wall seconds. Real vehicle displacement was 20.133 m.

Delivery remained **FAIL**: at the F press the car was near `(0.206, 0.559, 27.217)` while the fixed destination was `(3.6, 0.15, 27.5)`, outside the 2.6 m horizontal reach. No mission milestone was promoted. Actual frames also showed mirrored, oversized HUD text and an opaque backing obscuring the game.

Candidate `bf11d0a` then compiled and ran in native evidence `q0005-1fcece47`. Its actual HUD says "grab the YELLOW parcel" before pickup and "parcel in hand" after pickup at 7.433 seconds. Anchoring, walking away and returning pass. Delivery still fails: three F samples are approximately 3.95–4.04 m from the fixed pad. Completion and reset presentation remain unverified.

The next builder saved no edit. Its separate replay role exhausted 8,192 output tokens with no parsed tool call; the owner paused at **16:16:49 UTC**. Recovery archived that stopped ledger and resumed at **16:22:58 UTC**, preserving all source, the accepted vehicle checkpoint and the original ceiling. Controller `939b56b` requests three exact local-Qwen edits: compact correctly facing HUD, a persistent delivery bay on the reachable paved west loading area, and proximity derived from the actual visible pad. The unchanged observed pickup/drive probe gains an ordinary R input after delivery. Native success is still unverified.

World-anchoring and actual input transitions are mandatory in automatic mission acceptance and checked again at promotion. Connected-mission acceptance also requires the four actual HUD states and a physical R reset after completion; rendered text readability remains a visual review requirement. Known temporary primitive mission meshes block final polish acceptance. The parcel, pad and beacon remain diagnostic art pending local-Qwen Blender replacements. **68 CPU tests pass on both machines**; CPU checks do not replace native execution or visual review.
