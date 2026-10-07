#!/usr/bin/env python3
"""Verify the local install/walk trial without claiming complete death integration."""
import json
from resume_camera_native_only import CameraNativeOnly, ACCEPTED
from resume_three_day_queue import main
from qualify_moving_encounter import checked
from loop_controller.core import Halt, atomic, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.player_death_checks import death_probe, inspect_player_death, CASES
from qwen_capacity import POLICY

BOOT = 'Assets/Game/Bootstrap.cs'
TASK = dict(id='capacity-trial-native', phase='mission', visual_facing=False,
    outcome='Current local source compiles, preserves the healthy route and stops dead walking with ordinary reset')


def validate_boundary(old, authored):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
        failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
        capacity_trial_author_attempted=True, shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Capacity trial saved local install/walk source; inspect capacity evidence and unload idle model before native verification')
    source = old.get('capacity_trial_source_outcome', {})
    if (any(old.get(k) != v for k,v in expected.items()) or old.get('capacity_trial_native_attempted')
            or not source.get('local_authored') or source.get('candidate') != old.get('source_checkpoint')
            or source.get('round') != old.get('current_round') or source.get('changed_files') != [BOOT]
            or source.get('complete_death_integration') is not False
            or not authored.get('ok') or authored.get('changed_files') != [BOOT]
            or authored.get('capacity_policy') != POLICY
            or old.get('active_model_settings', {}).get('reasoning_effort') != 'xhigh'):
        raise Halt('Require the completed local install/walk trial and unchanged acceptance history')
    return source['candidate']


def walking_scope(rows, injection, red):
    at = CASES['courier-pickup'][0]
    dead = [r for r in rows if at+.2 <= r.get('time',0) <= at+3.4 and r.get('restarts') == 0]
    relevant = {'missing-zero-health-window', 'health-revived-before-R-reset',
        'missing-player-position', 'player-moves-under-dead-input',
        'ordinary-R-reset-not-established', 'whole-reset-state-not-restored',
        'walking-not-restored-after-reset'}
    failures = sorted(relevant.intersection(red['failure']))
    if not red.get('setup_passed'): failures.append('invalid-death-setup')
    if injection.get('mode') != 'foot' or not dead or any(r.get('mode') != 'foot' for r in dead):
        failures.append('foot-only-dead-window-not-established')
    return dict(passed=not failures, failure=failures, zero_health_samples=len(dead),
        complete_death_integration=False, native_natural_damage_death_proven=False)


def validate_admission_boundary(old, authored):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round='q0146-05eff4e0',
        source_checkpoint='dbfc89901b813ced826e976eb79c3370c95471b2',last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,capacity_trial_native_attempted=True,
        shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Capacity wait: shared queue did not admit the engine within300seconds')
    source=old.get('capacity_trial_source_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('capacity_trial_native_outcome')
            or old.get('capacity_native_admission_recovery_attempted')
            or source.get('candidate')!=old['source_checkpoint'] or source.get('round')!='q0145-09d3f671'
            or source.get('changed_files')!=[BOOT] or not source.get('local_authored')
            or not authored.get('ok') or authored.get('changed_files')!=[BOOT]
            or authored.get('capacity_policy')!=POLICY
            or old.get('active_model_settings',{}).get('reasoning_effort')!='xhigh'):
        raise Halt('Require the exact no-engine admission timeout and preserved local source')
    return old['source_checkpoint']


class CapacityNative(CameraNativeOnly):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.c['native_admission_recheck_seconds']=1

    def validate_recovery(self, old):
        source = old.get('capacity_trial_source_outcome', {})
        authored = read_json(self.store.root/'evidence'/(source.get('round','missing')+'-capacity-author.json'))
        self.native_admission_recovery=old.get('capacity_trial_native_attempted',False)
        self.source = (validate_admission_boundary if self.native_admission_recovery else validate_boundary)(old, authored)
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(capacity_trial_native_attempted=True,
            capacity_native_admission_recovery_attempted=self.native_admission_recovery,
            recovery_route='capacity-trial-native-inference-unloaded',
            recovery_change='Keep the exact95-second healthy route and courier-pickup negative unchanged. '
            'Use one-second admission checks within the same300-second bound; preserve old timeout. '
            'Report scoped walking/reset proof separately from remaining fire/objective/HUD failures; no promotion.')

    def work(self):
        ident = self.begin(TASK, 'native-capacity-trial-source')
        original = read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        outcome = dict(candidate=self.source, model_unloaded=True, complete_death_integration=False,
            final_game_accepted=False, positive='pending', walking='pending')
        def save():
            atomic(self.store.root/'evidence'/(ident+'-capacity-native.json'), outcome)
            self.store.set(capacity_trial_native_outcome=outcome);self.store.report()
        positive = self.store.root/'evidence'/(ident+'-positive')
        raw = self.engines.unity(self.project, positive, original, self.source)
        outcome['positive'] = checked(positive,raw,'positive') if raw.get('passed') else raw;save()
        if not outcome['positive'].get('passed'):
            raise Halt('Capacity trial source failed native compile or healthy route; preserve actual evidence')
        bundle = self.store.root/'evidence'/(ident+'-courier-pickup')
        raw = self.engines.unity(self.project, bundle, death_probe(original,'courier-pickup'), self.source)
        if not raw.get('passed'):
            outcome['negative_native_failure']=raw;save()
            raise Halt('Capacity trial negative native prerequisite failed; no scoped success claimed')
        captures = bundle/'captures'
        rows = [json.loads(x) for x in (captures/'trace.jsonl').read_text().splitlines()]
        injection = read_json(captures/'death-injection.json')
        red = inspect_player_death(rows,injection,'courier-pickup')
        red.update(candidate=self.source,build_id=raw['build_id'],evidence=bundle.name)
        atomic(bundle/'player-death-gate.json',red)
        outcome['death_contract']=red;outcome['walking']=walking_scope(rows,injection,red);save()
        if not outcome['walking']['passed']:
            raise Halt('Local install/walk trial failed scoped native death/reset verification')
        raise Halt('Local install/walk source passes healthy route and dead-walking/reset verification; full death integration remains pending')


if __name__=='__main__':raise SystemExit(main(CapacityNative))
