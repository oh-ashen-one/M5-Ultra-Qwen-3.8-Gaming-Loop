# Plan

Status: model warmed and idle; game/agent loop held for launch-plan review. Updated 2026-10-05.

## Acceptance before implementation

Before any future start, agree on the gameplay brief and a fixed acceptance contract. It must define observable outcomes, a representative ten-minute route, controls, failure/restart behavior, visual targets, performance settings, and the evidence required to pass. The coder must not be able to weaken that contract.

One neighborhood with walking, driving, an objective, a pursuit, and an ending is a **discussion proposal**, not an approved mission. The name, setting, map size, narrative, combat scope, traffic density, and exact objective remain open. A larger world is not a substitute for a coherent finished slice.

| Acceptance area | Required future evidence |
| --- | --- |
| First launch | Native build boots; controls are visible; the first meaningful input works |
| Movement and camera | Input-driven walking/running, collision, slopes/steps, animation transitions, camera obstruction and recovery |
| Driving | Vehicle entry/exit, possession, steering/braking, camera handoff, collision, and recovery under real input |
| Mission | Approved objectives, progress, win/fail, ending, and restart in a complete playthrough |
| Pursuit, if approved | Measured sensing/chase/escape transitions and understandable player feedback |
| Presentation | In-engine captures against agreed art targets; no final placeholders; coherent sound mix |
| Performance | Declared hardware, resolution and quality settings; frame times, lows and hitches in representative and demanding views |
| Provenance | Local/cloud/human contribution ledger, source/license records, reproducible build and evidence tied to commit IDs |

A suggested performance target is 60 fps, subject to the approved resolution, quality settings, and hardware verification. No frame-rate or quality result has been measured for this project.

## Phases and exits

1. **Preparation and launch-plan review — current phase.** The prior benchmark campaign is closed. The owner selected Unity CLI/C# and Qwen BF16, authorized its data download and a short warm-up, and then held game generation for review. The model is now verified, warm and idle. Agree on the brief, settings, acceptance contract and bounded run before the explicit game start. No engine or asset generation has begun.
2. **Qualification.** In a session-owned project, pin versions and verify local model identity, edit tools, context retrieval, engine adapter, export path, resource budget, and recovery behavior. Deliberately broken fixtures must make the acceptance harness fail before it is trusted.
3. **Playable foundation.** Build a small input-driven movement/driving slice with camera handoff and collision. Temporary graybox assets are allowed. Verify behavior and capture actual gameplay before adding more systems.
4. **Visual target and asset pilot.** Agree on art direction. Process one representative character, vehicle, and environment asset through Meshy, Blender, and the engine; validate animation, material response, collision, scale, and performance before a larger batch.
5. **Approved mission and presentation.** Integrate the selected mission, NPC behavior, ending/restart, custom art, animation, lighting, and audio. Keep every earlier acceptance gate passing.
6. **Critique and polish.** Review rendered playthroughs; resolve three to five prioritized findings per round through small stories and permanent regression checks. Promote only candidates that pass the full contract.
7. **Delivery.** Provide the playable native build, editable art sources where redistributable, license/provenance manifest, complete playthrough evidence, build instructions, and known limitations. Record all cloud rescue contributions and unresolved defects.

Phase exits require evidence and a checkpoint record. Human taste reviews are especially valuable at brief approval, the first asset pilot, and final acceptance; automation must not silently advance an unresolved decision.

## Bounded future run

The proposed 8–72 hours is an initial planning envelope, not permission for an endless loop. At start, set wall-clock, iteration, retry, disk, memory, renderer, and any paid-service budgets. If more time is needed, produce a checkpoint and reassess the scope and budget. Watchdogs must not keep creating new budgets after exhaustion.

Two repeated failures with the same proven cause trigger diagnosis. After two interventions on one story, split/re-spec it or pause; continued retries are not progress. Acceptance failures never become passes merely because a deadline expired.

## Decisions needed before start

- Exact Unity release/render pipeline, native export target, license and physics/test/capture adapters.
- Approve the [audited BF16 runtime settings](RUNTIME-READINESS.md), working context/output/thinking budgets and functional tools/vision qualification. The loaded artifact and runtime are pinned; no fastest-runtime claim is made.
- Approved mission, art direction, controls, camera feel, driving style, audio scope, and content budget.
- How to measure the local coding share and how to authorize/disclose rescue coding.
- Exact dependencies and licenses, GPU/process ownership, acceptance-harness location, and stop/recovery policy.

See [Decisions](DECISIONS.md) and [Reuse catalog](REUSE-CATALOG.md).
