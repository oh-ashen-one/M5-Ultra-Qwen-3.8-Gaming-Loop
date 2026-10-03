# Reuse catalog

Research snapshot: 2026-10-03. Star counts are rounded discovery signals, not evidence of suitability. Primary repository metadata, license texts, and documentation informed this list. Versions below are upstream documentary claims or research observations; **nothing is installed, executed, or qualified together for this project**. Recheck exact releases, files, licenses, and compatibility before import.

## Prior user projects

| Public source | Candidate reuse | License and limits |
| --- | --- | --- |
| [ralph-loop-playbook](https://github.com/oh-ashen-one/ralph-loop-playbook) | Failure lessons, overseer diagnostic packets, bounded supervision, story/checkpoint ideas | MIT. Review helpers and write fences; see [pinned findings](PRIOR-ATTEMPTS.md). Replace marker replay with mediated edits. |
| [slop-of-tsushima-qwen](https://github.com/oh-ashen-one/slop-of-tsushima-qwen) | Character integration lessons and evidence about missing context | Repository MIT metadata; audit asset-level rights independently. No existing art imported. |
| [grindline](https://github.com/oh-ashen-one/grindline) | Real input/physics simulation bridge and acceptance patterns | [License text](https://github.com/oh-ashen-one/grindline/blob/2c0932270778ee1392f72d9815860987b0b4080c/LICENSE): code MIT; asset notices separate, described as CC0. `NOASSERTION` metadata was resolved by reading the text. Builder lineage includes `ox-alpha` and human management. |
| [space-salvage](https://github.com/oh-ashen-one/space-salvage) | Godot wrappers, capture, progress and loop-supervision patterns | [License text](https://github.com/oh-ashen-one/space-salvage/blob/172474406bd2801676a3189595c17a3475724945/LICENSE): code MIT; art/audio/fonts separately described as CC0. Gate reliability still needs deliberate red tests. |

Authorized private-source research is not a public dependency or evidence bundle. No private repository content is included in this initial commit. Publishable lessons are expressed as general acceptance requirements rather than private logs.

## Agent and engine tooling

The proposed lean stack is **one harness + Blender MCP + one engine adapter**. OpenCode is the harness recommendation for qualification, not a final dependency selection. Keep Git checkpoints and protected acceptance gates regardless of harness choice.

| Candidate | Approx. stars | License | Proposed use and qualification limits |
| --- | --- | --- | --- |
| [OpenCode](https://github.com/anomalyco/opencode) | 212k | MIT | Local OpenAI-compatible provider, role permissions, tool calls and session API. Verify the exact model's tool behavior. [Providers](https://opencode.ai/docs/providers/), [agents](https://opencode.ai/docs/agents/), and [server](https://opencode.ai/docs/server/) document these interfaces. Persistence/revert does not prove exactly-once workflow execution. |
| [MCP for Blender](https://github.com/ahujasid/mcp-for-blender) | 30k | MIT | Scene/material/Python work, viewport inspection and export. Upstream requirements include Blender 3+, Python 3.10+ and `uv`. Separate Meshy step; qualify permissions, safe mode, and telemetry controls. |
| [Godot MCP](https://github.com/Coding-Solo/godot-mcp) | 5.9k | MIT | Narrow editor/project/debug adapter. Requires installed Godot and Node 18+; UID features require Godot 4.4+. Not an autonomous input-driven playtester. Metadata shows a last push in April 2026; inspect maintenance and version support. |
| [Unity MCP](https://github.com/CoplayDev/unity-mcp) | 14.7k | MIT | Alternative if Unity is selected: scenes/C#, tests, profiling and build tooling. Upstream documents Unity 2021.3 LTS–6.x and Python 3.10+. README recommends pinning `v10.0.0` for that release; qualify a pinned release rather than moving `beta`. |
| [LangGraph](https://github.com/langchain-ai/langgraph) | 42.7k | MIT | Deferred orchestration candidate if recovery/state needs justify it. Not a default dependency; avoid stacking frameworks. |

## Godot gameplay candidates

| Candidate | Approx. stars | License distinction | Potential use and limitations |
| --- | --- | --- | --- |
| [GDQuest third-person controller](https://github.com/gdquest-demos/godot-4-3d-third-person-controller) | 1k | [MIT code/resources; CC BY-NC-SA 4.0 textures/models](https://github.com/gdquest-demos/godot-4-3d-third-person-controller/blob/main/LICENSE) | Movement and camera-relative shooter foundation. Research observed a Godot 4.7 project. **Code-only candidate: replace demo art with custom Meshy/Blender work.** No driving, city or police system supplied. |
| [Phantom Camera](https://github.com/ramokz/phantom-camera) | 3.6k | MIT | Follow/spring-arm/damped camera transitions. Documents Godot 4.4+; research identified a 4.7.1 fix in release 0.11.0.3. Deliberately retain or replace the starter camera; do not stack conflicting controllers. |
| [Easy Vehicle Physics](https://github.com/DAShoe1/Godot-Easy-Vehicle-Physics) | 400 | MIT code; demo Kenney Car Kit has separate CC0 attribution | Raycast arcade driving, keyboard preset and steering assists; Godot 4.2+, GodotPhysics/Jolt documented. Test the recommended 120 Hz physics rate and frame budget. Vehicle entry/exit, AI driving, damage and pursuit remain integration work. |
| [Godot Road Generator](https://github.com/TheDuckCow/godot-road-generator) | 1.2k | MIT | Roads/intersections/lane curves and RoadLaneAgent; custom meshes possible. Godot 4.4+ documented; research identified release 0.9.4. Feature-incomplete: procedural intersection lane/edge support is pending. Authored intersections are preferable initially; traffic logic is not supplied. |
| [LimboAI](https://github.com/limbonaut/limboai) | 3k | MIT code; logo/demo art CC BY 4.0 | Behavior trees/state machines for NPCs, not a ready-made wanted system. Research identified 1.8.1; 1.8.x GDExtension documents Godot 4.6+, module builds target 4.7. Pin a compatible extension; no custom engine build proposed initially. |
| [Questify](https://github.com/TheWalruzz/godot-questify) | 250 | MIT | Mission graphs/state/signals/save. Godot 4 project; research observed a 4.5 example. Validate chosen-engine compatibility. A tiny custom state machine may be simpler for one short mission. |
| [Godot demo projects](https://github.com/godotengine/godot-demo-projects/tree/master/3d/navigation) | 9.6k for collection | MIT code; inspect individual asset notices | Built-in navigation examples. Select a stable-version branch: `master` tracks upcoming development. Not a city simulation package. |

First integration proposal: GDQuest code, Easy Vehicle Physics, small authored roads, built-in navigation, and a tiny mission state machine. Add Phantom Camera, LimboAI or Questify only when a concrete requirement justifies them. Qwen should write the gameplay integration: possession, camera handoff, mission triggers, sensing/chase/escape where approved, failure and restart.

## Unity alternative and exclusion

[OpenKCC](https://github.com/nicholas-maltbie/OpenKCC) (~800 stars, MIT) is a Unity controller candidate with third-person/Cinemachine, foot IK and navigation examples. Its documentation names a Unity 2023.1.6f1 demo; research identified a 1.5 release. Unity 6 compatibility is unverified. Resolve this only if Unity is selected.

[SanAndreasUnity](https://github.com/in0finite/SanAndreasUnity) (~2.6k stars) is excluded as the production base. MIT engine code does not grant rights to original game data; its README requires an owned GTA installation. This project plans original assets and a small original game.

## Import checklist for the future

Select only the needed component; pin repository/ref and hashes; inspect the exact license and file-level exceptions; retain upstream notices; record modifications and transitive dependencies; replace restricted art; prove engine/API compatibility and a red/green acceptance test. A link in this catalog is not permission to copy a whole repository or a claim that it works in this stack.
