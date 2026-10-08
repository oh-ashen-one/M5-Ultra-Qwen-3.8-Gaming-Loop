# M5 Ultra Qwen 3.8 Gaming Loop

**Status: completed research experiment, October 2026.** Development is finished and the source is preserved. We produced a rough original Chicago action/driving prototype. The polished ten-minute target was not established, and the standalone keyboard/mouse test remains unresolved.

## What we did

We tested a locally running Qwen model building a native 3D game through a durable edit/build/test loop, original Blender assets, rendered feedback and disclosed cloud supervision.

The prototype includes walking, car entry/driving/exit, collision, combat, pursuit, health/reset, HUD and basic audio. Its route includes courier delivery, a dead drop, relay activation, moving interception and a Counter-Exfil incident with real shooting, maintained physical car obstruction and a foot exit.

Local Qwen authored substantive gameplay and original Blender character/clothing, rig/animation, coupe, street/building geometry, materials and props. Editable scripts, `.blend` files, textures and FBX exports are in [game](game/). Codex authored orchestration, acceptance tools, diagnostics, manual-window tooling, summaries and disclosed mechanical restorations. The approximately 90% local-coding goal was not established as an audited percentage.

## What we were testing

| Area | Result and limits |
| --- | --- |
| Local model workflow | Serial planner/coder/critic roles, exact scoped source, mediated edits, checkpoints and bounded recovery. Code saves and elapsed time alone did not count as acceptance. |
| Unity/Blender pipeline | Native compilation, original asset export/import, Metal rendering and source-linked captures worked. |
| Gameplay | Input-driven routes, walking/car interaction, mission mechanics, physical obstruction, escape/contact/reset/death negatives and prior regressions passed at scoped milestones. |
| Animation and presentation | Native motion/held-aim continuity, boarding/seat fit, roof/feet clearance, wheel/material properties and parcel contact were checked. Overall art remains coarse. |
| Map breadth | Ordinary-input tours covered connected outdoor areas. A tour timeout banner does not prove a successful mission ending. |
| Lighting and parcel | Modest lighting improvements and a lowered carried-parcel position were retained. The bright parcel still crowds the reticle. |
| Brick/asphalt refinements | Both local material passes were exported, rendered and reviewed, then rejected for insufficient useful visual benefit and restored exactly. |
| Standalone window | A presentation-only build enabled resizing and windowed play. Compilation and actual window resizing succeeded. |
| Physical keyboard/mouse | **Unresolved.** The owner reported unresponsive controls. A normal macOS relaunch and bounded diagnostic did not establish a fix. Automated replay is not physical-input qualification. |

[The completed report](docs/COMPLETED-EXPERIMENT.md) records exact checkpoints, native bindings, rejected passes and the manual-input findings.

## Final saved state

- Current kept game source: [`c4f43907e2bf8eeceb86274dc9c984c029f154fa`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/c4f43907e2bf8eeceb86274dc9c984c029f154fa).
- Accepted gameplay fallback: [`de0b3360fa7d7a1722aa981ee4dbf3a1c223ccd7`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/de0b3360fa7d7a1722aa981ee4dbf3a1c223ccd7).
- Final restored native build SHA-256: `3a6113539f34c2baee9271e54a783c995801acb8137908a89917751586b275e0`.

The final kept source passed an 18-second carry/contact check and 125-second map replay. Three matched native PNGs exactly equaled the kept baseline. Imported geometry/material/image/slot/tangent properties and all 1,402 lighting observations matched. This verifies restoration and preservation; it does not mean every historical negative case was freshly rerun on that commit.

The accepted Counter-Exfil route completed at 114.433 seconds, with a 124-second replay including reset checks. The intended polished, varied ten-minute experience was not established. Character/car silhouettes, surfaces, animation, camera transitions, audio and scene composition still need work.

## Environment

Development ran on a verified M5 Ultra with 256 GB memory and 80 GPU cores. The selected model was `mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp`, with thinking/xhigh, serial requests and pinned configuration. The later runtime was oMLX 0.7.0; Unity was 6000.6.4f1 and Blender 5.2.0. The game uses Unity's Built-in Render Pipeline.

This was a bounded three-day development experiment, not a claim of continuous inference for three days. The cap ended October 8, 2026 at **2:33:12 a.m. EDT (06:33:12 UTC)**. The automatic operation and owned model/engine/controller processes stopped beforehand. Later requested manual window/input diagnostics were separate walkthrough work and did not restart autonomous development.

## Inspect or build

The completed branch contains the saved game and closeout; historical `main` contains earlier planning:

```sh
git clone --branch completed/chicago-experiment-20261008 \
  https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop.git
cd M5-Ultra-Qwen-3.8-Gaming-Loop
```

Open `game` with the matching Unity editor. The game initializes through an external bootstrap harness rather than a hand-authored scene. [Manual-player instructions and tooling](tools/manual-play/README.md) explain how to prepare the bootstrap and build a resizable macOS player. That fresh-clone recipe was not requalified during this publication; there is no packaged player download here.

Intended controls: WASD to walk/drive, E to enter/exit the car, F for context actions, left-click to fire, R to reset. The camera follows the player; free mouse-look was not implemented. Read the unresolved physical-input result before treating this as a ready-to-play release.

## Research, provenance and license

See [architecture](docs/ARCHITECTURE.md), [original brief](docs/CHICAGO-BRIEF.md), [prior attempts](docs/PRIOR-ATTEMPTS.md), [reuse catalog](docs/REUSE-CATALOG.md), [game provenance](game/Notes/CONTROLLER-PROVENANCE.md) and per-asset provenance alongside the Blender sources.

Original project material uses [MIT](LICENSE). [Third-party notices](THIRD_PARTY_NOTICES.md) retain upstream attribution and component-specific terms. Runtime/model weights are not bundled.

This closeout adds source tooling and sanitized research summaries. Private conversations, hidden reasoning, credentials, machine routing/operational paths, raw private logs, native recordings and screenshots remain outside the public snapshot. Earlier plans are historical; this README and the completed report describe the final outcome.
