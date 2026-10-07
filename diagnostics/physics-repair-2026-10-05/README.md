# Fresh measured physics repair

Parent management authorized a new bounded attempt after the prior diagnostic window expired. It began at **09:37:50 UTC**, with a **30-minute repair deadline at 10:07:50 UTC**. The expired run, its original captures and its measured transform defects remain untouched.

The model receives only a selected source span and relevant measurements. The controller enforces the full-file read hash, unique span identity, replacement-size limits and preservation of unselected code. Original visual dimensions must be retained: the player visual is approximately 1.57 m tall even though the misplaced CharacterController inherited a 100× transform. Game edits remain local-Qwen authored; cloud work is controller infrastructure, measured diagnosis and task instructions. No new art is enabled.

Two initial selected-block requests saved nothing: finish reason `length`, 2,048 / 4,096 completion tokens, 48.21 / 95.34 seconds. These failed requests remain in the new ledger. The same repair then decomposed the work into six elementary selected-line edits: empty unit physics root, original visual attachment, measured visual feet alignment, independent ground, ground height and spawn. Each stage permits at most two requests; the original repair deadline is unchanged. Every saved edit is immediately checkpointed, including incomplete candidates.

The native check has a four-second no-input lead-in. Stationary measurements precede screenshot readback and WASD. It requires an upright unit-scale controlled root, stable Y and observed grounding, then real horizontal walking and native frames. A fresh local critic must also see a readable existing street/building and visible upright player. At most three native repair checks are admitted.

After actual grounded control qualifies, the owner has authorized continuation of the original game plan using small read-backed C# edits. Framing is still assessed from actual images, and a FIX verdict remains a required task rather than a successful scene acceptance. The overall ceiling is 12 hours from this run's start, with existing no-accepted-progress and repeated-failure safeguards. A mechanical grounded checkpoint is separate from acceptance of the larger game tasks; no completion claim follows from time, tokens or compilation.

Twenty-six CPU tests pass, including stale/ambiguous/oversized selected-edit rejection and stationary-grounding red cases. Current machine-local status and exact tool action results govern live progress. See [prior measured evidence](../recovery-2026-10-05/README.md) for the diagnosis.

## 09:50 UTC: actual grounded control passes; framing still fails

All six elementary edits completed on their first requests with `finish_reason: tool_calls` and `source-edit: ok`. Their completion-token / elapsed-second pairs were: unit root **294 / 7.89**, visual attachment **720 / 16.27**, feet alignment **111 / 2.90**, independent ground **160 / 3.96**, ground height **380 / 8.79**, spawn **283 / 6.68**. Each edit was checkpointed.

The first build rejected an unqualified `Instantiate` call. Local Qwen then made small span corrections, producing [candidate 43e336c](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/blob/43e336c30e90ed5c1ed56f5af3142368dd2586eb/game/Assets/Game/Bootstrap.cs). The next native build and [grounding gate](grounding-2/gate.json) passed: **23 stationary samples**, `grounded: true`, unchanged player Y approximately **0.135 m**, scale **[1,1,1]**, up **[0,1,0]**, then **19.014 m** horizontal movement. The measured visual height remains approximately **1.57 m**. See [world observations](grounding-2/world-observations.json).

Actual [stationary](grounding-2/frame-000.png) and [post-walk](grounding-2/frame-003.png) frames still fail framing: the initial view is obstructed and the moved player stands against an empty background. The [fresh local critic returned FIX](grounding-2/framing-review.json), asking for readable existing street/building geometry along the walking path. This is a grounded mechanical candidate, not a qualified framing or game checkpoint.

The framing coder called an unavailable `read_line_count` tool, which had previously halted the controller. The adapter now returns a bounded error listing the available tools and explains that `read_file` already supplies `total_lines`; no unsupported tool is executed. Twenty-seven CPU tests pass, including this recovery case. The same repair resumed at 09:56 UTC with one native check remaining and its original 10:07:50 UTC deadline unchanged. No new art or cloud-authored game code was introduced.

## 10:08 UTC: continue the authorized game from proven grounded control

The final repair check again passed stationary grounding and native walking on the same saved candidate, with **18.985 m** horizontal movement. Framing remained **FIX**: a 4,096-token framing edit request had ended with `length` and no source change. This failure is preserved; the repeated native check does not count as a visual success.

The parent's explicit instruction was to continue the game loop once basic grounded control passed. Grounding qualified within the repair window, so the game phase now continues under the existing **21:37:50 UTC overall ceiling**, with the original two-hour no-accepted-progress bound and other safeguards. The repair deadline was not extended and no whole-game checkpoint was accepted. The prior operational plan's extra requirement to clear framing before continuing work has been removed; framing remains the first unresolved task and still blocks acceptance.

Each continuing job now separates a **local-Qwen micro-plan** (at most eight selected existing lines, a goal of at most 40 words) from a **local-Qwen edit** (at most 12 replacement lines). Exact read hashes protect every edit. Every changed candidate gets native testing and actual rendered critique; source is checkpointed even when a task or budget fails. Both planning and game code stay local. No new art tools are enabled.

## 10:18 UTC: controller handoff repair

The first continuation's local planner returned a valid plan, but a controller logging call passed two values for `kind`. That `TypeError` stopped the run before a game edit. The stopped attempt and its successful model requests remain recorded. Controller commit `99158a0` distinguishes the event type from the plan kind and adds a regression that exercises a local plan through actual hash-checked edit dispatch. All **28 CPU tests pass on both machines**.

The same run resumed with no new owner, ledger, deadline or acceptance claim. A real local planner has selected an existing-street instancing change; the selected-span local editor is active. The run's recorded continuation condition now explicitly reflects the owner's authorization: mechanical grounding qualifies continuation, while framing FIX remains required game work. This clarification preserves the old condition in the event ledger.

## 10:27 UTC: continuation stops at its configured no-progress limit

The controller paused at **10:26:41 UTC** after **three consecutive jobs saved no source**. Each local planner returned a valid short selection, but the requested changes still described street tiling rather than a single elementary assignment. All six selected-span coding requests ended with `finish_reason: length`; no partial tool call was executed. The two request timings per job were **46.83 / 95.96 s**, **46.38 / 94.25 s**, and **46.40 / 94.99 s**, with **2,048 / 4,096 completion tokens** per pair. The [sanitized action receipt](tool-outcomes.json) contains exact request and saved-edit outcomes without private prompts or reasoning.

The source remains `43e336c30e90ed5c1ed56f5af3142368dd2586eb`. The [second native grounding result](grounding-3.json) confirms stable grounding and 18.985 m walking, while its independent rendered review remains FIX. There is **no accepted full game task**. The eight successful earlier source edits and all failed requests/candidates remain preserved; no duplicate build was run for these unchanged continuation candidates.

At **10:27:19 UTC**, no controller or owned engine remained. The existing model was healthy, with zero active/queued requests; the latest resource sample showed **88.26 GiB available** and **zero swap growth**. The separate Blender process was preserved. Hashes of the previous expired run's status and ledger still match. The original repair deadline, two-hour no-accepted-progress bound and 21:37:50 UTC overall ceiling were not extended or reset.

The next diagnosis should reduce the semantic task to a single camera assignment or one existing-object placement, supplying exact observed world bounds and the selected code. A short selected span alone did not make the tiling task elementary. This is a proposed correction to orchestration, not a claim that the untested framing fix works.
