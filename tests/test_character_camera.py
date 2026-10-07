import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resume_character_camera import validate_boundary, follow_replacement, PRIOR, PREVIEW, ACCEPTED, MARKER
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class CharacterCameraTests(unittest.TestCase):
    def fixture(self):
        state = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=PRIOR, stage='native-original-character-preview',
            last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
            failure_streak=1, diagnosis_used=True, focused_character_attempted=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, source_checkpoint='exported-source',
            blocker='Halt: Original character export and native preview preserved; inspect actual pixels before camera work')
        artifact = dict(candidate='exported-source', evidence=PREVIEW, export={'ok': True},
                        native_gate={'passed': True, 'candidate_commit': 'exported-source'})
        review = dict(candidate='exported-source', inspected_actual_pixels=True, camera_followup_ready=True,
                      observations=['Visible character inspected'],
                      frames={'frame-000.png': 'a' * 64, 'frame-002.png': 'b' * 64})
        return state, artifact, review

    def test_requires_idle_original_owner_boundary_and_preserved_history(self):
        state, artifact, review = self.fixture()
        validate_boundary(state, artifact, review)
        for changes in [dict(status='running'), dict(controller_pid=42), dict(owned_process={'pid': 42}),
                        dict(task_failures=0), dict(current_round='another-round'),
                        dict(character_camera_attempted=True), dict(blocker='Resource fault')]:
            with self.assertRaises(Halt):
                validate_boundary({**state, **changes}, artifact, review)

    def test_source_only_or_stale_pixel_review_cannot_start_camera(self):
        state, artifact, review = self.fixture()
        for target, key, value in [('artifact', 'export', {'ok': False}),
                ('artifact', 'native_gate', {'passed': False, 'candidate_commit': 'exported-source'}),
                ('artifact', 'candidate', 'old-source'), ('review', 'candidate', 'old-source'),
                ('review', 'inspected_actual_pixels', False), ('review', 'camera_followup_ready', False),
                ('review', 'frames', {}), ('review', 'observations', [])]:
            a, r = copy.deepcopy(artifact), copy.deepcopy(review)
            (a if target == 'artifact' else r)[key] = value
            with self.assertRaises(Halt):
                validate_boundary(state, a, r)

    def test_follow_edit_preserves_prefix_and_rejects_replay_or_hiding(self):
        prefix = 'namespace Example {\n// Existing Bootstrap and Walker bytes\n'
        body = MARKER + '\n{ public Transform target; public Vector3 offset; }\n}\n'
        changed = body.replace('public Vector3 offset;', 'public Vector3 offset; public float damping = 8f;')
        result = follow_replacement(changed, prefix + body)
        self.assertEqual(result, prefix + changed)
        for forbidden in ['LoopInput.Replay', 'LoopSignals.Health = 100;', 'actor.enabled = false;',
                          'public class Other {}', 'System.IO.File', 'Destroy(actor);']:
            with self.assertRaises(ValueError):
                follow_replacement(changed.replace('public float damping = 8f;', forbidden), prefix + body)


if __name__ == '__main__':
    unittest.main()
