import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import resume_coupe_export as recovery
from loop_controller.core import Halt, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH


class CoupeExportRecoveryTests(unittest.TestCase):
    def test_exact_pause_is_preserved_and_unrelated_faults_are_rejected(self):
        state = dict(source_checkpoint=recovery.SOURCE, last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND, task_index=7, task_failures=6, failure_streak=1,
            diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH, blocker=recovery.BLOCKER)
        original = copy.deepcopy(state); recovery.validate_coupe_export_pause(state)
        self.assertEqual(state, original)
        for key, value in [('blocker', 'runtime fault'), ('task_failures', 0),
                           ('source_checkpoint', 'other'), ('last_playable_checkpoint', 'other'),
                           ('overall_deadline_epoch', HARD_CAP_EPOCH + 1),
                           ('coupe_export_completion_attempted', True)]:
            with self.subTest(key=key), self.assertRaises(Halt):
                recovery.validate_coupe_export_pause({**state, key:value})

    def test_export_only_role_cannot_retry_or_finish_without_export(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root); (project / 'Art').mkdir()
            script = project / recovery.SCRIPT; script.write_text('local original art\n')
            engine = Mock(return_value={'ok': True})
            def session(*args, **kwargs):
                dispatch = args[5]
                self.assertEqual(set(dispatch), {'run_blender', 'finish_task'})
                with self.assertRaises(ValueError): dispatch['finish_task']('a', {'summary': 'early'})
                dispatch['run_blender']('b', {})
                with self.assertRaises(Halt): dispatch['run_blender']('c', {})
                return dispatch['finish_task']('d', {'summary': 'exported'})
            runner = SimpleNamespace(project=project, c={}, store=Mock(),
                engines=SimpleNamespace(blender=engine), model=SimpleNamespace(session=session))
            with patch.object(recovery, 'SCRIPT_SHA', sha(script.read_bytes())), \
                    patch.object(recovery, 'validate_exports') as validate:
                recovery.export_saved_coupe(runner)
            engine.assert_called_once(); self.assertEqual(validate.call_count, 3)

    def test_changed_source_stops_before_model_or_engine_call(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root); (project / 'Art').mkdir()
            (project / recovery.SCRIPT).write_text('unexpected changes')
            runner = SimpleNamespace(project=project, model=Mock(), engines=Mock())
            with self.assertRaises(Halt): recovery.export_saved_coupe(runner)
            runner.model.session.assert_not_called(); runner.engines.blender.assert_not_called()


if __name__ == '__main__': unittest.main()
