import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.counter_exfil_death_checks import inspect_frozen

def state(armed=True,**changes):
    fields=dict(armed=armed,active=False,complete=False,failed=False,killedCount=0,escapedCount=0,activeTime=0.0,failReason='')
    fields.update(changes)
    return dict(available=True,actors=[],chapter=[dict(name=k,type='Boolean' if isinstance(v,bool) else 'Single' if isinstance(v,float) else 'Int32' if isinstance(v,int) else 'String',value=str(v)) for k,v in fields.items()])

class CounterDeathEvidenceTests(unittest.TestCase):
    def sample(self):
        injection=dict(time=85.2,counterBefore=state())
        rows=[dict(time=85.21+.1*i,restarts=0,health=0,counterExfil=state()) for i in range(30)]
        rows += [dict(time=89.11+.1*i,restarts=1,health=100,counterExfil=state(False)) for i in range(7)]
        return rows,injection
    def test_exact_edge_freeze_and_reset(self):
        rows,inj=self.sample();self.assertTrue(inspect_frozen(rows,inj,'armed-start')['passed'])
    def test_one_posthumous_progress_sample_is_rejected(self):
        for change in [dict(active=True),dict(activeTime=.02),dict(killedCount=1),dict(complete=True)]:
            rows,inj=self.sample();rows[0]['counterExfil']=state(**change)
            self.assertFalse(inspect_frozen(rows,inj,'armed-start')['passed'])
    def test_missing_actual_injection_edge_or_stale_reset_cannot_pass(self):
        rows,inj=self.sample();bad=copy.deepcopy(inj);bad.pop('counterBefore')
        self.assertFalse(inspect_frozen(rows,bad,'armed-start')['passed'])
        rows[-1]['counterExfil']=state()
        self.assertIn('counter-state-or-actors-survive-R',inspect_frozen(rows,inj,'armed-start')['failure'])

if __name__=='__main__':unittest.main()
