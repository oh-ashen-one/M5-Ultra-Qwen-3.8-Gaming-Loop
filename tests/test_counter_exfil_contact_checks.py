from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.counter_exfil_contact_checks import inspect_contact_release

class ContactReleaseTests(unittest.TestCase):
    def data(self):
        rows=[]
        for i in range(980,1251):
            t=i/10;reset=t>=123
            raw=dict(armed=not reset,active=not reset,complete=False,failed=False,killedCount=0,escapedCount=0,activeTime=0)
            fields=[dict(name=k,type='Boolean' if isinstance(v,bool) else 'Int32',value=str(v)) for k,v in raw.items()]
            actor=dict(entityId='r1',name='CounterExfilRunner1',hp=6,alive=True,hasBody=True,kinematic=False,
                colliderEnabled=True,position=[10,.14,16],contacts=[dict(vehicle=True)] if t<115 else [],
                state=[dict(name='hold',type='Single',value='1' if t<115 else '0')])
            rows.append(dict(time=t,restarts=int(reset),counterExfil=dict(available=True,chapter=fields,actors=[] if reset else [actor])))
        events=[dict(time=t,kind=k,entityId='r1',otherId='car',otherIsVehicle=True,contacts=[dict(vehicle=True)] if k=='enter' else []) for t,k in [(97,'enter'),(115,'exit')]]
        return rows,events
    def test_real_pin_then_separation_and_reset_pass(self):
        rows,events=self.data();self.assertTrue(inspect_contact_release(rows,events)['passed'])
    def test_stale_pin_credit_fails(self):
        rows,events=self.data()
        next(r for r in rows if r['time']==115.1)['counterExfil']['actors'][0]['state'][0]['value']='1'
        self.assertIn('pin-credit-survives-real-contact-separation',inspect_contact_release(rows,events)['failure'])
    def test_exit_without_a_qualified_pin_fails(self):
        rows,events=self.data();events[0]['time']=114.8
        self.assertFalse(inspect_contact_release(rows,events)['passed'])

if __name__=='__main__':unittest.main()
