#!/usr/bin/env python3
"""Validate already-saved local camera source without loading an inference model."""
from resume_character_camera import CharacterCamera, TASK, ACCEPTED, paired_positions
from resume_three_day_queue import main
from repair_camera_clearance import CameraRepair
from qualify_moving_encounter import checked
from loop_controller.adapters import Engines
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone
from loop_controller.native_without_resident import engine, require_unloaded

SOURCE = '8fd4c9e5bb93455bfe5e4b2207f52f279a1e70d3'
PRIOR = 'q0131-aae363f5'


def validate_boundary(old, baseline):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=PRIOR,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='native-original-character-camera',
        character_camera_attempted=True,
        blocker='URLError: <urlopen error [Errno 61] Connection refused>')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('camera_native_only_attempted'):
        raise Halt('Require the preserved saved-camera stop without resetting owner/source/history')
    if not baseline.get('gate', {}).get('passed'):
        raise Halt('Require the completed current-character baseline')


class CameraNativeOnly(CharacterCamera):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engines.unity = Engines.unity.__get__(self.engines, Engines)
        self.machine.engine = lambda label, timeout: engine(self.machine, label, timeout)
        def no_inference(*args, **kwargs):
            raise Halt('Native-only continuation cannot invoke or reload a model')
        self.model.api = self.model.session = self.model.ready = no_inference

    def validate_recovery(self, old):
        self.before = self.store.root / 'evidence' / (PRIOR + '-character-before-camera')
        baseline = read_json(self.before / 'character-before-camera.json')
        validate_boundary(old, baseline)
        self.original_files = {str(p.relative_to(self.store.root)): sha(p.read_bytes()) for p in
            (self.before / 'character-before-camera.json', self.before / 'captures/scenario.json',
             self.before / 'captures/trace.jsonl',
             self.store.root / 'private/sessions' / (PRIOR + '-camera-source') / 'response-000.json')}
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def wait_for_capacity(self):
        require_unloaded(self.machine)

    def recovery_settings(self):
        return dict(camera_native_only_attempted=True, recovery_route='saved-camera-native-only',
            recovery_change='Keep inference unloaded. Validate the already-saved camera with unchanged '
            'native resource/slot guards and bounded admission; preserve pending local visual criticism.')

    def work(self):
        ident = self.begin(TASK, 'native-saved-camera-model-unloaded')
        for name, digest in self.original_files.items():
            if sha((self.store.root / name).read_bytes()) != digest:
                raise Halt('Original saved response or native baseline changed')
        scenario = read_json(self.before / 'captures/scenario.json')
        after = self.store.root / 'evidence' / (ident + '-positive')
        raw = self.engines.unity(self.project, after, scenario, SOURCE)
        gate = checked(after, raw, 'positive') if raw.get('passed') else raw
        pairs = paired_positions(self.before, after, (0, 2)) if raw.get('passed') else []
        result = dict(candidate=SOURCE, evidence=str(after.relative_to(self.store.root)),
            model_unloaded=True, native_gate=gate, matched_positions=pairs,
            visual_review='pending local actual/reference pixel criticism',
            broad_visual_review='pending all five target images', full_regressions='pending',
            final_game_accepted=False)
        atomic(after / 'character-camera-outcome.json', result)
        self.store.set(character_camera_outcome=result); self.store.report()
        frames = sorted((after / 'captures').glob('frame-*.png'))
        if frames:
            queue_milestone(self.store, 'native-milestone', TASK, after, gate,
                frames, {f'frame-{i:03d}.png': t for i, t in enumerate(scenario['captures'])})
        if not gate.get('passed') or not all(p['matched'] for p in pairs):
            raise Halt('Saved camera native evidence failed; preserve actual result before further authoring')
        _, clearance = CameraRepair.camera_probe(self, ident+'-camera-clearance', SOURCE)
        result['camera_clearance'] = clearance
        atomic(after / 'character-camera-outcome.json', result)
        if not clearance.get('passed'):
            raise Halt('Saved camera failed actual wall/near-plane clearance; preserve source and frames')
        self.store.set(stage='saved-camera-model-unloaded-regressions'); self.store.report()
        result['full_regressions'] = self.regress(TASKS[7], ident, SOURCE)
        atomic(after / 'character-camera-outcome.json', result)
        self.store.set(character_camera_outcome=result); self.store.report()
        if not result['full_regressions'].get('passed'):
            raise Halt('Saved camera has a native regression; preserve evidence for focused diagnosis')
        raise Halt('Saved camera native checks complete with model unloaded; local visual criticism remains required')


if __name__ == '__main__':
    raise SystemExit(main(CameraNativeOnly))
