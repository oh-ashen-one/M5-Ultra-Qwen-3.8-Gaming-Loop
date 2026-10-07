import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.core import Halt
from loop_controller.scene_inventory import inspect_inventory, require_complete_inventory, require_gameplay_compile_failure
import resume_complete_inventory as recovery
import resume_inventory_api as api_recovery


class SceneInventoryTests(unittest.TestCase):
    def observation(self,count=2200):
        objects=[dict(kind='renderer',entityId=str(i+1),enabled=i%2==0) for i in range(count)]
        objects.append(dict(kind='BoxCollider',entityId=str(count+1)))
        return dict(schemaVersion=2,observedAtSeconds=.5167,complete=True,truncated=False,
            rendererTotal=count,rendererRecorded=count,colliderTotal=1,colliderRecorded=1,objects=objects)

    def test_complete_inventory_above_old_cap_is_accepted_without_dropping_inactive_objects(self):
        data=self.observation();old=copy.deepcopy(data);result=inspect_inventory(data)
        self.assertTrue(result['passed']);self.assertEqual(result['observed_counts']['renderer'],2200)
        self.assertEqual(data,old);require_complete_inventory({'scene_inventory':result})

    def test_truncated_records_fail_even_when_complete_flag_claims_success(self):
        data=self.observation();data['objects']=data['objects'][:2048]+data['objects'][-1:]
        result=inspect_inventory(data)
        self.assertFalse(result['passed']);self.assertIn('renderer-inventory-count-mismatch',result['failure'])
        with self.assertRaises(Halt):require_complete_inventory({'passed':True,'scene_inventory':result})

    def test_explicit_truncation_and_missing_legacy_metadata_fail_closed(self):
        data=self.observation()
        self.assertFalse(inspect_inventory({**data,'truncated':True})['passed'])
        self.assertFalse(inspect_inventory({'objects':data['objects'][:2048]})['passed'])
        with self.assertRaises(Halt):require_complete_inventory({'passed':True})

    def test_duplicate_component_ids_cannot_pad_a_capped_inventory(self):
        data=self.observation(3);data['objects'][1]['entityId']=data['objects'][0]['entityId']
        result=inspect_inventory(data);self.assertFalse(result['passed'])
        self.assertIn('missing-or-duplicate-scene-component-identity',result['failure'])

    def test_snapshot_must_follow_initialization_and_precede_replay_input(self):
        for time in [0,.49,4,float('nan')]:
            self.assertFalse(inspect_inventory({**self.observation(2),'observedAtSeconds':time})['passed'])

    def test_harness_compile_errors_stop_before_local_gameplay_repairs(self):
        require_gameplay_compile_failure(['Assets/Game/Example.cs(3): error CS1002'])
        for path in ['Assets/LoopHarness/LoopRuntime.cs','Assets\\LoopHarness\\LoopRuntime.cs']:
            with self.assertRaises(Halt):require_gameplay_compile_failure([path+'(52): error CS0619'])

    def test_recovery_preserves_intervening_local_edit_and_exact_fault_history(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=21,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,blocker='Halt: Explicit controller stop',
            street_native_probe_attempted=True,saved_door_accepted=False,second_street_attempts=2)
        before=copy.deepcopy(state);recovery.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('complete_inventory_recovery_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('second_street_attempts',0),('blocker','other fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_pause({**state,key:value})

    def test_api_recovery_preserves_both_failed_rounds_and_counters(self):
        state=dict(source_checkpoint=api_recovery.SOURCE,last_playable_checkpoint=api_recovery.ACCEPTED,
            current_round=api_recovery.ROUND,task_index=7,task_failures=22,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=api_recovery.HARD_CAP_EPOCH,
            blocker='Halt: Explicit controller stop',street_native_probe_attempted=True,
            saved_door_accepted=False,second_street_attempts=3,
            complete_inventory_recovery_attempted=True,complete_inventory_native_attempts=1)
        before=copy.deepcopy(state);api_recovery.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('inventory_api_recovery_attempted',True),('task_failures',21),
                          ('source_checkpoint',api_recovery.EARLIER_SOURCE),('second_street_attempts',2),
                          ('complete_inventory_native_attempts',0),('current_round',api_recovery.COMPILE_ROUND)]:
            with self.subTest(key=key),self.assertRaises(Halt):api_recovery.validate_pause({**state,key:value})


if __name__=='__main__':unittest.main()
