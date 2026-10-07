# Coupe verification and continuous-corridor work

The next management priority is a continuous usable street corridor from existing original Blender assets. The tested route must stay within visible road/sidewalk/building edges; more camera micro-polish is not the goal. Native start/middle/end frames are compared with the private Chicago reference. Target images remain private; images in this folder are actual game output.

## Coupe: correct resource and actual instance

The source at `8423ad6` used the nonexistent `Generated/vehicle/coupe` resource. Local Qwen corrected it to `Generated/coupe/scene` in `ebdb584`, matching the real `Assets/Resources/Generated/coupe/scene.fbx` asset. Inspection then found that `Coupe()` was only an unused helper: correcting a resource string alone did not place a car.

After the parent's focused instruction was queued for the next round, local Qwen [saved the actual invocation and placement at `47bc042`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/blob/47bc04266b0e88ecd21eede5ade269b1a0b0b038/game/Assets/Game/Bootstrap.cs). The coupe is parked at `(3.6, 0, 8)` using its existing imported mesh and materials. [Native grounding/walking passes](coupe/gate.json): four frames and **18.909 m** horizontal movement.

The blue coupe is visibly present in the [middle frame](coupe/frame-001.png) and [end frame](coupe/frame-003.png). The [start frame](coupe/frame-000.png) still shows the original short sidewalk. These images also show the unresolved gap: dressing is concentrated near the facade and the end of the route remains mostly empty ground. This is verified car placement, **not** a successful continuous corridor or completed game.

## Measured layout corrections

The existing sidewalk measures approximately **14 × 0.14 × 3.2 m**, while the recorded route spans world X **0 to 3.2003 m** and Z **1.7 to 20.3354 m**. Existing L-track rails span approximately **28.6 m** along the asset's original world-X direction. Both assets need deliberate alignment with the route and preserved import transforms.

Local candidate `4abfc978` aligned Props using absolute Euler angles, overwriting its imported FBX orientation. Native measurements rejected that visual result: an 8 m vertical pier became an 8 m horizontal object, and rail/walkway heights were wrong. The next local edit, `341ed1b`, applies world-Y yaw relative to the original imported orientation; native pier bounds are again approximately **1.05 × 8 × 1.05 m**.

The Street module acquired the equivalent absolute-rotation defect in `3a66b6e`. Its measured cornice center fell to Y **−0.14 m**. Local `95a11d3` applies the same import-preserving correction; the cornice returns to approximately Y **8.9 m**. Player and ground physics remain intact. Failed visual candidates and their native evidence are preserved.

Local `4712eba` moved the Props assembly to the east edge, and `122f23e` added a second aligned Street section. Their centres are Z 7 and 21 m, extending the facade/sidewalk row over approximately Z 0–28 m. All substantive game changes came from local Qwen; cloud work supplied measured supervision and controller infrastructure.

## Actual corridor result

Latest source: [`122f23eb3c024d23ff5d8f78505bc398076500f4`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/commit/122f23eb3c024d23ff5d8f78505bc398076500f4).

| Replay position | Actual native image | Observed result |
| --- | --- | --- |
| Start, 3.2 s | [frame-000.png](extended-row/frame-000.png) | Upright facade and visible sidewalk; road remains unrendered. |
| Middle, 6 s | [frame-001.png](extended-row/frame-001.png) | Existing blue coupe is plainly visible beside the sidewalk/facade row. |
| End, 15 s | [frame-003.png](extended-row/frame-003.png) | Facades and sidewalk continue, but the player is outside the paved width on brown background. |

The [unchanged native gate](extended-row/gate.json) records successful compilation/execution, four captures, stationary grounding, **18.95 m horizontal movement**, and 0.158 m vertical change. FPS, HUD and audio remain unqualified by this capture route. Each published image is hash-matched to the original run evidence; [hashes and safe request counts](closeout.json) are retained.

Length is now sufficient for the tested route. Width is not: aligned sidewalks span approximately **X −0.8 to 2.4 m**, but the route reaches **X 3.2003 m**, with a controller radius of 0.32 m. The original collision ground's renderer is removed, so collision success cannot establish visible road coverage. The next local edit must add bounded visible pavement across the full route with clearance, reusing existing sidewalk geometry/materials and preserving ground height/physics. A created helper must also be invoked before it counts as integration.

Compared with the private Chicago neighborhood reference, these actual frames establish a longer facade row, car and street props. They still lack a coherent paved road, readable complete street composition, final materials and finished character presentation. The corridor remains **FIX**, and no full game task has passed. The local critic also returns FIX; its claim that only a 14 m module remains is stale relative to the two-section source and rendered row. The measured remaining surface gap is lateral coverage.

## Planner stop

At **11:27:05 UTC**, round `r0019-1920814d` stopped before saving source. The fresh `xhigh` planner used **5,959 prompt tokens and all 4,096 completion tokens in 99.7 seconds**, ending with `finish_reason: length` and **zero parsed tool calls**. The safe accounting contains no closing thinking marker or tool-call opening marker; raw response text and private reasoning are excluded. The controller's generic message says to inspect tool-format errors, but the observed failure is output-budget exhaustion, not a demonstrated malformed submitted plan. No identical retry was launched.

At 11:35 UTC the controller was absent and the existing resident model was healthy with one loaded model, zero active requests and zero waiting requests. The owner's separate Blender remained running. Source `122f23e` is published on `game/chicago-20261005`; earlier failure-record hashes remain unchanged.

## Ownership and acceptance

Management focus was added to the next task read while each healthy edit/build/critic completed. No competing owner or inference request was started, and no game code was written in the cloud. Local Qwen supplied substantive planning, low-effort mechanical edits with thinking enabled, and fresh rendered critique until the bounded stop. The original full-task acceptance, no-accepted-progress deadline at **11:37:50 UTC**, and overall **21:37:50 UTC** ceiling remain unchanged.

As of **11:35 UTC**, the coupe and extended upright row are verified, the usable corridor is incomplete, and execution is paused on the planner stall above. No corridor or full-game acceptance is claimed. Neither original deadline was extended or reset.
