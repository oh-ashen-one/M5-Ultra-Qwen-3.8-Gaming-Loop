from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_death_completed_controls as module
from loop_controller.core import Halt


class CompletedControlsTests(unittest.TestCase):
    def fixture(self):
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=module.PRIOR,
            source_checkpoint=module.SOURCE,last_playable_checkpoint=module.ACCEPTED,task_index=7,
            task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=module.HARD_CAP_EPOCH,
            death_context_recovery_attempted=True,player_death_completion_attempted=True,
            shared_workload_priority='simultaneous-no-default-priority',
            blocker='Halt: Focused death verify-retained-controls incomplete; preserve source and diagnose changed continuation')
        content='Verified all three saved gates directly in current source\nNo missing control path within the stated scope, so I made no edit, as this phase permits.'
        response=json.dumps({'choices':[{'finish_reason':'stop','message':{'content':content}}]}).encode()
        return old,response,{'summary':content}

    def test_only_exact_inspected_response_can_be_recovered(self):
        old,response,saved=self.fixture()
        with self.assertRaises(Halt):module.validate_boundary(old,response,saved)
        with patch.object(module,'sha',return_value=module.RESPONSE_SHA):
            module.validate_boundary(old,response,saved)
            for changes in ({'controller_pid':4},{'source_checkpoint':'other'},{'task_failures':0},
                    {'death_controls_result_recovered':True},{'player_death_green_attempted':True}):
                with self.subTest(changes=changes),self.assertRaises(Halt):
                    module.validate_boundary(dict(old,**changes),response,saved)
            with self.assertRaises(Halt):module.validate_boundary(old,response,{'summary':'different'})

    def test_completed_controls_are_not_requested_again(self):
        self.assertEqual([x[0] for x in module.CompletedControls.phases],
            ['route-relay-death','interception-hud-death'])
        self.assertEqual(module.CompletedControls.allow_unchanged_phases,())


if __name__=='__main__':unittest.main()
