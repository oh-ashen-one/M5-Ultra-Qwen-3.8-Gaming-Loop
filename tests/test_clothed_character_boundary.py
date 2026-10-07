from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from author_clothed_character import ACCEPTED, STOP, validate_boundary, validate_art
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class ClothedCharacterBoundaryTests(unittest.TestCase):
    def fixture(self):
        return dict(status='paused', controller_pid=None, owned_process=None,
            source_checkpoint=ACCEPTED, last_playable_checkpoint=ACCEPTED,
            current_round='q0184-e64fca5c', task_index=7, task_failures=24,
            failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker=STOP, counter_exfil_scoped_acceptance=dict(candidate=ACCEPTED, accepted_utc='accepted'))

    def test_no_takeover_or_unaccepted_fallback(self):
        validate_boundary(self.fixture())
        for change in [dict(controller_pid=2), dict(owned_process={'pid':2}), dict(source_checkpoint='other'),
                       dict(last_playable_checkpoint='other'), dict(overall_deadline_epoch=HARD_CAP_EPOCH+1),
                       dict(blocker='resource failure'), dict(clothed_character_author_attempted=True),
                       dict(counter_exfil_scoped_acceptance={})]:
            with self.assertRaises(Halt):
                validate_boundary(dict(self.fixture(), **change))

    def test_original_bounded_source_only(self):
        self.assertEqual(validate_art('import bpy\nfrom mathutils import Euler\n'), 'import bpy\nfrom mathutils import Euler\n')
        for source in ['import requests', 'from pathlib import Path', 'open("secret")',
                       'bpy.ops.wm.open_mainfile(filepath="other")', 'bpy.data.images.load("asset")',
                       'x=1\n'*701, 'x="'+('a'*36000)+'"']:
            with self.assertRaises(ValueError): validate_art(source)
        with self.assertRaises(SyntaxError): validate_art('def incomplete(')


if __name__ == '__main__': unittest.main()
