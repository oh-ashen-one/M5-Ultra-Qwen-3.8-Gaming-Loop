import copy
import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from loop_controller.prop_clone_checks import inspect_alley_clones
from unittest.mock import patch
import resume_alley_prop_transforms as recovery
from loop_controller.core import Halt
from continue_game_queue import review_evidence_seal


class PropCloneChecks(unittest.TestCase):
    def test_review_reuses_manifest_bytes_and_rejects_changed_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            captures=Path(temp);(captures/'frame.png').write_bytes(b'original evidence')
            first=review_evidence_seal(captures,'candidate','scope')
            manifest=(captures/'manifest.json').read_bytes()
            self.assertEqual(review_evidence_seal(captures,'candidate','scope'),first)
            self.assertEqual((captures/'manifest.json').read_bytes(),manifest)
            with self.assertRaises(Halt):review_evidence_seal(captures,'other','scope')
            (captures/'frame.png').write_bytes(b'changed')
            with self.assertRaises(Halt):review_evidence_seal(captures,'candidate','scope')

    def test_completed_critic_recovery_is_exact_and_one_time(self):
        import resume_prop_completed_review as completed
        s=dict(source_checkpoint=completed.SOURCE,last_playable_checkpoint=completed.ACCEPTED,
            current_round=completed.ROUND,task_index=7,task_failures=18,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=completed.HARD_CAP_EPOCH,
            alley_prop_transforms_attempted=True,blocker='Halt: Evidence manifest changed',last_valid_replay={})
        before=copy.deepcopy(s)
        with patch.object(completed,'replay_identity',return_value=completed.REPLAY):
            completed.validate_completed_review_pause(s);self.assertEqual(s,before)
            for key,value in [('source_checkpoint','other'),('task_failures',0),
                              ('blocker','Evidence bytes changed'),('prop_completed_review_attempted',True)]:
                with self.assertRaises(Halt):completed.validate_completed_review_pause({**s,key:value})

    def test_resume_does_not_reset_prior_failures_or_accept_another_stop(self):
        s=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=18,failure_streak=1,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,
            alley_saved_visuals_attempted=True,blocker=recovery.BLOCKER,last_valid_replay={})
        before=copy.deepcopy(s)
        with patch.object(recovery,'replay_identity',return_value=recovery.REPLAY):
            recovery.validate_prop_pause(s);self.assertEqual(s,before)
            for key,value in [('task_failures',0),('source_checkpoint','other'),
                              ('blocker','runtime fault'),('alley_prop_transforms_attempted',True)]:
                with self.assertRaises(Halt):recovery.validate_prop_pause({**s,key:value})

    def fixture(self):
        def obj(name,size,center,kind='renderer'):
            return dict(name=name,kind=kind,boundsSize=size,boundsCenter=center,
                        up=[-1,0,0],forward=[0,1,0])
        return [obj('Props/alley_props/bollard01',[.24,1.05,.24],[6,.52,19.3]),
                obj('Props/alley_props/dumpster_a/body',[1.25,1.15,2.4],[5.5,.62,8.8]),
                obj('Props/alley_props/dumpster_a/body',[1.25,1.15,2.4],[5.5,.62,8.8],'BoxCollider'),
                obj('WorldCollision/AlleyBollardS',[.24,1.05,.24],[8,.665,8.8]),
                obj('WorldCollision/AlleyBollardN',[.24,1.05,.24],[8,.665,19.65]),
                obj('WorldCollision/AlleyDumpster/body',[1.25,1.15,2.4],[16,.715,9.5]),
                obj('WorldCollision/AlleyDumpster/body',[1.25,1.15,2.4],[16,.715,9.5],'BoxCollider')]

    def test_native_sized_upright_grounded_copies_pass(self):
        rows=self.fixture();before=copy.deepcopy(rows)
        self.assertTrue(inspect_alley_clones(rows)['passed'])
        self.assertEqual(rows,before)

    def test_tiny_rotated_import_cannot_pass(self):
        rows=self.fixture()
        for row in rows:
            if row['name'].startswith('WorldCollision/'):
                row['boundsSize']=[x/100 for x in row['boundsSize']]
                row['up']=[0,1,0];row['forward']=[0,0,1]
        result=inspect_alley_clones(rows)
        self.assertFalse(result['passed'])
        self.assertTrue(any(x.endswith(':world-size') for x in result['failure']))
        self.assertTrue(any(x.endswith(':world-orientation') for x in result['failure']))

    def test_missing_collider_and_displaced_floor_are_detected(self):
        rows=self.fixture();rows.pop()
        rows[-1]['boundsCenter'][1]+=1
        result=inspect_alley_clones(rows)
        self.assertFalse(result['passed'])
        self.assertIn('WorldCollision/AlleyDumpster:missing-original-components',result['failure'])
        self.assertIn('WorldCollision/AlleyDumpster:floor-placement',result['failure'])
