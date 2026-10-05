# Verified limited foundation and vehicle follow-through

**Completed bounded scope:** foundation, forward vehicle entry/driving/exit mechanics, and a readable grounded exit view are verified separately. Final game source/metadata is [`754dd595`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/754dd5956cb5a24c18507aef638c29c4781baa53); the final gameplay edit is [`da0e0e6`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/da0e0e6eb12673a324f87bb68dd350bda13d17db). The controller stopped cleanly after the original walking regression passed. **42 CPU tests pass on both machines.** All gameplay edits came from local Qwen; cloud work supplied controller/test infrastructure, measured supervision and evidence metadata. No full game checkpoint is accepted.

At **11:56:27 UTC**, the fresh bounded attempt accepted **foundation-short-walk**. This is a development milestone: grounded control, readable third-person camera, the actual blue coupe, and continuously visible paving along the short tested walk. The Chicago art target and complete ten-minute game remain unmet.

## Saved local edit and actual native result

Local Qwen instantiated an original sidewalk mesh/material as `Pavement` in [`155b420`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/155b4201863a45e3739d659cf7f96e0cc6c030e7). Native measurements caught swapped imported axes: the first candidate was only 0.14 m wide and 7 m tall. It failed the new surface-coverage check despite passing grounded walking. The failed candidate and evidence remain preserved.

The next direct local request changed **one scale assignment**, retaining the imported rotation and original mesh/material. Source [`142f7e0`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/142f7e0ee87840a50a5074dad7fa206c39e2e82e) saves that correction. The request used thinking-enabled `low` effort, **1,050 completion tokens**, and **27.29 seconds**. No planning request or cloud gameplay-code substitution was used.

The corrected surface spans X **−1 to 6 m**, Z **−2 to 30 m**, with its top near Y **0.14 m**. The [native gate](foundation/grounding-gate.json) records successful compilation/execution, four frames, stationary grounding, and **18.971 m horizontal movement**. The [surface check](foundation/pavement-coverage.json) covers **124 of 124** settled walking samples, including the player's 0.32 m radius; **zero** samples are uncovered.

| Actual replay image | Observation |
| --- | --- |
| [Start](foundation/frame-000.png) | Existing upright facade and player, with the added paved apron visible. |
| [Middle](foundation/frame-001.png) | Existing blue coupe remains visibly rendered beside continuous paving. |
| [End](foundation/frame-003.png) | Player remains over grey pavement where the previous candidate ended over brown background. |

A [fresh scoped local critic](foundation/scoped-critic.json) returned PASS using **1,169 completion tokens / 30.95 seconds**, at `xhigh`. Cloud supervision independently viewed the three actual frames. Remaining rough character geometry, fencing, facade materials and overall composition are visible and remain final-quality work. These camera captures do not establish HUD, audio or FPS.

The explicit limited milestone is committed at [`6f112fd`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/6f112fde19e86eae6c7b77bfd47fadd7584ed60a), separately from final game acceptance. Its metadata attributes game code to local Qwen and evidence bookkeeping to the cloud controller. Source/capture identity and hashes are in the [manifest](foundation/manifest.json).

## Preserved failures and bounds

The original local pavement response completed a tool call with 3,760 output tokens in 89.99 seconds, but supplied 15 lines against a 14-line save limit. The exact submitted local code was recovered with a 16-line allowance and committed-source/hash checks; no new inference or cloud rewrite was used. Future direct pavement requests allow 20 lines. The subsequent one-line axis repair came from actual failed native measurements. Neither failure received progress credit.

The earlier paused run is preserved. The fresh attempt began at **11:47:40 UTC**, has an unchanged **12:47:40 UTC** ceiling, and stops after 20 minutes without a newly verified subfeature. Foundation acceptance starts that new run's verified-progress window; it does not rewrite any previous run or set final acceptance. See [the acceptance policy](../../docs/SUBFEATURE-ACCEPTANCE.md). The one-hour bound remains subordinate to the original 21:37:50 UTC overall ceiling.

## Vehicle result and important rejected candidates

Local Qwen created `VehicleInteraction.cs`, corrected the input read to the real edge-triggered API, and invoked installation from Bootstrap. It implements proximity-based E entry, W/S movement, A/D steering code and E exit with restored walking. The native scenario exercises W/S and entry/exit; steering feel and obstacle handling are not established by that straight replay.

The first replay moved the car 16.34 m and received a local critic PASS, but cloud inspection found the visual nose opposed travel and the longer return walk left the pavement. Runtime front/rear bumper measurements confirmed alignment **−1**. The [original result was superseded](vehicle/superseded-first-result.json), and its progress credit was withdrawn. A local visual-yaw correction preserved imported tilt/scale while aligning the car's nose with motion. The explicitly shortened drive tests the existing bounded street; it does not prove a longer route.

Further actual frames found exit occlusion by a pillar, then by the facade. Local selected edits moved the exit to the clear side and faced the player along the corridor, leaving camera code unchanged. One native test also caught a 30 cm exit spawn lift; a final local assignment reduced it to near the controller skin width. The coverage threshold was not relaxed. These failed candidates and reviews remain in the run record.

The [final native vehicle gate](vehicle/grounding-gate.json) passes with **10.639 m** movement and forward alignment approximately **+1**. [Observed E transitions](vehicle/trace-summary.json) enter at about 7.16 s and exit at 12.07 s; the player resumes grounded walking. All **102/102** checked foot samples remain over pavement with radius clearance. The [fresh scoped exit critic](vehicle/scoped-critic.json) passes, and cloud supervision independently viewed the actual exit and return frames.

| Actual vehicle capture | What it establishes |
| --- | --- |
| [Approach](vehicle/frame-001.png) | Same original coupe near the player before entry. |
| [Driving](vehicle/frame-002.png) | Actual running vehicle view; movement/direction come from the trace and bumper measurements. |
| [Exit](vehicle/frame-003.png) | Character visibly standing beside the car on pavement, with an open view along the street. |
| [Return to walking](vehicle/frame-004.png) | Character clearly visible and still on paving after exit. |

After vehicle integration, the **original** short-walk replay passed again at final HEAD: [stationary grounding and 18.960 m movement](final-walk/grounding-gate.json), with [125/125 pavement-covered samples](final-walk/pavement-coverage.json). [Start](final-walk/captures/frame-000.png) and [end](final-walk/captures/frame-003.png) are actual regression frames. The safe request accounting, distinct milestone records, superseded result, unchanged prior-record verification and final idle status are in [the closeout](run-closeout.json).

## Remaining work and handoff

The bounded owner is stopped with scope complete; the resident model is healthy and idle, and the owner's separate Blender remains preserved. The old ledger and its expired deadline were not rewritten. The fresh 12:47:40 UTC ceiling was not extended. Milestones refresh only the new run's verified-subfeature clock; final acceptance remains separate.

Next work is actual horizontal obstacle/collision handling, steering/braking qualification and camera transition robustness, then the original HUD/audio, combat/pursuit and mission plan. The current vehicle module translates its root and raycasts the ground; it does not implement horizontal obstacle resolution. No final handling, sound, FPS, damage, animation or ten-minute playthrough is claimed. The rough character, fencing, materials, lighting and overall Chicago composition still require substantial work against the private visual targets. The clear straight route does not establish robust camera behavior throughout the scene.
