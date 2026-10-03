# Decisions

Updated 2026-10-03. Requirement, recommendation, and unresolved choice are separate states.

## Confirmed requirements

| Requirement | Interpretation |
| --- | --- |
| New public open-source repository | Owner `oh-ashen-one`; display title **M5 Ultra Qwen 3.8 Gaming Loop**; publish original research/planning and appropriately attributed reuse |
| Planning first | Existing M5 tests finish before a future game run; separate explicit user start required |
| Local model goal | Requested Qwen3.8 27B and M5 Ultra 256 GB / 80 GPU configuration; verify actual model/hardware/runtime before execution |
| Sustained future iteration | Initial 8–72-hour planning window or further agreed time needed; bounded budgets and stop criteria |
| Majority of gameplay coding local | About 90% goal; cloud critic and some rescue coding allowed, logged and disclosed |
| Playable quality | Roughly ten-minute GTA5-style urban action/driving experience with original content; no AAA parity promise |
| Native engine priority | Godot or Unity CLI; browser fallback only |
| Custom art pipeline | Meshy 3D assets plus Blender MCP cleanup, rigging and animation; polished movement, driving, camera, art, lighting and audio |
| Reuse prior work | Learn from and selectively reuse authorized Ralph/game projects; do not copy private repositories wholesale |
| Public scope | User-facing research, concise decision rationale, architecture and planning; exclude private chat, hidden reasoning, credentials and private operational records |

## Current recommendations

- **Engine: Godot.** A promising fit for a small native slice, scripted tooling and prior Godot test patterns. Unity remains an alternative; this is not a finalized engine choice or a measured comparison.
- **Harness: OpenCode for qualification**, Blender MCP, and one engine adapter. Use mediated edits, external acceptance and Git checkpoints. Do not adopt a second orchestration framework without a concrete need.
- **Gameplay foundation:** third-person code, arcade vehicle physics, authored roads, built-in navigation, small mission state machine. Add optional camera/AI/quest packages only after identifying the integration need.
- **Quality loop:** mostly sequential local roles; real rendered playthroughs; frontier critic returns three to five prioritized fixes; bounded retries and known-good promotion.
- **Licensing:** MIT for original project material; per-component/asset/model licensing remains separate.

## Open choices

| Choice | Evidence needed to resolve it |
| --- | --- |
| Godot vs Unity and exact version | Export/adapter/dependency compatibility, workflow friction, input/rendered QA, performance qualification |
| Model artifact/runtime/quant/context | Existing M5 test results, exact loaded model identity, license, tool-use reliability and resource budget |
| Final game design | User-approved brief and acceptance route; neighborhood/walk-drive-objective-pursuit-ending is only a proposal |
| Visual/audio direction | Approved references, asset pilot and budget; no default theme or provider silently selected |
| Local contribution accounting | Defined scope and primary metric, mixed-edit handling, rescue classification and evidence ledger |
| Dependencies | Exact refs/licenses and red/green qualification; catalog popularity is not compatibility proof |
| Run budgets and recovery | Agreed duration, iteration/retry limits, resource ownership, paid-service budget and stop/resume conditions |
| Delivery target | Supported native platform(s), build format, controls, resolution, quality settings and acceptance signoff |

## Decision record convention

Future entries record date, decision status, concise user-facing rationale, alternatives considered where useful, supporting evidence, and effect on the acceptance contract. A proposed choice becomes confirmed only through explicit approval or verified evidence within an already authorized scope. Do not paste private conversations or hidden reasoning into the record.

The initial documentation publication is complete planning work; it is not a game start decision.
