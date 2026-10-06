import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import qualify_visual_replay as visual
from continue_game_queue import ContinuousRunner
from loop_controller.core import Halt, Store, atomic, seal, sha
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from resume_visual_replay import validate_visual_replay_pause, SOURCE, ACCEPTED, ROUND, BLOCKER


def regression_result(candidate):
    tests = []
    for name in visual.REGRESSIONS:
        gate = {'passed': True}
        if name.startswith('combat-'):
            kind = name.removeprefix('combat-')
            gate['combat_contract'] = dict(scope=kind, candidate=candidate, passed=True,
                facts={'longest_continuous_escape_seconds': 3})
        aim = {'combat-foot': 'aligned', 'combat-wall': 'wall',
               'aim-miss': 'miss', 'aim-near-cover': 'near-cover'}.get(name)
        if aim:gate['aim_contract'] = dict(scope=aim, candidate=candidate, passed=True)
        tests.append({'test': name, 'gate': gate})
    return {'passed': True, 'regressions': tests}


class VisualReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name);self.project = self.root / 'repo/game'
        self.store = Store(self.root / 'run');self.addCleanup(self.store.db.close)
        self.captures = self.store.root / 'evidence/v0040-aaaaaaaa/captures'
        self.probe = dict(id='observed-combat', coverage='combat', duration=52,
            steps=[dict(start=4, end=5, keys=['W'])], captures=[3.2, 6.9, 7.55, 9.25, 11.1, 15.5])
        atomic(self.captures / 'scenario.json', self.probe)
        for name in ['frame-000.png', 'frame-005.png']:
            (self.captures / name).write_bytes(b'actual-test-image')
        self.digest = seal(self.captures, {'candidate': 'old-source'})
        self.review = dict(ok=True, verdict='PASS', summary='before.png and after.png show new geometry', fixes=[])
        self.record = dict(candidate='old-source', evidence='evidence/v0040-aaaaaaaa',
            review=self.review, capture_manifest_sha256=self.digest, final_game_accepted=False)
        atomic(self.captures.parent / 'scoped-gate.json', dict(passed=True,
            candidate_commit='old-source', regressions=regression_result('old-source')))
        atomic(self.captures.parent / 'visual-critic.json', self.review)
        atomic(self.store.root / visual.ORIGINAL_REPLAY, self.probe)
        self.sha_patch = patch.object(visual, 'SCENARIO_SHA', sha((self.captures / 'scenario.json').read_bytes()))
        self.sha_patch.start();self.addCleanup(self.sha_patch.stop)
        self.changed = ['game/Art/street.py', 'game/ArtSources/street/source.blend',
            'game/ArtSources/street/provenance.json', 'game/Assets/Resources/Generated/street/scene.fbx']
        (self.project / 'Art').mkdir(parents=True);(self.project / 'Art/street.py').write_text('original script\n')
        files = []
        for name in ['ArtSources/street/source.blend', 'Assets/Resources/Generated/street/scene.fbx']:
            p = self.project / name;p.parent.mkdir(parents=True, exist_ok=True);p.write_bytes(b'local export')
            files.append(dict(path=name, sha256=sha(p.read_bytes())))
        atomic(self.project / 'ArtSources/street/provenance.json', dict(author='local-Qwen',
            script='Art/street.py', script_sha256=sha((self.project / 'Art/street.py').read_bytes()), files=files))
        self.store.set(last_playable_checkpoint='accepted', task_index=7, task_failures=2,
            failure_streak=1, diagnosis_used=False, latest_visual_milestone=self.record)
        self.head = 'candidate'
        self.runner = SimpleNamespace(store=self.store, repo=self.project.parent, project=self.project,
            refs=self.root / 'references', c={}, regress=Mock(return_value=regression_result('candidate')),
            model=SimpleNamespace(session=Mock(return_value=self.review)), reject_scoped=Mock())

    def fake_git(self, repo, *args):
        if args[0] == 'show':return json.dumps(self.record)
        if args[0] == 'diff':
            return 'game/Notes/visual-v0040-aaaaaaaa.json' if args[2] == 'old-source' else '\n'.join(self.changed)
        if args[:2] == ('rev-parse', 'HEAD'):return self.head
        if 'commit' in args:self.head = 'promoted'
        return ''

    def native(self, runner, task, ident, candidate, probe):
        self.assertEqual(task, TASKS[6]);self.assertEqual(probe, self.probe)
        p = self.store.root / 'evidence' / ident
        atomic(p / 'captures/scenario.json', probe)
        for name in ['frame-000.png', 'frame-005.png']:(p / 'captures' / name).write_bytes(b'new native image')
        return p, dict(passed=True, candidate_commit=candidate, build_id='test-build',
                       scoped_facts={'mission_anchors': {'passed': True}})

    def test_only_exported_existing_art_qualifies(self):
        self.assertEqual(visual.asset_only_changes(self.changed), ['street'])
        for extra in ['game/Assets/Game/Combat.cs', 'game/Assets/Game/CameraFollow.cs',
                      'game/Assets/Scenes/Main.unity', 'game/ProjectSettings/physics.asset',
                      'game/Art/new_asset.py', 'game/Art/../Assets/Game/Mission.cs']:
            with self.subTest(path=extra):self.assertFalse(visual.asset_only_changes(self.changed + [extra]))
        self.assertFalse(visual.asset_only_changes([]))
        self.assertFalse(visual.asset_only_changes(self.changed[1:]))

    def test_unexported_script_and_changed_export_are_rejected(self):
        visual.validate_exports(self.project, ['street'])
        script = self.project / 'Art/street.py';original = script.read_bytes();script.write_bytes(b'new unsaved export')
        with self.assertRaises(Halt):visual.validate_exports(self.project, ['street'])
        script.write_bytes(original)
        (self.project / 'Assets/Resources/Generated/street/scene.fbx').write_bytes(b'unproven geometry')
        with self.assertRaises(Halt):visual.validate_exports(self.project, ['street'])

    def test_original_inputs_and_camera_times_cannot_change(self):
        with patch.object(visual, 'git', side_effect=self.fake_git):
            _, _, probe = visual.accepted_fixture(self.runner, self.record)
            self.assertEqual(probe, self.probe)
            atomic(self.captures / 'scenario.json', {**self.probe, 'captures': [3.2, 8, 12, 20]})
            with self.assertRaises(Halt):visual.accepted_fixture(self.runner, self.record)

    def test_stale_note_or_missing_real_regression_rejects_reuse(self):
        with patch.object(visual, 'git', side_effect=self.fake_git):
            with self.assertRaises(Halt):visual.accepted_fixture(self.runner, {**self.record, 'candidate': 'other'})
            p = self.captures.parent / 'scoped-gate.json';d = json.loads(p.read_text())
            d['regressions']['regressions'].pop();atomic(p, d)
            with self.assertRaises(Halt):visual.accepted_fixture(self.runner, self.record)

    def test_visual_pass_preserves_final_gate_and_original_failure_counters(self):
        with patch.object(visual, 'git', side_effect=self.fake_git), \
                patch.object(ContinuousRunner, 'native', autospec=True, side_effect=self.native), \
                patch.object(visual, 'queue_milestone') as delivery:
            self.assertTrue(visual.qualify_saved_visual_candidate(self.runner, TASKS[7], 'q0041-test0001', 'candidate'))
            self.assertEqual(self.store.get('last_playable_checkpoint'), 'promoted')
            self.assertEqual([self.store.get(k) for k in ['task_index', 'task_failures', 'failure_streak', 'diagnosis_used']],
                             [7, 2, 1, False])
            self.assertFalse(self.store.get('latest_visual_milestone')['final_game_accepted'])
            self.runner.regress.assert_called_once();self.runner.model.session.assert_called_once()
            self.runner.reject_scoped.assert_not_called();delivery.assert_called_once()
            self.assertIn('beacon', self.store.get('task_design'))
            self.assertIn('Do not spend another pass adding windows', self.store.get('task_design'))

    def test_changed_gameplay_never_uses_visual_shortcut(self):
        self.changed.append('game/Assets/Game/Mission.cs')
        with patch.object(visual, 'git', side_effect=self.fake_git):
            self.assertFalse(visual.qualify_saved_visual_candidate(self.runner, TASKS[7], 'unused', 'candidate'))
        self.runner.model.session.assert_not_called();self.runner.regress.assert_not_called()

    def test_missing_current_source_aim_contract_blocks_promotion(self):
        result = regression_result('candidate')
        for x in result['regressions']:x['gate'].pop('aim_contract', None)
        self.runner.regress.return_value = result
        with patch.object(visual, 'git', side_effect=self.fake_git), \
                patch.object(ContinuousRunner, 'native', autospec=True, side_effect=self.native):
            with self.assertRaises(Halt):
                visual.qualify_saved_visual_candidate(self.runner, TASKS[7], 'q0041-test0002', 'candidate')
        self.assertEqual(self.store.get('last_playable_checkpoint'), 'accepted')
        self.runner.model.session.assert_not_called()

    def test_visual_fix_remains_rejected_and_uses_existing_failure_policy(self):
        self.runner.model.session.return_value = dict(ok=True, verdict='FIX', summary='after.png unchanged', fixes=['Fix camera'])
        with patch.object(visual, 'git', side_effect=self.fake_git), \
                patch.object(ContinuousRunner, 'native', autospec=True, side_effect=self.native):
            visual.qualify_saved_visual_candidate(self.runner, TASKS[7], 'q0041-test0003', 'candidate')
        self.runner.reject_scoped.assert_called_once()
        self.assertEqual(self.store.get('last_playable_checkpoint'), 'accepted')

    def test_recovery_admits_only_original_stop_without_resetting_it(self):
        state = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=ROUND,
            task_index=7, task_failures=2, failure_streak=1, diagnosis_used=False,
            overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
        original = copy.deepcopy(state);validate_visual_replay_pause(state);self.assertEqual(state, original)
        for key, value in [('source_checkpoint', 'other'), ('task_failures', 0), ('current_round', 'other'),
                           ('blocker', 'resource fault'), ('visual_replay_recovery_attempted', True),
                           ('overall_deadline_epoch', HARD_CAP_EPOCH + 1)]:
            with self.subTest(key=key), self.assertRaises(Halt):validate_visual_replay_pause({**state, key:value})


if __name__ == '__main__':unittest.main()
