# Camera and marker qualification

Camera polish must preserve the accepted mission route, delivery position and boarding rules. General presentation edits cannot modify `Mission.cs` or `VehicleInteraction.cs`. A measured mechanics defect requires a separate scoped local-Qwen repair with its own evidence. Comments claiming a route cannot complete do not supersede native completion evidence.

The external camera fixture places a disposable wall behind the stationary player at three measured distances: 0.65 m, 3 m and approximately 5.40 m. It never moves the actor or camera, changes mission outcomes, or enters the shipped project. The actual game camera runs normally. The observer records whether the camera lies inside/beyond the wall, whether its near plane intersects the wall, and how many target bounds samples are in frame and unobstructed. After removing the wall, normal W input verifies that the native game still runs.

The endpoint-distance predicate and actor visibility are separate observations. A short distance between the obstacle and desired camera endpoint does not establish player or vehicle visibility. Bounds samples are descriptive; actual frames remain necessary. These three stationary wall cases are bounded evidence, not proof for every moving or angled obstacle.

For source `6fe8ed8`, actual native evidence found the camera beyond the 0.65 m wall in all 15 settled samples, with zero unobstructed target samples. At the endpoint wall, all 14 settled samples placed the camera inside the wall. The first local correction `f1169bd` passes the geometry cases, but its close view fills the image with the player's body. That correction alone is not visually accepted.

Qualification requires the unchanged accepted normal-input route, all ten current-source mechanics/aim regressions, sealed captures and a fresh local image critic. A fixture PASS cannot promote a playable checkpoint. A scoped camera/beacon PASS does not advance the final ten-minute game gate or reset the existing full-task failure counters.

Native mission observations identify the actual `CourierMission.padRend` interaction target. The beacon and any ground ring must stay fixed and share its horizontal world position within 5 cm; their intentional vertical offsets are recorded separately. This catches a relocated interaction pad even when a stationary marker remains behind. The actual route still must demonstrate pickup, delivery, failure and retry through normal inputs.

All game changes remain authored through local Qwen's scoped edit tools. Cloud work supplies the external observer, acceptance checks, controller and disclosed image review. Original failed candidates, source histories and failure counters are retained. The absolute project cap remains October 8, 2026 at 06:33:12 UTC.
