# Measured delivery regression, October 5

The accepted courier route remains `ca12a18` (gameplay source `7ad8e37`, native
q0012). Later failure/retry edits moved its pad and widened its gameplay radius.
Those changes did not establish reachability. The independent gate still requires
delivery within 2.6 m of the actual fixed destination.

| Native evidence | Delivery F time | Vehicle X/Z | Pad X/Z | Actual XZ distance | Result |
| --- | ---: | --- | --- | ---: | --- |
| q0012 accepted | 14.35 s | 0.486 / 24.925 | 1 / 26 | 1.19 m | Completed |
| q0019 | 62.03 s | -0.003 / 0.151 | 1 / 26 | 25.87 m | Steered away; no delivery |
| q0020 | 58.93 s | 0.410 / 25.563 | 3.6 / 26 | 3.22 m | Outside even widened 3.2 m radius |
| q0021 | 22.07 s | 0.220 / 27.553 | 3.6 / 26 | 3.72 m | No parcel pickup or delivery |

Vehicle collision remained enabled at these sampled F edges. Observed penetration
was approximately 0.0017, 0.0025, 0.0007 and 0 m respectively. These measurements
describe the observed routes; they do not prove every possible approach to the
relocated destination is obstructed. Widening a radius or repeating a source
comment is not evidence of a usable delivery.

The deadline changed from 45 to 30 seconds in `59aedf6`, after `8549c59`. q0021
ended at 29.98 s and never observed failure or R. q0022 then exhausted its replay
submission output budget and naturally paused at 18:44:57 UTC. No q0022 native
attempt ran. The five recorded task failures, diagnosis flag and accepted
checkpoint remain preserved.

The scoped recovery asks local Qwen to restore the verified west-bay pad and
original 2.6 m gameplay reach, and align the visual beacon over that pad. It reads
the actual current deadline, waits two seconds beyond it, presses R, and repeats
the measured successful q0012 inputs. Native observations must still prove
failure, reset, pickup, vehicle delivery and completion. The unchanged accepted
courier replay is now also a mandatory regression for this task, along with
walking, world collision and motor reset.

External diagnostics now include actual vehicle/pad positions, XZ distance and
collision observations at delivery F edges. Replay validation rejects failure/retry
submissions without R followed by later interaction. The fixed project cap and
individual failure protections remain unchanged. CPU tests qualify this controller
change; a new native PASS is still required.

## Recovery result, 18:55 UTC

Local Qwen saved the three corrections as `9eeda60`. The current 30-second deadline
was preserved. Native q0023 **passes**: actual failure at 30.08 s, ordinary R reset
at 32.03 s, pickup at 39.43 s and completion at 46.33 s. At the successful F edge,
the vehicle was X0.487/Z24.906, **1.21 m** from the pad at X1/Z26; collision was
enabled and penetration was 0.0026 m.

Walking, world collision, motor reset and the accepted courier replay all pass.
The courier regression again delivers at 14.35 s and 1.19 m, reproducing the
accepted route without loosening its reach. See [native evidence](failure-retry-native-pass.json).
The source is published; fresh local visual review is running, so promotion is
not yet claimed. Actual failure, reset and successful-retry frames from
18:50:36–18:50:55 UTC are privately saved to Library for the owner's milestone
update. The art remains a blockout with flat lighting and an oversized bright
beacon. This scoped success does not establish final visual quality.
