# Counter-Exfil: one incident accepted

Accepted October 7 at 08:35 UTC: [`de0b3360fa7d7a1722aa981ee4dbf3a1c223ccd7`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/de0b3360fa7d7a1722aa981ee4dbf3a1c223ccd7), on `game/chicago-20261005`. This is a scoped playable checkpoint. The polished ten-minute game is unfinished. The previous accepted checkpoint, `d4d13937`, remains preserved.

After the existing interception ending, the player still has 28 health and must retrieve the coupe about 20 metres away through ordinary walking/E. The ending and reset remain usable while the new chapter is merely Armed. F while seated and stationary starts one lead with 6 HP and two runners with 3 HP each. Real shooting and maintained physical car obstruction resolve them; a living player must then cross the west exit on foot. An unresolved escape fails the chapter.

The verified success uses nine actual camera-aligned shots: the two standard runners die once each, and the lead remains alive at 3 HP. The parked coupe keeps the lead physically pinned while the player crosses the exit at **114.433 seconds**, still at 28 health. At completion, contact has lasted 12.193 seconds; the maximum measured westward speed in the final qualification interval is 0.0002003 m/s. Activation was at 92.433 seconds. The replay ends at 124 seconds to test reset; that extra time is not new gameplay.

| Verification | Result |
| --- | --- |
| Original 95-second healthy route and complete Armed HUD | PASS; original ending and handoff preserved |
| Ordinary retrieval, foot-F rejection, seated activation, 6/3/3 HP spawn | PASS |
| Genuine unresolved westbound escape and ordinary R | PASS; lead escape at 107.933 seconds in the separate escape case |
| Actual shots, distinct kills, continuous obstruction and foot completion | PASS |
| Ordinary car departure after a qualified pin | PASS; real separation clears pin credit |
| Early foot exit with unresolved runners and repeated F | PASS; no premature completion or duplicated wave |
| Four new and six original death boundaries | PASS; explicitly declared health-zero injections |
| Ten unchanged walking/world/driving/mission/combat/aiming regressions | PASS |
| Fresh local xhigh visual review | Scoped PASS; eight native images plus one visual target |

These are 25 native replays on the same game source, supported by 44 relevant controller checks on both hosts. Death injections test the exact control/progression boundary, not natural lethal damage. The early-exit case keeps the runners unresolved while the player waits beyond the exit; it does not separately prove resolving every runner later from that position.

The actual physics defect was velocity-forced runners pushing an unoccupied 1,200 kg coupe too quickly to maintain obstruction. Local Qwen replaced active velocity forcing with finite mass-scaled propulsion and a material on only the new runner capsules. It also shortened the Armed hint and corrected the installed material API and terminal/death stop. The original car, world, camera, aim, health and older actors stay intact. Cloud work supplied diagnosis, ordinary acceptance inputs, protected observers, exact final-response recovery and factual review; substantive game C# remained local Qwen authored. No new asset batch was made.

The original local visual verdict is preserved alongside [cloud factual annotations](../diagnostics/counter-exfil-2026-10-07/cloud-pixel-annotation.json). The critic mislabeled the third-person view as first person, overstated what the completion still identifies, and confused some failure-card content and separate contact-release evidence. Those descriptions are corrected without rewriting its verdict or the native evidence. Its cosmetic suggestions do not authorize changes to the protected camera. Actual cards are readable in the reviewed frames; art, animation, lighting, audio, broader composition and varied ten-minute pacing remain unfinished.

Evidence and provenance:

- [Measured first failure](../diagnostics/counter-exfil-2026-10-07/physical-route-failure.json) and [local source correction](../diagnostics/counter-exfil-2026-10-07/local-propulsion-repair.json).
- [First physical success](../diagnostics/counter-exfil-2026-10-07/first-physical-success.json), including source/build, actual shot events and capture hashes.
- [Complete native qualification](../diagnostics/counter-exfil-2026-10-07/native-qualification.json), including separate contact, death, early-exit and regression evidence.
- [Scoped acceptance and original local review](../diagnostics/counter-exfil-2026-10-07/scoped-acceptance.json), with verified visual payload and final-response provenance. Private reasoning is excluded.

Actual Armed, combat, completion, death and reset screenshots are saved privately in Library for parent review. The native evidence build is preserved. At the handoff, the game checkout is clean, the controller is paused, and the owned review resident/server/keeper have stopped gracefully. No other workload was managed. Failure history and the fixed October 8 06:33:12 UTC cap remain unchanged.
