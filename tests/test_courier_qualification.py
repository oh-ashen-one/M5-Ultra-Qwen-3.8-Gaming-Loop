import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import resume_courier_qualification as recovery
from qualify_visual_replay import verify_completed_native
from loop_controller.adapters import encode_directory
from loop_controller.core import Halt, atomic, seal, sha


class CourierQualificationTests(unittest.TestCase):
    def test_only_exact_diagnosed_stop_can_resume_once(self):
        state = dict(source_checkpoint=recovery.SOURCE, last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND, task_index=7, task_failures=7, failure_streak=1,
            diagnosis_used=True, overall_deadline_epoch=recovery.HARD_CAP_EPOCH, blocker=recovery.BLOCKER)
        original = copy.deepcopy(state)
        recovery.validate_pause(state)
        self.assertEqual(state, original)
        for key, value in [('source_checkpoint', 'other'), ('task_failures', 0),
                           ('blocker', 'memory fault'), ('process_scan_recovery_attempted', True),
                           ('overall_deadline_epoch', recovery.HARD_CAP_EPOCH + 1)]:
            with self.subTest(key=key), self.assertRaises(Halt):
                recovery.validate_pause({**state, key:value})

    def test_reuse_rejects_changed_source_probe_gate_build_or_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / 'saved-native'
            app = bundle / 'build/ChicagoLocalSlice.app'
            app.mkdir(parents=True);(app / 'binary').write_bytes(b'native')
            captures = bundle / 'captures';captures.mkdir()
            probe = {'duration':16, 'coverage':'foundation', 'steps':[], 'captures':[3]}
            atomic(captures / 'scenario.json', probe)
            (captures / 'frame-000.png').write_bytes(b'preserved')
            gate = dict(passed=True, candidate_commit='source', build_exit=0, player_exit=0,
                capture_id=bundle.name, build_id=sha(encode_directory(app)))
            atomic(bundle / 'scoped-gate.json', gate)
            receipt = dict(gate_sha256=sha((bundle / 'scoped-gate.json').read_bytes()),
                build_id=gate['build_id'], capture_manifest_sha256=seal(captures, {'candidate':'source'}))
            with patch('loop_controller.adapters.evaluate_runtime', return_value={'passed':True}) as evaluate:
                self.assertEqual(verify_completed_native(bundle, 'source', probe, receipt), gate)
                evaluate.assert_called_once()
                for candidate, changed_probe in [('other',probe), ('source',{**probe,'duration':17})]:
                    with self.assertRaises(Halt): verify_completed_native(bundle,candidate,changed_probe,receipt)
                for path in [app/'binary', captures/'frame-000.png', bundle/'scoped-gate.json']:
                    original=path.read_bytes();path.write_bytes(b'changed')
                    with self.assertRaises(Halt): verify_completed_native(bundle,'source',probe,receipt)
                    path.write_bytes(original)
            with patch('loop_controller.adapters.evaluate_runtime', return_value={'passed':False}):
                with self.assertRaises(Halt): verify_completed_native(bundle,'source',probe,receipt)


if __name__ == '__main__': unittest.main()
