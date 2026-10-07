# Three-day delivery boundary

The owner kept the existing Chicago game plan and set a hard cap of **2026-10-08 06:33:12 UTC** (**02:33:12 America/New_York**): exactly three days from the first substantive build at 2026-10-05 06:33:12 UTC. This supersedes the old October 5 overall ceiling. It does not reset individual failure counts, repeated-failure diagnosis limits, accepted-progress timestamps, resource guards or engine ownership.

The controller checks the fixed cap before model/tool/engine admission and arms an absolute-time interrupt for the active process. The persisted policy is also checked by the shared machine guard on later resumptions. It cannot silently extend the deadline. At the cap it stops new work, gracefully stops any owned engine through the existing shutdown path, checkpoints available local source, and writes an honest `FINAL-HANDOFF.json` plus a dated closeout. The last verified playable checkpoint remains separate from the latest candidate. Existing source, rendered evidence and provenance are preserved; a failed final candidate never replaces the best runnable checkpoint merely because time expired.

The lightweight checkpoint publisher has up to five minutes after the game-work cap to transmit final saved commits. That is closeout transport only: it grants no additional model, engine, asset or game-development time. If source checkpointing or publication fails, the closeout records the failure and retained local files rather than claiming a successful delivery.

## Milestone screenshots and owner involvement

Each new native milestone and each accepted feature writes a durable private outbox record under the active run's `milestones/outbox/`. It includes the actual candidate/build identity, capture timestamps and hashes, observed behavior, fresh visual-review problems, and the next step. Start, carrying/action, completion, reset and failure frames are selected from actual trace states when available. Reference images are always clearly separated from real output.

Parent oversight remains the existing ten-minute process. It consumes pending outbox records and delivers their original PNGs through the proven private Library route, recording confirmed Library IDs and delivery status back into the record. A queued file is **not** a delivered screenshot. No public image upload, duplicate schedule, thread or game owner is created. The owner can redirect work from these updates.

Every fresh visual critique now sees an existing Chicago reference alongside actual native frames. The reference guides improvements within the unchanged plan. A mechanical or scoped PASS never establishes good appearance or final quality; blocky art, weak framing, poor lighting, unreadable UI and other visible defects must be stated plainly.

## Current migration

The old owner stopped naturally after another replay-only output-limit failure. Its complete stopped database/status/config are archived before applying the new cap. The same run resumes through `tools/resume_three_day_queue.py`; failure streak and task-failure counts remain unchanged. Three exact local-Qwen HUD line edits replace another broad rewrite, followed by the previously observed passing pickup/delivery/reset inputs and full native requalification. All gameplay source remains local Qwen; cloud changes are controller, evidence, supervision and delivery infrastructure.

Seventy-six CPU tests cover the fixed cap, refusal to extend, retry-state preservation, honest closeout and persistent private milestone delivery records, together with the existing controller suite. Native tests and visual reviews remain separate evidence.
