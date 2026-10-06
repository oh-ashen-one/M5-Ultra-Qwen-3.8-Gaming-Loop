import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_saved_door as recovery
from loop_controller.core import Halt
from loop_controller.prop_clone_checks import inspect_door_layers
from qualify_map_extension import outside_distance, inspect_extension


class SavedDoorTests(unittest.TestCase):
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
