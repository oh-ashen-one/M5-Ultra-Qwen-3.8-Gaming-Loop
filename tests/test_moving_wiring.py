import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_moving_wiring import validate_pause,SOURCE,ROUND,ACCEPTED,wiring
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class MovingWiringTests(unittest.TestCase):
    def test_recovery_cannot_reinterpret_another_stop_or_weaken_history(self):
        old=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            stage='local-hud-polish-moving-encounter-current-objective',
            blocker='Halt: Local HUD correction not saved: moving-encounter-current-objective: {"bounded_stop": "turns", "summary": "Tool-turn budget exhausted; preserve partial work for the next task."}')
        validate_pause(old)
        for changes in [dict(source_checkpoint='other'),dict(task_failures=0),dict(moving_wiring_recovered=True),dict(blocker='other')]:
            with self.assertRaises(Halt):validate_pause({**old,**changes})
        with self.assertRaises(Halt):wiring(b'changed-public-submission')


if __name__=='__main__':unittest.main()
