# East Dead-Drop additive contract

The local-Qwen plan is preserved in [the original design receipt](../diagnostics/map-2026-10-06/connected-mission-local-plan.json). This short chapter is a step toward the full game, not ten-minute acceptance.

## Actual API and authorship boundary

The protected external `LoopSignals` exposes `Mission` as a string; it has no `MissionComplete` field. Local gameplay observes the real courier `Mission == "complete"` handoff. The new game-owned `ChicagoGame.RouteMission` component exposes public instance fields `RouteStage` (0 inactive, 1 active, 2 chapter complete), `RouteComplete`, `Cache` (Transform) and `Objective` (string). The passive observer reads these fields and actual actor/mesh transforms. It never writes them.

Only local Qwen may create `Assets/Game/RouteMission.cs` and add its one `RouteMission.Install(body, cam)` call. Legacy mission, vehicle, combat, camera and external harness are unavailable to that authoring role. The new chapter reads existing signals and does not write them.

## Positive proof

- Actual courier completion activates the chapter; the short courier ending retains its original meaning.
- Cache root stays at **(50, 0.14, 18)**, independent of the player/car. Visible marker children reuse an existing original mesh, with grounded geometry and copied status materials.
- After activation the real vehicle must approach within **6 m**, then ordinary **E** input must produce vehicle-to-foot exit.
- A fresh **F** press, on foot and within **1.5 m**, completes the short chapter. The marker and objective text visibly respond.
- **R** resets progress, hides the chapter marker and requires a new courier handoff. No elapsed-time-only completion or fixture branch is allowed.
- Capture objective activation, the connected junction/approach, cache, exit/interaction, chapter completion and reset. No new timer or idle padding creates duration.

## Negative proof and unchanged gates

A no-handoff run containing remote F presses must stay inactive. The independent gate rejects missing arrival, exit without E, wrong mode, remote interaction, stale held F, premature completion, moved/actor-parented markers, missing original mesh, empty objective and stale reset state. CPU red fixtures validate these rejection paths; native positive and negative runs remain separately necessary.

An initial native activation/reset probe deliberately has no east arrival. Its PASS cannot count as chapter completion. Full chapter qualification requires a separate ordinary-input route within 180 seconds, all ten existing mechanics regressions and fresh scoped visual criticism.

The broader second-street critic remains **FIX**. No short chapter result changes the accepted checkpoint or constitutes final art, audio, performance or ten-minute acceptance. The original October 8, 2026, 06:33:12 UTC cap remains unchanged.

