from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_death_context_boundary import (validate_boundary,SOURCE,PRIOR,ACCEPTED,
    HARD_CAP_EPOCH,DeathContextRecovery)
from resume_player_death_focused import FocusedDeath
from loop_controller.core import Halt


class DeathContextBoundaryTests(unittest.TestCase):
    def boundary(self):
        return dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            player_death_completion_attempted=True,shared_workload_priority='simultaneous-no-default-priority',
            blocker='Halt: Focused death remaining-controls incomplete; preserve source and diagnose changed continuation',
            active_model_settings={'reasoning_effort':'xhigh'})

    def test_exact_context_stop_preserves_owner_source_and_failures(self):
        old=self.boundary();validate_boundary(old,{'bounded_stop':'context'})
        for changes in ({'controller_pid':7},{'source_checkpoint':'other'},{'task_failures':0},
                {'death_context_recovery_attempted':True},{'player_death_green_attempted':True},
                {'active_model_settings':{'reasoning_effort':'low'}}):
            with self.subTest(changes=changes),self.assertRaises(Halt):
                validate_boundary(dict(old,**changes),{'bounded_stop':'context'})
        for cause in ['output','resource','turns',None]:
            with self.subTest(cause=cause),self.assertRaises(Halt):
                validate_boundary(old,{'bounded_stop':cause})

    def test_no_edit_completion_is_only_for_verified_retained_controls(self):
        self.assertEqual(FocusedDeath.allow_unchanged_phases,())
        self.assertEqual(DeathContextRecovery.allow_unchanged_phases,('verify-retained-controls',))
        self.assertEqual([len(names) for _,names,_ in DeathContextRecovery.phases],[3,2,2])
        self.assertNotIn('Bootstrap.cs',{n for _,names,_ in DeathContextRecovery.phases for n in names})


if __name__=='__main__':unittest.main()
