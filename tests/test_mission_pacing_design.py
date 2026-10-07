import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_mission_pacing_design as m
from loop_controller.core import Halt

class MissionPacingDesignTests(unittest.TestCase):
    def state(self):
        return dict(source_checkpoint=m.SOURCE,last_playable_checkpoint=m.ACCEPTED,current_round=m.ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
            overall_deadline_epoch=m.HARD_CAP_EPOCH,camera_overlap_micro_attempted=True,
            blocker='Halt: Cause-based camera/street correction did not qualify; preserve measured failure')

    def test_distinct_scope_cannot_erase_failures_extend_cap_or_resume_twice(self):
        state=self.state();before=copy.deepcopy(state);m.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('task_failures',0),('failure_streak',0),('diagnosis_used',False),
                          ('last_playable_checkpoint',m.SOURCE),('overall_deadline_epoch',m.HARD_CAP_EPOCH+1),
                          ('mission_pacing_design_attempted',True),('blocker','resource failure')]:
            with self.subTest(key=key),self.assertRaises(Halt):m.validate_pause({**state,key:value})

    def test_requires_every_current_source_regression_and_both_original_review_scopes(self):
        gate=dict(passed=True,candidate_commit=m.SOURCE,return_camera_review={'verdict':'PASS'},
            regressions={'regressions':[{'test':name,'gate':{'passed':True,'candidate_commit':m.SOURCE}}
                                         for name in sorted(m.REQUIRED)]})
        review=dict(ok=True,verdict='FIX',summary='Unaccepted broad street visuals')
        manifest=dict(candidate=m.SOURCE,scope='connected-map-extension')
        before=copy.deepcopy(gate);self.assertEqual(m.validate_native_outcome(gate,review,manifest),review)
        self.assertEqual(gate,before)
        for mutation in ['missing','duplicate','old-source','failed','camera']:
            altered=copy.deepcopy(gate);checks=altered['regressions']['regressions']
            if mutation=='missing':checks.pop()
            if mutation=='duplicate':checks[-1]=checks[0]
            if mutation=='old-source':checks[0]['gate']['candidate_commit']=m.ACCEPTED
            if mutation=='failed':checks[0]['gate']['passed']=False
            if mutation=='camera':altered['return_camera_review']['verdict']='FIX'
            with self.subTest(mutation=mutation),self.assertRaises(Halt):
                m.validate_native_outcome(altered,review,manifest)
        with self.assertRaises(Halt):m.validate_native_outcome(gate,{**review,'verdict':'PASS'},manifest)

    def test_plan_is_not_source_or_native_acceptance_and_incomplete_submission_fails(self):
        fields={name:'Concrete normal-input mission decision.' for name in m.FIELDS}
        result=m.submitted_plan('',fields)
        self.assertEqual(result,dict(ok=True,**fields))
        for altered in [{**fields,'decision':''},{k:v for k,v in fields.items() if k!='normal_input_proof'},
                        {**fields,'game_accepted':True}]:
            with self.assertRaises(ValueError):m.submitted_plan('',altered)

if __name__=='__main__':unittest.main()

