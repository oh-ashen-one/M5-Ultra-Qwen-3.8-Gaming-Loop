# Flash-Next readiness

Verified 2026-10-05. **Model service ready; overnight game loop not ready.** Flash-Next remains loaded and idle after a two-request image/tool warm-up. This qualifies a small functional path, not sustained coding, game quality or an unattended overnight run.

## Model and runtime

- Hardware: verified Apple M5 Ultra / Mac17,15, 256 GB memory, 80 GPU cores. The M3 controller performs lightweight orchestration only.
- Pack: [`mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp`](https://huggingface.co/mlx-community/Qwen3.8-Flash-Next-oQ6e-mtp/tree/e171af86f499f1855b0fb71d781105e8dd609610), revision `e171af86f499f1855b0fb71d781105e8dd609610`.
- Download: 150,473,112,037 bytes; 39 files including 28 safetensor shards; 3,748 indexed tensors including 76 MTP tensors. File sizes, index/header coverage, tensor shapes/dtypes/payload offsets and supporting-file hashes were verified. A full cryptographic rehash of every weight payload was not performed. MTP weights are present but unused.
- Runtime: official [oMLX 0.6.4](https://github.com/jundot/omlx/releases/tag/v0.6.4), commit `1d7826185c5b5b69b38b27cbe57d7597b7551fd7`, installed in an isolated environment. The CPython 3.12 macOS universal wheel SHA-256 matched the release asset digest: `f13d92900bf6c7e925e9a6d5525b4465c615c404ee796d328ffc5d4d379ddb0b`. Dependency consistency checks passed.
- Runtime versions: Python 3.12.13, MLX/MLX-Metal 0.32.0, MLX-LM 0.31.3, MLX-VLM 0.6.3, Transformers 5.12.1. The earlier runtime environment was preserved.
- Model service: one pinned VLM engine, `qwen4_exp` configuration and `qwen3_coder` tool parser, authenticated on M5 loopback `http://127.0.0.1:8027/v1`. Credentials and routing remain private. Remote-code trust and distributed inference are disabled.

The first attempt with the previously installed MLX-VLM 0.7.4 stopped cleanly with `Missing FP8 PLE shards`. That loader did not handle this pack's affine-packed PLE shards and shared scale. The selected oMLX release contains explicit support for applying the shared scale correctly. No scale was discarded and no model weights were modified to bypass the error.

The owner directly confirmed permanent deletion of the 15 old model variants already in a scoped Trash bundle. Exactly 360 inventoried files were deleted, reclaiming approximately 667.1 GB; all 39 new model files were preserved. Other Trash contents, software, projects and benchmark records were left intact. Exact deletion and download manifests remain machine-local because they contain operational paths.

## Applied settings and evidence limits

Sampling follows the upstream [thinking-mode defaults](https://huggingface.co/Qwen/Qwen3.8-Flash-Next#best-practices). These are a supported starting configuration; this audit does not establish an optimum for overnight game development.

| Control | Actual configuration | Verification and limit |
| --- | --- | --- |
| Thinking and effort | Thinking enabled; `reasoning_effort: "xhigh"` | Actual oMLX forwarding and the exact model template passed CPU fixtures. Both live requests returned reasoning. Effort is a template instruction, not a guaranteed compute amount. |
| Reasoning history | `preserve_thinking: true` | A synthetic template fixture retained earlier reasoning after a tool result/new user turn; the live round trip replayed returned reasoning privately. Raw reasoning is not published. |
| Sampling | Temperature 1.0; top-p 0.95; top-k 20; min-p 0; presence penalty 0; repetition penalty 1 | Persistent configuration and the two request payloads agree. No sampling sweep was run. |
| Context | 262,144 configured native context | Reported by loaded-model status. A near-limit request was not tested; long-context memory and quality remain unqualified. |
| Output | Default 8,192 tokens, shared by thinking and answer | Warm-up requests were bounded to 1,024 and 512. Production story budgets and truncation handling require qualification. |
| KV cache | Quantization disabled; native floating-point cache behavior | Configuration/source audit only; individual live cache tensor dtypes were not inspected. Do not assume every cache tensor is BF16. |
| MTP / drafter | MTP, VLM MTP and DFlash disabled | Explicit configuration verified. Downloaded MTP tensors do not imply speculative decoding is enabled or qualified. |
| Concurrency | One active request; one pinned model | Runtime settings and read-only status agree. Planner/coder/critic role scheduling remains unimplemented. |
| Prefix cache | Persistent prefix cache disabled | No durable game memory or restart recovery follows from keeping a model resident. |
| Vision | Full vision path; in-memory image-feature cache, 20 entries, image/model hash keys; SSD vision cache disabled | Fresh Flash-Next recognition of the original Unity frame passed. Production capture resolution and gameplay criticism remain unqualified. |
| Tools | Parsed `qwen3_coder` call and tool-result continuation | One inert observation-file write passed. Arbitrary file edits, shell execution, Blender, Unity and MCP use by this model remain unqualified. Health reports no attached MCP server. |
| PLE weights | Packed PLE resident; SSD offload disabled | Model loaded successfully with the compatible release. No performance comparison was performed. |
| Resource guard | 192 GiB runtime ceiling; supervisor requires at least 64 GiB available and no more than 512 MiB positive swap growth | Supervisor checks approximately every ten seconds and stops its owned server on a fault; it never automatically restarts. It is not the game progress/alert manager. |

The [13-check settings audit](../diagnostics/flash-next-2026-10-05/omlx-settings-audit.json) exercised actual installed oMLX settings/effort merging and the pinned template with accelerator imports blocked. The [live receipt](../diagnostics/flash-next-2026-10-05/warmup-receipt.json) records exactly two requests: identify a blue sphere on the left and a red cube on the right from the image, call `record_visual_observation`, then continue from the tool result and return `READY`. The prompt did not supply the expected object identities.

Earlier 27B file/shell/Blender evidence is useful setup history and does not qualify Flash-Next for those actions. Earlier native Unity 6000.6.4f1 import, C# compilation and Metal rendering passed. SSH-side CLI account storage and live Pipeline/MCP remain distinct qualification gaps; the active editor license did work for the native fixture.

## Overnight launch blockers

| Missing piece | Required evidence before an unattended game run |
| --- | --- |
| Actual game controller | Implement bounded story scheduling, separate role histories and mediated edit/engine tools. Qualify Flash-Next against those real adapters. The two-request warm-up is the only current model workflow. |
| Acceptance and promotion | Approve the gameplay brief and external acceptance contract; protect it from mutation. Demonstrate that deliberate failures fail, then promote exact passing commits with immutable rendered/input-driven evidence. |
| Durable recovery | Persist run/role state, tool actions, candidate and known-good commits, and artifact hashes. Prove idempotent restart/recovery in a disposable project. Resident model state is insufficient. |
| Fresh visual critic | Build a scheduler using a separate history and immutable captures; prove detection of a known visual/gameplay defect and bounded three-to-five-fix feedback. |
| Management and alerts | Implement artifact/progress timestamps, stale-progress detection, stop escalation and reliable report/alert delivery. Current process receipts do not provide an ongoing manager or artifact-freshness policy. |
| Production integration | Select the production Unity render pipeline and qualify the actual edit/import/build/play/capture adapter, Blender authoring/rigging/animation workflow and resource handoffs. |
| Bounded start | Record the approved brief, iteration/time/resource budgets and explicit game-start instruction. Preparation and readiness review grant no new start authority. |

The next work is controller and integration qualification, not another broad model benchmark. The proposed architecture is documented in [Architecture](ARCHITECTURE.md); implementation gaps must stay visible until evidenced.

## Read-only monitoring

On the M5, use the existing private bearer credential with `GET /health`, `GET /api/status`, and `GET /v1/models/status`. Those endpoints report health, active/waiting requests and the loaded model without inference, unloading or reloading. The machine-local `resident-state.json` is refreshed about every ten seconds; `warmup-receipt.json` is the completed functional check. Never publish the token, absolute paths or raw server logs.

The [final snapshot](../diagnostics/flash-next-2026-10-05/service-snapshot.json), taken at 04:57:19 UTC, reports one healthy loaded model, two total requests, zero active/waiting requests, about 143.8 GiB OS-reported available memory and 11.75 MiB swap. Memory figures can change as macOS reclaims pages; available memory and process RSS are not substitutes for the runtime's model-allocation accounting. No sustained-load stability claim follows from this snapshot.

An operator can inspect these endpoints and receipts now. Continuous remote management, artifact freshness checks and alert delivery still need implementation; there is no promise of unattended monitoring merely because this conversation produced a readiness report.
