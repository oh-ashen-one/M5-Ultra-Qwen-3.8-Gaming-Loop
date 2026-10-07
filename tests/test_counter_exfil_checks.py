from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.counter_exfil_checks import inspect_activation_escape,values,old_ending_with_armed_hint

class CounterExfilObservationTests(unittest.TestCase):
    def test_armed_hint_requires_actual_old_ending_and_measured_distance(self):
        raw=dict(armed=True,active=False,complete=False,failed=False)
        original='INTERCEPTION COMPLETE\nAll stopped, no escapes\nStopped 3 / Escaped 0\nRelay complete | R reset'
        row=dict(health=28,mode='foot',player=[28,0,14],vehicle=[48,0,14],
            interception=dict(valid=True,complete=True,failed=False,stopped=3,escaped=0,objective=original),
            counterExfil=dict(available=True,actors=[],chapter=[dict(name=k,type='Boolean',value=str(v)) for k,v in raw.items()]))
        text=original+'\nEXFIL coupe 20m | E board, F launch'
        self.assertTrue(old_ending_with_armed_hint(row,text))
        for invalid in (text.replace('All stopped, no escapes','COMPLETE'),text.replace('20m','2m'),text+'\nEXTRA',text.replace('F launch','launch')):
            self.assertFalse(old_ending_with_armed_hint(row,invalid))
        row['counterExfil']['actors']=[{'alive':True}]
        self.assertFalse(old_ending_with_armed_hint(row,text))
        row['counterExfil']['actors']=[];row['health']=0
        self.assertFalse(old_ending_with_armed_hint(row,text))
        row['health']=28;row['interception']['complete']=False
        self.assertFalse(old_ending_with_armed_hint(row,text))
    def test_controller_claims_cannot_replace_actual_runners(self):
        def row(t):
            claimed=dict(armed=True,active=True,failed=True,escapedCount=1,complete=True,killedCount=0,activeTime=20)
            return dict(time=t,restarts=0,health=28,mode='vehicle',player=[28.187391,0,13.939845],
                vehicle=[47.605087,0,17.460318],vehiclePhysics=dict(velocity=[0,0,0]),rivals=[],
                interception=dict(complete=True,stopped=3,escaped=0),counterExfil=dict(available=True,actors=[],
                    chapter=[dict(name=k,type='Boolean' if isinstance(v,bool) else 'Int32',value=str(v)) for k,v in claimed.items()]))
        result=inspect_activation_escape([row(t) for t in (77.2,85.25,110,136.6)])
        self.assertFalse(result['passed'])
        self.assertIn('exact-three-physical-runners-not-observed',result['failure'])
        self.assertIn('failure-without-genuine-unresolved-crossing',result['failure'])
    def test_nonfinite_native_values_are_rejected(self):
        with self.assertRaises(ValueError):values([dict(name='ActiveTime',type='Single',value='NaN')])

if __name__=='__main__':unittest.main()
