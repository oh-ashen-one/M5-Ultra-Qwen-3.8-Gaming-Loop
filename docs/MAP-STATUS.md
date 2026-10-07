# Playable map measurement and next milestone

Measured 2026-10-06 at accepted checkpoint `d269dc43ac66c39afca4cb98ea53f9e7ed36806f`.

The actual traversal boundary and visible core pavement are **7 m × 32 m**, X −1..6 and Z −2..30. That is 224 m² gross; buildings, piers, bins and the car reduce usable space. This is one fenced street/sidewalk corridor with two repeated façade sections, no connected cross-streets, no additional playable blocks and no accessible interiors or rooftops.

`game/Assets/Game/WorldColliders.cs` places the enclosing colliders at X −1.25/6.25 and Z −2.25/30.25, each 0.5 m thick. The accepted native `q0048` scene observation provides rendered dimensions; the measurement is independent of screenshots and replay duration. Native scenery spans approximately 22.55 × 35.10 m in XZ. The underlying invisible 400 × 400 m support collider is not a playable map.

Next is one bounded, locally authored connector. Native acceptance requires walking at least 6 m past an old boundary and physically returning, then driving beyond a boundary and physically returning, with real colliders, visible support and actual captures of both modes in the extension. Reset teleportation cannot establish a return. All ten existing mechanics regressions and a fresh local visual review still apply. This accepts only the demonstrated extension, not a large map or final quality.

Following that checkpoint, the provisional spatial target is two connected street segments and a side alley spanning at least 60 m along one axis and 20 m across. Exact topology remains a local design decision. Add a meaningful objective outside the original corridor before extending mission pacing toward ten minutes. Do not count decoration, invisible support ground or idle waiting as progress toward either goal.

The existing fixed overall cap remains 2026-10-08 06:33:12 UTC. Substantive game and Blender source remain locally authored by Qwen; cloud changes in this recovery are controller, acceptance and documentation work.
