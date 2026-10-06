#!/usr/bin/env python3
"""Local camera correction after inspected original-character export/native proof."""
import json
import re

from resume_reference_visuals import ReferenceVisuals, BOOT, ART, ACCEPTED, paired_positions
from resume_three_day_queue import main
from continue_game_queue import review_evidence_seal
from loop_controller.core import Files, Halt, atomic, read_json, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone
from loop_controller.model import tool
from loop_controller.visual_context import TARGETS, contract
from loop_controller.continuous_tasks import TASKS
from repair_camera_clearance import CameraRepair
from qualify_moving_encounter import checked

PRIOR = 'q0128-3f59c879'
PREVIEW = 'evidence/' + PRIOR + '-character-preview'
REVIEW = PREVIEW + '/character-pixel-inspection.json'
MARKER = '    public class Follow : MonoBehaviour'
TASK = dict(id='camera-after-original-character', phase='polish', polish=True,
            visual_facing=True, outcome='Readable camera and real center-ray reticle on the exported original character')


def validate_boundary(old, artifact, review):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        current_round=PRIOR, stage='native-original-character-preview',
        last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
        failure_streak=1, diagnosis_used=True, focused_character_attempted=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Original character export and native preview preserved; inspect actual pixels before camera work')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('character_camera_attempted'):
        raise Halt('Require the completed character preview and unchanged sole-owner history')
    candidate = old.get('source_checkpoint')
    if (not candidate or artifact.get('candidate') != candidate or artifact.get('evidence') != PREVIEW
            or not artifact.get('export', {}).get('ok') or not artifact.get('native_gate', {}).get('passed')
            or artifact.get('native_gate', {}).get('candidate_commit') != candidate):
        raise Halt('Saved source alone is insufficient: require successful export and native preview on that source')
    frames = review.get('frames', {})
    if (review.get('candidate') != candidate or review.get('inspected_actual_pixels') is not True
            or review.get('camera_followup_ready') is not True or not review.get('observations')
            or set(frames) != {'frame-000.png', 'frame-002.png'}
            or any(not re.fullmatch(r'[0-9a-f]{64}', str(v)) for v in frames.values())):
        raise Halt('Require actual source-matched character pixel inspection before camera authoring')


def follow_replacement(content, original):
    if (not isinstance(content, str) or len(content.encode()) > 26000
            or len(content.splitlines()) > 400 or not content.lstrip().startswith('public class Follow : MonoBehaviour')):
        raise ValueError('Submit only the complete Follow class and final namespace brace, under 26 KB/400 lines')
    if original.count(MARKER) != 1 or re.findall(r'\bclass\s+(\w+)', content) != ['Follow']:
        raise ValueError('Only the exact existing Follow class may change')
    for word in ('LoopRuntime', 'LoopInput', 'LoopSignals', 'LoopAimObservation', 'LoopInterceptionObservation',
                 'GetCommandLineArgs', 'Time.timeScale', 'System.IO', 'System.Reflection', 'Destroy(', 'SetActive(false'):
        if word in content:
            raise ValueError('Camera presentation must preserve gameplay, assets and external acceptance: ' + word)
    if re.search(r'\.enabled\s*=\s*false\b', content):
        raise ValueError('Do not hide actors or disable their physics to change framing')
    if 'public Transform target' not in content or 'public Vector3 offset' not in content:
        raise ValueError('Preserve the existing target and offset interface')
    return original.split(MARKER)[0] + content.rstrip() + '\n'


class CharacterCamera(ReferenceVisuals):
    def validate_recovery(self, old):
        preview = self.store.root / PREVIEW
        artifact = read_json(preview / 'character-artifact.json')
        review = read_json(self.store.root / REVIEW)
        validate_boundary(old, artifact, review)
        for name, digest in review['frames'].items():
            if sha((preview / 'captures' / name).read_bytes()) != digest:
                raise Halt('Inspected native character frame changed')
        self.character_review = review
        self.character_candidate = old['source_checkpoint']
        self.before = self.store.root / 'evidence/q0126-657b9ebf-positive'
        self.proof = {str(p.relative_to(self.store.root)): sha(p.read_bytes()) for p in
            [preview / 'character-artifact.json', self.store.root / REVIEW,
             preview / 'captures/scenario.json', preview / 'captures/trace.jsonl',
             self.before / 'captures/scenario.json', self.before / 'captures/trace.jsonl']}
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def wait_for_capacity(self):
        self.capacity.wait('native-character-before-camera')

    def recovery_settings(self):
        return dict(character_camera_attempted=True, recovery_route='inspected-character-then-local-camera',
            recovery_change='Preserve source/export/native character proof; use current actual aim pixels and targets '
            'for one local Follow edit, then matched native evidence and independent scoped/broad review.')

    def author_camera(self, ident, baseline):
        files = Files(self.project, self.store)
        original = files.path(BOOT).read_text()
        preimage = sha(files.path(BOOT).read_bytes())
        protected = {p: sha(p.read_bytes()) for p in self.project.rglob('*.cs') if p != files.path(BOOT)}
        protected[files.path(ART)] = sha(files.path(ART).read_bytes())
        def save(action, fields):
            replacement = follow_replacement(fields['content'], original)
            if replacement == original:
                raise ValueError('Save an actual camera/reticle improvement')
            result = files.edit(action, BOOT, preimage, content=replacement)
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: camera on original character'),
                           stage='original-character-camera-source-saved')
            self.store.report()
            return result
        images = [('AI-GENERATED TARGET ' + name + '; aspiration, not native output', self.refs / name)
                  for name in (TARGETS[0], TARGETS[2])]
        scenario = read_json(baseline / 'captures/scenario.json')
        for index in (0, 2):
            images.append((f'CURRENT EXPORTED CHARACTER, ACTUAL NATIVE frame-{index:03d}.png; '
                           f't={scenario["captures"][index]}s', baseline / 'captures' / f'frame-{index:03d}.png'))
        self.c.update(working_context_tokens=65536, output_tokens=8192, model_timeout_seconds=1200)
        self.store.set(stage='local-camera-after-original-character'); self.store.report()
        result = self.model.session('builder', ident + '-camera-source',
            'You are local Qwen, sole game camera-code author. Save the focused camera deliverable through finish_source.',
            'Use the actual current exported-character views and the neighborhood/combat targets. Improve readable '
            'third-person composition and add a restrained clearly visible reticle marking the ACTUAL camera center '
            'ray used by Combat. The reticle must appear in Camera.Render, not only OnGUI. Inspect the current pixels '
            'before choosing how much framing needs correction. Keep the character visible and avoid unnecessary '
            'camera changes if the new anatomy already removed crowding. Preserve wall/floor/near-plane clearance, '
            'target switches, existing walking/driving controls and thin-ray shooting. No aim assist, cast widening, '
            'health/mission writes, scene placement, asset edits or acceptance/replay-dependent behavior. '
            'Only the supplied Follow class and its final namespace brace may be replaced. Everything before Follow '
            'stays byte-for-byte intact; other files are protected. Retain public target and offset interfaces. '
            'This is one focused source save: current bytes/preimage are already pinned, so no read or hash call is '
            'needed. Use low thinking effort, keep the source compact and submit finish_source now. The controller '
            'runs actual native qualification and fresh reference-based review automatically. '
            'Do not write a long planning essay or a replay.\nCHARACTER PIXEL OBSERVATIONS:\n' +
            json.dumps(self.character_review['observations']) + '\nEXACT CURRENT FOLLOW SPAN:\n' +
            MARKER + original.split(MARKER)[1],
            [tool('finish_source', 'Save the complete replacement Follow span; native validation follows.',
                  {'content': {'type': 'string'}})], {'finish_source': save}, images=images,
            visual_contract=contract(images, [TARGETS[0], TARGETS[2]], 2), turns=2, reasoning_effort='low')
        atomic(self.store.root / 'evidence' / (ident + '-camera-author.json'), result)
        if not result.get('ok') or sha(files.path(BOOT).read_bytes()) == preimage:
            raise Halt('Camera source was not saved; preserve output and diagnose: ' + json.dumps(result))
        if any(sha(p.read_bytes()) != digest for p, digest in protected.items()):
            raise Halt('Camera author changed protected game or character source')
        return self.store.get('source_checkpoint')

    def work(self):
        ident = self.begin(TASK, 'native-character-before-camera')
        for name, digest in self.proof.items():
            if sha((self.store.root / name).read_bytes()) != digest:
                raise Halt('Preserved character or native replay proof changed')
        scenario = read_json(self.before / 'captures/scenario.json')
        baseline = self.store.root / 'evidence' / (ident + '-character-before-camera')
        raw = self.engines.unity(self.project, baseline, scenario, self.character_candidate)
        gate = checked(baseline, raw, 'positive')
        atomic(baseline / 'character-before-camera.json', dict(candidate=self.character_candidate, gate=gate))
        if not gate.get('passed'):
            raise Halt('Exported character has a native gameplay defect; inspect before camera changes')
        candidate = self.author_camera(ident, baseline)
        after = self.store.root / 'evidence' / (ident + '-positive')
        self.store.set(stage='native-original-character-camera'); self.store.report()
        raw = self.engines.unity(self.project, after, scenario, candidate)
        if not raw.get('passed'):
            raise Halt('Saved camera has a compile/native failure; preserve source and diagnostics')
        gate = checked(after, raw, 'positive')
        pairs = paired_positions(self.before, after, (0, 2))
        atomic(after / 'matched-positions.json', pairs)
        queue_milestone(self.store, 'native-milestone', TASK, after, gate,
            [after / 'captures/frame-000.png', after / 'captures/frame-002.png'],
            {'frame-000.png': 3.2, 'frame-002.png': 63.25})
        result = dict(candidate=candidate, evidence=str(after.relative_to(self.store.root)),
            targeted_gameplay_passed=gate.get('passed'), matched_positions=pairs,
            visual_review='pending', broad_visual_review='pending', full_regressions='pending',
            final_game_accepted=False)
        atomic(after / 'character-camera-outcome.json', result)
        self.store.set(character_camera_outcome=result); self.store.report()
        seal = review_evidence_seal(after / 'captures', candidate, 'original-character-camera')
        result['visual_review'] = self.critique(ident, after)
        result['broad_visual_review'] = self.critique(ident, after, True)
        verify_seal(after / 'captures', seal)
        atomic(after / 'character-camera-outcome.json', result)
        self.store.set(character_camera_outcome=result); self.store.report()
        if (not gate.get('passed') or not all(p['matched'] for p in pairs)
                or result['visual_review'].get('verdict') != 'PASS'):
            raise Halt('Character/camera evidence needs measured follow-up; no promotion')
        _, clearance = CameraRepair.camera_probe(self, ident + '-camera-clearance', candidate)
        result['camera_clearance'] = clearance
        if not clearance.get('passed'):
            atomic(after / 'character-camera-outcome.json', result)
            raise Halt('Camera correction failed actual wall/near-plane clearance')
        self.store.set(stage='original-character-camera-regressions'); self.store.report()
        result['full_regressions'] = self.regress(TASKS[7], ident, candidate)
        atomic(after / 'character-camera-outcome.json', result)
        self.store.set(character_camera_outcome=result); self.store.report()
        if not result['full_regressions'].get('passed'):
            raise Halt('Preserve the visual candidate and diagnose gameplay regression')
        raise Halt('Character/camera comparison and regressions recorded; broader reference quality and full mission remain open')


if __name__ == '__main__':
    raise SystemExit(main(CharacterCamera))
