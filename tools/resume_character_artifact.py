#!/usr/bin/env python3
"""Save one original character, export it, then stop at actual native inspection."""
import ast
import json

from resume_reference_visuals import ReferenceVisuals, SOURCE, ACCEPTED, ART
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone
from loop_controller.model import tool
from loop_controller.visual_context import TARGETS, contract

PRIOR = 'q0127-50cd61d4'
SESSION = PRIOR + '-coherent-visual-author'
TASK = dict(id='original-character-artifact', phase='polish', polish=True,
            visual_facing=True, outcome='One saved original character, Blender export and native visual inspection')


def validate_boundary(old, response, outcome):
    expected = dict(status='paused', controller_pid=None, source_checkpoint=SOURCE,
        last_playable_checkpoint=ACCEPTED, current_round=PRIOR, task_index=7,
        task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='local-reference-character-camera')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('focused_character_attempted'):
        raise Halt('Require the original stopped visual request and preserved source/history')
    if not old.get('blocker', '').startswith('Halt: Reference-backed visual source saved incompletely;'):
        raise Halt('Preserve any unrelated stop or resource fault')
    choices = response.get('choices', [])
    if len(choices) != 1 or choices[0].get('finish_reason') != 'length' or outcome.get('bounded_stop') != 'output':
        raise Halt('This recovery applies only to the completed output-budget stop')
    if choices[0].get('message', {}).get('tool_calls'):
        raise Halt('Inspect and preserve returned public tool calls before requesting replacement work')
    if (choices[0].get('message', {}).get('content') or '').strip():
        raise Halt('Inspect returned public content for usable source before requesting replacement work')


def validate_character(content):
    if not isinstance(content, str) or not content.strip() or len(content.encode()) > 32000 or len(content.splitlines()) > 650:
        raise ValueError('Submit one complete character script, at most 32 KB and 650 lines')
    try:
        ast.parse(content, filename=ART)
    except SyntaxError as error:
        raise ValueError(f'Complete Python source required: line {error.lineno}: {error.msg}') from error
    return content


class CharacterArtifact(ReferenceVisuals):
    def validate_recovery(self, old):
        self.prior_session = self.store.root / 'private/sessions' / SESSION
        response_path = self.prior_session / 'response-000.json'
        outcome_path = self.store.root / 'evidence' / (PRIOR + '-visual-author.json')
        validate_boundary(old, read_json(response_path), read_json(outcome_path))
        self.prior_proof = {str(p.relative_to(self.store.root)): sha(p.read_bytes())
            for p in (response_path, self.prior_session / 'history.json', outcome_path)}
        self.before = self.store.root / 'evidence/q0126-657b9ebf-positive'
        receipt = read_json(self.store.root / 'evidence' / (PRIOR + '-prior-isolation-reevaluation.json'))
        self.proof = receipt['original_files']
        if not receipt['result'].get('passed'):
            raise Halt('Require the preserved native baseline and separately recorded isolation reevaluation')
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def wait_for_capacity(self):
        self.capacity.wait('local-focused-character-source')

    def recovery_settings(self):
        return dict(focused_character_attempted=True, recovery_route='one-complete-character-then-native-inspection',
            recovery_change='Preserve the original budget-limited response and reasoning privately. '
            'Supply exact existing character source and relevant target/native pixels; save one complete source '
            'with its pinned preimage, export automatically, then inspect native output before camera work.')

    def work(self):
        ident = self.begin(TASK, 'local-focused-character-source')
        for name, digest in {**self.proof, **self.prior_proof}.items():
            if sha((self.store.root / name).read_bytes()) != digest:
                raise Halt('Preserved response or original native evidence changed')
        atomic(self.store.root / 'evidence' / (ident + '-preserved-prior-output.json'),
               dict(original_files=self.prior_proof, private_reasoning_preserved=True,
                    public_source_extracted_from_reasoning=False))
        files = Files(self.project, self.store)
        original = files.path(ART).read_text()
        preimage = sha(files.path(ART).read_bytes())
        integration = '\n'.join(files.path('Assets/Game/Bootstrap.cs').read_text().splitlines()[40:74])
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*.cs')}

        def save(action, fields):
            content = validate_character(fields['content'])
            if sha(content.encode()) == preimage:
                raise ValueError('Save a substantive original character revision, not the unchanged source')
            result = files.edit(action, ART, preimage, content=content)
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: save complete original character'),
                           stage='original-character-source-saved')
            self.store.report()
            return result

        images = [('AI-GENERATED CHARACTER/ART-DIRECTION TARGET; not native output', self.refs / TARGETS[0]),
                  ('BEFORE ACTUAL NATIVE character at t=3.2s', self.before / 'captures/frame-000.png')]
        required = contract(images, [TARGETS[0]], 1)
        self.c.update(working_context_tokens=65536, output_tokens=8192, model_timeout_seconds=1200)
        result = self.model.session('builder', ident + '-complete-character-source',
            'You are local Qwen, the sole original Blender character author. Save the complete source now.',
            'Deliver ONE coherent original character by calling finish_source with the complete replacement '
            'Art/player.py. The exact current source is supplied below and its preimage is already pinned; '
            'no read call or hash transcription is needed. Save the usable artifact in your next response. '
            'Thinking is enabled at medium with8192 output tokens; use it to make the source, not a long essay. '
            'The controller immediately exports your source and captures the real Unity result.\n'
            'Compare the attached reference and actual native character. Replace the crude box/sphere body '
            'with a substantially better original silhouette: proportioned torso/pelvis, tapered rounded limbs '
            'and joints, shoes, hands, head/hair, jacket/trousers with coherent material separation and restrained '
            'clothing detail. Resolve doubled parent offsets. Construct the meshes yourself through Blender; '
            'no external assets, downloads, packages or generated-image services. This is a complete character '
            'deliverable, not a recolor or isolated tiny patch.\n'
            'Use Blender +Z up and +Y forward, about1.8m anatomical height. Set world versus parent-local '
            'coordinates consistently; do not move a world-space pivot again by reparenting with its old local '
            'offset. Retain sensible named player_root/head_root/armL_root/armR_root/legL_root/legR_root pivots. '
            'The exact Unity integration below applies imported-asset correctionY=-0.79. Account for this '
            'existing translation in the exported presentation-root placement so native feet are grounded '
            'and the character fits its1.75m controller. Do not simply export feet atZ=0 and then bury them '
            'with the unchanged Unity offset. You cannot edit the integration or any C#. Camera, hits, '
            'mission, collision and movement remain unchanged. '
            'The same original visual is cloned for rivals. Avoid scene cameras/lights, filesystem reads/writes '
            'and networking; the fixed adapter saves the editable .blend and FBX after the script completes. '
            'Use existing Blender bpy/math/mathutils/bmesh APIs as needed. Maximum650lines/32KB; keep the code '
            'compact enough to save completely. Camera work follows only after this asset is exported and viewed.\n'
            'EXACT EXISTING UNITY IMPORT/PLACEMENT CONTRACT:\n' + integration + '\n'
            'CURRENT COMPLETE CHARACTER SOURCE:\n' + original,
            [tool('finish_source', 'Save the complete original character source; export follows automatically.',
                  {'content': {'type': 'string'}})], {'finish_source': save},
            images=images, visual_contract=required, turns=2, reasoning_effort='medium')
        atomic(self.store.root / 'evidence' / (ident + '-character-author.json'), result)
        if not result.get('ok') or sha(files.path(ART).read_bytes()) == preimage:
            raise Halt('Focused character source was not saved; preserve output and diagnose: ' + json.dumps(result))
        if any(sha(p.read_bytes()) != digest for p, digest in protected.items()):
            raise Halt('Character-only author changed protected gameplay source')
        self.store.set(stage='export-original-character'); self.store.report()
        exported = self.engines.blender(self.project, ART, ident + '-character-export')
        atomic(self.store.root / 'evidence' / (ident + '-character-export.json'), exported)
        candidate = self.checkpoint_source('Local Qwen: export complete original character')
        self.store.set(source_checkpoint=candidate); self.store.report()
        if not exported.get('ok'):
            raise Halt('Original character saved but Blender export failed; preserve source and diagnostics')
        original_probe = read_json(self.before / 'captures/scenario.json')
        scenario = dict(id='focused-character-preview', coverage='foundation', duration=18,
            steps=[step for step in original_probe['steps'] if step['end'] <= 18], captures=[3.2, 10, 17])
        bundle = self.store.root / 'evidence' / (ident + '-character-preview')
        self.store.set(stage='native-original-character-preview'); self.store.report()
        gate = self.engines.unity(self.project, bundle, scenario, candidate)
        frames = sorted((bundle / 'captures').glob('frame-*.png'))
        result = dict(candidate=candidate, export=exported, native_gate=gate,
                      evidence=str(bundle.relative_to(self.store.root)), camera_changed=False,
                      visual_review='pending actual pixel inspection', gameplay_promotion=False,
                      final_game_accepted=False)
        atomic(bundle / 'character-artifact.json', result)
        self.store.set(character_artifact_outcome=result); self.store.report()
        if frames:
            queue_milestone(self.store, 'native-milestone', TASK, bundle, gate, frames,
                            {f'frame-{i:03d}.png': t for i, t in enumerate(scenario['captures'])})
        raise Halt('Original character export and native preview preserved; inspect actual pixels before camera work')


if __name__ == '__main__':
    raise SystemExit(main(CharacterArtifact))
