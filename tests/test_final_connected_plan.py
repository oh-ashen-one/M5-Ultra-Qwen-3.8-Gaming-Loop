from pathlib import Path
import json
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import finalize_connected_plan as m
from loop_controller.core import Halt


class FinalPlanTests(unittest.TestCase):
    def test_only_complete_final_fields_are_saved(self):
        plan={k:'Concrete local design decision with enough source and acceptance detail.' for k in m.FIELDS}
        self.assertTrue(m.final_text_plan(json.dumps(plan))['ok'])
        for value in ['Plan saved.',json.dumps({'summary':'Plan saved.'}),json.dumps(plan)[:-1],
                'private prose before '+json.dumps(plan),json.dumps(dict(plan,next_actions='too short'))]:
            with self.subTest(value=value[:45]),self.assertRaises((ValueError,TypeError)):
                m.final_text_plan(value)

    def test_stop_claim_is_not_a_real_plan_or_tool_submission(self):
        text='Plan saved: retained local counter-exfil concept.'
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.SOURCE,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            connected_plan_retained_attempted=True,
            blocker='Halt: Death repair accepted; retain the bounded next-plan result for focused continuation',
            next_connected_expansion={'summary':text})
        response={'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':text}}]}
        m.validate_boundary(old,response)
        with self.assertRaises(Halt):m.validate_boundary(dict(old,connected_plan_final_attempted=True),response)
        with self.assertRaises(Halt):m.validate_boundary(dict(old,next_connected_expansion={'ok':True}),response)
        response['choices'][0]['message']['tool_calls']=[{}]
        with self.assertRaises(Halt):m.validate_boundary(old,response)


if __name__=='__main__':unittest.main()

