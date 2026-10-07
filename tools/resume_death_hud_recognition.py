#!/usr/bin/env python3
"""Preserve the native HUD false-negative and continue the unchanged death cases."""
import json
from resume_player_death_green import PlayerDeathGreen
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.player_death_checks import death_probe, inspect_player_death

SOURCE='d4d13937c63b9e056d3c40bf72fbf02e63eb3990'
PRIOR='q0152-4bb1d76f'
HASHES={
    'gate.json':'a59db8132cb60e39f2bb595b153127b3cb2cc99fad7f53c54c87a26df7da1b44',
    'player-death-gate.json':'2bf2961762b5a42787cd08368d38c21053183a9d9de7171efd3a50d9171409bc',
    'captures/scenario.json':'55b7d88820d7e027fc97540504b67e266ff1a27d2e0e232253d552841e279b9d',
    'captures/trace.jsonl':'5b05d23c2feaa48e9e9fccef5f0ec8402a1c1973151b704c2c1d996d1f127e5e',
    'captures/death-injection.json':'cc1df732a5962841ea64873012882eb3d51cf96dc034a5f5eeab7106d79cbb92',
    'captures/frame-001.png':'0b8d5b29cb9b3fea3c09156c00b40d2f6b36a061dca3295484c63b78dee6d4a7',
}


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        player_death_green_attempted=True,author_completion_claimed=False,
        blocker='Halt: Local death integration needs measured follow-up: courier-pickup: ["death-failure-and-reset-not-visible"]')
    result=old.get('player_death_green_outcome',{})
    cases=result.get('cases',[])
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('death_hud_recognition_recovered')
            or result.get('candidate')!=SOURCE or len(cases)!=1
            or cases[0].get('case')!='courier-pickup' or not cases[0].get('setup_passed')
            or cases[0].get('failure')!=['death-failure-and-reset-not-visible']
            or result.get('positive')!='pending' or result.get('regressions')!='pending'):
        raise Halt('Require the exact inspected HUD wording false-negative; preserve other failures')


class HudRecognitionRecovery(PlayerDeathGreen):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.bundle=self.store.root/'evidence'/(PRIOR+'-courier-pickup')
        for name,digest in HASHES.items():
            if sha((self.bundle/name).read_bytes())!=digest:raise Halt('Original native evidence changed')
        original=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        if read_json(self.bundle/'captures/scenario.json')!=death_probe(original,'courier-pickup'):
            raise Halt('Keep the exact ordinary-input prefix and declared death intervention')
        gate=read_json(self.bundle/'gate.json')
        if not gate.get('passed') or gate.get('candidate_commit')!=SOURCE:
            raise Halt('Require actual same-source native build/playthrough proof')
        self.source=SOURCE
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def prior_cases(self,ident):
        rows=[json.loads(line) for line in (self.bundle/'captures/trace.jsonl').read_text().splitlines()]
        result=inspect_player_death(rows,read_json(self.bundle/'captures/death-injection.json'),'courier-pickup')
        if not result['passed']:raise Halt('Corrected wording recognition must not hide a gameplay failure')
        result.update(candidate=self.source,build_id=read_json(self.bundle/'gate.json')['build_id'],
            evidence=self.bundle.name,reused_native_evidence=True,
            acceptance_revision='explicit-r-reset-retry-restart',original_gate_sha256=HASHES['player-death-gate.json'])
        atomic(self.store.root/'evidence'/(ident+'-hud-recognition-recheck.json'),result)
        return [result]

    def recovery_settings(self):
        return dict(death_hud_recognition_recovered=True,recovery_route='semantic-hud-wording-correction',
            recovery_change='Actual pixels and all30dead-window samples show immediate HEALTH DEPLETED / '
            'PRESS R TO RESTART. Add restart recognition and require explicit R; movement, firing, '
            'progression, timing, reset and input cases are unchanged. Preserve the original red gate '
            'and hash-sealed evidence; record a separate re-evaluation, then run the five remaining '
            'death cases, healthy95-second route and ten regressions on unchanged local source.')


if __name__=='__main__':raise SystemExit(main(HudRecognitionRecovery))
