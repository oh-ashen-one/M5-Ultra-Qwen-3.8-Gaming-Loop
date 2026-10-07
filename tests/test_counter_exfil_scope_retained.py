from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_counter_exfil_scope as m
from loop_controller.core import Halt


class RetainedScopeTests(unittest.TestCase):
    def test_only_measured_output_stop_can_use_larger_bounded_context(self):
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.SOURCE,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            counter_exfil_scope_review_attempted=True,
            blocker='Halt: Preserve original proposal and measured handoff; concise revised local scope not submitted',
            counter_exfil_reviewed_plan={'bounded_stop':'output'})
        response={'choices':[{'finish_reason':'length','message':{'role':'assistant','content':'private draft'}}],
            'usage':{'completion_tokens':16384}}
        m.validate_boundary(old,response)
        self.assertEqual(m.RetainedScope.scope_output_tokens,32768)
        self.assertLess(m.RetainedScope.scope_context_tokens,262144)
        for change in ({'counter_exfil_scope_retained_attempted':True},{'controller_pid':1},
                {'source_checkpoint':'other'},{'task_failures':0},{'counter_exfil_reviewed_plan':{'ok':True}}):
            with self.subTest(change=change),self.assertRaises(Halt):m.validate_boundary(dict(old,**change),response)
        response['choices'][0]['message']['tool_calls']=[{}]
        with self.assertRaises(Halt):m.validate_boundary(old,response)


if __name__=='__main__':unittest.main()
