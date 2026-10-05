# Framing output-budget diagnosis and repair

The owner authorized diagnosis of six capped coding requests, a supported task-appropriate reasoning setting, one or two small local edits followed by native frames, and adaptive continuation after actual progress. The successful physics checkpoint `43e336c` and all prior failures remain in history.

## What the capped requests actually returned

The six requests exhausted exactly 2,048 or 4,096 completion tokens. Each returned `finish_reason: length`, zero parsed tool calls, no separate reasoning field, and no closing thinking or tool-call markers. The returned text retokenized to the same total as the reported completion count. Because the actual generation template opens a thinking block, this is consistent with truncation before completing thinking; the server does **not** provide an authoritative separate reasoning-token total for these requests.

The [CPU-only audit](token-and-settings-audit.json) records counts without exporting private text. It executes the installed oMLX settings-merge helpers and renders the pinned template using an inert fixture. The resident default is `xhigh`, with no forced template keys. Request-level `low`, `medium`, and `xhigh` all override that default correctly while keeping thinking and history preservation enabled. Template SHA-256: `c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041`.

## Actual local edit and native result

The next request received only the exact camera class, its single selected offset assignment, measured world bounds, and a save-first instruction. It used **thinking enabled, effort `low`, and an 8,192-token ceiling**. The local model saved one line on its first request:

| Request | Actual completion tokens | Time | Outcome |
| --- | ---: | ---: | --- |
| Local camera editor, `low` | 1,102 | 27.89 s | `tool_calls`; saved edit `ok: true` |
| Independent framing critic, `xhigh` | 1,029 | 25.06 s | `tool_calls`; narrow framing PASS |

For the editor, the parsed reasoning field retokenized to 1,050 tokens. Retokenized field/argument counts are diagnostics and need not sum exactly to the server's completion total. The experiment also narrowed the task and increased the ceiling; it does not isolate reasoning effort as the sole cause of improvement.

[Game candidate `a840e65`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/blob/a840e659528b5c42917dd4e66e09e680853b2814/game/Assets/Game/Bootstrap.cs) changes only the camera offset's Z sign. [Native compilation and stationary/walking checks pass](gate.json): four real frames, 134 samples, **18.965 m horizontal movement**, and **0.158 m initial settling**. The unit upright physics root and approximately 1.57 m visual are retained.

The actual [stationary frame](frame-000.png) is outside the facade; the [post-walk frame](frame-003.png) retains a visible building. The [fresh local critic passed this narrow framing bar](framing-review.json). Cloud spot review agrees that obstruction improved, but the visible sidewalk ends well before the walking route; the remaining empty ground, art, animation, gameplay, audio and performance are unfinished. **No full game task or finished scene is accepted.**

## Adaptive continuation

The continuing controller uses `xhigh` planning/critique and thinking-enabled `low` elementary editing, explicitly recorded on each request. Existing edits select at most two old lines and save at most four lines. Plans request one assignment or one call, with measured world bounds, rather than a grid or repeated-object task. An unsaved coding request or invalid planning session stops for diagnosis without an identical automatic retry. Real source progress clears only the no-source-progress streak; it does not reset the no-accepted-game-progress deadline or promote a checkpoint.

The first continuation exposed an additional interface defect: planner fields lacked explicit enum choices, so valid small intentions arrived with unsupported values such as `edit` and `replace_line`. Three failed planning sessions were preserved. Controller `a19fb8d` publishes the exact allowed enum values, gives field-specific errors, and stops after one invalid planning session. **34 CPU tests pass on both machines.**

After that correction, the next local `xhigh` planner returned a valid assignment on its first request (**1,182 completion tokens / 31.43 s**); the `low` editor saved it immediately (**112 tokens / 4.08 s**). Candidate `1ddec8b682259ae1a0add25139a711f5f8e506ca` passed [actual native testing](continuation-native.json): stationary grounding, four frames, 137 samples and **19.032 m** horizontal walking. The broader fresh `xhigh` critic correctly returned **FIX** for missing HUD/minimap and street elements, unfinished environment, and unevidenced performance/collision/audio requirements. This full-task verdict is separate from the earlier narrow framing PASS.

At **10:53 UTC**, the same sole owner had advanced into its next local planning job with no blocker. All earlier requests remain preserved; the original 21:37:50 UTC ceiling and two-hour no-accepted-progress bound are unchanged. All substantive game edits remain local-Qwen authored.
