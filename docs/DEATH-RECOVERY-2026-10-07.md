# Death integration recovery and measured memory

Snapshot: 2026-10-07 00:28 UTC. A second measured memory stop has paused local integration. The other authorized Unreal workload now has user-assigned priority. Partial source, prior failures, the verified reticle and accepted checkpoint remain preserved; no repaired-source native acceptance exists.

## What consumed memory

The machine reports 256 GiB physical memory. The resident's existing guard stops when `psutil.virtual_memory().available / 1024**3 < 64`, or swap growth exceeds 512 MiB. On this installed macOS/psutil version, available is raw free plus inactive memory; the separately returned free figure excludes speculative pages. This is an explicit reserve threshold, not an out-of-memory report.

| Observation | Measured value and limitation |
| --- | --- |
| Guard stop, approximately 00:09:03–00:09:05 UTC | 61.804 GiB available; zero swap growth; no thermal warning; GPU device utilization 95%. The saved admission snapshot precedes the failing memory sample, so it is not an exact timestamp for that sample. |
| Loaded model receipt | 138.843 GiB measured load delta. Installed oMLX computes this from the difference between pre/post-load `max(MLX active memory, process physical footprint)`. It is not model disk size or a separately additive weight count. |
| Pool estimate | 147.119 GiB; an estimate, not an additional allocation to add to the measured load delta. |
| Qwen RSS in saved fault receipt | 31.126 GiB; overlaps unified/physical allocation and does not capture its full footprint. Do not add it to the loaded-model figure. |
| After unload, 00:14:59 UTC | 225.425 GiB available; 203.125 GiB free; 22.112 GiB active; 22.004 GiB inactive; 6.004 GiB wired. |
| Same post-unload VM sample | Compressor occupied 1.597 GiB; file-backed pages 16.624 GiB; speculative pages 0.296 GiB. These are overlapping classifications, not extra rows to sum with active/inactive/wired. |
| Same post-unload pressure/thermal sample | `memory_pressure -Q` reported 95% system-wide memory free by its own metric; no thermal warning. That percentage is not the psutil available percentage. |
| Swap | 42.8125 MiB used; zero growth through the observed request and shutdown. |
| Current Unreal editor, 00:16:02 UTC | 18.335 GiB physical footprint and 18.895 GiB RSS. These overlap. This is a different process from the one present at the fault. |
| Focused recovery, 00:24:03 UTC | Qwen physical footprint 139.690 GiB, RSS 31.482 GiB, system available 96.059 GiB. A read-only bounded observer now records process footprints every five seconds. |

Available memory was about 89.4 GiB shortly before a separate authorized Unreal render started, then crossed the 64 GiB floor. The fault record lacks per-process footprints and complete VM categories at that instant. Concurrent rendering is established; the precise share of the decline due to Unreal, Qwen buffers or macOS cannot be reconstructed. No model-file or Trash inspection was performed for this breakdown, and no other application or OS setting was changed.

## Static integration review

The local [partial component](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/b0254e416bc6592aac103d4a9885ae2fcb9d5b83) is not yet installed or used by the existing gameplay. Its positive-health grace releases a death latch without an R edge; the required contract is ordinary-reset-only release. Reflective access is unnecessary for the supplied concrete signal fields. A separate banner would also compete with the existing mission board.

| Integration point | Source observation and required local repair |
| --- | --- |
| Bootstrap / Walker | Install the authority and gate horizontal input; preserve the entire qualified Follow camera/reticle class. |
| VehicleInteraction | R is the actual reset owner. Keep reset reachable before the death exit; gate boarding/exiting/throttle/steering and stop residual commanded velocity. |
| Combat | Rival damage runs before player fire. A lethal hit in that update must prevent the following shot; preserve real damage and thin-ray collision semantics. |
| CourierMission | Its own stage/F logic can advance despite failed global mission state. Gate interaction after reset handling while preserving earned receipts. |
| RouteMission | Activation from old courier completion and cache F interaction lack a death decision. Preserve reset and earned route history. |
| RelaySequence | Arming and final F completion lack death gates. Prevent new progress while preserving previously earned relay counts. |
| InterceptionMission | The existing health test is after activation/receipt processing. Cover those windows plus physics and late-update paths; keep reset/temporary-target cleanup and specific failure reasons. |
| MissionDirectorHud | Chapter-priority text can hide death. Give failure and R-reset text priority on the existing visible MissionBoard. |

The saved six native traces reached all intended live chapter states and reproduced dead movement/fire in every case. Four advanced objective state; five lacked visible failure/reset text. All were explicit one-time zero-health injections, not proof of natural enemy-damage death in every chapter. Original traces and the separate float-boundary reconciliation remain intact.

## Changed recovery strategy

The [focused controller](../tools/resume_player_death_focused.py) uses three fresh local contexts: authority correction, player controls/reset, and chapter progression/HUD. Each source edit is checkpointed. The first actual request used 3,419 prompt tokens rather than the earlier 33,473. All phases retain `xhigh`, thinking preservation, a 16,384-token output allowance, a 49,152-token working bound and the existing elapsed/speed guards. No cloud gameplay implementation is supplied.

Capacity checks at 00:19:36 and 00:21:59 UTC found 233.2 and 234.4 GiB available, no active renderer, and both shared capture slots free. A single diagnosed load began at 00:22:38 with 236.2 GiB available; the same queue resumed at 00:23:09. All 53 targeted controller/recovery checks passed on both Macs and deployed file hashes matched. No automatic restart policy was added. The original memory fault remains a fault, and another authorized workload may still change admission during this phase.

After complete local integration, unload only the idle owned model and run the unchanged six negative cases, ordinary 95-second route and all ten gameplay regressions. Inspect actual failure/reset pixels before reporting a verified repair. Source saves and this static review do not satisfy that gate.

## Directly measured recurrence and current state

The smaller-context recovery saved [the corrected authority](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/ac0d7fe441a48377eb8d3bb420da2618ed797ed6) in a complete 7,108-token tool response, with 8,277 prompt tokens and 119.2 seconds total. Static review confirms direct signal access, no separate banner and no positive-health grace. The component remains uninstalled; no control/chapter edits or completed-author claim followed.

This time the bounded observer captured the concurrent allocations directly:

| UTC | System available, GiB | Qwen physical footprint, GiB | New Unreal process physical footprint, GiB |
| --- | ---: | ---: | ---: |
| 00:24:03.685 | 96.059 | 139.690 | Not present |
| 00:24:08.715 | 94.970 | 139.690 | 0.581 |
| 00:24:33.898 | 83.930 | 139.692 | 11.404 |
| 00:24:48.999 | 64.895 | 139.727 | 29.868 |
| 00:24:54.045 | 63.687 | 139.704 | 30.675 |
| 00:25:39.416, shutdown underway | 161.010 | 44.750 | 28.444 |
| 00:25:44.470 | 234.231 | 0.527 | Not present |

The resident's independently sampled guard recorded **63.811 GiB available**, **0.812 MiB swap growth** and **no thermal warning**. GPU device and renderer utilization were both 100%. The model's footprint stayed effectively flat while Unreal's grew by about 30 GiB; this is stronger attribution than the earlier incomplete snapshot. It still does not provide a perfectly additive accounting of every OS/shared allocation. RSS substantially underreported both compared with physical footprint and must not be added as separate memory.

At **00:28:33 UTC**, Qwen and its observer were stopped, no Unreal editor was present, available memory was about **231.6 GiB**, GPU utilization was 0%, and no thermal warning was recorded. Swap used was **43.625 MiB**. Idle GPU at this instant does not guarantee a sustained inference window: the preceding two native jobs began after admission. The user now assigns the other Unreal work priority; no further model reload or Unity verification was started after that change. A model-unloaded partial-source build/healthy-route/red check is prepared in [the native verification controller](../tools/verify_partial_death_native.py), but it has not run. The source remains partial and unaccepted.
