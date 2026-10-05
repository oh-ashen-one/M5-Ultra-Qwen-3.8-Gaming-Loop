# Runtime ownership recovery

The owner authorized recovery of the stopped combat qualification without a plan
change or a new game owner. The stopped resident receipt and candidate evidence
remain preserved.

Read-only inspection on the verified M5 found the original external Blender,
no other game/editor renderer, both capture locks free, and no shared holder or
queued job. A stale acknowledgement belonged to the departed controller. It was
archived only after verifying that controller had exited and its engine request
and processes were gone. No M3 workload was used in the M5 admission decision.

The old guard first sampled renderers, then separately queried the controller's
children. An editor exiting between those reads could appear in the first list
and disappear from the second, producing a false ownership fault. The old fault
record did not retain the offending process set, so this race is an identified
defect, not a retrospective assertion that every earlier stop had that cause.
The failed build's recorded import worker used the Null graphics device; current
inspection found no genuinely competing workload.

Controller `986c602` repairs the accounting and records private observations:

- One process snapshot ties identities to PID and creation time. Each engine
  lease also registers its private process group; reparented helpers retain that
  ownership while their group drains.
- Known Null import workers remain excluded from renderer counts. A real third
  renderer, foreign job or reused process identity still blocks admission.
- Idle capacity conflicts pause engine/inference admission while retaining the
  healthy loaded service. Memory, desktop, active-inference conflicts, unexpected
  model changes and actual runtime faults retain their stop protections.
- Every resident fault and game closeout records process, lease and shared-slot
  observations. Private command arguments and credentials are not published.
- Admission must obtain all slots required by its declared external-renderer
  count. Other holders and queued jobs keep priority.

One explicitly authorized reload restored the same pinned Flash-Next model in
the existing runtime. The former resident directory was not overwritten. One
model loaded healthy, and the sole game controller resumed. Native world,
vehicle and courier regressions subsequently passed through real handoffs.

Controller `211edf3` adds a separate **two-second continuous pursuit escape**
requirement. A single crossing or an R reset cannot satisfy it. The original
`f965eae` regression set and fresh actual-image critique are completed before
the focused local-Qwen gameplay correction is tested. The fixed project cap,
accepted `81659ed` and historical rejection counts remain preserved. **105 CPU
checks pass on both machines.** See current machine-local status for later
qualification results; resumed service alone does not promote a game checkpoint.
