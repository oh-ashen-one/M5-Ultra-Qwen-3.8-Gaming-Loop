# Flash-Next functional evidence

Verified 2026-10-05 on the M5 Ultra. **Two fresh inference requests passed; the game loop remains held.**

- [Settings audit](omlx-settings-audit.json): 13 CPU fixtures using the installed oMLX settings/effort functions and exact model template; thinking/xhigh, preserved reasoning, sampling and disabled optimizations verified without accelerator imports.
- [Warm-up receipt](warmup-receipt.json): original Unity image recognition, one parsed inert tool call, private reasoning replay, tool-result continuation and final `READY`. The model named the blue sphere on the left and red cube on the right without those identities in its prompt.
- [Service snapshot](service-snapshot.json): read-only health/status after warm-up; one resident model, exactly two requests, no active or waiting request.
- [Original Unity frame](../unity-2026-10-04/unity-frame.png): SHA-256 `45d5d0c0dbb093bec809cd674dad51f3360cded758cb26def6590e5c4610a148`. Existing original test geometry; no external art imported.

The [supervisor](../../tools/flash_next_resident.py) and [warm-up script](../../tools/flash_next_warmup.py) implement bounded preparation only. Their machine-local token, model manifest and work directory are required inputs. The supervisor also uses the existing `warmup_resident.py` and `unity_smoke.py` helpers beside it. These scripts are not an overnight game controller or a general tool executor.

No raw reasoning, credentials, private paths, model weights or private logs are included. Request timings are incidental functional receipts, not benchmark claims. Earlier 27B results do not establish Flash-Next game-editing or engine-tool reliability. See [current readiness and blockers](../../docs/FLASH-NEXT-READINESS.md).
