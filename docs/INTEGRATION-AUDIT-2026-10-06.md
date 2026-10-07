# Integration audit and native evidence

Snapshot: 2026-10-07 00:10 UTC. The game remains unfinished. The accepted checkpoint and fixed October 8 cap are unchanged.

## Reticle: repaired and verified within scope

The camera at `8fd4c9e5` passed the 95-second input-driven route, all ten existing gameplay regressions, and the wall/near-plane clearance probe. Its reticle was nevertheless absent from both explicit `Camera.Render` targets and completed normal player screens at 3.2 and 6.5 seconds. Source review confirmed that `OnPostRender` returned when `targetTexture` was present; normal-screen absence required additional investigation.

Local Qwen's final [C# and original shader revision](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/8d23aed0e90336118ece640e5a4e0f092bda6bd0) renders a centered white reticle with a dark outline in both paths. All four actual PNGs were inspected. In a 47-by-47-pixel region centered on (480, 270), white pixels increased from zero to 256 in each image. This numerical corroboration supplements pixel inspection; it does not establish art quality.

The revised source compiled, completed the dual-path run, passed the same 95-second route and passed the camera-clearance probe. Native build identifier: `0e18514a57379e270b6b43dcb248e7598791f3e3ca3cfcd2480222edd786b708`. The ten older regressions belong to the preceding camera source; the reticle source has the newly stated targeted checks. Broad visual criticism and final game acceptance remain open.

| Image | Actual PNG write completed, UTC | SHA-256 |
| --- | --- | --- |
| Camera target, 3.2 s | 2026-10-06 23:17:46.631183 | `158076aa832ef8e40e3095558f1b78ec6761d1df78192303e707ec907bb80b36` |
| Normal player screen, 3.2 s | 2026-10-06 23:17:46.653492 | `bb3ba4f0383b80910592645eb5c3f6b16e5712e7c8867f473cd4cb9dd860d6d7` |

These are timestamps recorded immediately after PNG writes by the native harness, not Library upload times or independent sensor exposure timestamps. Original PNGs were delivered privately; Library identities and private operational paths are not published.

## Preserved failures and changed strategy

- A high-reasoning request exhausted 8,192 tokens at 84.00 decode tokens/s without saving source. Retaining its exact private work with a 16,384-token allowance and `xhigh` produced a complete submission in 22.98 seconds, using 1,467 output tokens at 84.51 tokens/s.
- That submission used unsupported `GL.Disable`, `GL.Enable`, `GL.DepthMask` and `GL_DEPTH_TEST`. The installed Unity API documentation confirmed the incompatibility before native compilation. The source checkpoint was preserved; it was never promoted as a working fix.
- The next shader-authoring request exhausted 16,384 tokens at 73.42 tokens/s without a save. A changed retained-work submission, still `xhigh`, produced the complete matching C#/shader revision in 30.91 seconds with 1,866 output tokens at 83.14 tokens/s. Actual request receipts verify effort and all three target/native images. Private reasoning remains private.
- The first screen diagnostic used an API module absent from the project and failed compilation. The external harness now reads the completed framebuffer after `WaitForEndOfFrame` using already available APIs. The failed build is preserved.
- A native attempt stopped before engine launch because the inference port was temporarily unavailable after graceful shutdown. No model processes remained; a later exclusive bind succeeded. The original interruption was preserved and the same admission guard was retained.

The original existing-shader-only scope was too restrictive for the reticle's required depth behavior. Allowing one small original shader gave local Qwen a supported implementation route. Saving source, successful compilation and visible output remain separate gates.

## Death boundary reproduction

All six native negative cases reached their intended live state on `8d23aed0`: courier pickup, courier delivery, dead-drop interaction, final relay interaction, interception receipt and final interception shot. Each case injects health=0 once before the game's update, attempts ordinary movement/fire/interaction, then presses R. All six reproduced movement and firing after death; four also advanced objective state. Failure/reset presentation was absent in five cases. These are declared injected-health tests, not evidence of natural enemy damage causing death in every chapter.

The relay case initially received a false setup rejection: Unity serialized the float32 boundary 59.6 as `59.599998474121094`, while the Python validator compared against the stricter decimal double. The validator now compares the same float32 boundary. The original failed gate and native trace remain intact; a separate hashed reconciliation reuses the four completed captures, and only the two remaining native cases were run. The regression also rejects an earlier frame and a missing required input edge. This correction is acceptance infrastructure, not a game fix.

The local author phase uses the exact current eight-component context, hash-backed editing tools, `xhigh` reasoning and a 32,768-token output allowance. Safe receipts record actual request settings and a payload hash without publishing prompts or private reasoning. Saving source is not acceptance: the identical six negative cases, the ordinary 95-second route and all ten gameplay regressions must follow with inference unloaded. The complete camera/reticle class and shader remain protected.

### Partial source saved; resource stop preserved

Local Qwen saved [one original `DeathAuthority.cs` component](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/b0254e416bc6592aac103d4a9885ae2fcb9d5b83). The complete tool response used 33,473 prompt and 22,464 output tokens in 309.27 seconds, at 75.37 decode tokens/s. It did not hit the output cap. The existing eight components were not changed; installation, input gates and chapter integration remain unfinished. No native green run or new repaired screenshot exists.

During that request, available memory reached **61.804 GiB**, below the unchanged 64 GiB floor, with zero swap growth. An independently authorized Unreal render was active in the same observation. This establishes concurrent pressure, not a complete allocation-level cause. The resident began graceful shutdown; the complete response still arrived and its source was checkpointed before the next request received connection refused. The resident and controller are now stopped, with no automatic restart and no alteration of the other workload. The source checkpoint is clean and verified published; all original request and fault evidence remains private and intact.

Static review of the unintegrated component flags a latch-release fallback after 0.25 seconds of positive health without an R edge, which conflicts with the requested reset-only death latch. It also uses reflective access despite supplied concrete signal types. These require local-author review; they are not native-verified failure claims. Do not accept its descriptive comments as proof of integrated behavior.

The next attempt must retain this partial source and original fault, obtain actual shared capacity, and use a fresh bounded integration context with the known signal APIs instead of replaying the whole growing conversation. Smaller component groups can save complete changes before another context expansion; high reasoning, memory/swap limits and all external gates remain required. No runtime setting change or new launch is made as part of this diagnosis.

## Remaining integration findings

| Finding | Evidence and status |
| --- | --- |
| Death/failure authority after the courier chapter | All six native setups are valid and reproduce dead-player control defects. One unintegrated local component is saved; actual memory pressure stopped the author phase. No repaired-source acceptance. |
| Tracer and hostile material lifetime | Source-confirmed allocations without corresponding ownership cleanup; native repeated-fire/reset resource stability remains untested. |
| Missing prefab failure overwritten; spawn count incremented early | Source-confirmed; native fault reproduction and repair remain pending. |
| Countdown parsed from presentation text; repeated scene lookup | Source-confirmed design issue; typed cached gameplay state is a queued recommendation. |
| Character completeness | The exported character remains 49 primitive pieces without a demonstrated armature, skinning or animation consumer. It is a visible silhouette improvement, not finished art. |

The two earlier resident memory-floor stops and this new stop remain genuine measured faults, despite the successful throughput update. The current workflow deliberately separates its local authoring from its own native engine validation; that separation cannot guarantee headroom when another authorized workload starts. The 64 GiB available-memory floor, 512 MiB swap-growth guard, shared slots, other workloads and fixed deadline are unchanged. No automatic model restart loop is deployed.
