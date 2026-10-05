# Camera-aligned combat qualification

The 0.85 m sphere cast in `6102a3c` was not accepted. In a native deliberate-miss
test, its shot at **8.60 s** reduced rival HP **3→2** while the camera's center ray
hit a barrier and missed both the rival collider and visible bounds.

Local Qwen restored the previously accepted thin camera ray in
[`1295417`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/1295417194c0f2cdf9716982df06afebd6336c57).
The same inputs and original assets produced these paired results:

| Contract | Wide cast, `6102a3c` | Corrected ray, `1295417` |
| --- | --- | --- |
| Visible camera-aligned hits | 2 hits, HP 3→2→1 | 2 hits, HP 3→2→1 |
| Four intentional off-target shots | 1 damaging hit; **FAIL** | No hits or HP loss; **PASS** |
| Rival behind nearer wall | 2 blocked shots; no damage | 2 blocked shots; no damage |
| Rival behind near-camera cover | 2 blocked shots; no damage | 2 blocked shots; no damage |

Both versions passed the cover tests. The measured regression was off-target
damage. Complete build IDs, candidate hashes and observed events are in
[native-before-after.json](native-before-after.json).

The external observer records the actual camera ray, target collider and visible
bounds before gameplay fires, then checks shot counts and HP changes in that
frame. Normal input drives every shot. Disposable wall fixtures are identified
separately and cannot promote a playable game. No harness code aims, moves
actors, deals damage or manufactures a successful game state.

The earlier whole-route replay also fired forward while driving away from a
rival behind the car. Its later attempt recorded a hit but still failed pickup,
delivery and post-failure completion. The continuing local author must correct
that replay's camera/target geometry and mission interactions, preserving
accepted mechanics.

Controller `09bc68b` requires current-source aligned-hit, deliberate-miss, wall
and near-cover proof before future rough-route or polish promotion. Existing
foot/wall/driving regressions, sustained escape and the five baseline regressions
remain required. **121 CPU tests pass on both machines.** The original stop,
three route failures and accepted checkpoint `c32cfeb` remain preserved.

An actual corrected aligned-shot frame at **7.55 s**, captured
**2026-10-05 21:55:11.461957 UTC**, is confirmed in private Library for the
milestone update. Blockout art, final audio balance and the complete ten-minute
route remain unaccepted.


The fresh local image review corroborated the aligned hit and intentional miss.
It returned **UNVERIFIED for cover imagery**: the close cover fills the camera
view, and the review omitted the separate wall frame. That verdict is preserved.
The native cover results remain measured passes; [per-shot detail](cover-event-detail.json)
records the exact first collider, camera ray, target intersection, unchanged HP
and zero hit increments. Improved cover framing remains an evidence task.
No new playable checkpoint was promoted from this diagnostic. The same owner
continued rough-whole-route in q0032 with the review and geometry feedback.

A supplemental native run keeps game source `1295417` unchanged and moves only
the disposable close-cover fixture so its edge and the surrounding scene remain
visible. It still intersects the center ray and overlaps the former sphere-cast
origin; both shots are blocked with no rival HP loss. The new image, open control
view, previously omitted wall frame and exact per-shot geometry are supplied to
a fresh review. See [visible cover proof](visible-cover-proof.json).

The expanded local cover review reached its **8,192 output-token limit** without
a verdict; that response and the earlier UNVERIFIED review remain preserved.
A disclosed [cloud visual spot review](cloud-cover-review.json) inspected the
actual wall, open control and improved cover-edge frames together with their
independent ray/collider/HP records and corroborated scoped cover occlusion.
This is not represented as a local-Qwen PASS or a whole-route promotion.

The sole queue resumes the complete local-Qwen q0032 replay proposal preserved
at the boundary, with source `1295417`, counters 4/2 and accepted `c32cfeb` intact.
Every baseline/combat/aim regression and the normal fresh local full-route review
remain required for promotion. **123 CPU tests pass on both machines.**
