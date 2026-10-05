# Verified limited foundation and vehicle follow-through

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

## Next microtasks

After the foundation milestone, the same sole controller started local-Qwen vehicle-module authoring, followed by native walking regression, explicit component integration, and input-driven entry/driving/exit testing. This launch statement does not claim vehicle success. Consult the current handoff for the actual latest result. The final game checkpoint remains unaccepted.
