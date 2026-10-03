# M5 Ultra Qwen 3.8 Gaming Loop

**Status: planning, research and licensed source preparation. No game-development loop has started.**

An open-source plan for a local-first coding loop that aims to produce a polished, roughly ten-minute playable urban action/driving game. The intended workload is Qwen3.8 27B on the requested M5 Ultra configuration: 256 GB memory and 80 GPU cores. That configuration, the exact model artifact, and its runtime remain to be verified before a future run.

The game should evoke the movement, driving, camera, atmosphere, and mission flow of a GTA5-style experience while using original content and custom Meshy/Blender assets. This is a small playable slice, with no promise of AAA parity. Native Godot or Unity is the goal; a browser build is a fallback.

## Start boundary

The future game run comes **after the existing M5 tests and a separate, explicit user instruction to start**. The initial 8–72-hour window is a planning range, subject to an agreed budget and stop conditions. Time alone is never a completion criterion.

This repository contains documentation and a small, attributed set of unintegrated source references. Publishing or copying source does not authorize model inference, benchmark changes, installations, engine execution, paid generation, or changes to another active project. There is no runnable game, development-loop automation, or asset bundle.

## What success should mean

- A player can discover the controls, play the approved ten-minute experience, reach its ending, and restart reliably.
- Movement, driving, camera transitions, art, animation, lighting, and audio receive real gameplay review. Programmer art is acceptable during development, not final acceptance.
- About 90% of actual gameplay coding is the local-model goal. Cloud criticism and limited rescue coding are allowed and disclosed. The accounting method must be agreed before the run; a token share is not a coding share.
- External acceptance gates, rendered playthroughs, and known-good Git checkpoints determine progress. A green log line or compilation alone cannot establish playability.

## Proposed architecture

One controller coordinates mostly sequential local planner, coder, and tester contexts. It supplies exact source context, mediates edits, runs protected acceptance checks, records provenance, and promotes only verified checkpoints. A frontier critic reviews actual gameplay evidence and returns three to five prioritized fixes. See [Architecture](docs/ARCHITECTURE.md).

Godot is the current recommendation, with Unity still open. A single agent harness, Blender MCP, and one engine adapter form the proposed lean tooling stack. None of the candidates has been installed or qualified together for this project.

The [source references](reference/README.md) include selected MIT diagnostic, input, camera and vehicle code with pinned refs, checksums and full notices. They are preparation for later qualification, not an integrated game. The [NPC plan](docs/NPC-ARCHITECTURE.md) specifies distinct persistent NPC memories and relationships on a shared backend, and discloses remote runtime brains separately from local Qwen development.

## Navigation

| Document | Purpose |
| --- | --- |
| [Plan](docs/PLAN.md) | Acceptance-first phases, start gate, unresolved choices |
| [Architecture](docs/ARCHITECTURE.md) | Context, edit boundaries, verification, recovery, provenance |
| [Prior attempts](docs/PRIOR-ATTEMPTS.md) | Pinned static evidence and limits on success claims |
| [Asset pipeline](docs/ASSET-PIPELINE.md) | Meshy → Blender → engine, including rigs and animation |
| [Reuse catalog](docs/REUSE-CATALOG.md) | Prior user projects and external code/tool candidates |
| [Source references](reference/README.md) | Exact imported files, manifest, notices and integration gaps |
| [Dependency pins](docs/DEPENDENCY-PINS.json) | Framework refs only; nothing installed |
| [NPC architecture](docs/NPC-ARCHITECTURE.md) | Legal async decisions, persistent memory, costs and video evidence |
| [Horror concept](docs/concepts/TOWERING-MONSTER-INVESTIGATION.md) | Separate original monster-investigation discussion |
| [Decisions](docs/DECISIONS.md) | Confirmed requirements, recommendations, open decisions |
| [Third-party notices](THIRD_PARTY_NOTICES.md) | Attribution, component licensing, import policy |

## License and publication scope

[MIT](LICENSE) covers original project material. Third-party components retain their own notices and licenses. Selected MIT source is listed in the [import manifest](reference/IMPORT-MANIFEST.json); no third-party art, audio, model weights or demo assets are included. The root license does not relicense upstream material or generated assets.

Public records contain research summaries, decisions, plans, and sanitized evidence. Credentials, private conversations, hidden reasoning, private operational records, and machine-specific paths do not belong here.
