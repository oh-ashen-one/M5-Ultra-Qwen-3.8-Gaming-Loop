# Asset pipeline

Production workflow remains held for the explicit game start. A separately authorized disposable connector scene tests original mesh/material authoring and export; it is not production art or evidence of final rig/animation quality.

## Direction and provenance

Start from an approved art brief: environment/story tone, palette, character/vehicle silhouettes, measured proportions, materials, plausible lighting, and representative gameplay-camera compositions. **All eventual 3D assets must be authored by local Qwen using Blender from scratch**, including models, materials, rigs and animation. The precise visual theme is still open.

Meshy, Tripo and premade asset packs are excluded. Older assisted-generation recommendations are superseded. A Blender adapter must not silently call external asset services or import demo art. Original test material is MIT; third-party tool/model licenses remain separate.

For each asset, record local model/runtime/settings, approved brief, authoring script and edit history, source/export hashes, rights/license, intended use and final engine resource. Preserve editable `.blend` files and reproducible scripts. Log any cloud or human intervention separately rather than attributing it to local Qwen. Never use ripped Rockstar content or unreviewed demo art.

## Local Qwen → Blender → Unity

| Stage | Checks and deliverables |
| --- | --- |
| Original authoring pilot | Local Qwen creates one representative asset per important class from an empty Blender scene; measured silhouette, topology and materials match the approved brief before a batch |
| Geometry cleanup | Remove broken/duplicate geometry; check normals, manifold needs, smoothing, mesh density, and deformation topology |
| Scale and orientation | Real dimensions, consistent units/axes, applied transforms, meaningful names, stable origin/pivots; wheel/door/character roots placed deliberately |
| UVs and materials | Inspect UV coverage/seams, texture resolution and color space, PBR maps, material slots, and engine shader compatibility |
| Rig | Rest pose, bone hierarchy/names, weights, root motion policy, sockets, foot placement, and vehicle interaction alignment |
| Animation | Named clips and durations; idle/walk/run/turn, vehicle enter/exit and driving poses as required by the approved brief; retargeting, looping and blend transitions checked |
| Runtime packaging | Appropriate LODs, texture/memory budgets, simple colliders, collision layers, navigation relevance, export settings, and asset manifest |
| Engine validation | Reimport in the selected engine; compare gameplay views; test animation/IK, collision, camera clearance, lighting response, and real rendered performance |

Choose the export format after the exact Unity version/import adapter is qualified. FBX is a native-import candidate; GLB/glTF requires a compatible selected importer. A successful Blender export proves neither Unity import nor material fidelity. Preserve editable `.blend` sources.

## Engine acceptance

The gameplay scene is the final authority. Validate character height against doors/vehicles, wheel/seat/pivot alignment, grounded feet, collision shape, camera clipping, texture appearance, animation transitions, and frame-time impact. Render against the approved concept at comparable angles, then capture again after optimization.

An asset preview does not prove engine readiness, and importing a rig does not prove gameplay integration. Acceptance must observe the selected player mesh, animation clips and transitions in the actual movement/vehicle path.

Temporary primitives may establish gameplay foundations. They must be replaced before final visual acceptance. Audio needs the same provenance discipline: licensed/custom effects, ambience and music, engine playback checks, levels, spatial cues and transitions. No audio provider or generation budget has been selected.

## Future adapter controls

Pin and qualify the actual Blender control adapter. Keep a future MCP bridge local and project-scoped; constrain Python/file/network access and export paths. Consider upstream safe mode and `DISABLE_TELEMETRY=true` during qualification. The M5 inventory found Blender 5.2.0 but no installed MCP addon/server; the disposable test uses existing headless CLI control. No adapter installation is authorized by that test.
