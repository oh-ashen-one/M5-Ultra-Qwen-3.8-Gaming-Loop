# Native HUD lookup repair

The first consolidated-HUD candidate `a64f4bb` compiled, but its native relay playthrough correctly failed acceptance. The relay still completed through ordinary input at 59.633 seconds; the displayed objective disappeared during active relay play. Compilation and successful gameplay transitions did not establish a usable HUD.

The source searched for a TextMesh beneath the stationary `RelaySequence` host. Actual `RelaySequence.Hud.cs` creates `RelayHud` under the camera, with its Text child beneath that. The same writer already publishes its current text through `RelaySequence.Objective`. Local Qwen changed the board to read that actual objective instead.

The captured trace also exposed missing completed-stage receipts and an early overlap. A `RouteStage >= 3` condition could never display the delivery receipt because actual stages are 0, 1 and 2. `HudStatus` is installed after `MissionDirectorHud`, so a setup-only lookup cached null and never applied the intended placement. Local Qwen corrected the two receipt lines and added a late lookup before positioning the health panel.

Repair candidate `6ff5960` changes only `game/Assets/Game/MissionDirectorHud.cs`. The original failed source and native evidence remain preserved. Gameplay, inputs, timers, anchors, previous qualified relay and broad accepted checkpoint are unchanged. Four small local-Qwen edit submissions produced the source; cloud work diagnosed the failure and maintained external acceptance.

Native acceptance now additionally requires the displayed relay lines to match the actual live `RelaySequence.Objective`. Empty and stale-objective examples fail the CPU checks. The full native positive, wrong-order/timeout/reset and no-handoff cases, ten legacy regressions and fresh pixel review remain required. Existing failures are retained while the consolidated-HUD diagnostic runs, so one early gate no longer hides other observed presentation faults. There are 299 passing CPU tests on both hosts; these do not replace native qualification.

The original route remains 59.633 seconds including the 27.100-second relay. This presentation repair adds no mission duration and is not final game acceptance.
