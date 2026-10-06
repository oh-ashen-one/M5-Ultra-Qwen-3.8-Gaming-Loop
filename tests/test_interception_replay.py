import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from resume_interception_replay import corrected_probe,validate_pause,SOURCE,ROUND,FAILURES,ACCEPTED
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.core import Halt


class InterceptionReplayTests(unittest.TestCase):
    def test_changed_normal_input_preserves_prior_route_and_first_real_kill(self):
        original={'steps':[dict(start=4,end=5,keys=['W']),dict(start=59.6,end=59.9,keys=['F']),
            dict(start=80,end=80.3,keys=['R'])]};before=copy.deepcopy(original)
        probe=corrected_probe(original)
        self.assertEqual(original,before)
        self.assertEqual(probe['steps'][:2],original['steps'][:2])
        shots=[s['start'] for s in probe['steps'] if s['keys']==['Mouse0']]
        self.assertTrue({63.2,63.5,63.8,64.8,65,65.2}<=set(shots))
        turns=[s for s in probe['steps'] if s['keys']==['A'] and s['start']>=66]
        self.assertTrue(all(s['end']-s['start']>=.199 for s in turns))
        self.assertEqual([s['start'] for s in probe['steps'] if 'R' in s['keys']],[90])

    def test_cannot_repeat_unchanged_recovery_or_reclassify_other_failure(self):
        old=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            stage='native-moving-encounter-positive',blocker='Halt: Moving encounter positive needs measured diagnosis: '+json.dumps(FAILURES))
        validate_pause(old)
        for change in [dict(source_checkpoint='different'),dict(moving_replay_recoveries=1),dict(task_failures=0),dict(blocker='unrelated')]:
            with self.assertRaises(Halt):validate_pause({**old,**change})


if __name__=='__main__':unittest.main()
