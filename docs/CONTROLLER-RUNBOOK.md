# Chicago controller runbook

The owner authorized the full Chicago run after qualification. The execution controller is the sole game owner. Parent dot already supplies 30-minute oversight; no additional cloud schedule is created. Native qualification is a disposable infrastructure test, not a Chicago game result.

## What runs

`tools/game_loop.py` coordinates one resident Flash-Next model, with separate private planner, builder and critic histories. The builder writes original C# and Blender Python through canonical path and full-file hash checks. Blender can write only its assigned art output and scratch directories. Editable `.blend` sources live under `game/ArtSources`; only FBX and texture exports enter Unity Assets. This prevents Unity from launching redundant Blender conversions.

The controller builds a native macOS Unity app using a separate protected harness. It replays application input, samples actual transforms and gameplay signals, and captures the running camera. A fresh critic sees labeled target images, actual captures and trusted gate results, without builder reasoning. Only a mechanical pass plus a fresh critic PASS promotes a checkpoint. Rejected candidates and immutable evidence are retained.

SQLite WAL/FULL records actions, role usage, candidates and accepted commits. An interrupted action is reconciled without blindly replaying engine work. Resume preserves unfinished edits in Git. Three identical failures allow one restoration of the owned game directory to an accepted checkpoint; another such failure pauses with a readable blocker. Other projects are outside the controller's ownership.

## Bounds

- One model request at a time; one task-owned engine at a time. The loaded idle model yields shared engine admission and resumes after the engine exits.
- 65,536 conservative working-context bound, including image allowance and up to 16,384 output tokens; native runtime context remains 262,144. Output budget includes thinking.
- Thinking/xhigh and preserved private role reasoning; temperature 1, top-p .95, top-k 20. MTP, DFlash and KV quantization disabled.
- Initial ceiling: 12 hours, 96 candidates, 16 builder tool-response turns per session, 120 minutes without accepted progress, three identical failures, one rollback.
- At least 64 GiB available memory, no more than 512 MiB positive swap growth, at least 100 GiB free disk. Genuine runtime faults pause work; no automatic model restart.

## Operator commands

Use the qualified M5 runtime Python and private configuration. These are placeholders, not literal machine paths:

```sh
python -B tools/game_loop.py run --run-dir "$RUN_DIR" --config "$PRIVATE_CONFIG" --brief docs/CHICAGO-BRIEF.md --authorize-game-start
python -B tools/game_loop.py status --run-dir "$RUN_DIR"
python -B tools/game_loop.py stop --run-dir "$RUN_DIR"
python -B tools/game_loop.py resume --run-dir "$RUN_DIR" --config "$PRIVATE_CONFIG" --brief docs/CHICAGO-BRIEF.md --authorize-game-start
```

`status.json`, `PROGRESS.md` and `progress.html` show the current task, heartbeat, memory, accepted coverage, candidate, captures and blocker. `state.sqlite3` retains the action/event ledger. Private session histories and raw logs remain outside the public repository. Check the actual process and model status before resuming; a stale status file is not evidence of liveness.

`tools/checkpoint_publisher.py` transports only the configured `game/chicago-*` branch through the controller's existing GitHub and SSH authentication. It does not manage game work, force-push, merge main or copy credentials to the M5. Its receipt reports the last remotely verified published commit. Publication failure leaves local commits intact.

## Qualified and still unverified

Thirteen CPU fixtures cover stale/escaping edits, interrupted writes, durable process-exit state, evidence corruption, invalid replay, input-gate red cases, interrupted candidate preservation and bounded rollback. Actual native Unity green/red, scoped Blender export, coordinated model handoff, Flash-Next hash-checked editing and fresh known-failure criticism passed; see the [receipts](../diagnostics/controller-2026-10-05/README.md).

The disposable walking test does not prove a game exists, driving/combat/mission completeness, polished art, rigs/animation, collision correctness, audio, HUD or sustained performance. Runtime camera captures omit screen-space overlay HUD. Game-owned event signals are cooperative instrumentation, not an adversarial proof against arbitrary in-process C#. The external harness and source files are write-protected during execution; their observations still require review. Whole-game critique must disclose missing evidence rather than infer it from screenshots. Parent review and eventual human play remain necessary for final quality claims.

All cloud code in this branch is disclosed controller, acceptance or disposable fixture infrastructure. Substantive Chicago C#/Blender work belongs to local Qwen. The five Library visual target images are available privately on both machines and are not published. Original generated game assets retain per-asset provenance; no upstream art is imported.

## Context rotation correction — 2026-10-05 07:11 UTC oversight

The initial controller stopped after three context-limited roles despite saving new source/exports in each. The correction records partial source checkpoints and continues with fresh private role contexts. This is not test acceptance: known-playable checkpoints still require the same native gate and critic, and the 120-minute no-accepted-progress bound remains. Three bounded roles with no source/art change still stop for diagnosis. Existing engine/critic failure counters are preserved; the specifically diagnosed legacy builder-context classification is migrated once with an explicit event. New integration guidance prioritizes original player art and Bootstrap/movement/camera code once reusable environment exports exist. Sixteen CPU tests now cover these distinctions and the one-time migration.
