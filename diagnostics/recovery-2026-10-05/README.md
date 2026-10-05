# Bounded C# foundation recovery

The original run remains stopped at its original 120-minute no-accepted-progress deadline. Its failure record is retained. Parent management explicitly authorized a separate bounded recovery after diagnosing the blocker; this does not reclassify that failure as progress.

The rejected creation attempt had omitted the hash required by the existing-file replacement tool. Controller commit `d352ec2` introduced atomic `create_file(path, content)` with no-overwrite semantics. Existing-file replacement still requires the current full-file hash.

At **08:33:57 UTC**, one real resident local-Qwen request passed the production create tool. Its finish reason was `tool_calls`; the action returned `ok: true` and saved a 47-byte isolated note. Usage was 400 prompt / 171 completion tokens, 5.21 seconds. See [the receipt](create-tool-receipt.json) and [local-authored note](create-tool-check.md). This qualifies tool creation, not C# compilation or game quality.

The next recovery uses a fresh ledger and the existing original street/player/coupe/props exports. Its first objective is one self-contained, local-authored `Assets/Game/Bootstrap.cs`, followed immediately by the unchanged native build/input/capture gate. It allows at most two initial create requests, six game rounds and 45 minutes total, with the existing memory, swap, engine admission and failure safeguards. An explicit timer enforces the wall deadline even inside a long request. No new art tools or benchmark campaign are enabled.

Once the file is saved, the same owner continues through native acceptance, fresh criticism and local C# fixes. A file or compile alone cannot promote a playable checkpoint. Substantive game code remains local-Qwen authored; the cloud changes only controller infrastructure and prompt guidance. Current machine-local status is authoritative until a timestamped result is appended here.

## 08:55 UTC: first C# artifact after prompt decomposition

Both initial integrated-bootstrap requests ended with `finish_reason: length`, each at 16,384 completion tokens (386.96 and 387.77 seconds), with no saved file. Metadata from the first response showed zero parsed tool calls and zero tool-call syntax markers. The controller did not discard a successful file tool invocation: none was present. These failed actions remain in the same ledger.

The follow-up decomposed the task into three small writes within the **unchanged 09:23:10 UTC deadline**: an empty valid entry point, scene startup using existing exports, then movement/camera. The first step permits 2,048 output tokens; the next two permit 4,096 each. Hash enforcement for edits moved behind a fixed-path tool, so Qwen supplies only content while the controller still checks the exact source hash it provided. Existing-file concurrency protection is preserved.

The first small C# request completed in **3.58 seconds**, using 428 prompt / 97 completion tokens, with `finish_reason: tool_calls`. Atomic creation returned `ok: true` and saved `game/Assets/Game/Bootstrap.cs` at source checkpoint `5bdfa59f0628a1d7d356dd43b5bea6ae762a63dc`, SHA256 `f8b3260cc6032a74291090cbb08ab760dc411181f2dd6932d1dca4f427da96aa`. It is only the empty `ChicagoGame.Bootstrap.Create()` entry point; no gameplay, compilation or accepted checkpoint is implied. Scene integration was running at this observation.

## 09:05 UTC: native candidate, real grounding failure, recovery continues

All three decomposed writes completed with `finish_reason: tool_calls` and successful file actions. Scene startup used 3,831 completion tokens / 88.24 seconds. Movement/camera used 3,958 completion tokens / 92.48 seconds. The resulting **4,630-byte local-authored Bootstrap** is at [source checkpoint 828e917](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/blob/828e917c7077dbdf79b8ea9f7a1b16df9935ea6d/game/Assets/Game/Bootstrap.cs), SHA256 `d27fd334c6c07169305ba2a0a2b644010d6c74be5ce0960f06ef0eda916e1cfe`. Publication of this checkpoint was verified.

Unity compilation and native Metal execution completed with zero reported compile/runtime errors, 16.008 seconds, 132 trace samples and four actual frames. **The candidate is nevertheless rejected:** trace Y fell from 0.043 to -359.968, and the final frame shows an inverted small player against an empty background. There is no accepted playable checkpoint. The original v1 gate incorrectly counted the fall as useful 3D movement; cloud evidence review caught this before promotion and stopped the critic/controller gracefully.

The [original gate](native-falling-candidate/original-gate-v1.json), [actual failed frame](native-falling-candidate/frame-003.png) and [versioned re-evaluation](native-falling-candidate/grounding-v2.json) are retained. Acceptance contract v2 measures horizontal XZ displacement and rejects a foundation descent exceeding five metres. Re-evaluation rejects this real falling candidate, keeps the earlier actual native walking fixture green, and keeps the stationary fixture red. The contract migration is explicit in the new run's ledger; original evidence and the original expired run were not rewritten. Twenty-three CPU tests pass, including falling with and without horizontal input motion. This closes this false-positive class, not every possible collision or gameplay failure.

At 09:05 UTC the sole controller continued with one narrowly scoped **local-Qwen physics correction**, addressing world-meter collider roots versus imported visual transforms, followed by native testing and normal local C# continuation. No cloud game code or new art was introduced. The recovery's **09:23:10 UTC deadline remains unchanged**. Consult live status for the correction's eventual result.
