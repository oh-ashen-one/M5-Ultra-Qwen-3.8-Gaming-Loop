import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt
from loop_controller.replay_contract import MISSION_EXAMPLE, validate_submission
from recover_mission_replay import block_span


class ReplayContractTests(unittest.TestCase):
    task={'maximum':150,'coverage':'mission-core'}

    def test_all_missing_submission_fields_are_named_before_native_execution(self):
        with self.assertRaisesRegex(ValueError,'captures, duration, input_steps, summary'):
            validate_submission({},self.task)
        for key in MISSION_EXAMPLE:
            value=copy.deepcopy(MISSION_EXAMPLE);value.pop(key)
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,key):
                validate_submission(value,self.task)

    def test_replay_example_is_valid_but_rejects_schema_and_timing_shortcuts(self):
        result=validate_submission(MISSION_EXAMPLE,self.task)
        self.assertEqual(result['scenario']['coverage'],'mission-core')
        self.assertNotIn('passed',result)
        for defect in ('wrong_steps_key','no_idle','nan','no_captures','extra_step_field'):
            value=copy.deepcopy(MISSION_EXAMPLE)
            if defect=='wrong_steps_key':value['steps']=value.pop('input_steps')
            if defect=='no_idle':value['input_steps'][0]['start']=0
            if defect=='nan':value['duration']=float('nan')
            if defect=='no_captures':value['captures']=[]
            if defect=='extra_step_field':value['input_steps'][0]['teleport']=True
            with self.subTest(defect=defect),self.assertRaises(ValueError):validate_submission(value,self.task)

    def test_selected_block_is_bounded_and_ambiguous_source_is_rejected(self):
        source='before\nvoid Build()\n{\n if (x) { Work(); }\n}\nafter\n'
        self.assertEqual(block_span(source,'void Build()'),(2,5))
        with self.assertRaises(Halt):block_span(source+source,'void Build()')


if __name__=='__main__':unittest.main()
