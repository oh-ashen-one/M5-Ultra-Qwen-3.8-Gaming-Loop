#!/usr/bin/env python3
"""Preserve a cosmetic FIX without blocking the independently scoped next topology task."""
import json
from resume_saved_door import SavedDoor, SECOND_TASK, SOURCE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH

ROUND='q0078-0edc60bc'
GATE_SHA='8403aef78204bb092fe1a7aa882194f2bfebbbc004d82bca420dece1cbedd538'
CRITIC_SHA='1eac132c456b03a0277a6f97542dfa352cd18f9e5deb020f011dfc1ecb13a8f8'
MANIFEST_SHA='e97e68936700a9409049b69037bc408750fc7a3035a4688632027faa1c7d056b'
BLOCKER='Halt: Saved door did not qualify; accepted connector and local correction preserved'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=20,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,
        saved_door_recovery_attempted=True,second_street_attempts=0)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('door_fix_deferred_for_street'):
        raise Halt('Expected exact preserved door visual FIX before second-street work')


def validate_evidence(bundle):
    for name,expected in [('scoped-gate.json',GATE_SHA),('critic.json',CRITIC_SHA)]:
        if sha((bundle/name).read_bytes())!=expected:raise Halt('Original door evidence changed: '+name)
    manifest=verify_seal(bundle/'captures',MANIFEST_SHA)
    gate=json.loads((bundle/'scoped-gate.json').read_text())
    review=json.loads((bundle/'critic.json').read_text())
    checks=gate.get('regressions',{}).get('regressions',[])
    required={'walk','world','motor','courier','failure-retry','combat-foot','combat-wall','combat-driving','aim-miss','aim-near-cover'}
    if (not gate.get('passed') or gate.get('candidate_commit')!=SOURCE
            or manifest.get('candidate')!=SOURCE or manifest.get('scope')!='connected-map-extension'
            or not gate.get('scoped_facts',{}).get('door_layer_order',{}).get('passed')
            or len(checks)!=10 or {x['test'] for x in checks}!=required
            or not all(x['gate'].get('passed') and x['gate'].get('candidate_commit')==SOURCE for x in checks)
            or not review.get('ok') or review.get('verdict')!='FIX'):
        raise Halt('Require real native passes and an unchanged independent visual FIX, never a promoted door verdict')
    return review


class SecondStreet(SavedDoor):
    def validate_recovery(self,old):
        validate_pause(old)
        validate_evidence(self.store.root/'evidence'/ROUND)
        self.accepted_probe()

    def recovery_settings(self):
        return dict(door_fix_deferred_for_street=True,saved_door_accepted=False,
            recovery_route='next-topology-with-preserved-visual-fix',
            recovery_change='Keep the unaccepted door source and its visual FIX; continue independent second-street scope')

    def work(self):
        review=validate_evidence(self.store.root/'evidence'/ROUND)
        finding=dict(round=ROUND,candidate=SOURCE,scope='Door contrast and depth readability',
            verdict='FIX',summary=review['summary'],fixes=review['fixes'],
            native_regressions_passed=True,accepted=False,
            disposition='Deferred presentation work; no change to original critic verdict or accepted checkpoint')
        self.store.set(saved_door_probe=self.accepted_probe(),deferred_visual_findings=[finding],
            task_design=SECOND_TASK['instructions'],feedback={
                'current_scope':'Build the second connected street. Do not spend this topology role on door-material polish.',
                'deferred_presentation_finding':finding,
                'evidence_identity_note':'frame-001.png is an actual native junction capture. The separate target is AI-generated; the original critic misidentified that one image. Its FIX remains preserved.'})
        self.store.event('door-visual-fix-preserved-next-scope',**finding,
            last_playable_checkpoint_unchanged=ACCEPTED,original_counters_preserved=True)
        self.store.report()
        return self.advance_second_street()


if __name__=='__main__':raise SystemExit(main(SecondStreet))
