from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_connected_plan_retained as m
from loop_controller.core import Halt
from loop_controller.model import retained_submission,tool


class RetainedPlanTests(unittest.TestCase):
    def boundary(self):
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.SOURCE,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            death_pixel_resolution_attempted=True,
            blocker='Halt: Death repair accepted; retain the bounded next-plan result for focused continuation',
            next_connected_expansion={'bounded_stop':'output'},
            player_death_scoped_acceptance={'candidate':m.SOURCE})
        response=dict(choices=[dict(finish_reason='length',message=dict(role='assistant',content='private retained draft'))],
            usage={'completion_tokens':16384})
        return old,response

    def test_plan_resume_does_not_instruct_nonexistent_game_edits(self):
        for name in ['submit_plan','submit_review','finish_source','finish_task']:
            result=retained_submission([tool(name,'finish',{})])
            self.assertIn(name,result)
            if name=='submit_plan':
                self.assertNotIn('finish_task',result)
                self.assertNotIn('source-edit tools',result)

    def test_other_faults_or_tool_calls_cannot_be_replayed(self):
        old,response=self.boundary();m.validate_boundary(old,response)
        for changed in [{'controller_pid':9},{'source_checkpoint':'changed'},
                {'last_playable_checkpoint':'unaccepted'},{'connected_plan_retained_attempted':True},
                {'task_failures':0}]:
            with self.assertRaises(Halt):m.validate_boundary(dict(old,**changed),response)
        bad=copy.deepcopy(response);bad['choices'][0]['message']['tool_calls']=[{'function':'anything'}]
        with self.assertRaises(Halt):m.validate_boundary(old,bad)
        bad=copy.deepcopy(response);bad['choices'][0]['finish_reason']='stop'
        with self.assertRaises(Halt):m.validate_boundary(old,bad)


if __name__=='__main__':unittest.main()

