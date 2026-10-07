from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import refine_counter_exfil_scope as m
from loop_controller.core import Halt


class ScopeBoundaryTests(unittest.TestCase):
    def test_only_concrete_proposal_on_accepted_source_can_continue(self):
        plan={k:'A concrete local proposal decision with measured boundaries still requiring qualification.' for k in m.FIELDS}
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.SOURCE,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            connected_plan_final_attempted=True,
            blocker='Halt: Death repair accepted and next local connected scope saved; seal acceptance and continue implementation',
            next_connected_expansion=dict(ok=True,local_authored=True,**plan))
        m.validate_boundary(old)
        for change in ({'controller_pid':3},{'source_checkpoint':'another'},
                {'counter_exfil_scope_review_attempted':True},{'next_connected_expansion':{'summary':'Plan saved'}},
                {'last_playable_checkpoint':'unaccepted'},{'overall_deadline_epoch':m.HARD_CAP_EPOCH+1}):
            with self.subTest(change=change),self.assertRaises(Halt):m.validate_boundary(dict(old,**change))


if __name__=='__main__':unittest.main()
