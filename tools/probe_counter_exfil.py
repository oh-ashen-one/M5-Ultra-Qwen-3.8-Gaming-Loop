#!/usr/bin/env python3
"""Record the old healthy route and first real Counter-Exfil activation/escape probe."""
import json
from resume_camera_native_only import CameraNativeOnly
from resolve_death_pixel_review import SOURCE as ACCEPTED
from implement_counter_exfil import TASK
from resume_three_day_queue import main
from qualify_moving_encounter import checked
from loop_controller.core import Halt,atomic,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.counter_exfil_checks import inspect_activation_escape

def activation_probe(original):
    scenario=dict(original)
    scenario.update(id='counter-exfil-ordinary-retrieval-start-escape-reset',fixture='counter-exfil',
        duration=142,captures=[.6,76.8,83.9,85.5,110,130,140])
    scenario['steps']=[dict(s) for s in original['steps'] if s['start']<77]
    # Fixed normal-input proposal derived from the measured handoff. No state
    # injections: actual trace decides whether entry/start/escape were reached.
    scenario['steps'] += [dict(start=a,end=b,keys=keys) for a,b,keys in (
        (77.4,77.5,['F']), (78,79.1,['W']), (79.2,84.4,['D']),
        (84.6,84.7,['E']), (85.2,85.3,['F']), (136,136.1,['R']))]
    return scenario

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_source_attempted=True,
        blocker='Halt: Local Counter-Exfil source saved; unload idle inference and qualify actual inputs and negatives')
    result=old.get('counter_exfil_source_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_probe_attempted')
            or not result.get('ok') or not result.get('local_authored')
            or result.get('candidate')!=old.get('source_checkpoint') or not result.get('changed_files')):
        raise Halt('Require actual complete local incident source and unchanged accepted history')

class ProbeCounterExfil(CameraNativeOnly):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_probe_attempted=True,recovery_route='first-counter-exfil-real-input-probe',
            recovery_change='Inference unloaded. Recheck original95-second healthy route, then normal walking/E/F and unresolved escape/reset. Observe state/real contacts; this initial probe cannot establish full incident success or promote source.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-first-probe')
        original=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        outcome=dict(candidate=self.source,old_healthy='pending',activation_escape='pending',
            full_incident_success=False,regressions='pending',final_game_accepted=False)
        path=self.store.root/'evidence'/(ident+'-counter-exfil-probe.json')
        def save():
            atomic(path,outcome);self.store.set(counter_exfil_probe_outcome=outcome);self.store.report()
        save()
        bundle=self.store.root/'evidence'/(ident+'-old-healthy')
        raw=self.engines.unity(self.project,bundle,original,self.source)
        outcome['old_healthy']=checked(bundle,raw,'positive') if raw.get('passed') else raw;save()
        if not outcome['old_healthy'].get('passed'):
            raise Halt('Counter-Exfil source failed the unchanged healthy route prerequisite')
        scenario=activation_probe(original);bundle=self.store.root/'evidence'/(ident+'-activation-escape')
        raw=self.engines.unity(self.project,bundle,scenario,self.source)
        semantic=inspect_activation_escape([json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]) if raw.get('passed') else dict(passed=False,failure=['native-prerequisite'])
        semantic.update(candidate=self.source,build_id=raw.get('build_id'),evidence=bundle.name)
        atomic(bundle/'counter-exfil-probe-gate.json',semantic)
        outcome['activation_escape']=dict(native=raw,evidence=bundle.name,semantic=semantic);save()
        frames=sorted((bundle/'captures').glob('frame-*.png'))
        if frames:queue_milestone(self.store,'native-milestone',TASK,bundle,{**raw,'passed':raw.get('passed') and semantic.get('passed'),'counter_exfil_scope':semantic},frames,
            {f'frame-{i:03d}.png':t for i,t in enumerate(scenario['captures'])})
        raise Halt('First Counter-Exfil native recordings preserved; inspect actual activation/escape/reset before success route')

if __name__=='__main__':raise SystemExit(main(ProbeCounterExfil))
