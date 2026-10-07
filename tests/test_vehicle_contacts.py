import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_vehicle_contact import diagnose_contacts


class VehicleContactTests(unittest.TestCase):
    def rows(self):
        return [dict(time=t,mode='vehicle',vehicle=[3,-.01,8.4],keys=['W'],vehiclePenetration=.01,
            vehiclePhysics=dict(available=True,throttle=1,commandedSpeed=4,
                velocity=[.1,0,.1],contacts=[dict(collider='Rival',otherHasBody=False,
                    time=t,normal=[0,0,-1])])) for t in [22.3,22.4,22.5,22.6]]

    def test_requires_actual_static_actor_contact_under_stalled_throttle(self):
        self.assertTrue(diagnose_contacts(self.rows())['cause_verified'])
        for key,value in [('otherHasBody',True),('collider','GroundCollider'),('normal',[0,1,0]),('time',0)]:
            rows=self.rows()
            for r in rows:r['vehiclePhysics']['contacts'][0][key]=value
            self.assertFalse(diagnose_contacts(rows)['cause_verified'])
        rows=self.rows()
        for i,r in enumerate(rows):r['vehicle']=[3,-.01,8.4+i*.6]
        self.assertFalse(diagnose_contacts(rows)['cause_verified'])

    def test_commanded_velocity_does_not_substitute_for_actual_displacement(self):
        rows=self.rows()
        for r in rows:r['vehiclePhysics']['velocity']=[0,0,6]
        self.assertTrue(diagnose_contacts(rows)['cause_verified'])

    def test_no_measurement_is_not_proof(self):
        self.assertFalse(diagnose_contacts([{'mode':'vehicle','time':22}])['cause_verified'])
