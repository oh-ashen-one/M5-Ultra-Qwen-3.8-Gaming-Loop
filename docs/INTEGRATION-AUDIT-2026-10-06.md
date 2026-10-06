# Integration audit and native evidence

Snapshot: 2026-10-06 23:21 UTC. The game remains unfinished. The accepted checkpoint and fixed October 8 cap are unchanged.

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

## Remaining integration findings

| Finding | Evidence and status |
| --- | --- |
| Death/failure authority after the courier chapter | Source-confirmed missing health gates; six native zero-health chapter/action/reset diagnostics are running. They explicitly inject health=0 once and use ordinary input for progression. This is not yet proof of natural enemy damage causing death in every chapter. Local repair follows measured results. |
| Tracer and hostile material lifetime | Source-confirmed allocations without corresponding ownership cleanup; native repeated-fire/reset resource stability remains untested. |
| Missing prefab failure overwritten; spawn count incremented early | Source-confirmed; native fault reproduction and repair remain pending. |
| Countdown parsed from presentation text; repeated scene lookup | Source-confirmed design issue; typed cached gameplay state is a queued recommendation. |
| Character completeness | The exported character remains 49 primitive pieces without a demonstrated armature, skinning or animation consumer. It is a visible silhouette improvement, not finished art. |

Two earlier resident memory-floor stops remain genuine measured faults, despite the successful throughput update. The current workflow deliberately separates local authoring from native engine validation, unloading only the idle owned model at phase boundaries. The 64 GiB available-memory floor, 512 MiB swap-growth guard, shared slots, other authorized workloads and fixed deadline are unchanged. No automatic model restart loop is deployed.
