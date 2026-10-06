import copy
from pathlib import Path
import sys
import json
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.recovery_policy import recovery_route,admit_strategy,replay_identity
from loop_controller.core import Halt,Store
import resume_map_traversal as recovery


class RecoveryPolicyTests(unittest.TestCase):
    def test_native_failure_transitions_to_recovery_and_keeps_accounting(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner=recovery.MapTraversalRecovery.__new__(recovery.MapTraversalRecovery)
            runner.store=Store(Path(tmp))
            runner.store.set(status='running',task_failures=10,failure_streak=1,
                diagnosis_used=True,last_playable_checkpoint=recovery.ACCEPTED,
                map_traversal_strategies=[{'replay_sha256':'earlier'}])
            gate=dict(passed=False,build_exit=0,player_exit=0,compile_errors=[],
                failure=['foot-new-space-not-traversed'])
            runner.reject_scoped(recovery.MAP_TASK,'new-native-round',gate,'local-candidate')
            state=json.loads((Path(tmp)/'status.json').read_text())
            self.assertEqual(state['status'],'running')
            self.assertEqual(state['stage'],'changed-strategy-recovery')
            self.assertEqual(state['task_failures'],11)
            self.assertTrue(state['diagnosis_used'])
            self.assertEqual(state['last_playable_checkpoint'],recovery.ACCEPTED)
            self.assertEqual(state['map_traversal_feedback_round'],'new-native-round')
            runner.report_blocker('Budget exhausted','last-round')
            report=json.loads((Path(tmp)/'RECOVERY-BLOCKER.json').read_text())
            self.assertEqual(report['delivery_status'],'pending-existing-parent-oversight')
            self.assertFalse(report['approval_wait'])
            self.assertEqual(runner.store.get('recovery_route'),'report-blocker')
            runner.store.db.close()

    def test_only_measured_native_traversal_failures_recover_within_cap(self):
        gate=dict(passed=False,build_exit=0,player_exit=0,compile_errors=[],
            failure=['foot-new-space-not-traversed'])
        self.assertEqual(recovery_route(gate,0),'changed-strategy')
        self.assertEqual(recovery_route(gate,2),'changed-strategy')
        self.assertEqual(recovery_route(gate,3),'report-blocker')
        for defect in [dict(build_exit=1),dict(player_exit=1),dict(passed=True),
            dict(compile_errors=['error']),dict(failure='runtime fault'),
            dict(failure=['permission required']),dict(failure=['resource fault']),dict(failure=[])]:
            with self.subTest(defect=defect):
                self.assertEqual(recovery_route({**gate,**defect},0),'report-blocker')

    def test_changed_summary_or_captures_cannot_hide_identical_physical_replay(self):
        scenario={'duration':20,'steps':[{'start':4,'end':8,'keys':['W']}],'captures':[5,7,9,11]}
        record=admit_strategy(scenario,'Measured obstacle requires a different physical route.',[])
        unchanged=copy.deepcopy(scenario);unchanged['captures']=[6,8,10,12]
        with self.assertRaisesRegex(ValueError,'Unchanged'):admit_strategy(unchanged,'A new summary with the same physical actions.',[record])
        changed=copy.deepcopy(scenario);changed['steps'][0]['end']=9
        self.assertNotEqual(replay_identity(changed),record['replay_sha256'])
        self.assertEqual(admit_strategy(changed,'A different route based on the actual measured trace.',[record])['attempt'],2)
        with self.assertRaisesRegex(ValueError,'exhausted'):admit_strategy(changed,'A different strategy with new evidence.',[record]*3)

    def test_initial_resume_pins_failure_and_keeps_old_counters(self):
        old=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=10,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=recovery.HARD_CAP_EPOCH,blocker=recovery.BLOCKER,map_compile_recovery_attempted=True)
        before=copy.deepcopy(old);recovery.validate_traversal_pause(old);self.assertEqual(old,before)
        for key,value in [('map_traversal_recovery_attempted',True),('task_failures',0),('blocker','permission required'),('source_checkpoint','other')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_traversal_pause({**old,key:value})


if __name__=='__main__':unittest.main()
