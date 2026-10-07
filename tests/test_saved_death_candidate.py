from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import verify_saved_death_candidate as m
from resume_player_death_green import PlayerDeathGreen
from loop_controller.core import Halt


class SavedCandidateTests(unittest.TestCase):
    def fixture(self):
        old=dict(status='paused',controller_pid=None,owned_process=None,current_round=m.PRIOR,
            source_checkpoint=m.SOURCE,last_playable_checkpoint=m.ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=m.HARD_CAP_EPOCH,
            death_context_capacity_attempted=True,shared_workload_priority='simultaneous-no-default-priority',
            blocker='Halt: Focused death interception-hud-death incomplete; preserve source and diagnose changed continuation',
            active_model_settings={'reasoning_effort':'xhigh'})
        route=dict(ok=True,local_authored=True,changed_files=['Assets/Game/RouteMission.cs','Assets/Game/RelaySequence.cs'])
        return old,route,{'bounded_stop':'turns'},b'fixture'

    def test_exact_candidate_does_not_hide_author_incompletion(self):
        old,route,partial,response=self.fixture()
        with self.assertRaises(Halt):m.validate_boundary(old,route,partial,response)
        with patch.object(m,'sha',return_value=m.RESPONSE_SHA):
            m.validate_boundary(old,route,partial,response)
            for changes in ({'controller_pid':5},{'source_checkpoint':'other'},{'task_failures':0},
                    {'player_death_green_attempted':True},{'active_model_settings':{'reasoning_effort':'low'}}):
                with self.subTest(changes=changes),self.assertRaises(Halt):
                    m.validate_boundary(dict(old,**changes),route,partial,response)
            with self.assertRaises(Halt):m.validate_boundary(old,route,{'bounded_stop':'output'},response)
            with self.assertRaises(Halt):m.validate_boundary(old,dict(route,ok=False),partial,response)

    def test_all_existing_native_checks_are_inherited_without_changes(self):
        self.assertIs(m.SavedDeathCandidate.work,PlayerDeathGreen.work)
        settings=m.SavedDeathCandidate.recovery_settings(None)
        self.assertFalse(settings['author_completion_claimed'])
        self.assertTrue(settings['player_death_green_attempted'])


if __name__=='__main__':unittest.main()
