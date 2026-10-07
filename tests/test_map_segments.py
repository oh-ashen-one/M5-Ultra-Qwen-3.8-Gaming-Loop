import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_map_walk_first import combine_driving,inspect_walking_prefix
from loop_controller.replay_contract import MISSION_EXAMPLE,validate_submission
from loop_controller.core import Halt
import resume_map_prefix_budget as budget


class MapSegmentTests(unittest.TestCase):
    def test_larger_output_allowance_is_exact_once_and_does_not_erase_failures(self):
        state=dict(source_checkpoint=budget.SOURCE,last_playable_checkpoint=budget.ACCEPTED,
            current_round=budget.ROUND,task_index=7,task_failures=10,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=budget.HARD_CAP_EPOCH,blocker=budget.BLOCKER,
            map_segment_recovery_attempted=True,map_prefix_attempts=0,map_walking_prefix=None)
        old=copy.deepcopy(state);budget.validate_budget_pause(state);self.assertEqual(state,old)
        for key,value in [('map_prefix_budget_attempted',True),('map_prefix_attempts',1),
                          ('task_failures',0),('blocker','resource fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):budget.validate_budget_pause({**state,key:value})

    def test_driving_suffix_preserves_all_native_verified_prefix_inputs(self):
        prefix=validate_submission(MISSION_EXAMPLE,{'maximum':150,'coverage':'foundation'})['scenario']
        old=copy.deepcopy(prefix)
        fields={'summary':'A measured driving route around the actual blocking geometry.',
            'duration':40,'input_steps':[{'start':21,'end':24,'keys':['W']}],'captures':[25,29,33,38]}
        combined=combine_driving(prefix,fields)['scenario']
        self.assertEqual(prefix,old)
        self.assertEqual(combined['steps'][:len(prefix['steps'])],prefix['steps'])
        self.assertTrue(set(prefix['captures'])<=set(combined['captures']))
        fields['input_steps'][0]['start']=18
        with self.assertRaisesRegex(ValueError,'unchanged'):combine_driving(prefix,fields)

    def test_walk_prefix_requires_physical_return_and_actual_boarding(self):
        rows=[]
        for i,x in enumerate(list(range(13))+[12]*12+list(range(11,-1,-1))):
            rows.append(dict(time=4+i*.1,mode='foot',player=[x,.14,17],vehicle=[3.36,0,8],
                grounded=True,playerCollisionEnabled=True,playerPenetration=0,restarts=0,keys=['D']))
        scenario={'captures':[4,5.3,6,7.5]}
        self.assertIn('actual-boarding-missing',inspect_walking_prefix(rows,scenario)['failure'])
        rows.append({**rows[-1],'time':8,'mode':'vehicle'})
        self.assertTrue(inspect_walking_prefix(rows,scenario)['passed'])
        rows[-1]['mode']='foot';rows[-1]['keys']=['E']
        self.assertFalse(inspect_walking_prefix(rows,scenario)['passed'])


if __name__=='__main__':unittest.main()
