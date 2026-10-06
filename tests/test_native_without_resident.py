import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from loop_controller.native_without_resident import inference_process
from resume_camera_native_only import validate_boundary, SOURCE, ACCEPTED, PRIOR, HARD_CAP_EPOCH
from loop_controller.core import Halt


class NativeWithoutResidentTests(unittest.TestCase):
    def test_reject_live_inference_but_not_native_or_diagnostic_processes(self):
        for info in [dict(name='omlx-server', cmdline=[]),
                     dict(name='python', cmdline=['python', '-m', 'mlx_vlm.server']),
                     dict(name='python', cmdline=['/runtime/bin/omlx', 'serve'])]:
            self.assertTrue(inference_process(info))
        for info in [dict(name='Unity', cmdline=['Unity', '-batchmode']),
                     dict(name='python', cmdline=['python', '/tools/audit_omlx.py']),
                     dict(name='Blender', cmdline=None)]:
            self.assertFalse(inference_process(info))

    def test_only_exact_saved_camera_boundary_can_resume(self):
        state = dict(status='paused', controller_pid=None, owned_process=None,
            source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=PRIOR,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, stage='native-original-character-camera',
            character_camera_attempted=True,
            blocker='URLError: <urlopen error [Errno 61] Connection refused>')
        validate_boundary(state, {'gate': {'passed': True}})
        for change in [dict(source_checkpoint='different'), dict(controller_pid=1),
                       dict(task_failures=0), dict(blocker='other error'),
                       dict(camera_native_only_attempted=True)]:
            with self.assertRaises(Halt):
                validate_boundary({**state, **change}, {'gate': {'passed': True}})
        with self.assertRaises(Halt):
            validate_boundary(state, {'gate': {'passed': False}})


if __name__ == '__main__':
    unittest.main()
