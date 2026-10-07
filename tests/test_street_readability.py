import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import resume_street_readability as recovery
import resume_street_camera_micro as micro
from loop_controller.core import Halt


class StreetReadabilityTests(unittest.TestCase):
    def test_exact_pause_preserves_source_failure_counts_and_deadline(self):
        state=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=recovery.HARD_CAP_EPOCH,second_street_attempts=4,saved_door_accepted=False,
            blocker='Halt: Second-street replay supplied no complete bounded tool submission')
        before=copy.deepcopy(state);recovery.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('source_checkpoint','other'),('task_failures',0),('second_street_attempts',0),
                          ('street_readability_recovery_attempted',True),('blocker','resource failure')]:
            with self.subTest(key=key),self.assertRaises(Halt):recovery.validate_pause({**state,key:value})

    def test_reuse_requires_complete_same_source_suite_and_preserves_fix(self):
        gate=dict(passed=True,candidate_commit=recovery.BASE,scene_inventory={'passed':True},
            regressions={'regressions':[dict(test=n,gate=dict(passed=True,candidate_commit=recovery.BASE)) for n in recovery.REGRESSIONS]})
        manifest=dict(candidate=recovery.BASE,scope=recovery.SECOND_TASK['id'])
        review=dict(ok=True,verdict='FIX');before=copy.deepcopy(review)
        recovery.require_sealed_native(gate,manifest,review);self.assertEqual(review,before)
        for mutate in [lambda g:g.update(scene_inventory={'passed':False}),
                       lambda g:g['regressions']['regressions'].pop(),
                       lambda g:g['regressions']['regressions'][0]['gate'].update(candidate_commit='other'),
                       lambda g:g['regressions']['regressions'][0]['gate'].update(passed=False)]:
            altered=copy.deepcopy(gate);mutate(altered)
            with self.assertRaises(Halt):recovery.require_sealed_native(altered,manifest,review)
        with self.assertRaises(Halt):recovery.require_sealed_native(gate,manifest,{'ok':True,'verdict':'PASS'})

    def test_camera_span_rejects_fixture_coupling_and_collider_disabling(self):
        recovery.validate_camera_span('pos.y = Mathf.Max(pos.y, floorY);')
        for text in ['LoopSignals.Player','CameraClearanceWall','c.enabled = false','Destroy(c)','public class Follow']:
            with self.subTest(text=text),self.assertRaises(ValueError):recovery.validate_camera_span(text)

    def test_micro_recovery_cannot_skip_or_reset_the_camera_output_stop(self):
        state=dict(source_checkpoint=micro.SOURCE,last_playable_checkpoint=micro.ACCEPTED,
            current_round=micro.ROUND,task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=micro.HARD_CAP_EPOCH,second_street_attempts=4,
            street_readability_recovery_attempted=True,saved_door_accepted=False,
            blocker='Halt: Focused local camera role saved no correction; preserve fence and evidence')
        before=copy.deepcopy(state);micro.validate_pause(state);self.assertEqual(state,before)
        for key,value in [('source_checkpoint','other'),('task_failures',0),('current_round',recovery.ROUND),
                          ('street_camera_micro_attempted',True),('street_readability_recovery_attempted',False)]:
            with self.subTest(key=key),self.assertRaises(Halt):micro.validate_pause({**state,key:value})


if __name__=='__main__':unittest.main()
