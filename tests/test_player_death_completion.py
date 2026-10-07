import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from continue_player_death_integration import (validate_boundary, SOURCE, PRIOR, ACCEPTED,
    HARD_CAP_EPOCH, REMAINING, CompleteDeath)
from loop_controller.core import Halt


class CompleteDeathTests(unittest.TestCase):
    def boundary(self):
        native=dict(candidate=SOURCE,model_unloaded=True,walking={'passed':True},
            positive=dict(passed=True,candidate_commit=SOURCE,build_id='verified-build'),
            death_contract=dict(candidate=SOURCE,build_id='verified-build',setup_passed=True,
                failure=sorted(REMAINING)))
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
            task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            shared_workload_priority='simultaneous-no-default-priority',
            blocker='Halt: Local install/walk source passes healthy route and dead-walking/reset verification; full death integration remains pending',
            capacity_trial_native_outcome=copy.deepcopy(native),
            player_death_red_outcome={'all_setups_valid':True},
            active_model_settings={'reasoning_effort':'xhigh'})
        return old,native

    def test_preserves_real_source_owner_quality_and_failure_history(self):
        old,native=self.boundary();validate_boundary(old,native)
        for changed in ({'controller_pid':9},{'owned_process':{'pid':9}},{'source_checkpoint':'other'},
                {'task_failures':0},{'failure_streak':0},{'player_death_completion_attempted':True},
                {'player_death_green_attempted':True},{'active_model_settings':{'reasoning_effort':'low'}},
                {'overall_deadline_epoch':HARD_CAP_EPOCH+1}):
            with self.subTest(changed=changed),self.assertRaises(Halt):
                validate_boundary(dict(old,**changed),native)

    def test_requires_same_build_positive_walking_and_real_remaining_failures(self):
        for field,change in [('positive',{'passed':False}),('walking',{'passed':False}),
                ('death_contract',{'build_id':'different'}),('death_contract',{'failure':[]}),
                ('death_contract',{'setup_passed':False})]:
            old,native=self.boundary();native[field].update(change)
            old['capacity_trial_native_outcome']=copy.deepcopy(native)
            with self.subTest(field=field,change=change),self.assertRaises(Halt):
                validate_boundary(old,native)
        old,native=self.boundary();native['model_unloaded']=False
        with self.assertRaises(Halt):validate_boundary(old,native)

    def test_already_verified_bootstrap_and_authority_are_not_writable(self):
        names={name for _,files,_ in CompleteDeath.phases for name in files}
        self.assertEqual(names,{'VehicleInteraction.cs','Combat.cs','Mission.cs','RouteMission.cs',
            'RelaySequence.cs','InterceptionMission.cs','MissionDirectorHud.cs'})
        self.assertNotIn('Bootstrap.cs',names)
        self.assertNotIn('DeathAuthority.cs',names)


if __name__=='__main__':unittest.main()
