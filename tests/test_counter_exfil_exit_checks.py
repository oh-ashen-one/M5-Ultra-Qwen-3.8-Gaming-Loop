from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.counter_exfil_exit_checks import inspect_early_exit

class EarlyExitTests(unittest.TestCase):
    def rows(self):
        result=[]
        for time,x,keys,reset in [(99.4,8,['F'],False),(104.7,3.4,[],False),(104.8,3.1,[],False),(106.1,2.8,['F'],False),(111,2.8,[],False)]+[(120.4+i*.1,0,[],True) for i in range(8)]:
            fields=dict(armed=not reset,active=not reset,complete=False,failed=False,killedCount=0,escapedCount=0,activeTime=0)
            actors=[] if reset else [dict(entityId=str(i),name='CounterExfilRunner'+str(i),hp=6 if i==1 else 3,alive=True,hasBody=True,kinematic=False,colliderEnabled=True,position=[12+i,0,16],contacts=[]) for i in range(1,4)]
            raw=[dict(name=k,type='Boolean' if isinstance(v,bool) else 'Int32',value=str(v)) for k,v in fields.items()]
            result.append(dict(time=time,player=[x,.14,16],mode='foot',health=28,keys=keys,restarts=int(reset),counterExfil=dict(available=True,chapter=raw,actors=actors)))
        return result
    def test_early_real_crossing_without_completion_passes(self):
        self.assertTrue(inspect_early_exit(self.rows(),[])['passed'])
    def test_banked_completion_or_duplicate_spawn_is_rejected(self):
        rows=self.rows();next(v for v in rows[4]['counterExfil']['chapter'] if v['name']=='complete')['value']='True'
        self.assertFalse(inspect_early_exit(rows,[])['passed'])
        rows=self.rows();rows[4]['counterExfil']['actors'][0]['entityId']='another'
        self.assertIn('duplicate-wave-or-unearned-target-damage',inspect_early_exit(rows,[])['failure'])
    def test_missing_actual_crossing_cannot_pass(self):
        rows=self.rows()
        for r in rows:r['player'][0]=2.8
        self.assertFalse(inspect_early_exit(rows,[])['passed'])

if __name__=='__main__':unittest.main()
