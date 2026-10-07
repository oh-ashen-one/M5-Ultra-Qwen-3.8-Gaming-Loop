import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt
import resume_map_return_micro as recovery


class MapReturnMicroTests(unittest.TestCase):
    def test_composition_preserves_observed_prefix_and_never_inserts_state_changes(self):
        original={'steps':[{'start':4,'end':6.91,'keys':['W']},{'start':6.91,'end':10.82,'keys':['D']},
            {'start':10.82,'end':11.76,'keys':['W']},{'start':11.76,'end':12.7,'keys':['S']},
            {'start':12.7,'end':15.36,'keys':['A']}]}
        old=copy.deepcopy(original)
        fields={'north_seconds':1.86459375,'west_seconds':3.29165625,'south_seconds':2.8125,
            'summary':'Return north of the measured blocking pier, then approach the car.'}
        result=recovery.compose_return(original,fields)['scenario']
        self.assertEqual(original,old)
        self.assertEqual(result['steps'][:4],original['steps'][:4])
        self.assertEqual([r['keys'] for r in result['steps'][4:]],[['W'],['A'],['S'],['E']])
        self.assertLess(result['captures'][-1],result['duration'])
        for bad in (0,float('nan'),float('inf'),True,7):
            with self.subTest(bad=bad),self.assertRaises(ValueError):recovery.compose_return(original,{**fields,'north_seconds':bad})
        with self.assertRaises(Halt):recovery.compose_return({'steps':[]},fields)

    def test_exact_native_and_output_stops_remain_preserved(self):
        old=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=11,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=recovery.HARD_CAP_EPOCH,blocker=recovery.BLOCKER,
            map_prefix_budget_attempted=True,map_prefix_attempts=1,map_walking_prefix=None)
        before=copy.deepcopy(old);recovery.validate_micro_pause(old);self.assertEqual(old,before)
        for k,v in [('map_return_micro_attempted',True),('task_failures',0),('map_prefix_attempts',0),('blocker','permission fault')]:
            with self.subTest(key=k),self.assertRaises(Halt):recovery.validate_micro_pause({**old,k:v})


if __name__=='__main__':unittest.main()
