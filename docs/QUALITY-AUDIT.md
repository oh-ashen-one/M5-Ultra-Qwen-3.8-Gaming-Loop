# Measured quality audit

Audit date: 2026-10-06. This is an audit of the existing local run, not a model benchmark. The visible output remains below the requested standard. The evidence does not isolate intrinsic model capability from the authoring and review workflow.

## Model and execution

The loaded model is `mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp`, revision `e171af86f499f1855b0fb71d781105e8dd609610`, on official oMLX 0.6.4, runtime commit `1d7826185c5b5b69b38b27cbe57d7597b7551fd7`. Health reports one loaded vision-language model. Thinking and history preservation are enabled; planner/critic default to `xhigh`, while authorized small edits use `low`. MTP, KV quantization and APC are disabled. Sampling is temperature 1.0, top-p 0.95, top-k 20, min-p 0, repetition penalty 1 and presence penalty 0. No evidence in this audit shows an accidental replacement model, disabled vision or disabled thinking.

The runtime context is 262,144 tokens; the controller working bound is 65,536, including output and a conservative image allowance. The usual output cap is 8,192, shared by thinking and the answer. These distinct limits must not be described as equivalent.

## What the model sees

Actual PNG bytes are attached to model requests, with hashes recorded separately. Native screenshot criticism is real. However, attaching an image does not prove that every feature was understood.

The current recovery ledger records 158 builder sessions: 18 have image attachments and 140 do not. It records 33 critic sessions with 154 image attachments. Across all recorded roles, target attachment occurrences are neighborhood 21, driving 4, combat 10 and night 1; the river reference has zero occurrences. These are attachment records, not counts of unique images or proof of completed inference for every session. They cover this recovery ledger, not the earlier foundation run.

All five references are not supplied together. Typical visual authoring selects one relevant target. Recent small code edits are text-only. The moving-encounter critic receives four actual native frames and no target reference; its prompt explicitly leaves broad character/street quality unfinished. Thus a scoped mechanical or presentation PASS does not enforce the requested overall visual standard. This is a workflow gap, not evidence that the model has matched the references.

## Budgets and effort allocation

The recovery ledger contains 615 model-request records, of which 612 are complete and three historical records remain pending. Output-limit stops total 35: 17 builder, 16 replay author, one critic and one planner. Seven context-budget stops are recorded. Truncated tool fragments are not executed.

The same ledger records five Blender export actions, 137 source-edit actions and 13 source-create actions. These counts show the imbalance toward code and verification; they do not provide a defensible wall-time percentage for infrastructure versus art. Builder tokens also include thinking and tool interaction, not only authored content. Earlier small output caps and overly strict tool validators caused documented lost work; see the [framing diagnosis](../diagnostics/framing-budget-2026-10-05/README.md).

## Why the art remains rough

Four original Blender scripts generate the street, coupe, props and player, then export FBX for Unity. The 101-line character script builds boxes and low-resolution spheres with simple materials. It uses parented animation pivots, not an armature with skin weights or authored animation clips. The inspected asset inventory contains those four generated FBX files and no texture or animation assets of the inspected types. This is a simple procedural character pipeline, not a completed production character pipeline.

Recent mission work clones those existing meshes. Small facade, material and HUD repairs cannot by themselves create the reference images' density, anatomy, material detail, animation and lighting. Camera crowding compounds the asset problems. The next visual priority is a local-authored camera/aim readability repair, compared at the same native positions, while retaining actual hit, cover, movement, driving and reset checks.

## Concrete orchestration defect

The authorized coexistence policy removes the veto based merely on open application count, but the older shared admission helper still rejects any holder record and reserves both capture slots when another renderer is present. Actual observation found one free capture slot and no measured memory, swap-growth or thermal guard violation while Qwen waited. This is an admission-policy mismatch, not measured proof of inadequate hardware. Preserve real slot locks, exclusive performance reservations and other jobs when repairing it; never bypass actual resource or ownership safeguards.

The evidence supports improving the workflow and assets before attributing the poor result solely to the model. It does not establish that this model can achieve the requested final quality. No model change, download or benchmark is implied by this audit.
