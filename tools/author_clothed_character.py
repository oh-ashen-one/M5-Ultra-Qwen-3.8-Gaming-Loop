#!/usr/bin/env python3
"""Save a bounded local original character before early export/native inspection."""
import ast
import json
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.visual_context import TARGETS, contract

ACCEPTED = 'de0b3360fa7d7a1722aa981ee4dbf3a1c223ccd7'
ART = 'Art/player.py'
TASK = dict(id='clothed-character-and-motion', phase='polish', polish=True,
    visual_facing=True, outcome='Original clothed human with actual native motion; protected accepted gameplay')
STOP = 'Halt: One Counter-Exfil incident accepted after native and actual-pixel proof; preserve this checkpoint and report remaining full-game limitations'
SAVED = 'Halt: Local clothed character source saved; unload the idle resident, export and inspect native pixels before runtime animation'


def validate_boundary(old):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        source_checkpoint=ACCEPTED, last_playable_checkpoint=ACCEPTED,
        current_round='q0184-e64fca5c', task_index=7, task_failures=24,
        failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker=STOP)
    if any(old.get(k) != v for k, v in expected.items()) or old.get('clothed_character_author_attempted'):
        raise Halt('Require accepted incident fallback and the unchanged stopped owner/history')
    acceptance = old.get('counter_exfil_scoped_acceptance', {})
    if acceptance.get('candidate') != ACCEPTED or not acceptance.get('accepted_utc'):
        raise Halt('Require actual scoped acceptance before this presentation pass')


def validate_art(content):
    if not isinstance(content, str) or not content.strip() or len(content.encode()) > 36000 or len(content.splitlines()) > 700:
        raise ValueError('Save one complete Blender script under 36 KB/700 lines')
    tree = ast.parse(content, filename=ART)
    allowed = {'bpy', 'bmesh', 'math', 'mathutils', 'random'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(n.name.split('.')[0] not in allowed for n in node.names):
            raise ValueError('Only existing Blender/math APIs; no external assets or filesystem/network imports')
        if isinstance(node, ast.ImportFrom) and (node.module or '').split('.')[0] not in allowed:
            raise ValueError('Only existing Blender/math APIs')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'open', 'exec', 'eval', '__import__'}:
            raise ValueError('The fixed adapter handles export; no arbitrary file/code loading')
    for token in ('bpy.ops.wm.', 'bpy.ops.import_', 'bpy.ops.export_', 'bpy.data.libraries.load', 'bpy.data.images.load'):
        if token in content:
            raise ValueError('Author original geometry only; adapter owns import/export and files')
    return content


class ClothedCharacter(CapacityAuthor):
    def validate_recovery(self, old):
        validate_boundary(old)
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(clothed_character_author_attempted=True,
            recovery_route='local-original-clothed-character-early-artifact',
            recovery_change='Accepted de0 source/build stays fallback. Use real native/reference pixels, original local Blender authorship and xhigh. Save one complete articulated clothed model now, export/preview before animation integration; protect all current C# and fixed cap.')

    def work(self):
        ident = self.begin(TASK, 'local-clothed-character-source')
        files = Files(self.project, self.store)
        original = files.path(ART).read_text()
        preimage = sha(files.path(ART).read_bytes())
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        images = [('AI-GENERATED ART TARGET '+name+'; aspiration, not game output', self.refs/name)
                  for name in (TARGETS[0], TARGETS[2])]
        for label, path in [
            ('FRONT reset at92s', 'q0182-0282975a-death-active-runners/captures/frame-003.png'),
            ('BACK Armed at77s', 'q0181-016a3dd5-old-healthy/captures/frame-007.png'),
            ('COMBAT after shots at107.6s', 'q0181-016a3dd5-success/captures/frame-005.png')]:
            images.append(('ACTUAL NATIVE accepted de0 '+label, self.store.root/'evidence'/path))
        packet = contract(images, [TARGETS[0], TARGETS[2]], 3)
        proof = {p: sha(p.read_bytes()) for _, p in images}
        def save(action, fields):
            content = validate_art(fields['content'])
            if sha(content.encode()) == preimage:
                raise ValueError('Save a substantive coherent character improvement')
            result = files.edit(action, ART, preimage, content=content)
            candidate = self.checkpoint_source('Local Qwen: original clothed articulated character source')
            outcome = dict(candidate=candidate, prior_playable=ACCEPTED, local_authored=True,
                script=ART, script_sha256=sha(content.encode()), native_verified=False,
                animation_integration='pending after early export/native inspection')
            atomic(self.store.root/'evidence'/(ident+'-character-source.json'), outcome)
            self.store.set(source_checkpoint=candidate, clothed_character_source_outcome=outcome,
                stage='clothed-character-source-saved')
            self.store.report()
            return result
        self.c.update(working_context_tokens=98304, output_tokens=16384, model_timeout_seconds=1200)
        result = self.model.session('builder', ident+'-clothed-character',
            'You are local Qwen, the sole original Blender character author. Deliver one complete usable source artifact through finish_source.',
            'Inspect the attached native front/back/combat pixels and neighborhood/alley targets. '
            'The current character reads as a segmented gray mannequin: separated ellipsoid muscles, bead-like joints, '
            'weak jacket/trouser shapes, skinny straight hanging arms even during shots. Target: coherent clothed human '
            'silhouette, relaxed bomber/work jacket with collar/hem/cuffs and readable cloth panels/folds, dark blue '
            'trousers, believable hands/head/hair, grounded shoes, natural proportions and connected joints. '
            'Do not merely recolor the same ellipsoids. Create original shaped mesh surfaces and sensible topology, '
            'restrained seams/creases/material separation. No external assets/textures/downloads/packages. '
            'Use the native camera scale: detail must read at current full-body size. Do not enlarge the body or '
            'change height to force the reference framing. The accepted camera, reticle and capsule stay fixed. '
            'The center reticle visually overlaps the present head in combat; improve body/weapon pose readability '
            'through articulation, not camera edits. Runtime aim will be implemented immediately after this export.\n'
            'THIS FIRST BOUNDED SAVE IS ONLY Art/player.py. Produce a complete articulated character now so the '
            'controller can export/import/preview early. Provide a usable armature or hierarchical shoulder/elbow/wrist '
            'and hip/knee/ankle pivots, torso/head articulation and right-hand weapon with consistent documented names '
            'and local axes. Meshes must remain visually connected when bending for idle/walk/jog/two-handed aim/seated '
            'driving. Avoid independent spheres that look dislocated. Preserve root convention player_root, +Z up, '
            '+Y forward, meters, feet at Z=.79 under root and about1.8m anatomical height, because Unity subtracts .79 '
            'on import. Correct parent-local/world coordinates once; no doubled offsets. You may retain the old '
            'head_root/armL_root/armR_root/legL_root/legR_root names and add nested articulation. Document axis/rest '
            'contracts concisely in source for your subsequent Unity animation pass. Do not add colliders, cameras or '
            'lights. The same prefab also supplies rivals; keep visible body geometry inside its existing capsule '
            'envelope and material names stable/readable. All current C# and other assets are protected.\n'
            'The fixed Blender adapter runs this script in factory-startup, saves editable .blend then exports '
            'FBX with add_leaf_bones=False; authoring script must not read/write files or invoke export. Supported '
            'Blender5.2 APIs: use mathutils.Euler(...).to_matrix().to_4x4(), not Matrix.Euler. Use bpy/bmesh/mathutils '
            'only as needed. Save in the next response with finish_source: max36KB/700lines; thinking enabled xhigh, '
            '16384tokens. No broad planning essay, no camera or mission work.\nEXACT CURRENT SCRIPT:\n'+original,
            [tool('finish_source', 'Save the complete original articulated clothed Blender character; early export follows.',
                {'content': {'type': 'string'}})], {'finish_source': save},
            images=images, visual_contract=packet, turns=2, reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-character-author.json'), result)
        if any(sha(p.read_bytes()) != h for p, h in {**protected, **proof}.items()):
            raise Halt('Protected game source or supplied visual evidence changed')
        if not result.get('ok') or sha(files.path(ART).read_bytes()) == preimage:
            raise Halt('No complete local character source saved; preserve output and diagnose: '+json.dumps(result))
        raise Halt(SAVED.removeprefix('Halt: '))


if __name__ == '__main__':
    raise SystemExit(main(ClothedCharacter))
