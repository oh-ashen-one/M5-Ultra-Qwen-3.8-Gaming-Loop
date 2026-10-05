# Decisions

Updated 2026-10-05. Requirement, recommendation, and unresolved choice are separate states. The dated operational update below supersedes earlier engine/model-role recommendations.

## Confirmed requirements

| Requirement | Interpretation |
| --- | --- |
| New public open-source repository | Owner `oh-ashen-one`; display title **M5 Ultra Qwen 3.8 Gaming Loop**; publish original research/planning and appropriately attributed reuse |
| Planning first | Benchmarks are closed; game/agent loop held for launch-plan and settings review; download/load/short warm-up authorized separately |
| Local model goal | Qwen3.8 27B BF16 on verified M5 Ultra 256 GB / 80 GPU; one resident model, serial roles and explicit thinking |
| Sustained future iteration | Initial 8–72-hour planning window or further agreed time needed; bounded budgets and stop criteria |
| Majority of gameplay coding local | About 90% goal; substantive planning/coding/fresh visual critique local; intelligent Codex supervision and disclosed spot reviews; separately approved rescue code accounted independently |
| Playable quality | Roughly ten-minute GTA5-style urban action/driving experience with original content; no AAA parity promise |
| Native engine priority | Unity CLI/C# selected for initial game; browser fallback only |
| Custom art pipeline | Meshy 3D assets plus Blender MCP cleanup, rigging and animation; polished movement, driving, camera, art, lighting and audio |
| Reuse prior work | Learn from and selectively reuse authorized Ralph/game projects; do not copy private repositories wholesale |
| Persistent model-powered NPCs | Distinct identity, permitted observations, factual memories and player relationships per NPC; cheap Chinese/GPT models or Jev candidates may share one backend |
| Honest video claims | Disclose local development versus cloud NPC runtime inference; record observed state, actions, memory changes, latency, costs and fallbacks |
| Public scope | User-facing research, concise decision rationale, architecture and planning; exclude private chat, hidden reasoning, credentials and private operational records |

## Current recommendations

- **Engine: Unity CLI/C# selected by the owner on October 5.** Exact release, render pipeline, license and adapters remain open. The earlier Godot recommendation is historical.
- **Harness: OpenCode for qualification**, Blender MCP, and one engine adapter. Use mediated edits, external acceptance and Git checkpoints. Do not adopt a second orchestration framework without a concrete need.
- **Gameplay foundation:** third-person code, arcade vehicle physics, authored roads, built-in navigation, small mission state machine. Add optional camera/AI/quest packages only after identifying the integration need.
- **Quality loop:** serial local roles and fresh local visual criticism; Codex management reviews evidence and progress; bounded retries and known-good promotion.
- **Licensing:** MIT for original project material; per-component/asset/model licensing remains separate.

## Open choices

| Choice | Evidence needed to resolve it |
| --- | --- |
| Exact Unity version/pipeline/license | Export/adapter compatibility, input/rendered QA and runtime qualification |
| Working runtime settings/context | Pinned BF16 and installed MLX-VLM audited; native vision/tool execution still requires functional qualification and budget review |
| Final game design | User-approved brief and acceptance route; neighborhood/walk-drive-objective-pursuit-ending is only a proposal |
| Visual/audio direction | Approved references, asset pilot and budget; no default theme or provider silently selected |
| Local contribution accounting | Defined scope and primary metric, mixed-edit handling, rescue classification and evidence ledger |
| Dependencies | Exact refs/licenses and red/green qualification; catalog popularity is not compatibility proof |
| Run budgets and recovery | Agreed duration, iteration/retry limits, resource ownership, paid-service budget and stop/resume conditions |
| Delivery target | Supported native platform(s), build format, controls, resolution, quality settings and acceptance signoff |

## Decision record convention

Future entries record date, decision status, concise user-facing rationale, alternatives considered where useful, supporting evidence, and effect on the acceptance contract. A proposed choice becomes confirmed only through explicit approval or verified evidence within an already authorized scope. Do not paste private conversations or hidden reasoning into the record.

The initial documentation publication is complete planning work; it is not a game start decision.

## Source reuse update: 2026-10-03

Bounded, attributed source preparation is authorized. The [import manifest](../reference/IMPORT-MANIFEST.json) includes selected MIT source and excerpts; it does not finalize Godot or qualify runtime behavior. Frameworks are pinned references only. The [NPC architecture](NPC-ARCHITECTURE.md) now includes persistent factual memory and relationships, with provider candidates and dated illustrative prices. No provider is selected or connected.

The [towering-monster investigation note](concepts/TOWERING-MONSTER-INVESTIGATION.md) is a separate original horror concept, not a replacement for the local-loop game scope. Other game/video projects are outside this repository's implementation scope. The explicit-start hold remains in force.

## Operational update: 2026-10-05

The owner retired the closed benchmark campaign's automatic-inference prohibition for future local-model work. Historical counters, actual errors and closeout remain untouched. New errors and the shared renderer/security rules still apply.

The exact BF16 revision, hardware, installed runtime and settings were audited. The owner then authorized one model load and a short warm-up, which completed with `READY` and returned reasoning content. The model remains idle; the separate game/agent-loop review hold remains in force. No TensorFold, DFlash, quantized replacement, Unity launch, Blender launch, paid generation or main merge was performed.

This Codex thread owns intelligent cloud supervision. Its exact model identifier is not exposed in the task context; do not assume Astra. Local Qwen remains the substantive game worker and fresh critic after start. See [runtime evidence](RUNTIME-READINESS.md).
