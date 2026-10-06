import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.replay_contract import MISSION_EXAMPLE,validate_submission
from loop_controller.core import Halt
import resume_map_drive_micro as drive
import resume_map_drive_exact as exact


class MapDriveMicroTests(unittest.TestCase):
    def test_exact_parameter_recovery_preserves_the_failed_four_field_request(self):
        state=dict(source_checkpoint=exact.SOURCE,last_playable_checkpoint=exact.ACCEPTED,
            current_round=exact.ROUND,task_index=7,task_failures=11,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=exact.HARD_CAP_EPOCH,blocker=exact.BLOCKER,map_drive_micro_attempted=True,
            map_walking_prefix={'candidate':exact.SOURCE,'native_round':exact.PREFIX,'walk':{'passed':True}})
        old=copy.deepcopy(state);exact.validate_exact_pause(state);self.assertEqual(state,old)
        for k,v in [('map_drive_exact_attempted',True),('task_failures',0),('map_walking_prefix',None),('blocker','runtime fault')]:
            with self.subTest(key=k),self.assertRaises(Halt):exact.validate_exact_pause({**state,k:v})

    def test_composed_controls_keep_verified_prefix_and_use_no_state_shortcuts(self):
        prefix=validate_submission(MISSION_EXAMPLE,drive.MAP_TASK)['scenario'];old=copy.deepcopy(prefix)
        fields=dict(approach_seconds=.75,turn_seconds=1.444,out_seconds=.8,reverse_seconds=5.5,
            summary='Use measured approach and a bounded turn, then reverse physically.')
        result=drive.compose_maneuver(prefix,fields)['scenario']
        self.assertEqual(prefix,old)
        self.assertEqual(result['steps'][:len(prefix['steps'])],prefix['steps'])
        self.assertEqual([s['keys'] for s in result['steps'][len(prefix['steps']):]],[['W'],['W','D'],['W'],['S']])
        self.assertLess(result['captures'][-1],result['duration'])
        for key in drive.LIMITS:
            for bad in (-1,99,float('nan'),True):
                with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):drive.compose_maneuver(prefix,{**fields,key:bad})

    def test_resume_requires_real_passed_prefix_and_preserved_failure_counts(self):
        state=dict(source_checkpoint=drive.SOURCE,last_playable_checkpoint=drive.ACCEPTED,
            current_round=drive.ROUND,task_index=7,task_failures=11,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=drive.HARD_CAP_EPOCH,blocker=drive.BLOCKER,map_return_micro_attempted=True,
            map_walking_prefix={'candidate':drive.SOURCE,'native_round':drive.PREFIX,'walk':{'passed':True}})
        old=copy.deepcopy(state);drive.validate_drive_pause(state);self.assertEqual(state,old)
        for k,v in [('map_drive_micro_attempted',True),('task_failures',0),('map_walking_prefix',None),('blocker','permission fault')]:
            with self.subTest(key=k),self.assertRaises(Halt):drive.validate_drive_pause({**state,k:v})


if __name__=='__main__':unittest.main()
