# Failure/retry recovery

At 17:47:33 UTC on October 5, the sole queue stopped when local Qwen requested
`read_file` for the `Notes` directory. The uncaught `IsADirectoryError` ended the
controller. The resident model remained healthy and idle. Accepted courier
checkpoint `ca12a18` was preserved; latest source `8bdb226` only added timer fields.

Three preceding native attempts, q0013 through q0015, compiled but stayed in the
active mission state. None proved failure, retry or completion. The subsequent
bounded diagnosis exhausted its turns without a plan, but the old controller
incorrectly reset failure counters. That historical ledger is preserved.

The controller now returns a recoverable validation error for directory reads,
and an unsuccessful repeated-blocker diagnosis stops without resetting counters.
Failure/retry acceptance requires an observed failure, ordinary R input with an
increased reset count and active mission, then completion after that reset.
Completion before failure cannot satisfy the gate.

`tools/resume_failure_retry.py` admits only this inspected pause and clean source,
archives its state, and preserves the accepted checkpoint, retry history and
October 8 06:33:12 UTC cap. Six exact small edits are requested from local Qwen:
timer initialization/reset, deadline latch, failure text and two countdown lines.
The external probe waits for genuine expiry, presses R and repeats the previously
verified route. All substantive gameplay source remains local Qwen; controller,
acceptance tests and probe composition are cloud-authored infrastructure.

The repair passes 81 CPU tests. This does not establish a native failure/retry
PASS or final game quality; actual evidence must follow execution.
