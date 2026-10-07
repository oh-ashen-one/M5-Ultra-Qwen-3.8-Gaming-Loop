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

    def test_known_key_casing_changes_no_timing_or_original_submission(self):
        value=copy.deepcopy(MISSION_EXAMPLE)
        for step in value['input_steps']:step['keys']=[key.lower() for key in step['keys']]
        original=copy.deepcopy(value)
        result=validate_submission(value,self.task)
        self.assertEqual(value,original)
        self.assertEqual(result['scenario']['steps'],MISSION_EXAMPLE['input_steps'])
        self.assertEqual(result['scenario']['duration'],original['duration'])
        self.assertEqual(result['scenario']['captures'],original['captures'])
        self.assertEqual(len(result['input_key_normalizations']),len(value['input_steps']))
        for bad in ([],['unknown'],[' w'],['W','unknown']):
            invalid=copy.deepcopy(value);invalid['input_steps'][0]['keys']=bad
            with self.subTest(keys=bad),self.assertRaises(ValueError):
                validate_submission(invalid,self.task)

    def test_failure_retry_cannot_submit_a_route_without_R_and_later_interaction(self):
        task={**self.task,'checks':['failure_retry']};value=copy.deepcopy(MISSION_EXAMPLE)
        with self.assertRaisesRegex(ValueError,'ordinary R reset'):validate_submission(value,task)
        value['input_steps'].insert(0,dict(start=4,end=4.3,keys=['R']))
        self.assertTrue(validate_submission(value,task)['ok'])
        value['input_steps'][0].update(start=19,end=19.3)
        with self.assertRaises(ValueError):validate_submission(value,task)


if __name__=='__main__':unittest.main()
