# Prior attempts: evidence and limits

Reviewed 2026-10-03. The findings below are **static source observations**. No legacy runner, game, test, or model was executed during this repository's creation. They describe specific revisions, not every later version of a project.

## Verified public source findings

| Source | Static observation | Consequence for this design |
| --- | --- | --- |
| [ralph-loop-playbook: source snapshot](https://github.com/oh-ashen-one/ralph-loop-playbook/blob/11f068df8fd2c260d7490adf300dff5cc7067821/reference/qwen_iteration.py#L625) | Tree/source collection excludes every path containing a `scripts` directory. `file_snapshot` skips files over 80,000 bytes and limits accumulated source text to 55,000 characters. It lists some omitted files but cannot supply their integration code. | Exact retrieval and explicit omissions; do not assume an allowlisted file is fully present. The 55,000 limit is characters, not measured tokens. |
| [ralph-loop-playbook: strip helper](https://github.com/oh-ashen-one/ralph-loop-playbook/blob/11f068df8fd2c260d7490adf300dff5cc7067821/reference/strip_markers.py) and [writer state](https://github.com/oh-ashen-one/ralph-loop-playbook/blob/11f068df8fd2c260d7490adf300dff5cc7067821/reference/qwen_iteration.py#L41) | The helper imports `write_files` in a fresh process and replays the saved reply. The imported module starts with empty allowlist/protection state; the writer applies those checks only when populated. The helper does not initialize the current story's restrictions. | Static evidence of a mutation path that can bypass story-specific fences. Not exploited or executed here. Every helper must enforce the same permissions; acceptance must not rewrite gameplay. |
| [slop-of-tsushima-qwen: RoninRig](https://github.com/oh-ashen-one/slop-of-tsushima-qwen/blob/24ebe66c4acb73071aa0734df3bcbecca0a39b93/src/player/rig/RoninRig.js#L1) | The module comment defers player wiring because a 101 KB `Player.js` was absent from that agent's snapshot. It describes integration steps rather than establishing their completion. | An asset loader can exist without appearing in gameplay. Assert the actual rig and animation in the rendered input path. |
| [grindline: simulation bridge](https://github.com/oh-ashen-one/grindline/blob/2c0932270778ee1392f72d9815860987b0b4080c/game/sim/sim_bridge.gd#L384) | The bridge injects real keyboard/gamepad events, advances physics frames, and records assertion results. | A promising input/physics testing pattern; port only after API/license review and deliberate red tests. Its existence is not proof of this future game's acceptance. |
| [grindline: README](https://github.com/oh-ashen-one/grindline/blob/2c0932270778ee1392f72d9815860987b0b4080c/README.md) | The account identifies an `ox-alpha` builder and human specifications/judgment. | Attribute that lineage accurately. It is not evidence of an unattended Qwen-only run. |
| [space-salvage: Godot wrappers](https://github.com/oh-ashen-one/space-salvage/tree/172474406bd2801676a3189595c17a3475724945/scripts/ralph/godot) | The source tree contains parse/simulation/test wrappers and capture tooling, plus progress/supervisor files in its parent directory. | Reuse candidates, not trusted gates. Audit exit/error propagation, test isolation, and resource ownership before use. |

The [failure catalog](https://github.com/oh-ashen-one/ralph-loop-playbook/blob/11f068df8fd2c260d7490adf300dff5cc7067821/FAILURES.md) and [overseer directory](https://github.com/oh-ashen-one/ralph-loop-playbook/tree/11f068df8fd2c260d7490adf300dff5cc7067821/overseer) are useful research sources for bounded retries, diagnostic packets, and supervision. Their scripts are not copied into this commit.

## Claims that remain unverified

Earlier reviews reported false green outcomes from grep-style gates and success sentinels coexisting with engine errors. This initial public record does not reproduce those outcomes or publish private verification logs. Treat them as test-design warnings: a sentinel must not override parse/autoload errors, nonzero exits, absent assertions, or a broken playthrough.

No claim is made here that prior projects achieved the proposed ten-minute experience, 90% local coding share, target frame rate, chosen quantization speed, or unattended quality on the requested M5 Ultra configuration. Those need new, attributable evidence tied to the future run.

## Lessons adopted

1. Context selection is part of correctness: integration cannot be completed against unseen source.
2. Verification must observe behavior and actual rendered play, not file presence or matching strings.
3. The external judge must be immutable to every coder mutation path, including helpers.
4. Preserve useful ideas and attribution; do not inherit historical success claims or trust scripts without red tests.
5. Human/cloud assistance and asset authorship must be visible in provenance.
