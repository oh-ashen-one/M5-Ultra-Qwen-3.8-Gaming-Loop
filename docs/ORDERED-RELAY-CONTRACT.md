# Ordered relay additive contract

This implements local Qwen's saved three-site proposal as a short new gameplay increment. It does not establish ten-minute pacing, route-choice variation or final quality.

## Fixed physical scope

| Order | Player-facing location | Root anchor |
| --- | --- | --- |
| 1 | North frontage | (53, 0.20, 27) |
| 2 | South frontage | (41, 0.20, 9) |
| 3 | Northwest frontage | (29, 0.20, 27) |

Each stationary prop reuses the original dumpster mesh, fits within a maximum dimension of 1 m, and stands with its rendered base at sidewalk Y0.20. One matching solid collider represents each prop. Number labels and a compact lower-right objective panel identify the next site without changing existing HUD panels, actors, pavement or camera.

Local Qwen owns `Assets/Game/RelaySequence.cs` and one `RelaySequence.Install(body,cam);` line immediately after the existing `RouteMission.Install(body,cam);` in Bootstrap. The actual Walker speed is 3.2 m/s. No new assets, primitives, external game-state writes or fixture-specific code.

## Gameplay state

The new component reads the actual RouteMission instance and activates only after its stage2/complete handoff. It owns Active, ActivationCount, ExpectedIndex, WrongOrderCount, AllComplete, Failed, Remaining, Objective and three Relays transforms.

A fresh F on foot within 1.5 m of the expected site advances once. A wrong site resets relay progress to zero, increments its wrong-order counter and flashes that site red for 0.3 seconds; it does not restart the deadline. Far F and F held before entering reach do nothing. Three correct interactions complete the relay. The 45-second deadline creates a real failure, not forced waiting; failed or complete state remains latched until R. Global R clears/hides all relay state and requires a fresh earlier chapter completion.

No legacy Mission/Health/Restarts writes. The courier and east-cache endings retain their independent meaning.

## External acceptance

The passive observer records actual component fields, root/render/collider bounds, original mesh reuse, HUD rectangles and scene positions. It never moves actors or writes game state. The immutable contract uses the real input trace and observed proximity to validate every transition.

Normal-input probes preserve the proven chapter through its 32.53-second completion:

- Positive: remote F; hold F while approaching site1, release and press again; visit sites1/2/3; ending; R and remote F after reset.
- Wrong order and timeout: site1 then site3, with the wrong F held; progress resets exactly once, the original deadline expires, F cannot revive it, then R clears state.
- No handoff: walk and press F without completing the earlier chapters; relay stays inactive.

The proposed 64-second positive and 82-second negative replays are acceptance schedules, not measured successful game durations. Waiting in the timeout test never counts as mission content. Native success, all ten prior regressions and fresh scoped pixel review remain required. Exact chapter gates and the broad accepted fallback remain unchanged.

## Continuing scope

After first native proof, diagnose actual failures and continue the existing queue under standing authority. Planning boundaries do not require another permission request. Preserve original failures and the October8,2026,06:33:12 UTC cap. DS1 remains user-paused and outside this task. Art follow-up includes the observed striped/stepped lower-window/transom artifacts, repetitive facades, character and camera quality.
