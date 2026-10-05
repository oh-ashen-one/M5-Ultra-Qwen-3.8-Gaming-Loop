# M5 Ultra Qwen 3.8 Gaming Loop

**Status: Qwen BF16 verified, warmed and resident on the M5. Disposable connector qualification is authorized; game development remains held for readiness review.**

An open-source plan for a local-first coding loop that aims to produce a polished, roughly ten-minute playable urban action/driving game. The M5 Ultra was verified with 256 GB memory and 80 GPU cores. Qwen3.8 27B BF16 is pinned and loaded through the installed MLX-VLM 0.7.4 runtime. See [runtime readiness](docs/RUNTIME-READINESS.md) for exact evidence and remaining qualification.

The game should evoke the movement, driving, camera, atmosphere, and mission flow of a GTA5-style experience while using original content. Local Qwen must author every eventual 3D model, material, rig and animation from scratch through Blender. No Meshy, Tripo or premade asset packs. This is a small playable slice, with no promise of AAA parity. Native Unity CLI/C# is selected; a browser build is a fallback.

## Start boundary

The existing M5 tests are closed. The owner authorized model preparation and a short warm-up, while requiring review of the launch plan before the game/agent loop starts. The initial 8–72-hour window is a planning range, subject to an agreed budget and stop conditions. Time alone is never a completion criterion.

This repository contains documentation, bounded preparation/diagnostic tools and a small attributed set of unintegrated source references. There is no runnable game or development loop. The current authorization covers one BF16 model and a small disposable connector test, including original test geometry and available engine qualification. It does not start the game-generation loop or authorize installations or paid services.

## What success should mean

- A player can discover the controls, play the approved ten-minute experience, reach its ending, and restart reliably.
- Movement, driving, camera transitions, art, animation, lighting, and audio receive real gameplay review. Programmer art is acceptable during development, not final acceptance.
- About 90% of actual gameplay coding is the local-model goal. Local Qwen supplies planning, coding and fresh visual critique. Codex supplies intelligent cloud supervision and transparent spot reviews/interventions. Any separately approved cloud rescue code is disclosed. A token share is not a coding share.
- External acceptance gates, rendered playthroughs, and known-good Git checkpoints determine progress. A green log line or compilation alone cannot establish playability.

## Proposed architecture

Parent midir manages project direction and approvals; the execution lead performs approved work and reports evidence and blockers. Separate, serial local Qwen planner, coder, tester and visual-critic contexts receive exact context and mediated tools. Protected acceptance checks govern checkpoint promotion. A fresh local critic returns three to five prioritized fixes from actual gameplay evidence; disclosed cloud supervision can spot-review and escalate. See [Architecture](docs/ARCHITECTURE.md).

The owner selected native Unity CLI/C# for the initial game, with local Blender tools as needed. The exact Unity release, render pipeline, licensing and adapter remain to be qualified; no Unity editor was found on the M5. Godot source references remain useful lessons, not an integrated Unity foundation.

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
| [Runtime readiness](docs/RUNTIME-READINESS.md) | Pinned BF16, exact settings audit, warm-up and remaining launch gates |
| [Connector evidence](diagnostics/connector-2026-10-05/README.md) | Actual file/shell, original Blender and vision results; Unity/MCP blockers |
| [Unity installation](docs/UNITY-INSTALL.md) | Verified Hub installation, selected LTS package and user sign-in/admin/license gates |
| [NPC architecture](docs/NPC-ARCHITECTURE.md) | Legal async decisions, persistent memory, costs and video evidence |
| [Horror concept](docs/concepts/TOWERING-MONSTER-INVESTIGATION.md) | Separate original monster-investigation discussion |
| [Decisions](docs/DECISIONS.md) | Confirmed requirements, recommendations, open decisions |
| [Third-party notices](THIRD_PARTY_NOTICES.md) | Attribution, component licensing, import policy |

## License and publication scope

[MIT](LICENSE) covers original project material. Third-party components retain their own notices and licenses. Selected MIT source is listed in the [import manifest](reference/IMPORT-MANIFEST.json); no third-party art, audio, model weights or demo assets are included. The root license does not relicense upstream material or generated assets.

Public records contain research summaries, decisions, plans, and sanitized evidence. Credentials, private conversations, hidden reasoning, private operational records, and machine-specific paths do not belong here.
