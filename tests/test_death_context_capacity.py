from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_death_context_capacity as m
from resume_player_death_focused import FocusedDeath,validate_edit
from loop_controller.core import Halt


class ContextCapacityTests(unittest.TestCase):
    def boundary(self):
        return dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            death_controls_result_recovered=True,shared_workload_priority='simultaneous-no-default-priority',
            blocker='Halt: Focused death route-relay-death incomplete; preserve source and diagnose changed continuation',
            active_model_settings={'reasoning_effort':'xhigh'})

    def test_larger_context_requires_exact_measured_boundary(self):
        old=self.boundary();result={'bounded_stop':'context'}
        budget={'session_id':m.PRIOR+'-death-route-relay-death','conservative_prompt_bound':34713}
        m.validate_boundary(old,result,budget)
        for change in ({'controller_pid':8},{'source_checkpoint':'other'},{'task_failures':0},
                {'death_context_capacity_attempted':True},{'active_model_settings':{'reasoning_effort':'low'}}):
            with self.subTest(change=change),self.assertRaises(Halt):
                m.validate_boundary(dict(old,**change),result,budget)
        with self.assertRaises(Halt):m.validate_boundary(old,{'bounded_stop':'output'},budget)
        with self.assertRaises(Halt):m.validate_boundary(old,result,dict(budget,conservative_prompt_bound=20000))

    def test_cross_phase_api_visibility_does_not_grant_write_access(self):
        self.assertEqual(FocusedDeath.phase_context_tokens,49152)
        self.assertEqual(m.DeathContextCapacity.phase_context_tokens,65536)
        label,names,_=m.DeathContextCapacity.phases[1]
        self.assertIn('RouteMission.cs',m.DeathContextCapacity.phase_readonly[label])
        with self.assertRaises(ValueError):
            validate_edit('Assets/Game/RouteMission.cs','changed',{'Assets/Game/'+n for n in names},'')


if __name__=='__main__':unittest.main()
