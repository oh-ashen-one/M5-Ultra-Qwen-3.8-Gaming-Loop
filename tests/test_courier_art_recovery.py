import copy
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import resume_courier_art as recovery
from resume_coupe_export import export_saved_asset
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class CourierArtRecoveryTests(unittest.TestCase):
    def state(self):
        return dict(source_checkpoint=recovery.SOURCE, last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND, task_index=7, task_failures=7, failure_streak=1,
            diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH, blocker=recovery.BLOCKER)

    def test_exact_rejected_attempt_is_preserved_without_reset(self):
        state = self.state(); original = copy.deepcopy(state)
        recovery.validate_courier_pause(state); self.assertEqual(state, original)
        for key, value in [('blocker', 'runtime fault'), ('task_failures', 6),
                           ('source_checkpoint', 'other'), ('last_playable_checkpoint', 'other'),
                           ('overall_deadline_epoch', HARD_CAP_EPOCH + 1),
                           ('courier_art_continuation_attempted', True)]:
            with self.subTest(key=key), self.assertRaises(Halt):
                recovery.validate_courier_pause({**state, key:value})

    def test_continuation_refuses_a_changed_fallback_game_tree(self):
        runner = SimpleNamespace(repo=Path('/unused'), project=Path('/unused/game'))
        with patch.object(recovery, 'git', return_value='game/Assets/Game/Bootstrap.cs'), \
                self.assertRaises(Halt):
            recovery.CourierArtResume.validate_recovery(runner, self.state())

    def test_export_completion_cannot_expand_into_new_or_executable_paths(self):
        runner = SimpleNamespace(model=Mock(), engines=Mock())
        for path in ['Art/new_asset.py', 'Assets/Game/Mission.cs', '../Art/player.py']:
            with self.subTest(path=path), self.assertRaises(Halt):
                export_saved_asset(runner, path, 'digest', 'unused')
        runner.model.session.assert_not_called(); runner.engines.blender.assert_not_called()


if __name__ == '__main__': unittest.main()
