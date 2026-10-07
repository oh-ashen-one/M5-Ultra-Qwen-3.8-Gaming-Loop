# Connected mission milestones

Updated October 6, 2026. This is an implementation and acceptance plan, not a completed game.

The current courier component starts a 30-second timer at spawn and completes after a short pickup-and-drive delivery. It cannot serve as the final ten-minute experience. Its tested pickup anchors, driving delivery and real timeout/retry behavior remain valuable component contracts.

The next work has a dedicated mission scope. The general presentation editor intentionally blocks mission and vehicle-mechanics edits; asking that editor for longer pacing would not resolve this conflict.

1. **Define a connected follow-on objective.** Local Qwen chooses a small meaningful objective across the existing core, alley and provisional east street. The decision must identify real world anchors, ordinary input, actor/mode requirements, visible guidance, reset behavior and externally observable progress. Preserve the short courier component or explain a legitimate player-facing transition before changing its contract. A distinct overall-route state must not silently reinterpret the courier's existing completion flag.
2. **Qualify the first increment in at most three minutes.** Seal additive acceptance before implementation. Require physical travel, proximity and deliberate interaction, clear objective transitions and a recoverable reset. No-input, distant-interaction, wrong-mode, stale-state/reset and premature-ending cases must fail. Retain all ten existing mechanics regressions. A short objective PASS is only a component milestone.
3. **Build varied connected pacing.** Add purposeful objectives, encounter/escape and a return/ending using local-authored game code and original art. Measure time spent progressing through actions and routes. Waiting, repeated empty laps, timer locks and elapsed-time-only completion cannot establish ten-minute gameplay.
4. **Qualify the whole game separately.** Preserve the approximately 540–660 second ending target, real failure/retry, combat/aim/pursuit, controls, collisions, readable HUD and rendered playthrough evidence. All previously rejected visual findings remain outstanding. Final art must satisfy the existing original-Blender-asset requirement; primitive markers are still temporary.

The second street's October 6 q0092 native traversal and all ten regressions passed, as did the focused return-angle review. Its broader critic returned **FIX** for street/junction presentation, camera framing and HUD visibility. The accepted checkpoint remains `c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188`; latest source `9522003c685cf9e74afdcc45bae94368baa04e7e` is preserved but has not replaced it. Moving to mission work does not promote that street or waive its findings.

Cloud work defines orchestration, acceptance and recorded evidence. Local Qwen owns substantive game design and implementation. The same queue, failure history, resident model and **October 8, 2026, 06:33:12 UTC** cap remain in force.

