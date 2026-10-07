import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from continue_game_queue import validate_scoped_review, verified_time_citations
from loop_controller.core import Halt
import resume_timed_map_review as recovery
from qualify_map_extension import promote_qualified_extension, MAP_TASK


class TimedReviewTests(unittest.TestCase):
    def test_seconds_suffixes_resolve_real_frames_but_not_coordinates_or_ambiguous_times(self):
        times={'frame-008.png':27.3234,'frame-014.png':38.8,'frame-016.png':45.5,'frame-018.png':50.6}
        summary='HUD28m at27.3s, frames at 38.8s/45.5s, reset at 50.6 seconds.'
        # Require a token boundary: prose glued to a number is not a citation.
        self.assertNotIn('frame-008.png',verified_time_citations(summary,times))
        summary=summary.replace('at27.3s','at 27.3s')
        self.assertEqual(verified_time_citations(summary,times),times)
        self.assertFalse(verified_time_citations('Coordinates (50,0.87,18)',times))
        self.assertFalse(verified_time_citations('at 38.8s',{'a':38.81,'b':38.82}))

    def test_ground_recovery_pins_complete_response_and_keeps_summary_unchanged(self):
        import resume_ground_cited_review as ground
        import json
        from loop_controller.core import sha
        times={'a.png':27.3234,'b.png':38.8}
        fields=dict(verdict='PASS',summary='Active at 27.3s, supported sidewalk at 38.8s.',fixes=[])
        raw=json.dumps({'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[
            {'function':{'name':'submit_review','arguments':json.dumps(fields)}}]}}]}).encode()
        with patch.object(ground,'RESPONSE_SHA',sha(raw)):
            result=ground.recover_review(raw,times)
            self.assertEqual(result['summary'],fields['summary'])
            with self.assertRaises(Halt):ground.recover_review(raw,{**times,'missing.png':45.5})
        with self.assertRaises(Halt):ground.recover_review(raw,times)

    def test_actual_rounded_times_are_valid_without_rewriting_independent_verdict(self):
        times={'frame-001.png':10.817,'frame-002.png':12.89791,
               'frame-006.png':26.84647,'frame-010.png':34.99647}
        fields=dict(verdict='PASS',summary='Frames at t=10.8/12.9, then t=26.8 and t=35.0 prove the route.',fixes=['Keep polishing.'])
        before=copy.deepcopy(fields);result=validate_scoped_review(fields,list(times),times)
        self.assertEqual(fields,before)
        self.assertEqual(result['summary'],fields['summary'])
        self.assertEqual(result['fixes'],fields['fixes'])
        self.assertEqual(result['verified_capture_time_citations'],times)

    def test_unmatched_ambiguous_or_uncited_times_cannot_validate_a_review(self):
        for summary,times in [('The budget is150seconds.',{'frame-001.png':150}),
                              ('At t=9.2.',{'frame-001.png':10.817}),
                              ('At t=10.8.',{'a.png':10.81,'b.png':10.82})]:
            self.assertFalse(verified_time_citations(summary,times))
            with self.assertRaises(ValueError):validate_scoped_review(dict(verdict='PASS',summary=summary,fixes=[]),list(times),times)

    def test_recovery_rejects_changed_response_and_preserves_exact_failure_state(self):
        with self.assertRaises(Halt):recovery.recover_review(b'changed',{})
        s=dict(source_checkpoint=recovery.SOURCE,last_playable_checkpoint=recovery.ACCEPTED,
            current_round=recovery.ROUND,task_index=7,task_failures=19,failure_streak=2,
            diagnosis_used=True,overall_deadline_epoch=recovery.HARD_CAP_EPOCH,
            prop_completed_review_attempted=True,blocker=recovery.BLOCKER,last_valid_replay={})
        before=copy.deepcopy(s)
        with patch.object(recovery,'replay_identity',return_value=recovery.REPLAY):
            recovery.validate_timed_review_pause(s);self.assertEqual(s,before)
            for key,value in [('task_failures',0),('source_checkpoint','other'),('timed_map_review_recovered',True)]:
                with self.assertRaises(Halt):recovery.validate_timed_review_pause({**s,key:value})

    def test_promotion_rejects_missing_native_or_critic_proof_before_any_mutation(self):
        for gate,review in [({'passed':True},{'ok':True,'verdict':'PASS'}),
                            ({'passed':False},{'ok':True,'verdict':'PASS'}),
                            ({'passed':True},{'ok':True,'verdict':'FIX'})]:
            with self.assertRaises(Halt):promote_qualified_extension(None,MAP_TASK,None,gate,review)
