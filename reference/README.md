# Licensed source references

**Unintegrated and untested.** These are selected source files and excerpts for later qualification, not a playable foundation or an active loop. No engine project, launch script, model client, cron job, dependency install, or paid-service integration is supplied.

[IMPORT-MANIFEST.json](IMPORT-MANIFEST.json) records each upstream commit, file/blob, source SHA-256, excerpt range where applicable, local SHA-256, modifications, and full license location. Imports retain upstream text unless the manifest explicitly describes an excerpt wrapper. [Dependency pins](../docs/DEPENDENCY-PINS.json) record framework references without vendoring or installing them.

| Imported component | Included source | Integration gaps and limits |
| --- | --- | --- |
| Ralph diagnostics | Exact stdlib `stuck_detector.py` | Reads legacy trajectory fields; no inference or mutation. Suggestions and legacy three/four-event thresholds are historical, not this project's two-failure intervention policy. Schema/error handling needs qualification. No marker replay runner or overseer launcher imported. |
| Grindline input bridge excerpt | `_inject_input` and `_key_for`, with an explicit `SceneTree` wrapper | Real input events and physics-frame waits only; no original game's scene loading, probes, assertion dispatcher, time acceleration, or acceptance authority. Key aliases are skating-specific and include repeated match aliases; replace/qualify them against the approved input contract. |
| Space-salvage verification excerpts | Parse-error marker string and timeout/exit-code fragment | Reference text only. Original wrappers omit some paths and do not establish complete failure detection or assertion completion. No `env.sh`, absolute host path, or runnable wrapper copied. Add full diagnostics, nonzero-exit handling, required assertion IDs, and red tests later. |
| GDQuest camera | Exact MIT camera script | Requires named camera/pivot/spring-arm/raycast nodes, input actions, and an anchor exposing `_ground_height`. Qualify clamp bounds, camera initialization, obstruction and transitions. Full movement player remains a pinned candidate because it couples weapons, UI, scenes, skin and audio. No restricted textures/models or demo scene copied. |
| Easy Vehicle Physics | Exact `vehicle.gd`, `wheel.gd`, `vehicle_controllergd.gd` | A source-only `Vehicle`/`Wheel`/input-controller set. Needs authored body/wheel hierarchy, four wheel references, collider, surface configuration, input maps, physics tuning and custom art. Global class names may collide with future code. No demo vehicle, audio, UI, smoke, camera or scene assets copied. No possession or AI driving integration yet. |

The vehicle scripts preserve Dechode/Baron Wittman lineage comments and David Shoemaker's full multi-author MIT notice. GDQuest's full upstream license is retained for transparency; its CC BY-NC-SA art is excluded. Each other imported component has its original full license alongside it.

The overseer pattern remains a [pinned source reference](https://github.com/oh-ashen-one/ralph-loop-playbook/tree/11f068df8fd2c260d7490adf300dff5cc7067821/overseer): read-only evidence packets, structured proposals, capped trusted execution, and an audit trail. Machine-specific paging, scheduling, process management and model calls were not imported.

## Safe source audit

Run `python3 tools/verify_imports.py` from the repository root to check local hashes, notice files, pinned commit syntax, and unexpected vendor files. This validator uses only the Python standard library, reads files, and does not import or execute vendor code, contact a network, launch an engine, or prove runtime compatibility.

Future integration requires the user's separate start authorization, engine/version selection, dependency review, intentional red tests, actual input/physics/rendered qualification, and a provenance entry. Hash equality establishes faithful source copying, not correctness.
