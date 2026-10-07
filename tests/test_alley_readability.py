import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_alley_readability as r
from continue_game_queue import review_captures
from loop_controller.core import Halt


class AlleyReadabilityTests(unittest.TestCase):
    def test_saved_visual_recovery_preserves_partial_source_and_failure_history(self):
        import resume_alley_saved_visuals as saved
        s=dict(source_checkpoint=saved.SOURCE,last_playable_checkpoint=saved.ACCEPTED,
            current_round=saved.ROUND,task_index=7,task_failures=17,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=saved.HARD_CAP_EPOCH,
            alley_readability_recovery_attempted=True,last_valid_replay={},
            blocker='Halt: Scoped readability edit not saved; prior local source preserved')
        original=copy.deepcopy(s)
        with patch.object(saved,'replay_identity',return_value=saved.REPLAY):
            saved.validate_saved_visual_pause(s);self.assertEqual(s,original)
            for key,value in [('source_checkpoint','other'),('task_failures',0),
                              ('blocker','native regression'),('alley_saved_visuals_attempted',True)]:
                with self.assertRaises(Halt):saved.validate_saved_visual_pause({**s,key:value})

    def test_recovery_cannot_reset_failures_or_admit_an_unrelated_pause(self):
        s=dict(source_checkpoint=r.SOURCE,last_playable_checkpoint=r.ACCEPTED,current_round=r.ROUND,
            task_index=7,task_failures=17,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=r.HARD_CAP_EPOCH,alley_completed_recovery_attempted=True,
            blocker=r.BLOCKER,last_valid_replay={})
        original=copy.deepcopy(s)
        with patch.object(r,'replay_identity',return_value=r.REPLAY):
            r.validate_readability_pause(s);self.assertEqual(s,original)
            for key,value in [('task_failures',0),('blocker','resource failure'),
                              ('source_checkpoint','other'),('alley_readability_recovery_attempted',True)]:
                with self.assertRaises(Halt):r.validate_readability_pause({**s,key:value})

    def test_junction_capture_addition_preserves_inputs_and_keeps_outside_images(self):
        probe=dict(duration=35,steps=[dict(start=4,end=30,keys=['W'])],captures=[5,12,20,34])
        original=copy.deepcopy(probe)
        rows=[dict(time=10.7,mode='foot',player=[6.7,0,17]),
              dict(time=24.9,mode='vehicle',vehicle=[6.7,0,17])]
        changed=r.add_junction_captures(probe,rows)
        self.assertEqual(probe,original)
        self.assertEqual(r.replay_identity(changed),r.replay_identity(probe))
        self.assertEqual(changed['captures'],[5,10.7,12,20,24.9,34])
        with self.assertRaises(Halt):r.add_junction_captures(probe,rows[:1])

    def test_critic_sees_actual_junction_and_both_distant_excursions(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle=Path(temp);c=bundle/'captures';c.mkdir()
            times=[5,10.7,12.9,20,26.85,34]
            rows=[dict(time=t,mode=m,player=[x,0,17],vehicle=[x,0,17]) for t,m,x in
                  [(5,'foot',1),(10.7,'foot',6.7),(12.9,'foot',12.5),
                   (20,'foot',1),(26.85,'vehicle',19.7),(34,'vehicle',4)]]
            for i in range(6):(c/('frame-%03d.png'%i)).touch()
            (c/'scenario.json').write_text(json.dumps({'captures':times}))
            (c/'trace.jsonl').write_text('\n'.join(json.dumps(x) for x in rows))
            chosen,mapping=review_captures({'id':'connected-map-extension'},bundle)
            self.assertEqual([p.name for p in chosen],
                ['frame-001.png','frame-002.png','frame-004.png','frame-005.png'])
            self.assertEqual(mapping['frame-001.png'],10.7)
