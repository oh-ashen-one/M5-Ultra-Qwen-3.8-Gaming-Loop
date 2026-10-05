# Qwen BF16 runtime readiness

Verified 2026-10-05. **Model warmed and resident; game/agent loop held for the owner's launch-plan review.** This is functional preparation, not another benchmark campaign or proof of game-building quality.

## Actual state

- Host: Apple M5 Ultra, Mac17,15, 36 CPU cores, 80 GPU cores, 256 GB memory, macOS 27.0.1. The older M3 performs lightweight orchestration only.
- Artifact: [`mlx-community/Qwen3.8-27B-bf16`](https://huggingface.co/mlx-community/Qwen3.8-27B-bf16/tree/6f265714824f3c38d4452baa1628aef3d9b9aae9), revision `6f265714824f3c38d4452baa1628aef3d9b9aae9`, 54,743,805,107 data bytes, Apache-2.0 metadata. All 23 data files verified; all 1,184 weight tensors declare BF16. Full vision weights are included; quantization metadata is absent. See the [lock](../config/QWEN-BF16-LOCK.json).
- Existing installed runtime: MLX-VLM **0.7.4**, commit [`d73f4b1ad90194d53e37beac6e9eef76976aadc5`](https://github.com/Blaizzy/mlx-vlm/tree/d73f4b1ad90194d53e37beac6e9eef76976aadc5); MLX/MLX-Metal 0.32.3, MLX-LM 0.31.3, Transformers 5.17.0, Python 3.12.13. Nine critical installed source files exactly match that commit. No runtime installation or benchmark environment changes were needed.
- One authenticated loopback endpoint on the **M5**: `http://127.0.0.1:8027/v1`. The private token and connection adapter remain outside Git. This URL refers to M5 localhost, not controller localhost.
- Warm-up: one short request returned `READY`, a normal stop and nonempty `reasoning_content`, with explicit thinking and `xhigh`. Request: 57 prompt tokens, 30 generated tokens, maximum 512 generation tokens and a 256-token thinking budget. Raw reasoning is not published.
- Immediate post-warm-up snapshot: 183.536 GiB available, 51.497 GiB server RSS, 1.112 GiB existing swap and **zero positive swap growth**. These are a small functional snapshot, not a sustained workload measurement.
- No Unity editor/Hub/license installation was found. Blender 5.2.0 is installed. The separately authorized [connector diagnostic](../tools/connector_smoke.py) qualifies scoped tools and headless Blender control; its actual results are recorded separately. No game-generation loop, TensorFold, drafter, external asset generation or main merge started.

## Exact supported settings

The [CPU audit](RUNTIME-STATIC-AUDIT.json) passed 31 source/template/parser fixtures with accelerator imports blocked. It checks request normalization, native Transformers Jinja compilation, XML argument types and context rejection. It does not test image preprocessing, model-generated tool calls or gameplay quality.

Supporting records: [artifact verification](QWEN-BF16-VERIFICATION.json), [warm-up snapshot](WARMUP-EVIDENCE.json) and [installed/upstream source hashes](RUNTIME-SOURCE-HASHES.json). These contain sanitized evidence only.

| Control | Audited behavior / current choice |
| --- | --- |
| Thinking | Top-level `enable_thinking: true` reaches the template and generation arguments. Server `--enable-thinking` also sets its default. The server default without that flag is false; the template's native default alone is insufficient evidence. |
| Effort | Top-level `reasoning_effort: "xhigh"`. Exact template accepts `low`, `medium`, `xhigh`; default is `xhigh`. `high` and `max` fail. Effort supplies a template instruction, not a numerical compute guarantee. |
| Thinking budget | Top-level `thinking_budget`; the runtime counts thinking tokens and forces a newline/closing sequence after the budget is exceeded. This has small closing-token overhead. It is separate from effort and still consumes the generation budget. Warm-up used 256; a 4,096 working budget is a proposal. |
| Generation cap | Chat Completions uses `max_tokens`, including reasoning and final output. `max_completion_tokens` is accepted as an unknown field but not consumed by this path. Warm-up used 512; server default for subsequent requests is 8,192. |
| Sampling | Explicit `temperature: 1.0`, `top_p: 0.95`, `top_k: 20`, `min_p: 0.0`, `presence_penalty: 0.0`, `repetition_penalty: 1.0`. These are source-backed thinking settings, not a measured optimum. |
| Context | Model declares 262,144. Current server `--max-kv-size 32768` admits **expanded prompt + maximum generation** up to 32,768; over-budget requests fail. Avoid automatic history truncation and silent omission of large files. Working contexts remain scoped, usually below 16K prompt tokens. |
| Serial requests | `--max-num-seqs 1`, one worker and one loaded model; separate builder/critic histories. Queued concurrency is not a second resident model. |
| Prefill/cache | `--prefill-step-size 2048`; KV quantization unset; APC disabled; no drafter. Native health confirms the 32K effective context and parser. |
| Tools | Standard top-level `tools` schemas; XML parser `qwen3_coder`, detected from the exact template. Parse returned calls, validate required fields/types/path/hash boundaries, then execute permitted tools. A parser fixture is not proof that Qwen will use tools reliably. |
| Multi-turn reasoning | Preserve returned `reasoning_content` in the relevant private role history. The template retains it by default. Never publish it or leak builder history into a fresh critic. |
| Vision | Use actual immutable image bytes or unique immutable screenshot paths/URLs. The server extracts user `image_url` content and adds visual markers. Path-based feature-cache keys can become stale if files are overwritten. Prepare the intended resolution before sending; do not rely on `resize_shape` in the normal queued path. Actual image understanding remains unqualified. |

Do not put thinking fields inside a generic `chat_template_kwargs` object: this installed request-normalization path does not forward it. UI effort labels do not establish the actual server request. See pinned [normalization](https://github.com/Blaizzy/mlx-vlm/blob/d73f4b1ad90194d53e37beac6e9eef76976aadc5/mlx_vlm/server/request_normalization.py), [generation](https://github.com/Blaizzy/mlx-vlm/blob/d73f4b1ad90194d53e37beac6e9eef76976aadc5/mlx_vlm/server/generation.py), [chat/vision transport](https://github.com/Blaizzy/mlx-vlm/blob/d73f4b1ad90194d53e37beac6e9eef76976aadc5/mlx_vlm/server/openai.py) and the [model template](https://huggingface.co/mlx-community/Qwen3.8-27B-bf16/blob/6f265714824f3c38d4452baa1628aef3d9b9aae9/chat_template.jinja).

## TensorFold decision

TensorFold's M5 tensor kernels do not establish BF16-checkpoint compatibility. Its Qwen MLX loader at [`609ca419…`](https://github.com/ashhart/TensorFold/blob/609ca419abecebdc5a059498a613680bd3aa847f/src/tensorfold/families/qwen3_5/__init__.py) explicitly rejects unquantized checkpoints without affine metadata. The [recipe](https://github.com/ashhart/TensorFold/blob/609ca419abecebdc5a059498a613680bd3aa847f/docs/recipes/qwen3.8-27b.md) describes packed affine formats. Switching the kernel toggle does not remove that admission rule. Keep the requested BF16 baseline on the verified MLX-VLM implementation; no quantized substitute or speculative drafter has been introduced.

## Ownership and monitoring

The [warm-up supervisor](../tools/warmup_resident.py) holds the existing shared GPU slot, owns only its server, enforces at least 64 GiB available and at most 512 MiB positive swap growth, checks desktop/health/model identity, and stops on a new fault. It never launches an engine, generates another request automatically or restarts a failed server. The model is deliberately left loaded and idle.

Parent midir manages project direction and approvals. The execution lead performs approved work and reports actual artifacts, progress, failures and blockers. The watchdog supplies resource/liveness signals. Cloud judgments/interventions are logged separately from local game authorship; the execution model's exact ID is not exposed here and is not assumed to be Astra.

The preparation/downloader/audit/resident/diagnostic tools were authored by Codex and are cloud preparation work, not local gameplay coding. Diagnostic scene code is authored by local Qwen. No substantive game code has been authored. A scheduled Codex heartbeat could not be created because this delegated cloud thread does not support that local-thread feature; no scheduled AI follow-up is claimed. Future game supervision remains under parent management after explicit approval.

The closed benchmark's two-event stop remains historical and campaign-scoped. Its counters, failures and closeout were not changed. Shared renderer limits, real new faults, permissions, security controls and other task ownership remain enforced.

Before the game start: review this configuration and the acceptance/design plan; qualify actual tool edits and immutable-image criticism; resolve Unity release/pipeline/license and capture adapters; prove protected red/green acceptance and last-playable checkpoint recovery. The one-request warm-up does not clear those gates.

The separately authorized [disposable connector check](../diagnostics/connector-2026-10-05/README.md) passed real Qwen tool edits/shell tests, original Blender CLI mesh/material save/export/render and fresh image recognition. Unity import/compile/render and Blender MCP remain **NOT RUN** because prerequisites are absent. One simple image is functional vision evidence, not proof of reliable game criticism. No production game generation began.
