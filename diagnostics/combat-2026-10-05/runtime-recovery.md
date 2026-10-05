# Runtime ownership recovery

## Current measured result

Local-Qwen source **`5034b67`** changes the rival's walking speed from 2 to 1 m/s.
The 18 m pursuit and 16 m attack thresholds, vehicle physics and world geometry
remain unchanged. Native driving now establishes **5.783 seconds** of continuous
pursuit clearance, with no reset, and maximum separation **23.069 m**. Open combat,
both directions of wall occlusion, the 1.57 m imported visual, the combined route
and all five accepted baseline regressions pass. Actual Mouse0 events at 7.533 s
and 9.217 s hit the Rival collider and reduce its HP 3→2→1. See
[the measured evidence](sustained-escape.json).

The original `f965eae` fresh visual review returned FIX. The later `5034b67`
review returned unsupported `partial`, then exhausted its correction context.
Neither was converted into a PASS. Controller **`c1d2d26`** supplies explicit
verdict choices and a compact actual-evidence report distinguishing enemy damage,
player-shot rival damage and pursuit arming/clearance transitions. The fresh
actual-image review returned **scoped PASS at 20:49:45 UTC**, promoting source
`5034b67` to accepted checkpoint **`bbb0a91`**. The original failed reviews and
earlier accepted `81659ed` remain preserved. This accepts combat/pursuit in the
short connected mission, not final game quality.

The same sole queue has advanced to **mission-hud-audio**, with local-Qwen source
`202b53b` awaiting native qualification. Next are a single rough route combining
the accepted mechanics and failure/retry, then Chicago presentation and meaningful
roughly ten-minute pacing. No new owner or schedule was created.

Controller **`e1e60ec`** also retains the resident reservation throughout inference
and counts the standalone native player. It was applied at an inference-idle
engine handoff, preserving the game controller. The resident stayed healthy
through subsequent real handoffs; its reservation identity remained unchanged
across the later idle period and fresh review. **109 CPU checks pass on both
machines.** Current-source foot/wall/driving contracts, including two-second
stable escape, now also gate future combat promotions and changes.

Three actual rival/escape/completion images are confirmed in private Library.
The accepted combined run's requested combat frame 002 (8.0 s) and mission-action
frame 005 (24.4 s) are also privately delivered. Frame 005 shows pursuit active;
the separate continuous driving trace establishes sustained escape.
Blocky silhouettes, limited firing feedback and the oversized beacon remain
visible weaknesses. Native mechanics are not final visual-quality acceptance.

## Recovery diagnosis and protections

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
