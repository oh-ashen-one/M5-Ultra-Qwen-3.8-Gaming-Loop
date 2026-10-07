#!/usr/bin/env python3
"""Observe actual westbound corridor geometry on the accepted native source."""
from resume_camera_native_only import CameraNativeOnly
from resolve_death_pixel_review import SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0159-025c6c2a'
TASK=dict(id='counter-exfil-native-preflight',phase='mission',visual_facing=False,
    outcome='Native westbound capsule and actual coupe clearance before local implementation')

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Reviewed local counter-exfil scope saved; implement and qualify the first complete incident')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_preflight_attempted'):
        raise Halt('Require the accepted unchanged source and completed local scope boundary')

class CounterExfilPreflight(CameraNativeOnly):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_preflight_attempted=True,recovery_route='native-westbound-counter-exfil-preflight',
            recovery_change='Read-only actual capsule/box overlaps, swept segments and ground/render bounds on accepted source. No scene or gameplay mutations. Next is local source implementation, not more prose planning.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-preflight')
        scenario=read_json(self.store.root/'evidence/q0132-45fc0624-positive/captures/scenario.json')
        scenario.update(id=ident,fixture='counter-exfil-survey',duration=78,captures=[76.8,77.3])
        scenario['steps']=[s for s in scenario['steps'] if s['start']<77]
        bundle=self.store.root/'evidence'/(ident+'-survey')
        gate=self.engines.unity(self.project,bundle,scenario,SOURCE)
        if not gate.get('passed'):raise Halt('Native preflight prerequisite failed: '+str(gate.get('failure')))
        result=read_json(bundle/'captures/counter-exfil-survey.json')
        result.update(candidate=SOURCE,build_id=gate['build_id'],evidence=bundle.name,gameplay_verified=False)
        atomic(self.store.root/'evidence'/(ident+'-counter-exfil-preflight.json'),result)
        self.store.set(counter_exfil_preflight=result);self.store.report()
        raise Halt('Native westbound geometry recorded; local Qwen must implement the one-incident parent contract')

if __name__=='__main__':raise SystemExit(main(CounterExfilPreflight))
