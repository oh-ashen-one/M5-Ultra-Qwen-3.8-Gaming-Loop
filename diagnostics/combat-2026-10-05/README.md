# Combat qualification

## Measured correction and runtime stop, 20:03 UTC

Local Qwen saved five small corrections in source **`f965eae`**. The paired
native tests now show:

| Contract | Before | After |
| --- | --- | --- |
| Imported rival basis/scale | 0.0157 m tall, then flat while turning | Consistent 1.57 m height with unit physical wrapper |
| Open-line fighting | Two genuine player hits; enemy attacks | Both remain functional |
| World occlusion | Both sides damage through the nearer test wall | Wall blocks both sides; 84 blocked attack samples and 6 firing-input samples |
| Controlled vehicle targeting | Inactive foot actor drives pursuit/damage | Rival follows actual car; attack range uses that car |
| Driving escape | Not exercised by delayed entry | Direct approach reaches18.11 m and pursuit 0 without reset |

The last escape is **brief: one 10 Hz sample**, after which the car reaches the
street boundary and the rival can reacquire it. This establishes the current
distance rule, not sustained or polished escape gameplay. Damage was not observed
beyond the actual controlled actor's 16 m attack range.

The first edit attempt's 70-line replacement exceeded the 65-line selected-edit
budget and was rejected without changing source; a compact local rewrite passed.
Two driving input routes reached only 16.55 m and 17.05 m. The direct approach then
crossed the real 18 m escape threshold, but an extra 0.25 m margin in the diagnostic
incorrectly rejected it. The corrected observer revalidated the original trace;
game thresholds and source were unchanged, and original rejection records remain.
Retry counters remain 3 until a normal successful milestone promotion.

See [sanitized before/after contracts](targeted-contracts.json). Controller
**`941f0a7`** passes 97 CPU tests on both machines. The combined combat/courier route
and accepted walking regression passed. During the following world-collision
regression, the resident supervisor reported **renderer ownership/capacity** and
shut down its model server. The world build finished; its runtime handoff was not
granted. Memory was 148.14 GiB available and swap growth 2.875 MiB; this was not a
memory-pressure stop. The recorded import worker used the Null graphics device.
The supervisor did not record the offending process set, so the exact capacity
event versus a process-ownership race remains unresolved. No automatic restart,
cap change, counter reset or external-process termination was performed.

World runtime, motor, courier, failure/retry regressions and fresh scoped criticism
remain pending after diagnosis. Best accepted playable remains **`81659ed`**.
Actual rival
and explicitly labelled wall-fixture captures are privately saved to Library.
The visible blockout models, flat lighting and missing combat HUD are not final
quality. No public screenshots, new assets or cloud gameplay source were added.

## Original diagnostic

The first combat source, `2d66481`, saved before a replay-output-limit stop at
19:13:46 UTC. No combat native acceptance had run. Accepted courier/retry
checkpoint `81659ed` remained preserved.

A normal-input diagnostic on the accepted courier route measured these defects:

- While driving, the car reached **22.69 m** from the live rival, but pursuit stayed
  at level 3 and health fell from 72 to 40. The inactive foot player remained
  **3.00 m** away and still drove chase/range/pursuit calculations.
- The rival's visible mesh started **0.0157 m** tall and became approximately
  **0.004 m** tall while turning. Its collider remained roughly 1.9 m tall.
  The imported scale and orientation were being overwritten on the gameplay root.
- Static source inspection found player gunfire selecting a rival from all ray
  hits while discarding nearer walls, and enemy attacks applying damage without
  a world-occlusion test. These need paired native verification.

The observation instrument reads actual actors, rival HP/aliveness, renderer
bounds, collision surfaces and distances. It never moves actors or changes HP.
The first diagnostic build is
`989245fec0e819bce92c9312651663dbf78836bf09517a14f482f7e0acaff5f6`.
Its generic runtime PASS is not combat acceptance.

## Focused qualification

Run identical ordinary movement/firing inputs in open and walled native scenes.
The walled run adds one plainly labelled disposable acceptance obstacle between
the actual combatants at seven seconds. It does not move actors or alter signals.
This fixture is controller infrastructure, absent from ordinary game runs and
ineligible for playable checkpoint promotion. Open-line hits and attacks must
work; nearer wall collisions must block both sides.

Local Qwen then makes bounded exact-span corrections to the imported visual
wrapper, pavement height, actual controlled-actor targeting, nearest-hit player
fire and enemy line of sight. Keep existing combat ranges for measurement; no
blind target shifts or threshold loosening. Repeat foot, wall and driving probes.
Only after those pass, run the combined combat/courier route, walking/world/motor,
accepted courier and accepted failure/retry regressions, and fresh scoped critique.
Any concrete contract failure pauses for its actual observations. Preserve the
accepted checkpoint, failure history and unchanged project cap.
