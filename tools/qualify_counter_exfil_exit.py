#!/usr/bin/env python3
"""Prove an early physical foot exit cannot earn or bank incident completion."""
from resume_camera_native_only import CameraNativeOnly
from probe_counter_exfil import activation_probe,ACCEPTED,TASK
from probe_counter_exfil_driving import maneuver
from verify_counter_exfil_propulsion import lines
from review_counter_exfil_incident import require_native
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.counter_exfil_exit_checks import inspect_early_exit

STOP='Halt: One Counter-Exfil incident passes physical success, contact/death negatives and original regressions; source-matched pixel review required'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_negatives_attempted=True,blocker=STOP)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_exit_negative_attempted'):
        raise Halt('Require all completed native prerequisites before the distinct early-exit negative')
    require_native(old.get('counter_exfil_negatives_outcome',{}),old.get('source_checkpoint'))

def early_exit(original):
    scenario=dict(original,id='counter-exfil-unresolved-foot-exit-does-not-complete',duration=125,
        captures=[.6,98.5,104.95,110,118,121,124])
    scenario['steps']=[dict(s) for s in original['steps'] if s['start']<99]
    sequence=[(99.3,99.6,['F']),(100.2,100.3,['E']),(100.4,101.9,['S']),
        (102,102.43,['A']),(102.6,103.55,['W']),(103.7,104.9,['A']),
        (106,106.3,['F']),(120,120.1,['R']),(122,123,['W'])]
    scenario['steps'] += [dict(start=a,end=b,keys=k) for a,b,k in sequence]
    scenario['steps'].sort(key=lambda x:x['start']);return scenario

class QualifyCounterExit(CameraNativeOnly):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint'];self.native_round=old['current_round']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_exit_negative_attempted=True,counter_exfil_native_round=self.native_round,
            recovery_route='native-unresolved-foot-crossing-negative',
            recovery_change='All prior checks remain preserved. One distinct ordinary-input negative crosses the validated west exit before all runners resolve, waits beyond it, repeats F while active and resets. No source change, injection or repeat of already-passing suites.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-early-exit-negative')
        original=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        scenario=early_exit(maneuver(activation_probe(original)));bundle=self.store.root/'evidence'/(ident+'-early-exit')
        native=self.engines.unity(self.project,bundle,scenario,self.source)
        gate=inspect_early_exit(lines(bundle/'captures/trace.jsonl'),lines(bundle/'captures/counter-exfil-contacts.jsonl')) if native.get('passed') else dict(passed=False,failure=['native-prerequisite'])
        gate.update(candidate=self.source,build_id=native.get('build_id'),native=native,evidence=bundle.name)
        atomic(bundle/'early-exit-gate.json',gate);self.store.set(counter_exfil_exit_negative_outcome=gate);self.store.report()
        if not gate['passed']:raise Halt('Actual unresolved-foot-exit negative failed: '+str(gate['failure']))
        raise Halt(STOP.removeprefix('Halt: '))

if __name__=='__main__':raise SystemExit(main(QualifyCounterExit))
