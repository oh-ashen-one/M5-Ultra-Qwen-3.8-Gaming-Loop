# M5 Ultra Qwen 3.8 Gaming Loop

**Status, 2026-10-05 13:01 UTC: continuous local game queue running.** One owner is working on collision from preserved baseline `754dd595`, then automatically advances through reset, mission/failure/retry, combat/pursuit/HUD/audio and whole-route polish after scoped passes. **49 controller tests pass on both machines.** The original overall deadline remains **21:37:50 UTC**. See [queue behavior and evidence limits](docs/CONTINUOUS-QUEUE.md). No new collision or whole-game PASS is claimed by this launch status.

The accepted baseline includes continuous paving, proximity entry, **10.639 m forward driving**, and a visibly grounded exit/return walk. Its original walking regression passed **18.960 m**, with **125/125** sampled positions over pavement. The tag `baseline/walk-drive-20261005` preserves it. Chicago-target quality, robust collision/handling and the complete ten-minute game remain unfinished. See [actual baseline frames and rejected candidates](diagnostics/subfeatures-2026-10-05/README.md) and [separate subfeature/final acceptance](docs/SUBFEATURE-ACCEPTANCE.md).

An open-source plan for a local-first coding loop that aims to produce a polished, roughly ten-minute playable urban action/driving game. The M5 Ultra was verified with 256 GB memory and 80 GPU cores. The selected model is now `mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp`, pinned and loaded through isolated oMLX 0.6.4. See [current readiness](docs/FLASH-NEXT-READINESS.md) for exact settings, evidence and launch blockers. Earlier 27B BF16 records are historical.

The game should evoke the movement, driving, camera, atmosphere, and mission flow of a GTA5-style experience while using original content. Local Qwen must author every eventual 3D model, material, rig and animation from scratch through Blender. No Meshy, Tripo or premade asset packs. This is a small playable slice, with no promise of AAA parity. Native Unity CLI/C# is selected; a browser build is a fallback.

## Start boundary

The existing M5 tests are closed. The owner subsequently authorized implementing the controller, qualifying it, and starting the full Chicago run autonomously. [The consolidated brief](docs/CHICAGO-BRIEF.md) is authoritative. The initial controller has a 12-hour wall-clock bound with bounded failure recovery; time and round counts never imply completion. Parent dot supplies the existing 30-minute oversight schedule.

This repository contains documentation, a durable serial controller, native Unity/Blender adapters, bounded diagnostic tools, descriptions of private Chicago visual targets and a small attributed set of source references. Actual game code/art comes from local Qwen on a separate game branch. Public progress must distinguish controller qualification, generated targets and actual game evidence.

## What success should mean

- A player can discover the controls, play the approved ten-minute experience, reach its ending, and restart reliably.
- Movement, driving, camera transitions, art, animation, lighting, and audio receive real gameplay review. Programmer art is acceptable during development, not final acceptance.
- About 90% of actual gameplay coding is the local-model goal. Local Qwen supplies planning, coding and fresh visual critique. Codex supplies intelligent cloud supervision and transparent spot reviews/interventions. Any separately approved cloud rescue code is disclosed. A token share is not a coding share.
- External acceptance gates, rendered playthroughs, and known-good Git checkpoints determine progress. A green log line or compilation alone cannot establish playability.

## Proposed architecture

Parent midir manages project direction and approvals; the execution lead performs approved work and reports evidence and blockers. Separate, serial local Qwen planner, coder, tester and visual-critic contexts receive exact context and mediated tools. Protected acceptance checks govern checkpoint promotion. A fresh local critic returns three to five prioritized fixes from actual gameplay evidence; disclosed cloud supervision can spot-review and escalate. See [Architecture](docs/ARCHITECTURE.md).

The owner selected native Unity CLI/C# with local Blender tools. Unity 6000.6.4f1 native compilation, Metal play, input replay and real captures pass with active editor licensing. The first controller uses the Built-in Render Pipeline and fixed CLI adapters. Live Editor Pipeline/MCP is not required by this route and remains unqualified. Godot references remain useful design lessons.

The [source references](reference/README.md) include selected MIT diagnostic, input, camera and vehicle code with pinned refs, checksums and full notices. They are preparation for later qualification, not an integrated game. The [NPC plan](docs/NPC-ARCHITECTURE.md) specifies distinct persistent NPC memories and relationships on a shared backend, and discloses remote runtime brains separately from local Qwen development.

## Navigation

| Document | Purpose |
| --- | --- |
| [Plan](docs/PLAN.md) | Acceptance-first phases, start gate, unresolved choices |
| [Architecture](docs/ARCHITECTURE.md) | Context, edit boundaries, verification, recovery, provenance |
| [Prior attempts](docs/PRIOR-ATTEMPTS.md) | Pinned static evidence and limits on success claims |
| [Asset pipeline](docs/ASSET-PIPELINE.md) | Local Qwen → original Blender models/materials/rigs/animation → Unity |
| [Reuse catalog](docs/REUSE-CATALOG.md) | Prior user projects and external code/tool candidates |
| [Source references](reference/README.md) | Exact imported files, manifest, notices and integration gaps |
| [Dependency pins](docs/DEPENDENCY-PINS.json) | Framework refs only; nothing installed |
| [Current runtime readiness](docs/FLASH-NEXT-READINESS.md) | Flash-Next/oMLX settings, warm-up, read-only monitoring and overnight launch blockers |
| [Flash-Next evidence](diagnostics/flash-next-2026-10-05/README.md) | Fresh image/tool round trip and actual oMLX settings fixtures |
| [Historical BF16 readiness](docs/RUNTIME-READINESS.md) | Earlier model/runtime qualification, superseded by Flash-Next |
| [Connector evidence](diagnostics/connector-2026-10-05/README.md) | Earlier file/shell, original Blender and vision results |
| [Post-reboot qualification](diagnostics/unity-2026-10-04/README.md) | Actual Unity/C# import, Metal frame, Qwen recognition and current setup distinctions |
| [Unity installation](docs/UNITY-INSTALL.md) | Original official installation record and link to the later qualified editor |
| [NPC architecture](docs/NPC-ARCHITECTURE.md) | Legal async decisions, persistent memory, costs and video evidence |
| [Horror concept](docs/concepts/TOWERING-MONSTER-INVESTIGATION.md) | Separate original monster-investigation discussion |
| [Decisions](docs/DECISIONS.md) | Confirmed requirements, recommendations, open decisions |
| [Third-party notices](THIRD_PARTY_NOTICES.md) | Attribution, component licensing, import policy |

## License and publication scope

[MIT](LICENSE) covers original project material. Third-party components retain their own notices and licenses. Selected MIT source is listed in the [import manifest](reference/IMPORT-MANIFEST.json); no third-party art, audio, model weights or demo assets are included. The root license does not relicense upstream material or generated assets.

Public records contain research summaries, decisions, plans, and sanitized evidence. Credentials, private conversations, hidden reasoning, private operational records, and machine-specific paths do not belong here.
