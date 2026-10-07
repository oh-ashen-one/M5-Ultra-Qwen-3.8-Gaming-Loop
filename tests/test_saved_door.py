import copy
from pathlib import Path
import sys
import unittest
import json
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_saved_door as recovery
import resume_second_street as second
from loop_controller.core import Halt, atomic, seal, sha
from loop_controller.prop_clone_checks import inspect_door_layers
from qualify_map_extension import outside_distance, inspect_extension


class SavedDoorTests(unittest.TestCase):
    def test_deferred_visual_fix_keeps_exact_rejection_and_counters(self):
        state=dict(source_checkpoint=second.SOURCE,last_playable_checkpoint=second.ACCEPTED,
            current_round=second.ROUND,task_index=7,task_failures=20,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=second.HARD_CAP_EPOCH,blocker=second.BLOCKER,
            saved_door_recovery_attempted=True,second_street_attempts=0)
        before=copy.deepcopy(state);second.validate_pause(state);self.assertEqual(before,state)
        for key,value in [('door_fix_deferred_for_street',True),('task_failures',0),
                          ('source_checkpoint','other'),('blocker','runtime fault'),('second_street_attempts',1)]:
            with self.subTest(key=key),self.assertRaises(Halt):second.validate_pause({**state,key:value})

    def test_deferral_requires_real_same_candidate_native_passes_and_preserved_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle=Path(tmp);captures=bundle/'captures';captures.mkdir()
            (captures/'frame.png').write_bytes(b'actual preserved frame')
            manifest=seal(captures,dict(candidate=second.SOURCE,scope='connected-map-extension'))
            checks=[dict(test=name,gate=dict(passed=True,candidate_commit=second.SOURCE)) for name in
                ['walk','world','motor','courier','failure-retry','combat-foot','combat-wall','combat-driving','aim-miss','aim-near-cover']]
            gate=dict(passed=True,candidate_commit=second.SOURCE,
                scoped_facts=dict(door_layer_order=dict(passed=True)),regressions=dict(regressions=checks))
            review=dict(ok=True,verdict='FIX',summary='Preserve this visible concern.',fixes=['Improve contrast'])
            def validate(g,r):
                atomic(bundle/'scoped-gate.json',g);atomic(bundle/'critic.json',r)
                with patch.object(second,'GATE_SHA',sha((bundle/'scoped-gate.json').read_bytes())),\
                     patch.object(second,'CRITIC_SHA',sha((bundle/'critic.json').read_bytes())),\
                     patch.object(second,'MANIFEST_SHA',manifest):
                    return second.validate_evidence(bundle)
            self.assertEqual(validate(gate,review),review)
            with self.assertRaises(Halt):validate({**gate,'passed':False},review)
            with self.assertRaises(Halt):validate(gate,{**review,'verdict':'PASS'})
            checks[0]['gate']['candidate_commit']='different source'
            with self.assertRaises(Halt):validate(gate,review)

    def test_native_geometry_failure_with_null_base_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle=Path(tmp);(bundle/'captures').mkdir()
            atomic(bundle/'captures/scene-transforms.json',{'objects':[]})
            gate=dict(passed=True,failure=None,scoped_facts={})
            runner=recovery.SavedDoor.__new__(recovery.SavedDoor)
            with patch.object(recovery.ContinuousRunner,'native',return_value=(bundle,gate)):
                _,result=runner.native(recovery.DOOR_TASK,'round','candidate',{})
            self.assertFalse(result['passed'])
            self.assertIn('missing-unique-door-renderers',result['failure'])

    def test_recovery_is_one_time_exact_pause_and_preserves_failure_history(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=19,failure_streak=2,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,blocker=recovery.BLOCKER)
        old=copy.deepcopy(state);recovery.validate_pause(state);self.assertEqual(state,old)
        for key,value in [('saved_door_recovery_attempted',True),('task_failures',0),
                          ('source_checkpoint','other'),('blocker','resource failure')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_pause({**state,key:value})

    def test_only_saved_panel_change_can_reuse_old_physical_replay(self):
        line='dgo.transform.position += new Vector3(16f - db.center.x, 0.14f - db.min.y, 19.92f - db.center.z);'
        old='panel\n'+line+'\nsurround\n'+line
        new=old.replace(line,'// measured outward depth\n'+line.replace('19.92f','19.85f'),1)
        self.assertTrue(recovery.door_only(old,new))
        self.assertFalse(recovery.door_only(old,old))
        self.assertFalse(recovery.door_only(old,new.replace('19.92f','19.85f')))
        self.assertFalse(recovery.door_only(old,new+'\nother change'))

    def door(self,panel_z):
        return [dict(name='WorldCollision/ServiceDoor',kind='renderer',boundsCenter=[16,1.19,panel_z],
                     boundsSize=[1.06,2.10,.10],enabled=True),
                dict(name='WorldCollision/ServiceDoorSurround',kind='renderer',boundsCenter=[16,1.43,19.92],
                     boundsSize=[1.46,2.58,.22],enabled=True)]

    def test_native_layer_order_detects_hidden_wood_and_excessive_displacement(self):
        self.assertFalse(inspect_door_layers(self.door(19.92))['passed'])
        result=inspect_door_layers(self.door(19.85));self.assertTrue(result['passed'])
        self.assertAlmostEqual(result['wood_front_ahead_of_stone_m'],.01)
        self.assertFalse(inspect_door_layers(self.door(19))['passed'])
        self.assertFalse(inspect_door_layers(self.door(float('nan')))['passed'])
        self.assertFalse(inspect_door_layers(self.door(19.85)[:1])['passed'])

    def test_repeat_of_old_alley_does_not_establish_a_second_extension(self):
        bounds=recovery.SECOND_TASK['prior_bounds']
        self.assertEqual(outside_distance([19.76,0,17],bounds),0)
        self.assertGreater(outside_distance([19.76,0,17]),6)
        self.assertEqual(outside_distance([28,0,17],bounds),6)
        self.assertEqual(outside_distance([10,0,31],bounds),4)
        rows=[]
        for mode,key,start in [('foot','player',4),('vehicle','vehicle',10)]:
            for i in range(30):
                x=5+min(i,29-i)
                rows.append(dict(time=start+i*.1,mode=mode,**{key:[x,.14,17]},grounded=True,
                    playerCollisionEnabled=True,vehicleCollisionEnabled=True,
                    playerPenetration=0,vehiclePenetration=0,restarts=0,keys=[]))
        self.assertTrue(inspect_extension(rows)['passed'])
        check=inspect_extension(rows,bounds);self.assertFalse(check['passed'])
        self.assertIn('foot-new-space-not-traversed',check['failure'])
        self.assertIn('vehicle-new-space-not-traversed',check['failure'])


if __name__=='__main__':unittest.main()
