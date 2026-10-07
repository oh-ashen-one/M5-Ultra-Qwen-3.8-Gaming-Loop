#!/usr/bin/env python3
"""Finish source-matched contact/death negatives and unchanged regressions."""
from resume_camera_native_only import CameraNativeOnly
from probe_counter_exfil import activation_probe,ACCEPTED,TASK
from probe_counter_exfil_driving import maneuver
from verify_counter_exfil_propulsion import lines
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.counter_exfil_success_checks import inspect_success
from loop_controller.counter_exfil_contact_checks import inspect_contact_release
from loop_controller import counter_exfil_death_checks as counter_death
from loop_controller import player_death_checks as old_death
from loop_controller.continuous_tasks import TASKS

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_propulsion_native_attempted=True,
        blocker='Halt: Current Counter-Exfil old route, free escape and physical success pass; contact/death/regressions and pixels remain required')
    proof=old.get('counter_exfil_propulsion_native_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_negatives_attempted')
            or proof.get('candidate')!=old.get('source_checkpoint')):
        raise Halt('Require completed source-matched first native qualification and unchanged history')
    for name in ('old_healthy','activation_escape','success'):
        result=proof.get(name,{})
        if (not result.get('native',{}).get('passed') or not result.get('gate',{}).get('passed')
                or result.get('candidate')!=proof['candidate'] or not result.get('build_id') or not result.get('evidence')):
            raise Halt('Require actual native and semantic success for '+name)

class QualifyCounterNegatives(CameraNativeOnly):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint'];self.prior=old['counter_exfil_propulsion_native_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_negatives_attempted=True,recovery_route='native-counter-contact-death-regressions',
            recovery_change='Re-evaluate original success evidence with every observed motion interval obstructed; preserve original gate. Prove ordinary car departure clears a genuine pin, all four new declared death boundaries, six unchanged old death boundaries and all ten regressions. Inference remains unloaded; no promotion before actual pixel review.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-negatives')
        original=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        activation=activation_probe(original)
        outcome=dict(candidate=self.source,prior_native=self.prior,success_continuity='pending',contact='pending',
            counter_deaths=[],old_deaths=[],regressions='pending',visual_review='pending',full_incident_accepted=False)
        path=self.store.root/'evidence'/(ident+'-counter-negatives.json')
        def save():
            atomic(path,outcome);self.store.set(counter_exfil_negatives_outcome=outcome);self.store.report()
        save()
        success=self.store.root/'evidence'/self.prior['success']['evidence']
        inputs=[success/'captures'/name for name in ('trace.jsonl','counter-exfil-contacts.jsonl','aim-shots.jsonl')]
        gate=inspect_success(*(lines(p) for p in inputs))
        gate.update(candidate=self.source,build_id=self.prior['success']['build_id'],evidence=success.name,
            evidence_sha256={p.name:sha(p.read_bytes()) for p in inputs})
        outcome['success_continuity']=gate;save()
        if not gate['passed']:raise Halt('Original success evidence lacks continuous obstruction: '+str(gate['failure']))
        def native(name,scenario,inspect):
            self.store.set(stage='native-counter-exfil-'+name);self.store.report()
            bundle=self.store.root/'evidence'/(ident+'-'+name)
            raw=self.engines.unity(self.project,bundle,scenario,self.source)
            gate=inspect(bundle) if raw.get('passed') else dict(passed=False,failure=['native-prerequisite'])
            gate.update(candidate=self.source,build_id=raw.get('build_id'),evidence=bundle.name,native=raw)
            atomic(bundle/'counter-negative-gate.json',gate)
            frames=sorted((bundle/'captures').glob('frame-*.png'))
            if frames:queue_milestone(self.store,'native-milestone',TASK,bundle,
                {**raw,'passed':bool(raw.get('passed') and gate['passed']),'counter_scope':name},frames,
                {f'frame-{i:03d}.png':t for i,t in enumerate(scenario['captures'])})
            return gate
        outcome['contact']=native('contact-release',maneuver(activation),lambda b:inspect_contact_release(
            lines(b/'captures/trace.jsonl'),lines(b/'captures/counter-exfil-contacts.jsonl')));save()
        if not outcome['contact']['passed']:raise Halt('Actual Counter-Exfil contact interruption failed: '+str(outcome['contact']['failure']))
        for case in counter_death.CASES:
            result=native('death-'+case,counter_death.probe(activation,case),lambda b:counter_death.inspect(
                lines(b/'captures/trace.jsonl'),read_json(b/'captures/death-injection.json'),case))
            outcome['counter_deaths'].append(result);save()
            if not result['passed']:raise Halt('Counter-Exfil death boundary failed '+case+': '+str(result['failure']))
        for case in old_death.CASES:
            result=native('old-death-'+case,old_death.death_probe(original,case),lambda b:old_death.inspect_player_death(
                lines(b/'captures/trace.jsonl'),read_json(b/'captures/death-injection.json'),case))
            outcome['old_deaths'].append(result);save()
            if not result['passed']:raise Halt('Original death boundary regressed '+case+': '+str(result['failure']))
        self.store.set(stage='native-counter-exfil-all-regressions');self.store.report()
        outcome['regressions']=self.regress(TASKS[7],ident,self.source);save()
        if not outcome['regressions'].get('passed'):raise Halt('Counter-Exfil regressed an original gameplay contract')
        raise Halt('One Counter-Exfil incident passes physical success, contact/death negatives and original regressions; source-matched pixel review required')

if __name__=='__main__':raise SystemExit(main(QualifyCounterNegatives))
