import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from verify_capacity_trial_native import validate_boundary, walking_scope, ACCEPTED, HARD_CAP_EPOCH, BOOT, POLICY
from loop_controller.core import Halt


class CapacityNativeTests(unittest.TestCase):
    def boundary(self):
        outcome=dict(candidate='local-source',round='q-test',changed_files=[BOOT],
            local_authored=True,complete_death_integration=False)
        old=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,capacity_trial_author_attempted=True,
            shared_workload_priority='simultaneous-no-default-priority',source_checkpoint='local-source',
            current_round='q-test',capacity_trial_source_outcome=outcome,active_model_settings={'reasoning_effort':'xhigh'},
            blocker='Halt: Capacity trial saved local install/walk source; inspect capacity evidence and unload idle model before native verification')
        return old,dict(ok=True,changed_files=[BOOT],capacity_policy=POLICY)

    def test_requires_actual_partial_submission_without_resetting_history(self):
        old,authored=self.boundary();self.assertEqual(validate_boundary(old,authored),'local-source')
        for changed in ({'source_checkpoint':'other'},{'controller_pid':7},{'capacity_trial_native_attempted':True},
                {'task_failures':0},{'active_model_settings':{'reasoning_effort':'low'}}):
            with self.subTest(changed=changed),self.assertRaises(Halt):validate_boundary(dict(old,**changed),authored)
        with self.assertRaises(Halt):validate_boundary(old,dict(authored,ok=False))

    def test_walking_proof_does_not_hide_remaining_contract_failures(self):
        rows=[dict(time=8,mode='foot',restarts=0)]
        red=dict(setup_passed=True,failure=['player-can-fire-while-dead','objective-progression-after-zero-health'])
        result=walking_scope(rows,{'mode':'foot'},red)
        self.assertTrue(result['passed']);self.assertFalse(result['complete_death_integration'])
        for failure in ('player-moves-under-dead-input','ordinary-R-reset-not-established',
                'walking-not-restored-after-reset','missing-zero-health-window'):
            with self.subTest(failure=failure):
                self.assertFalse(walking_scope(rows,{'mode':'foot'},dict(red,failure=[failure]))['passed'])
        self.assertFalse(walking_scope(rows,{'mode':'vehicle'},red)['passed'])
        self.assertFalse(walking_scope(rows,{'mode':'foot'},dict(red,setup_passed=False))['passed'])


if __name__=='__main__':unittest.main()
