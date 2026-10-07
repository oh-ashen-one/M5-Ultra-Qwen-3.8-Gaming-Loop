#!/usr/bin/env python3
"""Resume the same native probe after correcting external observer identity API."""
from probe_counter_exfil import ProbeCounterExfil,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,sha,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='ff3564295c6f8cb97cade915e089abf19056743a'
PRIOR='q0170-58c8b23a'
GATE_SHA='6b4dabcef45dbd71419c439ac7320d914d51f103309dbad4f62fd8142ff80d87'

class ResumeCounterObserver(ProbeCounterExfil):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_probe_attempted=True,
            blocker='Halt: Protected controller harness compilation failed; stop gameplay edits and repair infrastructure')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_observer_api_recovered'):
            raise Halt('Require the exact original observer-only compile failure and unchanged source/history')
        gate=self.store.root/'evidence'/(PRIOR+'-old-healthy')/'gate.json'
        if sha(gate.read_bytes())!=GATE_SHA:raise Halt('Original compile evidence changed')
        errors=read_json(gate).get('compile_errors',[])
        if not errors or any('GetInstanceID' not in e and e!='Scripts have compiler errors.' for e in errors):
            raise Halt('Do not broaden the diagnosed observer identity API repair')
        self.source=SOURCE
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_observer_api_recovered=True,recovery_route='native-probe-after-observer-entity-id-api',
            recovery_change='Replace obsolete external observer instance IDs with the already-qualified GetEntityId string API. Preserve the failed gate and every game source byte; rerun unchanged real-input acceptance.')

if __name__=='__main__':raise SystemExit(main(ResumeCounterObserver))
