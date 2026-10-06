import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_moving_encounter import exploratory_probe,validate_pause,SOURCE,ROUND,ACCEPTED
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.core import Halt


class MovingEncounterTests(unittest.TestCase):
    def test_exploration_preserves_real_route_removes_old_reset_and_does_not_fake_hits(self):
        original={'steps':[dict(start=4,end=5,keys=['W']),dict(start=59.6,end=59.9,keys=['F']),
                           dict(start=80,end=80.3,keys=['R'])]}
        probe=exploratory_probe(original)
        self.assertEqual(probe['steps'][:2],original['steps'][:2])
        self.assertEqual([s['start'] for s in probe['steps'] if 'R' in s['keys']],[90])
        self.assertFalse(any('Mouse0' in s['keys'] for s in probe['steps']))
        self.assertEqual(probe['duration'],95)

    def test_unqualified_death_or_different_history_cannot_start_source(self):
        old=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            stage='native-combat-lethal-reset',
            blocker='Halt: Actual lethal-hit/reset qualified; continue local moving-target encounter implementation',
            combat_death_outcome=dict(candidate=SOURCE,passed=True))
        validate_pause(old)
        for change in [dict(combat_death_outcome=dict(candidate=SOURCE,passed=False)),dict(task_failures=0),
                       dict(moving_encounter_attempted=True),dict(overall_deadline_epoch=HARD_CAP_EPOCH+1)]:
            with self.assertRaises(Halt): validate_pause({**old,**change})


if __name__=='__main__':unittest.main()
