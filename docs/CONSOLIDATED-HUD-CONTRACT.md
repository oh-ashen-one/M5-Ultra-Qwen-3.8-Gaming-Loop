# Consolidated mission HUD

The owner requested one clear current objective alongside health/wanted. This scope explicitly replaces the older simultaneous delivery/cache/relay card layout. It does not change mission anchors, inputs, timers, progression, physical cache/relay props or reset rules.

Local Qwen authors `MissionDirectorHud` and its one Bootstrap installation. `MissionBoard` reads actual courier/cache/relay state and source TextMeshes. `HudStatus` supplies health/wanted only. Existing objective scripts and their text remain live; only their renderers are suppressed after their updates. The new board shows truthful next actions, distance, remaining time and compact receipts for already completed stages. Global R restores the initial grab objective and removes stale receipts.

External acceptance observes both the live 4:3 window and native 16:9 capture. It requires one primary panel plus health/wanted, no remaining legacy card renderers, contained text, no panel overlap, stable positioning and at least twelve pixels of text height per objective line at the 540px capture height. The objective is limited to four short lines. Actual pixel review remains mandatory; rectangle checks alone do not establish visual quality.

The existing relay positive, wrong-order/timeout/reset and no-handoff cases remain unchanged. Physical cache geometry/emission checks are retained. All ten legacy regressions run on the candidate, with additional HUD observations across those sessions, then a fresh local scoped critic reviews actual captures. Prior three-card presentation evidence remains historical; the new layout is evaluated against this explicit replacement contract.

The next proposed gameplay increment is an east-street moving-target encounter. It remains unimplemented and unmeasured. Before implementation, the actual single firing handler needs a scoped death-target correction, followed by original combat regressions; moving targets need grounded collision proof and whole-mission reset gating. No second firing handler or automatic success is allowed. The current measured 59.633-second progression already includes the 27.100-second relay. A 21.25-second nominal runner crossing is a design calculation, not observed mission duration. Ten-minute pacing remains open.

See [saved local plan and research status](../diagnostics/map-2026-10-06/post-relay-plan-and-live-hud.json). No new native HUD result is claimed by this plan.
