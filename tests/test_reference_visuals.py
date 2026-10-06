import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_reference_visuals import validate_pause,validate_visual_source,SOURCE,ROUND,FAILURE,ACCEPTED,BOOT
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.core import Halt


class ReferenceVisualTests(unittest.TestCase):
    def test_recovery_preserves_exact_completed_replay_and_history(self):
        old=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker=FAILURE)
        validate_pause(old)
        for change in [dict(source_checkpoint='other'),dict(task_failures=0),dict(blocker='different'),
                       dict(reference_visual_repair_attempted=True)]:
            with self.assertRaises(Halt):validate_pause({**old,**change})

    def test_coherent_camera_rewrite_cannot_change_walker_or_bootstrap(self):
        source='protected gameplay\n    public class Follow : MonoBehaviour\n{ old camera; }'
        changed=source.replace('old camera','new camera')
        self.assertEqual(validate_visual_source(BOOT,changed,source),changed)
        with self.assertRaises(ValueError):validate_visual_source(BOOT,changed.replace('protected gameplay','different'),source)
        with self.assertRaises(ValueError):validate_visual_source('Assets/Game/Combat.cs','different',source)


if __name__=='__main__':unittest.main()
