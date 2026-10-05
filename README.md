# M5 Ultra Qwen 3.8 Gaming Loop

**Status: Qwen3.8 Flash-Next is loaded, warmed and idle on the M5. Image recognition and a tool-call round trip pass. The overnight game controller is not implemented; game development remains held.**

An open-source plan for a local-first coding loop that aims to produce a polished, roughly ten-minute playable urban action/driving game. The M5 Ultra was verified with 256 GB memory and 80 GPU cores. The selected model is now `mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp`, pinned and loaded through isolated oMLX 0.6.4. See [current readiness](docs/FLASH-NEXT-READINESS.md) for exact settings, evidence and launch blockers. Earlier 27B BF16 records are historical.

The game should evoke the movement, driving, camera, atmosphere, and mission flow of a GTA5-style experience while using original content. Local Qwen must author every eventual 3D model, material, rig and animation from scratch through Blender. No Meshy, Tripo or premade asset packs. This is a small playable slice, with no promise of AAA parity. Native Unity CLI/C# is selected; a browser build is a fallback.

## Start boundary

The existing M5 tests are closed. The owner authorized model preparation and a short warm-up, while requiring review of the launch plan before the game/agent loop starts. The initial 8–72-hour window is a planning range, subject to an agreed budget and stop conditions. Time alone is never a completion criterion.

This repository contains documentation, bounded preparation/diagnostic tools and a small attributed set of unintegrated source references. There is no runnable game or development loop. The owner authorized model replacement, permanent deletion of 15 old variants, compatible runtime setup, warm-up and readiness review, following earlier Unity and connector qualification. Game-generation and paid production services remain separate from this preparation.

## What success should mean

- A player can discover the controls, play the approved ten-minute experience, reach its ending, and restart reliably.
- Movement, driving, camera transitions, art, animation, lighting, and audio receive real gameplay review. Programmer art is acceptable during development, not final acceptance.
- About 90% of actual gameplay coding is the local-model goal. Local Qwen supplies planning, coding and fresh visual critique. Codex supplies intelligent cloud supervision and transparent spot reviews/interventions. Any separately approved cloud rescue code is disclosed. A token share is not a coding share.
- External acceptance gates, rendered playthroughs, and known-good Git checkpoints determine progress. A green log line or compilation alone cannot establish playability.

## Proposed architecture

Parent midir manages project direction and approvals; the execution lead performs approved work and reports evidence and blockers. Separate, serial local Qwen planner, coder, tester and visual-critic contexts receive exact context and mediated tools. Protected acceptance checks govern checkpoint promotion. A fresh local critic returns three to five prioritized fixes from actual gameplay evidence; disclosed cloud supervision can spot-review and escalate. See [Architecture](docs/ARCHITECTURE.md).

The owner selected native Unity CLI/C# for the initial game, with local Blender tools as needed. Unity 6000.6.4f1 import, C# compilation and Metal rendering passed with active editor licensing. The production render pipeline, game adapter and live Editor Pipeline/MCP remain unqualified. Godot source references remain useful lessons for the planned Unity implementation.

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
