#!/usr/bin/env python3
"""Recover a complete critic PASS whose genuine time citations failed a filename-only rule."""
import json
from continue_game_queue import ContinuousRunner, review_captures, validate_scoped_review
from resume_three_day_queue import ThreeDayRunner, main
from resume_map_traversal import ACCEPTED, BLOCKER
from resume_alley_presentation import REPLAY
from qualify_map_extension import MAP_TASK, promote_qualified_extension
from loop_controller.core import Halt, atomic, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git

SOURCE='3466851c2a2b032bd337485c8e44e09c37e2c244'
CANDIDATE='2ab467692d10a715500bf89e0d8982694fa5eb80'
ROUND='q0076-3b01e800'
RESPONSE_SHA='16905159f31b1dad4297c0ef63530186633b18862ef65e8828a50c325095e75a'
GATE_SHA='5f6a2bf9f9c9785155a951e0c5d02023ea97ed19929bd02c2b571340949cfd81'
MANIFEST_SHA='6238bf4d527a44fc909320b863f497d261f5342359e7ddc61b57a454bc772c76'
NEXT_CONNECTED=(
    'The first connected alley is now independently accepted: original X-1..6,Z-2..30 core plus '
    'X6..22,Z8..20 alley, with actual foot/vehicle out-and-back, all regressions and scoped critic PASS. '
    'Advance beyond that milestone, do not repeat its original build. First preserve original door-layer '
    'offset: ServiceDoor panel should be0.07m outward toward decreasingZ from ServiceDoorSurround, '
    'whose center isZ19.92. Their current same-depth placement lets the solid stone backing hide the wood. '
    'Then prioritize a second connected street, toward60m along one axis and20m across, using existing '
    'original meshes and real continuous rendered support/collisions. Existing win0_0_* meshes provide '
    'one original window assembly; preserve component-relative positions/world transforms when reusing '
    'it for limited facade detail. Avoid rebuilding the accepted core or introducing new asset volume. '
    'After connected-space proof, add a second meaningful objective beyond the original corridor and '
    'extend actual travel/objectives/pursuit toward8-12minutes, never waiting/idle padding. Preserve '
    'all accepted regressions and finish by the fixed original project cap. A scoped connector PASS '
    'is not final Chicago art, whole-map size or ten-minute acceptance. Save one small local edit at a time.')


def recover_review(raw,capture_times):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original complete critic response changed')
    c=json.loads(raw)['choices'][0];calls=c['message'].get('tool_calls',[])
    if c.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='submit_review':
        raise Halt('Expected one complete actual critic submission')
    fields=json.loads(calls[0]['function']['arguments'])
    review=validate_scoped_review(fields,list(capture_times),capture_times)
    if review.get('verdict')!='PASS' or set(review.get('verified_capture_time_citations',{}))!=set(capture_times):
        raise Halt('Require original PASS and unambiguous citations for every supplied native frame')
    if any(review[k]!=fields[k] for k in ('summary','fixes','verdict')):
        raise Halt('Never author or rewrite the independent verdict')
    return review


def validate_timed_review_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=19,failure_streak=2,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,prop_completed_review_attempted=True,blocker=BLOCKER)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('timed_map_review_recovered'):
        raise Halt('Expected exact preserved complete-review citation rejection')
    if replay_identity(old['last_valid_replay'])!=REPLAY:raise Halt('Preserve the proven physical replay')


class TimedMapReview(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_timed_review_pause(old)
        bundle=self.store.root/'evidence'/ROUND
        if sha((bundle/'scoped-gate.json').read_bytes())!=GATE_SHA:raise Halt('Qualified native gate changed')
        verify_seal(bundle/'captures',MANIFEST_SHA)
        if json.loads((bundle/'critic.json').read_text()).get('bounded_stop')!='context':
            raise Halt('Preserve the original retry-context stop')
        _,times=review_captures(MAP_TASK,bundle)
        recover_review((self.store.root/'private/sessions'/(ROUND+'-critic')/'response-000.json').read_bytes(),times)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Preserve accepted fallback before restoring qualified source')

    def recovery_settings(self):
        return dict(timed_map_review_recovered=True,recovery_route='complete-critic-time-citation-recovery',
            recovery_change='Validate actual cited times; preserve original PASS and caveats, then continue next connected space')

    def work(self):
        self.machine.guard()
        bundle=self.store.root/'evidence'/ROUND
        _,times=review_captures(MAP_TASK,bundle)
        review=recover_review((self.store.root/'private/sessions'/(ROUND+'-critic')/'response-000.json').read_bytes(),times)
        archive=bundle/'critic-context-stop-after-time-citation.json'
        if archive.exists():raise Halt('Original citation/context failure already archived')
        archive.write_bytes((bundle/'critic.json').read_bytes())
        atomic(bundle/'critic.json',review)
        self.store.event('completed-critic-time-citations-validated',response_sha256=RESPONSE_SHA,
            original_verdict_unchanged=True,original_summary_unchanged=True,original_fixes_unchanged=True,
            verified_capture_times=review['verified_capture_time_citations'],new_inference_claimed=False)
        git(self.repo,'restore','--source='+CANDIDATE,'--','game')
        saved=self.checkpoint_source('Restore natively qualified map after complete critic citation recovery')
        self.store.set(source_checkpoint=saved)
        gate=json.loads((bundle/'scoped-gate.json').read_text())
        record=promote_qualified_extension(self,MAP_TASK,bundle,gate,review)
        self.store.set(task_design=NEXT_CONNECTED,recovery_route='accepted',
            feedback={'accepted_connector':record,'next_required_milestone':NEXT_CONNECTED,
                      'cloud_visual_notes':'Door layer order is measured; walls/ground still sparse. Preserve actual game controls and mission anchors.'})
        self.store.report()
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(TimedMapReview))
