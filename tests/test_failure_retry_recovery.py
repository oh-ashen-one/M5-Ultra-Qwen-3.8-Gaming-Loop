import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from resume_failure_retry import PAUSED_SOURCE,ACCEPTED_COURIER,validate_failure_pause,failure_probe
from resume_verified_courier import PAUSED_SOURCE as GEOMETRY_SOURCE,validate_geometry_pause,current_deadline


class FailureRecoveryTests(unittest.TestCase):
    def test_recovery_preserves_history_and_rejects_other_faults(self):
        project=Path('/fixture/game')
        state=dict(task_index=3,blocker="IsADirectoryError: [Errno 21] Is a directory: '/fixture/game/Notes'",
            source_checkpoint=PAUSED_SOURCE,last_playable_checkpoint=ACCEPTED_COURIER,
            overall_deadline_epoch=HARD_CAP_EPOCH,diagnosis_used=True,failure_streak=0,task_failures=0)
        before=copy.deepcopy(state);validate_failure_pause(state,project);self.assertEqual(state,before)
        for changes in [dict(task_index=4),dict(blocker='resource fault'),dict(source_checkpoint='other'),
                        dict(last_playable_checkpoint='other'),dict(overall_deadline_epoch=HARD_CAP_EPOCH+1)]:
            with self.subTest(changes=changes),self.assertRaises(Halt):
                validate_failure_pause({**state,**changes},project)

    def test_probe_preserves_observed_route_after_failure_and_normal_reset(self):
        original=dict(duration=20,steps=[dict(start=4,end=5,keys=['W']),dict(start=17,end=17.3,keys=['R'])])
        before=copy.deepcopy(original)
        result=failure_probe(original,dict(maximum=180,coverage='mission-core'))
        self.assertEqual(original,before)
        self.assertEqual(result['steps'][0],dict(start=47,end=47.3,keys=['R']))
        self.assertEqual(result['steps'][1],dict(start=51,end=52,keys=['W']))
        self.assertIn(46,result['captures']);self.assertIn(47.5,result['captures'])
        self.assertEqual(result['duration'],67)

    def test_probe_uses_current_deadline_and_keeps_post_reset_settle(self):
        original=dict(duration=20,steps=[dict(start=4,end=5,keys=['W'])])
        result=failure_probe(original,dict(maximum=180,coverage='mission-core'),deadline=30)
        self.assertEqual(result['steps'][0]['start'],32)
        self.assertEqual(result['steps'][1]['start'],36)
        self.assertIn(31,result['captures'])
        self.assertEqual(result['duration'],52)

    def test_geometry_recovery_preserves_five_failures_and_current_timeout(self):
        state=dict(task_index=3,source_checkpoint=GEOMETRY_SOURCE,last_playable_checkpoint=ACCEPTED_COURIER,
            blocker='Halt: Replay-only role supplied no valid finish_task; details',task_failures=5,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH)
        before=copy.deepcopy(state);validate_geometry_pause(state);self.assertEqual(state,before)
        for changes in [dict(task_failures=0),dict(diagnosis_used=False),dict(blocker='resource fault'),
                        dict(source_checkpoint='different'),dict(overall_deadline_epoch=HARD_CAP_EPOCH+1)]:
            with self.subTest(changes=changes),self.assertRaises(Halt):validate_geometry_pause({**state,**changes})
        self.assertEqual(current_deadline('const float DEADLINE = 30f;'),30)
        for source in ['not declared','const float DEADLINE = 999f;',
                       'const float DEADLINE = 30f; const float DEADLINE = 45f;']:
            with self.assertRaises(Halt):current_deadline(source)


if __name__=='__main__':unittest.main()
