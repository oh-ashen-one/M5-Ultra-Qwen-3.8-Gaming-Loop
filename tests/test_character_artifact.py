import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resume_character_artifact import validate_boundary, validate_character, SOURCE, ACCEPTED, PRIOR, REVIEWED_NONDELIVERABLE_RESPONSE
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class CharacterArtifactTests(unittest.TestCase):
    def state(self):
        return dict(status='paused', controller_pid=None, source_checkpoint=SOURCE,
            last_playable_checkpoint=ACCEPTED, current_round=PRIOR, task_index=7,
            task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, stage='local-reference-character-camera',
            blocker='Halt: Reference-backed visual source saved incompletely; output limit')

    def test_only_completed_budget_stop_can_resume(self):
        response = {'choices': [{'finish_reason': 'length', 'message': {}}]}
        outcome = {'bounded_stop': 'output'}
        validate_boundary(self.state(), response, outcome)
        for changes in [dict(status='running'), dict(controller_pid=12), dict(task_failures=0),
                        dict(source_checkpoint='changed'), dict(blocker='Memory fault'),
                        dict(focused_character_attempted=True)]:
            with self.assertRaises(Halt):
                validate_boundary({**self.state(), **changes}, response, outcome)
        with self.assertRaises(Halt):
            validate_boundary(self.state(), response, {'bounded_stop': 'context'})

    def test_complete_returned_tool_work_requires_inspection_before_new_request(self):
        response = {'choices': [{'finish_reason': 'length', 'message': {'tool_calls': [{'id': 'saved'}]}}]}
        with self.assertRaises(Halt):
            validate_boundary(self.state(), response, {'bounded_stop': 'output'})
        response['choices'][0]['message'] = {'content': 'Possible complete public source'}
        with self.assertRaises(Halt):
            validate_boundary(self.state(), response, {'bounded_stop': 'output'})
        # Only the caller's hash of the one already-inspected raw response
        # permits nonempty text; no model-controlled source bypass is added.
        validate_boundary(self.state(), response, {'bounded_stop': 'output'}, REVIEWED_NONDELIVERABLE_RESPONSE)

    def test_character_source_requires_complete_bounded_python_without_execution(self):
        source = 'raise RuntimeError("not executed by validation")\n'
        self.assertEqual(validate_character(source), source)
        for bad in ['def incomplete(', 'x=0\n' * 651, '#' * 32001, '']:
            with self.assertRaises(ValueError):
                validate_character(bad)


if __name__ == '__main__':
    unittest.main()
