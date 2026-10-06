import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_alley_presentation as p
from loop_controller.core import Halt


class PresentationRecoveryTests(unittest.TestCase):
    def test_changed_complete_proposal_cannot_be_recovered(self):
        from resume_alley_completed import completed_entrance
        with self.assertRaises(Halt):completed_entrance(b'changed original response')

    def test_exact_visual_recovery_preserves_counters_and_physical_replay(self):
        s=dict(source_checkpoint=p.SOURCE,last_playable_checkpoint=p.ACCEPTED,current_round=p.ROUND,
            task_index=7,task_failures=16,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=p.HARD_CAP_EPOCH,vehicle_contact_fix_submitted=True,
            blocker='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored',
            last_valid_replay={})
        old=copy.deepcopy(s)
        with patch.object(p,'replay_identity',return_value=p.REPLAY):
            p.validate_presentation_pause(s);self.assertEqual(s,old)
            for k,v in [('task_failures',0),('source_checkpoint','other'),('alley_presentation_recovery_attempted',True)]:
                with self.assertRaises(Halt):p.validate_presentation_pause({**s,k:v})
        with patch.object(p,'replay_identity',return_value='changed'):
            with self.assertRaises(Halt):p.validate_presentation_pause(s)
