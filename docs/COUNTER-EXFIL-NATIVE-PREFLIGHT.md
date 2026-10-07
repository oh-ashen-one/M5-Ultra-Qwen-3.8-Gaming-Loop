# Native corridor preflight — October7

The accepted `d4d13937` game was replayed through its ordinary handoff with a read-only external physics survey. At77seconds the player had28health, stood at approximately X28.19/Z13.94, and the unmoved coupe stood at X47.61/Z17.46. No gameplay source or scene geometry changed.

The central westbound polyline from the coupe through X22/Z16.57 and X6/Z16.01 to X3/Z16.01 passed capsule and coupe clearance:94overlap positions and91swept segments. The runner capsule was radius0.38m/height1.9m; the actual coupe box was1.8×1.2×4.3m with an additional0.2m horizontal clearance margin. The handoff-to-car foot path also passed the sampled capsule check.

| Candidate | Capsule | Coupe | Finding |
| --- | --- | --- | --- |
| Central westbound | Clear | Clear | Use as the initial incident corridor |
| Straight Z10 | Blocked | Blocked | Relay site, dumpster, elevated-track supports and curb/sidewalk geometry |
| Straight Z15 | Blocked | Blocked | Existing western dumpster |
| Straight Z19 | Clear | Blocked | Existing barrier and alley/nub walls |

Ground rays and the union of the existing thin pavement-renderer bounds cover the central capsule footprint. The original single-renderer test reported a seam at X22 because neither adjoining mesh alone spans the whole footprint. Their measured bounds meet exactly: AlleyPavement ends atX22 and StreetPavement begins there. The separate union calculation preserves real-gap failures. Bounds coverage is not mesh-triangle proof, and neither straight sweeps nor these bounds establish turning clearance or an input-driven westbound playthrough.

The original generic native gate is preserved as red for `unchanging-captures`: the two images were both recorded after the old ending at76.8/77.3seconds. The native player nevertheless completed78simulation seconds with zero runtime errors, a successful compile, complete scene inventory and an actual survey file. Scoped geometry qualification records that evidence separately; it does not turn the old generic result into a gameplay PASS. Wall time was99.79seconds, distinct from simulation and active play time.

[Source/build identity, original hashes and measured routes](../diagnostics/counter-exfil-2026-10-07/native-preflight.json). The next step is the fixed one-incident local implementation and independent input-driven acceptance, including turning, contact interruption, escape, death, reset and existing regressions.
