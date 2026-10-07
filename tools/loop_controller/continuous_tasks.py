"""Owner-authorized sequence: existing playable baseline through whole-route polish."""
from .continuous_checks import WORLD_PROBE, MOTOR_PROBE

BASELINE = '754dd5956cb5a24c18507aef638c29c4781baa53'
TASKS = [
    dict(id='world-collision', phase='foundation', checks=['world_collision'], probe=WORLD_PROBE,
         outcome='Keep grounded walking while real colliders stop the player at existing buildings, props and street boundaries.',
         instructions='Add one compact installed C# world-collision module. Use existing mesh-local bounds for major facade, '
         'pier, bin and fence BoxColliders, preserving imported transforms. Do not add collision to every tiny trim mesh. '
         'Existing visible Pavement spans X-1..6,Z-2..30,top Y0.14. Bound traversal to that visible area and use existing '
         'original fence meshes to make end barriers understandable. Keep the center walking corridor clear. '
         'The external replay holds W4..16s then A18..23s: movement must stop at real forward and western obstacles while '
         'input stays held, without penetrating or leaving the rendered pavement. Preserve the original 19m walking route, '
         'camera, spawn, coupe, materials and asset files. The module must actually be installed from Bootstrap.Create.'),
    dict(id='vehicle-collision-reset', phase='driving', checks=['motor_reset'], probe=MOTOR_PROBE,
         outcome='Collision-safe forward driving, usable exit and R reset of actual player and vehicle state.',
         instructions='Extend the existing VehicleInteraction. Replace unrestricted horizontal root translation with '
         'collision-safe swept movement using an upright physical vehicle body. Preserve its visual front heading. '
         'Do not let ground probes hit the vehicle itself. Keep E near-car entry and a clear, grounded E exit. '
         'R must restore the player at (0,0.3,1.7), car at (3.6,0,8), orientations, zero speed, visible player, enabled '
         'Walker/CharacterController, camera follow, foot mode and health. Let gravity settle the player. Increment Restarts '
         'only on this real reset. Keep LoopSignals.Vehicle registered to the actual root even on foot so reset is observable. '
         'External test: W4..5.6,D5.6..6.6,E7.2,W8..18 against the end boundary,E21,R24,W27..29. '
         'The car must stop physically under held throttle by16s; reset must restore positions and later walking must work.'),
    dict(id='connected-mission', phase='mission', checks=['mission_complete'], maximum=150, coverage='mission-core', design=True,
         outcome='A rough connected objective, pickup, drive/delivery and clear ending in the existing block.',
         instructions='Choose a concrete small original Chicago courier mission using the existing street/player/coupe/props. '
         'Start with a visible objective, require actual proximity/input pickup and driving to a distinct destination, then '
         'show an unmistakable ending. Use F for interaction if needed, preserve E and R. Add a camera-visible TextMesh HUD '
         'with a short objective, status and controls. Use built-in LegacyRuntime.ttf if a font is needed; no UI/TMP packages. '
         'This is a short rough route before expansion to ten minutes; do not pad with waiting. Provide a deterministic input '
         'replay that genuinely completes this route through normal controls, with captures at meaningful transitions. '
         'Mission signals must follow real gameplay. No replay inspection, clock-only completion or fabricated telemetry.'),
    dict(id='mission-failure-retry', phase='mission', checks=['mission_complete','failure_retry'], maximum=180, coverage='mission-core',
         outcome='An understandable mission failure can be retried with R and completed in the same native session.',
         instructions='Add a meaningful failure condition for the existing mission, communicate why it failed and how to retry. '
         'R must reset objective inventory, timers, actors and any mission state along with the existing physical reset. '
         'Provide a normal-input replay that first genuinely fails, then presses R, follows the objective and reaches its ending. '
         'Do not expose a fake acceptance shortcut or special replay-only branch. Keep the failure deadline usable for a human.'),
    dict(id='mission-combat-pursuit', phase='combat', checks=['mission_complete','combat','pursuit'], maximum=180, coverage='combat',
         outcome='Readable input-driven combat and an escapable pursuit belong to the connected mission.',
         instructions='Add a small original rival encounter and pursuit needed by the mission. Reuse the existing original '
         'player and coupe meshes; no new asset generation. Mouse0 fires through an actual aim/hit path at rendered collidable '
         'rivals; hits must reflect real target damage. Opponents must visibly act; pursuit rises from an actual encounter and '
         'clears through a reachable escape condition. Use camera-relative aiming appropriate to the unlocked native view. '
         'Preserve objective/ending and R retry. Provide a replay with walking, vehicle entry/drive/exit, a real hit, pursuit '
         'start/escape and ending. Keep modules small; save one concrete implemented mechanic at a time.'),
    dict(id='mission-hud-audio', phase='mission', checks=['mission_complete','combat','pursuit','hud_audio'], maximum=180, coverage='combat',
         outcome='Coherent objective/health/wanted presentation and original audible gameplay cues support the mission.',
         instructions='Make the native camera render the HUD: camera-child TextMesh or a qualified camera-space solution. '
         'Show Objective, Health and Wanted clearly with controls and ending/retry. Add original procedural audio for footsteps, '
         'engine, combat and mission cues with coherent level balance, using actual AudioSources/AudioListener. No downloaded '
         'audio. Keep input usable and views readable; do not add art volume. Submit the connected normal-input mission replay.'),
    dict(id='rough-whole-route', phase='mission', checks=['mission_complete','failure_retry','combat','pursuit','hud_audio'],
         maximum=240, coverage='combat',
         outcome='A single rough route exercises walking, driving, encounter, pursuit, failure/retry and ending together.',
         instructions='Integrate the existing modules without adding new features. Fix the biggest route-breaking issue from '
         'actual feedback, then submit one connected input replay covering the objective, physical movement, fire/hit, pursuit '
         'and escape, genuine failure, R retry and successful ending. A short complete rough route is the goal of this stage.'),
    dict(id='chicago-polish-whole-route', phase='polish',
         checks=['mission_complete','failure_retry','combat','pursuit','hud_audio','whole_route'], maximum=720, coverage='whole-route',
         polish=True, design=True,
         outcome='Polish the connected route against Chicago references and qualify a roughly ten-minute playable mission.',
         instructions='The rough connected mission now exists. Prioritize camera/controls, coherent Chicago architecture, '
         'lighting, character/vehicle presentation, audio, combat readability and useful ten-minute mission pacing against '
         'the supplied visual target. Improve the four existing original Blender assets as needed; no new asset volume. '
         'Expand meaningful objectives/interactions, not waiting or idle padding. Actual first mission ending should occur '
         'around540..660seconds; include an early failure/retry if necessary and finish within720seconds. Supply captures '
         'across meaningful transitions and normal input replay. This remains reviewable evidence, not a claim of AAA parity.')
]
