# Coupe verification and continuous-corridor work

The next management priority is a continuous usable street corridor from existing original Blender assets. The tested route must stay within visible road/sidewalk/building edges; more camera micro-polish is not the goal. Native start/middle/end frames are compared with the private Chicago reference. Target images remain private; images in this folder are actual game output.

## Coupe: correct resource and actual instance

The source at `8423ad6` used the nonexistent `Generated/vehicle/coupe` resource. Local Qwen corrected it to `Generated/coupe/scene` in `ebdb584`, matching the real `Assets/Resources/Generated/coupe/scene.fbx` asset. Inspection then found that `Coupe()` was only an unused helper: correcting a resource string alone did not place a car.

After the parent's focused instruction was queued for the next round, local Qwen [saved the actual invocation and placement at `47bc042`](https://github.com/oh-ashen-one/M5-Ultra-Qwen-3.8-Gaming-Loop/blob/47bc04266b0e88ecd21eede5ade269b1a0b0b038/game/Assets/Game/Bootstrap.cs). The coupe is parked at `(3.6, 0, 8)` using its existing imported mesh and materials. [Native grounding/walking passes](coupe/gate.json): four frames and **18.909 m** horizontal movement.

The blue coupe is visibly present in the [middle frame](coupe/frame-001.png) and [end frame](coupe/frame-003.png). The [start frame](coupe/frame-000.png) still shows the original short sidewalk. These images also show the unresolved gap: dressing is concentrated near the facade and the end of the route remains mostly empty ground. This is verified car placement, **not** a successful continuous corridor or completed game.

## Measured layout corrections

The existing sidewalk measures approximately **14 × 0.14 × 3.2 m**, while the recorded route spans world X **0 to 3.2003 m** and Z **1.7 to 20.3354 m**. Existing L-track rails span approximately **28.6 m** along the asset's original world-X direction. Both assets need deliberate alignment with the route and preserved import transforms.

Local candidate `4abfc978` aligned Props using absolute Euler angles, overwriting its imported FBX orientation. Native measurements rejected that visual result: an 8 m vertical pier became an 8 m horizontal object, and rail/walkway heights were wrong. The next local edit, `341ed1b`, applies world-Y yaw relative to the original imported orientation; native pier bounds are again approximately **1.05 × 8 × 1.05 m**.

The Street module acquired the equivalent absolute-rotation defect in `3a66b6e`. Its measured cornice center fell to Y **−0.14 m**, so the same one-line import-preserving correction is queued before extending surfaces. Player and ground physics remain intact. Failed visual candidates and their native evidence are preserved.

## Ownership and acceptance

Management focus is added to the next task read while the current healthy edit/build/critic completes. No competing owner or inference request was started, and no game code was written in the cloud. Local Qwen continues substantive planning, low-effort mechanical edits with thinking enabled, and fresh rendered critique. The original full-task acceptance, no-accepted-progress deadline at **11:37:50 UTC**, and overall **21:37:50 UTC** ceiling remain unchanged.

As of **11:16 UTC**, the coupe is visually verified, Props are upright and aligned along the route, and the Street correction plus continuous visible corridor remain in progress. No corridor or full-game acceptance is claimed.
