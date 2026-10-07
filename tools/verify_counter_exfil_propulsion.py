#!/usr/bin/env python3
"""Qualify current-source old route, free escape and physical incident success."""
import json
from resume_camera_native_only import CameraNativeOnly
from probe_counter_exfil import activation_probe,ACCEPTED,TASK
from probe_counter_exfil_driving import maneuver
from qualify_moving_encounter import checked
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.counter_exfil_checks import inspect_activation_escape
from loop_controller.counter_exfil_success_checks import inspect_success

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_propulsion_review_attempted=True,
        blocker='Halt: Reviewed local Counter-Exfil propulsion saved; unload idle inference and qualify actual incident')
    result=old.get('counter_exfil_propulsion_review_result',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_propulsion_native_attempted')
            or not result.get('ok') or not result.get('local_authored')
            or result.get('candidate')!=old.get('source_checkpoint')
            or old.get('counter_exfil_source_outcome',{}).get('candidate')!=result.get('candidate')):
        raise Halt('Require completed locally reviewed propulsion and unchanged accepted history')

def corrected_success(original):
    scenario=dict(original,id='counter-exfil-finite-force-pin-shoot-foot-exit',duration=124,
        captures=[.6,98.5,101.8,105.5,106.4,107.6,111.9,114.6,119,123])
    scenario['steps']=[dict(s) for s in original['steps'] if s['start']<100]
    sequence=[(100.2,100.3,['E']),(100.4,101.5,['S']),(101.6,104.3,['D']),
        (104.4,105.1,['W']),(105.2,105.4,['A']),
        (107.8,108.9,['S']),(109,111.92,['A']),(112.1,113.05,['W']),
        (113.3,114.5,['A']),(118,118.1,['R']),(120,121,['W'])]
    sequence += [(105.8+.2*i,105.88+.2*i,['Mouse0']) for i in range(9)]
    scenario['steps'] += [dict(start=a,end=b,keys=k) for a,b,k in sequence]
    scenario['steps'].sort(key=lambda s:s['start'])
    return scenario

def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

class VerifyCounterPropulsion(CameraNativeOnly):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_propulsion_native_attempted=True,recovery_route='native-finite-propulsion-qualification',
            recovery_change='Inference unloaded. Require the complete original healthy gate and real free escape/reset, then corrected ordinary movement and actual shots with independent continuous-contact/obstruction/kill/foot-crossing proof. No source edit or acceptance promotion; contact/death/regressions and actual pixels remain required.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-finite-propulsion')
        original=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        outcome=dict(candidate=self.source,old_healthy='pending',activation_escape='pending',success='pending',
            contact_negative='pending',death_negatives='pending',regressions='pending',visual_review='pending',
            full_incident_accepted=False,final_game_accepted=False)
        path=self.store.root/'evidence'/(ident+'-propulsion-native.json')
        def save():
            atomic(path,outcome);self.store.set(counter_exfil_propulsion_native_outcome=outcome);self.store.report()
        save()
        for name,scenario in [('old-healthy',original),('activation-escape',activation_probe(original)),
                ('success',corrected_success(maneuver(activation_probe(original))))]:
            self.store.set(stage='native-counter-exfil-'+name);self.store.report()
            bundle=self.store.root/'evidence'/(ident+'-'+name)
            raw=self.engines.unity(self.project,bundle,scenario,self.source)
            gate=raw
            if raw.get('passed'):
                if name=='old-healthy':gate=checked(bundle,raw,'positive')
                elif name=='activation-escape':gate=inspect_activation_escape(lines(bundle/'captures/trace.jsonl'))
                else:gate=inspect_success(lines(bundle/'captures/trace.jsonl'),
                    lines(bundle/'captures/counter-exfil-contacts.jsonl'),lines(bundle/'captures/aim-shots.jsonl'))
            result=dict(candidate=self.source,native=raw,gate=gate,evidence=bundle.name,build_id=raw.get('build_id'))
            atomic(bundle/'counter-propulsion-gate.json',result);outcome[name.replace('-','_')]=result;save()
            frames=sorted((bundle/'captures').glob('frame-*.png'))
            if frames:queue_milestone(self.store,'native-milestone',TASK,bundle,
                {**raw,'passed':bool(raw.get('passed') and gate.get('passed')),'counter_scope':name},frames,
                {f'frame-{i:03d}.png':t for i,t in enumerate(scenario['captures'])})
            if not raw.get('passed') or not gate.get('passed'):
                raise Halt('Finite-propulsion native qualification failed '+name+': '+json.dumps(gate.get('failure')))
        raise Halt('Current Counter-Exfil old route, free escape and physical success pass; contact/death/regressions and pixels remain required')

if __name__=='__main__':raise SystemExit(main(VerifyCounterPropulsion))
