import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from resume_integrated_route import validate_integrated_pause, integrated_probe, QUALIFIED, ACCEPTED, BLOCKER
from loop_controller.combat_checks import FOOT_PROBE
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class IntegratedRecoveryTests(unittest.TestCase):
    def test_only_exact_unattempted_replay_stop_is_admitted(self):
        state = dict(source_checkpoint=QUALIFIED, last_playable_checkpoint=ACCEPTED,
            task_index=6, task_failures=6, failure_streak=2, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
        original = copy.deepcopy(state)
        validate_integrated_pause(state)
        self.assertEqual(state, original)
        for key, value in [('source_checkpoint', 'other'), ('last_playable_checkpoint', 'other'),
                           ('task_failures', 0), ('failure_streak', 0), ('diagnosis_used', False),
                           ('blocker', 'runtime fault'), ('integrated_recovery_attempted', True),
                           ('overall_deadline_epoch', HARD_CAP_EPOCH + 1)]:
            with self.subTest(key=key), self.assertRaises(Halt):
                validate_integrated_pause({**state, key: value})

    def test_firing_and_retry_inputs_survive_without_early_reset_or_fixture(self):
        retry = dict(duration=52, steps=[dict(start=32, end=32.3, keys=['R']),
            dict(start=36, end=37.1, keys=['S']), dict(start=37.5, end=39.1, keys=['W', 'D']),
            dict(start=39.4, end=39.7, keys=['F']), dict(start=49, end=49.3, keys=['R'])],
            captures=[3.2, 31, 32.5, 50.5])
        original = copy.deepcopy(retry)
        probe = integrated_probe(retry)
        self.assertEqual(retry, original)
        self.assertEqual(probe['steps'][:len(FOOT_PROBE['steps'])], FOOT_PROBE['steps'])
        self.assertEqual(probe['steps'][-len(retry['steps']):], retry['steps'])
        self.assertFalse(any('R' in s['keys'] and s['start'] < 32 for s in probe['steps']))
        self.assertNotIn('fixture', probe)
        self.assertEqual(probe['coverage'], 'combat')
        self.assertIn(31, probe['captures'])
        self.assertIn(47.2, probe['captures'])
        with self.assertRaises(Halt):
            integrated_probe({**retry, 'duration': 51})


if __name__ == '__main__':
    unittest.main()
