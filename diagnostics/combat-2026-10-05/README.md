# Combat qualification

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
