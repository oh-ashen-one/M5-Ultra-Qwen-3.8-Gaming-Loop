import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from qualify_map_extension import inspect_extension
import resume_map_after_courier as recovery
from loop_controller.core import Halt


class MapExtensionTests(unittest.TestCase):
    def test_new_map_scope_preserves_exact_courier_rejection(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=8,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,
            blocker=recovery.BLOCKER,process_scan_recovery_attempted=True)
        old=copy.deepcopy(state);recovery.validate_map_pause(state);self.assertEqual(state,old)
        for key,value in [('source_checkpoint','other'),('task_failures',0),
                          ('map_after_courier_attempted',True),('blocker','memory fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):
                recovery.validate_map_pause({**state,key:value})

    def rows(self):
        rows=[]
        for mode in ['foot','vehicle']:
            # Continuous excursion six metres past the east boundary and back.
            for x in list(range(0,13))+[12]*12+list(range(11,-1,-1)):
                rows.append(dict(time=4+len(rows)*.1,mode=mode,player=[x,.14,10],
                    vehicle=[x,.14,10],grounded=True,playerCollisionEnabled=True,
                    vehicleCollisionEnabled=True,playerPenetration=0,vehiclePenetration=0,
                    restarts=0,keys=['W']))
        return rows

    def test_real_out_and_back_is_scoped_acceptance(self):
        result=inspect_extension(self.rows())
        self.assertTrue(result['passed'],result)
        self.assertEqual(result['traversal']['foot']['maximum_distance_beyond_old_boundary_m'],6)

    def test_old_corridor_alone_cannot_pass(self):
        rows=self.rows()
        for row in rows:row['player'][0]=min(row['player'][0],6);row['vehicle'][0]=min(row['vehicle'][0],6)
        self.assertFalse(inspect_extension(rows)['passed'])

    def test_reset_or_teleport_does_not_count_as_return(self):
        for reset in [True,False]:
            rows=self.rows()
            for row in rows[30:38]:
                if reset:row['restarts']=1;row['keys']=['R']
                else:row['player'][0]=0
            self.assertFalse(inspect_extension(rows)['passed'])

    def test_colliders_grounding_and_both_modes_required(self):
        for key,value in [('playerCollisionEnabled',False),('vehiclePenetration',1),('grounded',False)]:
            rows=self.rows()
            for row in rows:row[key]=value
            self.assertFalse(inspect_extension(rows)['passed'])
        self.assertFalse(inspect_extension([r for r in self.rows() if r['mode']=='foot'])['passed'])


if __name__=='__main__':unittest.main()
