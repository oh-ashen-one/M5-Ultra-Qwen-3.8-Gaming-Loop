import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from resume_visual_focus import changed_span, validate_visual_pause, SOURCE, ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class VisualFocusTests(unittest.TestCase):
    def test_restoration_span_preserves_unmodified_surroundings(self):
        current = 'head\nnew1\nnew2\ntail\n'; accepted = 'head\nold\ntail\n'
        start, end, content = changed_span(current, accepted)
        lines = current.splitlines(keepends=True)
        self.assertEqual(''.join(lines[:start-1])+content+''.join(lines[end:]), accepted)
        self.assertIsNone(changed_span(accepted, accepted))

    def test_visual_steering_does_not_clear_other_stops_or_counts(self):
        state = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, task_index=7,
            task_failures=2, failure_streak=1, diagnosis_used=False, overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker='Halt: Requested stop')
        original = copy.deepcopy(state); validate_visual_pause(state); self.assertEqual(state, original)
        for k, v in [('source_checkpoint','other'), ('task_failures',0), ('failure_streak',0),
                     ('blocker','resource fault'), ('visual_focus_attempted',True), ('task_index',6),
                     ('overall_deadline_epoch',HARD_CAP_EPOCH+1)]:
            with self.subTest(key=k), self.assertRaises(Halt): validate_visual_pause({**state,k:v})


if __name__ == '__main__': unittest.main()
