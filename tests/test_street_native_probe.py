import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_street_native_probe as recovery
from loop_controller.core import Halt
from loop_controller.recovery_policy import replay_identity


class StreetNativeProbeTests(unittest.TestCase):
    def probe(self):
        steps=[(4.0,8.78125,['W']),(8.78125,12.69791,['D']),
            (13.89791,17.18957,['A']),(17.18957,20.00207,['S']),
            (20.15207,20.50207,['E']),(21.95207,22.70207,['W']),
            (24.20207,25.64647,['W','D']),(25.64647,26.44647,['W']),
            (28.64647,34.14647,['S'])]
        return dict(duration=35.34647,steps=[dict(start=a,end=b,keys=k) for a,b,k in steps],
            captures=[8.58125,10.817,12.89791,13.69791,17.20957,20.80207,26.84647,27.84647,28.54647,33.333,34.99647])

    def test_retiming_keeps_proven_approach_steering_keys_and_relative_gaps(self):
        p=self.probe();before=copy.deepcopy(p)
        self.assertEqual(replay_identity(p),recovery.REPLAY)
        out=recovery.retimed_probe(p);self.assertEqual(p,before)
        self.assertAlmostEqual(out['duration'],50.84647)
        self.assertEqual(out['steps'][0],p['steps'][0])
        self.assertEqual([s['keys'] for s in out['steps']],[s['keys'] for s in p['steps']])
        expected=[0,5,5,0,0,0,0,1.5,4]
        for old,new,extra in zip(p['steps'],out['steps'],expected):
            self.assertAlmostEqual(new['end']-new['start'],old['end']-old['start']+extra)
        for i in range(1,len(p['steps'])):
            self.assertAlmostEqual(out['steps'][i]['start']-out['steps'][i-1]['end'],
                p['steps'][i]['start']-p['steps'][i-1]['end'])
        self.assertAlmostEqual(out['captures'][2],17.89791)
        self.assertAlmostEqual(out['captures'][6],38.34647)
        self.assertTrue(all(t<out['duration'] for t in out['captures']))

    def test_unverified_or_modified_base_inputs_cannot_be_retimed(self):
        p=self.probe();p['steps'][0]['keys'].append('R')
        with self.assertRaises(Halt):recovery.retimed_probe(p)

    def test_resume_pins_the_original_stop_and_preserves_counters(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=20,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,blocker=recovery.BLOCKER,
            street_submission_recovered=True,saved_door_accepted=False,second_street_attempts=1)
        before=copy.deepcopy(state);recovery.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('street_native_probe_attempted',True),('source_checkpoint','other'),
                          ('task_failures',0),('blocker','engine fault')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_pause({**state,key:value})


if __name__=='__main__':unittest.main()
