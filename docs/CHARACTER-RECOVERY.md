# Character artifact recovery and decode investigation

Measured snapshot: 2026-10-06 21:16:32 UTC. This is an existing game run, not a new model benchmark. The original overall deadline remains October 8 at 06:33:12 UTC.

## Broad authoring attempt: no artifact

Round q0127's character/camera request ended at 21:03:29 UTC after **4,117.70 seconds (68 minutes 38 seconds)**. Its prompt used 11,098 tokens; generation exhausted all 16,384 output tokens with `finish_reason=length`. No parsed tool call, saved character source, Blender export or new native preview resulted. Game source remained `c9aa15bdb02f0e81edd04c50598a28dc6092ae00`; broad accepted checkpoint remained `c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188`.

The response, role history and failure outcome are preserved privately. Structural inspection found no complete authoring artifact. A runtime putting truncated text in `message.content` does not make it a completed final answer or authorize extracting code from private reasoning. The exact response hash is pinned by the recovery guard. Advancing token counters established liveness, not useful progress. The watchdog exited normally when the response arrived and issued no signal.

## Focused recovery: pending

Controller revision [2d0dd5a](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/2d0dd5a0ae16d24b106d20cbc53494b215a0e0c2) was deployed at the completed-request boundary. Its three focused CPU tests passed on both hosts. Round q0128 started at **21:06:42 UTC**, using the same resident model and saved game state; there was no reload or identical broad retry.

The local author receives the complete existing `Art/player.py`, the exact Unity import/placement excerpt, one neighborhood target and one real native before frame. Both image deliveries have byte/hash receipts. This is one complete character-source submission through `finish_source(content)`, with medium thinking, a 4,963-token prompt and an 8,192-token output cap. C# remains protected. The supplied Unity placement offset must be accounted for so a corrected character does not sink into the road.

A valid complete source is parsed without execution, saved through the existing hash-bound file tool and immediately committed. The same controller then uses its sandboxed Blender export adapter and an 18-second native preview containing the unchanged first 18 seconds of the existing ordinary-input replay. Source, editable Blender file, FBX and actual native captures must exist before any claim of visual improvement. Pixel review precedes camera work; full regressions and the five-target broad review still precede promotion.

At **21:16:28 UTC**, request observations advanced from 1,628 to 1,657 generated tokens over 20 seconds; lifetime decode rate was 2.88 tokens/second. No response or new source/export/preview existed at the snapshot. The exact-request watchdog was observing. The original failures, counters and accepted checkpoint remain unchanged. Recovery success is **not yet established**.

## Slow decode: observations and unresolved cause

Earlier saved requests on the same pinned model completed at roughly 15–24 tokens/second including prefill. The broad failed request averaged about 4.0; the smaller focused request began near 3.0. Different prompts prevent treating these as a controlled benchmark, but the operational slowdown is real.

Read-only comparison found identical inference settings in the earlier and current resident configurations; differences were a metadata timestamp and an authentication secret. Startup logs show the same resident PLE mode, 96 projection pairs, 97 compiled decode paths, M5 gather reroute, vision feature cache, disabled oMLX prefix cache and stock NAX attention path. MTP, KV quantization, APC and PLE SSD offload remain off. No inspected runtime-tuning environment override was set.

The host runs macOS **27.0.1 (26A434)** and has been booted since October 4 at 22:43:09 UTC, covering both faster and slower requests. Low Power Mode is off. Available memory at the snapshot was 69.14 GiB; total swap was unchanged at 40.56 MiB. Prior `pmset` checks reported no thermal warning, which does not establish physical temperature or clock behavior. Aggregate GPU load does not attribute contention to another process. A single one-second stack sample placed most sampled model-worker activity in MLX evaluation/waiting and Metal submission; it does not identify the underlying cause.

Primary upstream findings:

- [Memory-guard telemetry fix 8da6d974](https://github.com/jundot/omlx/commit/8da6d974) avoids MLX calls in active background guard ticks. The installed code already uses cached executor memory and cached Metal caps, so this is not a missing patch here.
- [Issue 1835](https://github.com/jundot/omlx/issues/1835) includes an October 6 report of sudden cross-runtime degradation on the same OS build, with recovery after reboot and inconsistent power-mode workarounds. Different hardware and unisolated causes make this a relevant hypothesis, not a diagnosis or permission to reboot a shared host.
- [Issue 3723](https://github.com/jundot/omlx/issues/3723) describes degradation after hours with different model/offload/MTP settings. Our current resident was freshly started immediately before the slow broad request, so that report does not justify a blind service restart.

No established safe runtime fix has been identified. No benchmark, model change, OS/security change, power-mode change, cache clearing or other-job intervention was performed. Any justified runtime change belongs at an idle boundary with state preserved. Continue toward a saved artifact and record the exact recovery outcome when it arrives.
