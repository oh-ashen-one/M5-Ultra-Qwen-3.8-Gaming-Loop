import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resume_character_runtime import validate_boundary, PRIOR, RESPONSE, SOURCE, ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.request_speed_guard import sustained_slow


class RuntimeRecoveryTests(unittest.TestCase):
    def test_recovery_rejects_changed_owner_failure_source_or_unqualified_runtime(self):
        state = dict(status='paused', controller_pid=None, owned_process=None,
            source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
            current_round=PRIOR, task_index=7, task_failures=24, failure_streak=1,
            diagnosis_used=True, focused_character_attempted=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, stage='local-focused-character-source',
            blocker='Halt: Focused character source was not saved; output limit')
        response = {'choices': [{'finish_reason': 'length', 'message': {'role': 'assistant'}}]}
        qualified = dict(runtime='0.7.0', passed=True, tool_correct=True, vision_correct=True,
                         generation_tps={'text-160': 73.37})
        validate_boundary(state, response, RESPONSE, qualified)
        for change in [dict(controller_pid=9), dict(source_checkpoint='changed'),
                       dict(task_failures=0), dict(blocker='Resource failure'),
                       dict(runtime_character_recovery_attempted=True)]:
            with self.assertRaises(Halt):
                validate_boundary({**state, **change}, response, RESPONSE, qualified)
        for change in [dict(tool_correct=False), dict(vision_correct=False),
                       dict(generation_tps={'text-160': 2.6})]:
            with self.assertRaises(Halt):
                validate_boundary(state, response, RESPONSE, {**qualified, **change})
        with self.assertRaises(Halt):
            validate_boundary(state, response, 'changed', qualified)

    def test_speed_guard_requires_sustained_progress_on_same_request(self):
        def sample(t, n, request='owned'):
            return dict(elapsed=t, generated_tokens=n, request_id=request)
        self.assertFalse(sustained_slow([sample(0, 1), sample(59, 20)], 14.674))
        self.assertTrue(sustained_slow([sample(0, 1), sample(60, 157)], 14.674))
        self.assertFalse(sustained_slow([sample(0, 1), sample(60, 4400)], 14.674))
        self.assertFalse(sustained_slow([sample(0, 1), sample(60, 157, 'other')], 14.674))
        self.assertFalse(sustained_slow([sample(0, 300), sample(60, 1)], 14.674))


if __name__ == '__main__':
    unittest.main()
