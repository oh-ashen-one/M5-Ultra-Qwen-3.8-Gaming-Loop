from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from repair_character_clips import validate_boundary,SOURCE,PRIOR,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

class CharacterClipRepairBoundary(unittest.TestCase):
    def test_repair_cannot_take_over_or_erase_failed_history(self):
        state=dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=SOURCE,
            last_playable_checkpoint=ACCEPTED,current_round=PRIOR,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Local clothed character export failed; preserve source and actual Blender diagnostic')
        validate_boundary(state)
        for mutation in [dict(controller_pid=3),dict(owned_process={'pid':3}),dict(source_checkpoint='changed'),
                dict(last_playable_checkpoint=SOURCE),dict(task_failures=0),dict(diagnosis_used=False),
                dict(overall_deadline_epoch=HARD_CAP_EPOCH+1),dict(character_clip_repair_attempted=True),
                dict(blocker='memory fault')]:
            with self.assertRaises(Halt):validate_boundary(dict(state,**mutation))

if __name__=='__main__':unittest.main()
