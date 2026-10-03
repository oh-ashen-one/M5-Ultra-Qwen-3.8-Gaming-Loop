# Asset pipeline

Proposed workflow only. No assets have been generated, downloaded, rigged, animated, or imported for this project.

## Direction and provenance

Start from an approved art brief: environment/story tone, palette, character/vehicle silhouettes, measured proportions, materials, plausible lighting, and representative gameplay-camera compositions. Custom Meshy assets and Blender MCP cleanup/rigging/animation are user requirements. The precise visual theme is still open.

Meshy is a separate generation step; the proposed Blender MCP adapter is not assumed to include a Meshy connector. Before a future paid batch, verify the actual service terms, plan, output rights, commercial use, redistribution, and approved cost. A generated asset is not automatically covered by this repository's MIT license.

For each asset, record source/provider, creator, approved reference/prompt, generation/job ID where publishable, rights/license, edit history, content hash, intended use, and final engine resource. Retain original exports and editable Blender sources when rights permit. Never use ripped Rockstar content or unreviewed demo art.

## Meshy → Blender → engine

| Stage | Checks and deliverables |
| --- | --- |
| Generation pilot | One representative asset per important class; silhouette and proportions match the brief; topology/material output inspected before a batch |
| Geometry cleanup | Remove broken/duplicate geometry; check normals, manifold needs, smoothing, mesh density, and deformation topology |
| Scale and orientation | Real dimensions, consistent units/axes, applied transforms, meaningful names, stable origin/pivots; wheel/door/character roots placed deliberately |
| UVs and materials | Inspect UV coverage/seams, texture resolution and color space, PBR maps, material slots, and engine shader compatibility |
| Rig | Rest pose, bone hierarchy/names, weights, root motion policy, sockets, foot placement, and vehicle interaction alignment |
| Animation | Named clips and durations; idle/walk/run/turn, vehicle enter/exit and driving poses as required by the approved brief; retargeting, looping and blend transitions checked |
| Runtime packaging | Appropriate LODs, texture/memory budgets, simple colliders, collision layers, navigation relevance, export settings, and asset manifest |
| Engine validation | Reimport in the selected engine; compare gameplay views; test animation/IK, collision, camera clearance, lighting response, and real rendered performance |

Choose the export format only after the engine/version is selected. GLB/glTF is a candidate where supported; preserve the editable `.blend` source rather than treating an export as the only source of truth.

## Engine acceptance

The gameplay scene is the final authority. Validate character height against doors/vehicles, wheel/seat/pivot alignment, grounded feet, collision shape, camera clipping, texture appearance, animation transitions, and frame-time impact. Render against the approved concept at comparable angles, then capture again after optimization.

An asset preview does not prove engine readiness, and importing a rig does not prove gameplay integration. Acceptance must observe the selected player mesh, animation clips and transitions in the actual movement/vehicle path.

Temporary primitives may establish gameplay foundations. They must be replaced before final visual acceptance. Audio needs the same provenance discipline: licensed/custom effects, ambience and music, engine playback checks, levels, spatial cues and transitions. No audio provider or generation budget has been selected.

## Future adapter controls

Pin the Blender MCP release and verify the Blender/Python compatibility after start. Keep its bridge local and project-scoped; constrain Python/file/network access and export paths. Consider the documented safe mode and `DISABLE_TELEMETRY=true` during qualification. No Blender process, adapter installation, or configuration has been started or changed by this planning commit.
