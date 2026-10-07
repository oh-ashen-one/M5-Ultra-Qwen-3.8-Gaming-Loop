import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.counter_exfil_success_checks import physical_pins,inspect_success

class PhysicalPinEvidenceTests(unittest.TestCase):
    def actor(self,x):
        return dict(entityId='runner:1',name='CounterExfilRunner1',hp=6,alive=True,hasBody=True,
            kinematic=False,colliderEnabled=True,position=[x,.14,16],contacts=[dict(vehicle=True)])
    def rows(self):
        return [dict(time=t,restarts=0,counterExfil=dict(actors=[self.actor(10-.1*t)])) for t in (.1,.2,1.0)]
    def event(self,t,kind):
        return dict(time=t,kind=kind,entityId='runner:1',otherId='car:1',otherIsVehicle=True,contacts=[dict(vehicle=True)])
    def test_real_contact_and_measured_obstruction_required(self):
        rows=self.rows();events=[self.event(0,'enter')]
        self.assertEqual(len(physical_pins(rows,events,rows[-1])),1)
        rows[-1]['counterExfil']['actors'][0]['position'][0]=8
        self.assertEqual(physical_pins(rows,events,rows[-1]),[])
    def test_separation_restarts_continuous_contact_even_when_touching_again(self):
        rows=self.rows();events=[self.event(0,'enter'),self.event(.5,'exit'),self.event(.6,'enter')]
        self.assertEqual(physical_pins(rows,events,rows[-1]),[])
    def test_average_stop_cannot_hide_moving_interval(self):
        rows=[dict(time=t,restarts=0,counterExfil=dict(actors=[self.actor(x)])) for t,x in [(0,10),(.2,10),(.4,9.9),(1,9.9)]]
        self.assertEqual(physical_pins(rows,[self.event(0,'enter')],rows[-1]),[])
    def test_dead_or_nonphysical_contact_cannot_supply_a_pin(self):
        rows=self.rows();events=[self.event(0,'enter')]
        for field,value in [('alive',False),('kinematic',True),('colliderEnabled',False)]:
            before=rows[-1]['counterExfil']['actors'][0][field];rows[-1]['counterExfil']['actors'][0][field]=value
            self.assertEqual(physical_pins(rows,events,rows[-1]),[])
            rows[-1]['counterExfil']['actors'][0][field]=before
    def test_complete_claim_without_activation_physics_shots_is_not_success(self):
        rows=[dict(time=1,restarts=0,counterExfil=dict(available=True,chapter=[dict(name='complete',type='Boolean',value='True')],actors=[]))]
        self.assertFalse(inspect_success(rows,[],[])['passed'])

if __name__=='__main__':unittest.main()
