#!/usr/bin/env python3
"""Reuse the completed genuine critique after the diagnosed manifest reseal mismatch."""
import json
from resume_three_day_queue import main
from resume_alley_prop_transforms import PropTransforms, SOURCE, CANDIDATE, ROUND as NATIVE_ROUND, ACCEPTED, REPLAY
from qualify_map_extension import MAP_TASK
from loop_controller.core import Halt, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import replay_identity

ROUND='q0075-54c71a15'
MANIFEST_SHA='3b2cf1838abb9c5c68210630ad703b074ccf227c427206abd677d9a2946c7608'
CRITIC_SHA='b83d86d145891a20aaa5582650a3446fe90a1f515a260cd0f9cfa887bafadd68'


def validate_completed_review_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=18,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,alley_prop_transforms_attempted=True,
        blocker='Halt: Evidence manifest changed')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('prop_completed_review_attempted'):
        raise Halt('Expected exact metadata-reseal stop; preserve other evidence failures')
    if replay_identity(old['last_valid_replay'])!=REPLAY:raise Halt('Preserve physical inputs')


class CompletedPropReview(PropTransforms):
    def validate_recovery(self,old):
        validate_completed_review_pause(old)
        bundle=self.store.root/'evidence'/NATIVE_ROUND
        manifest=verify_seal(bundle/'captures',MANIFEST_SHA)
        if manifest.get('candidate')!=CANDIDATE or manifest.get('scope')!=MAP_TASK['id']:
            raise Halt('Current sealed observation identity changed')
        original=json.loads((bundle/'critic-context-stop.json').read_text())
        review=json.loads((bundle/'critic.json').read_text())
        if sha((bundle/'critic.json').read_bytes())!=CRITIC_SHA:raise Halt('Completed critique bytes changed')
        if original.get('bounded_stop')!='context' or not review.get('ok') or review.get('verdict')!='FIX':
            raise Halt('Require the preserved context stop and complete actual critic FIX')
        gate=json.loads((bundle/'scoped-gate.json').read_text())
        checks=gate.get('regressions',{}).get('regressions',[])
        if (gate.get('candidate_commit')!=CANDIDATE or not gate.get('passed') or len(checks)!=10
                or not all(x['gate'].get('passed') for x in checks)):
            raise Halt('Prior complete native qualification changed')

    def recovery_settings(self):
        return dict(prop_completed_review_attempted=True,recovery_route='completed-critic-native-prop-repair',
            recovery_change='Retain complete critic FIX and verified observation bytes; continue local transform/detail edits')

    def complete_prior_review(self,task,ident):
        bundle=self.store.root/'evidence'/NATIVE_ROUND
        expected=MANIFEST_SHA
        verify_seal(bundle/'captures',expected)
        review=json.loads((bundle/'critic.json').read_text())
        if sha((bundle/'critic.json').read_bytes())!=CRITIC_SHA:raise Halt('Completed critique bytes changed')
        self.store.event('completed-lighting-review-reused',prior_round=NATIVE_ROUND,review=review,
            manifest_sha256=expected,all_observation_bytes_verified=True,
            original_context_and_metadata_stops_preserved=True,new_inference_claimed=False)


if __name__=='__main__':raise SystemExit(main(CompletedPropReview))
