# Bounded Qwen capacity qualification

**Latest outcome, October 6 at 10:24 p.m. EDT (October 7 02:24 UTC): the approved trial ran and stopped during model loading.** The authorization blocker was resolved. After bounded admission waiting, the resident started at10:21:01p.m.EDT. A new Unreal preview ran concurrently, with each owner holding one shared capture slot. At10:21:17p.m., the trial's **2GiB compressor-growth limit** fired. The supervisor gracefully stopped its model; the model, supervisor and keep-awake process were verified absent afterward. Unreal was not stopped or modified.

| Measurement at the stop | Observed |
| --- | --- |
| Qwen physical footprint, still loading | 128.243 GiB |
| Unreal physical footprint | 7.863 GiB |
| Available memory | 116.705 GiB |
| Calculated remaining-load requirement | 83.894 GiB |
| Compressor growth since trial baseline | **11.072 GiB**, above the provisional2GiB stop |
| Swap growth | 3.188 MiB, below512MiB |
| OS pressure level / thermal warning | 1, normal /0 |

The final two observations were2.216seconds apart; compressor growth changed from0 to11.072GiB. These samples do not bound an unsampled peak. At10:23:15p.m.EDT after Qwen unloaded, compressor occupancy was about2.002GiB and available memory209.236GiB while an Unreal preview used22.364GiB. Whether compression would have settled with Qwen still loaded is **untested**; a later post-stop baseline reporting zero growth is not evidence that the earlier increase did not happen.

**No author request, request prefill, decode, game edit or native verification occurred.** The single trial is unsuccessful; no throughput or concurrent coding quality is established. The current source remains`ac0d7fe441a48377eb8d3bb420da2618ed797ed6`, accepted checkpoint`c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188`, counters and deadline remain unchanged. The paused ledger now records simultaneous operation, the actual load fault and the unattempted author phase. No automatic retry or guard relaxation followed.

The failure establishes that the provisional compressor-growth rule stopped this loading pattern. It does **not** establish an OS out-of-memory failure or a hardware capacity limit. The compressor measurement is system-wide, so these observations cannot attribute every compressed page to Qwen or Unreal. Apple describes compression as a way to make memory available and memory pressure as a combined assessment involving free memory, swap rate, wired memory and cached files; it does not specify this project's2GiB cutoff. [Apple memory-usage documentation](https://support.apple.com/guide/activity-monitor/view-memory-usage-actmntr1004/mac).

The next diagnosis must separate load-time compression and temporary allocations from sustained pressure during request prefill/decode, with a justified phase-aware allowance before another qualification. Neither the2GiB limit nor the40GiB Unreal envelope was raised. Official `safe` mode remained enabled; the runtime's generic wired-limit suggestion was not applied. Original artifacts and hashes are preserved in the [sanitized nine-sample outcome](../diagnostics/capacity-2026-10-07/load-stop.json).

A diagnostic defect was also found: the saved stop snapshot omitted the coexistence flag and consequently labeled the external renderer using legacy ownership rules. The live admission snapshot correctly showed simultaneous operation and passed; the actual stop reason was compressor growth. The reporting call is corrected for future use, with the original fault snapshot retained unchanged.

The [partial-source native check](../tools/verify_capacity_trial_native.py), published as`7e99602`, passes its10 focused CPU checks on both hosts. It uses the unchanged95-second route and courier-pickup negative, reporting walking/reset proof separately from the remaining death contract. It has not run natively because this attempt produced no authoring result. The trial controller's64 targeted checks also passed on both hosts before loading.

## Original plan and earlier checkpoints

**Earlier status, 2026-10-07 02:12 UTC:** simultaneous-operation reconciliation`30639bf` is published and deployed;64 targeted CPU checks pass on both hosts. Read-only admission succeeded at02:11UTC:234.663GiB available versus220GiB required, no active renderer, both capture slots free and no thermal warning. The subsequent resident launch was rejected by automatic authorization review before execution, citing the original inference prohibition despite the later bounded-trial confirmation. No new model load, author request or native verification occurred. This observation does not establish concurrent performance. Older snapshots below remain evidence of their respective times.

Status at **2026-10-07 00:50 UTC**: implementation published in `4922d1eeadcc92a8c8449d1b6c71d3f59b7d9ac7`, deployed into a separate runtime directory, and **59 targeted CPU checks pass on both hosts**. The original supervisor and configuration are preserved for rollback. **The new resident has not been started; authoring and native qualification remain pending.** A subsequent read-only admission check was rejected by automatic authorization review, so no launch followed. The last successful machine observation below is a dated sample, not current admission.

**Updated 2026-10-07 02:08 UTC:** the owner explicitly confirmed the concurrent trial. Neither Unreal nor Qwen has automatic priority; the earlier priority assignment is superseded. The read-only admission check now succeeds. At02:07:56UTC memory admission passed, while an existing exclusive performance reservation held both shared capture slots; no model was loaded. The stopped ledger retains its historical priority until the archived recovery migration records the current instruction.

 This experiment changes only Qwen's admission and memory accounting, preserving the pinned Flash-Next oQ6e model, official oMLX 0.7.0 / MLX 0.32.2, thinking with `xhigh`, sampling, native context, serial requests and quality settings. It does not change OS limits or another workload.

## Why change the fixed reserve

The earlier 64 GiB available-memory floor was a conservative task rule, not an established hardware failure boundary. In the measured q0144 overlap, Qwen's physical footprint remained approximately 139.7 GiB while Unreal grew to 30.7 GiB. The resident stopped at 63.811 GiB available with 0.812 MiB swap growth. This explains the stop without demonstrating an OS out-of-memory failure. See the [preserved measurement and source outcome](DEATH-RECOVERY-2026-10-07.md).

Official oMLX 0.7.0's `safe` mode derives a live ceiling from its own footprint and current available/reclaimable memory, with a 20% reserve clamped to 6–16 GiB. Its custom ceiling bypasses that dynamic calculation. The trial therefore selects `--memory-guard safe` and retains an independent 192 GiB Qwen footprint stop; a custom 192 GiB setting alone would not reserve space for Unreal. Source: [official memory enforcer](https://github.com/jundot/omlx/blob/v0.7.0/omlx/process_memory_enforcer.py).

Apple's recommended working-set value is performance guidance, not a promise that allocations below it are safe under arbitrary concurrent workloads. No wired-memory sysctl or community maximum is applied. See [MLX memory-limit documentation](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.set_memory_limit.html).

## Explicit trial budget

All values below use GiB. These are provisional allowances to qualify, not measured crash thresholds.

| Item | Allowance and rationale |
| --- | --- |
| Model resident footprint | 140, rounded above the observed 139.7 |
| Additional model-load allowance | 8; budget 148 total while loading |
| Unreal footprint envelope | 40, initially based on the observed 30.7 plus growth allowance |
| OS reserve | 16, matching the official safe tier's maximum reserve |
| Request/prefill allowance | 8; retain during idle/decode too |
| Sampling and exit allowance | 8 |

The required available memory is:

```text
steady reserve = 16 + 8 + 8 + max(0, 40 - current Unreal footprint)
load reserve   = steady reserve + max(0, 148 - current Qwen footprint)
```

Current Unreal allocations have already reduced available memory; only its remaining potential growth is reserved again. Likewise, loading reserves only the model allocation still outstanding. Process RSS is not used as a substitute for unified-memory physical footprint, and these overlapping OS metrics must not be added as independent totals.

With no Unreal process, the steady reserve is 72 GiB. With its measured 30.675 GiB footprint, the reserve is 41.325 GiB. Exceeding the 40 GiB Unreal envelope ends this trial and requires reassessment; it never authorizes stopping Unreal or silently raising the envelope.

At **00:46:00 UTC**, the read-only pre-load evaluation measured:

| Metric | Observation |
| --- | --- |
| Available memory | 206.778 GiB |
| Unreal footprint | 36.096 GiB |
| Qwen footprint | 0 GiB; unloaded |
| Remaining Unreal allowance | 3.904 GiB |
| Required pre-load available memory | 183.904 GiB |
| Margin above that requirement | 22.874 GiB |
| OS memory-pressure level | 1, normal |

This instantaneous budget passed. Its newly established baseline reports zero swap/compression growth by construction; it is not evidence of sustained stability. Thermal status was not supplied to this isolated evaluation. Shared-slot ownership, desktop, thermal, request throughput and current memory must still pass at actual admission.

## Retained safeguards and rollback

- Stop Qwen on pressure, more than 512 MiB swap growth, more than 2 GiB compressor growth, an OS thermal warning, a changed owned-process identity, a Qwen footprint above 192 GiB or an exceeded trial budget.
- Preserve desktop/graphics checks, shared slot and queue ownership, bounded request/progress checks, sustained throughput checks, one model and serial execution. Preserve actual shared lock ownership and exclusive performance reservations; a waiting workload alone does not preempt an admitted task. Never modify another owner's records or processes.
- Keep the original supervisor/configuration untouched and a rollback copy of the changed controller entry points. Ordinary and native-only runs retain the original 64 GiB guard. This opt-in entry point requires an explicit trial flag and a verified supervisor/server identity receipt.
- No automatic restart, model substitution, quality reduction, broad benchmark campaign or extension of **2026-10-08 06:33:12 UTC**.

The current policy identifier is `simultaneous-capacity-trial-v1`. Its reconciliation passes64 local CPU checks: seven capacity/boundary checks, ten death-contract checks,43controller checks and four shared-slot checks; the same64 checks also pass on the M5. The earlier implementation and observations retain their historical identifier; do not treat that label as current intent.

Implementation: [budget](../tools/qwen_capacity.py), [isolated resident](../tools/flash_next_capacity_trial.py), [single useful author task](../tools/qualify_qwen_capacity.py), and [focused tests](../tests/test_qwen_capacity.py). The 59 checks comprise six capacity tests, ten death-contract tests and 43 controller tests. Passing CPU checks does not qualify the policy under load.

## Pending useful qualification

The single local task installs the existing death authority and gates horizontal walking in `Bootstrap.cs`, preserving the complete qualified Follow camera class byte-for-byte. The remaining combat, vehicle, chapter and HUD integration is explicitly outside that first task. Source remains `ac0d7fe441a48377eb8d3bb420da2618ed797ed6`; accepted `c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188` is unchanged.

Record model loading separately from actual request prefill/decode, including physical footprints, Unreal's naturally occurring workload, pressure, compression, swap, thermal state, speed and the returned source. Do not start Unreal to manufacture overlap or claim coexistence from an idle-only run. After the task returns, preserve evidence and gracefully unload only the identified idle Qwen resident before native verification.

Partial-source native checks must be adapted to the actual new candidate; the older entry point is pinned to q0144 and cannot verify an arbitrary later source. Require compile and a healthy route, then honestly report the still-incomplete death contract. Complete all remaining local integration, six negative cases, the healthy route and regressions before any game promotion. Capacity qualification and game acceptance are separate decisions.
