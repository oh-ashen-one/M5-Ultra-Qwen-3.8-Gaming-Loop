#!/usr/bin/env python3
"""Requalify the saved local Armed-HUD correction with inference unloaded."""
from probe_counter_exfil import ProbeCounterExfil,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_hud_fit_attempted=True,
        blocker='Halt: Counter-Exfil Armed HUD fit saved; unload idle inference and requalify original route and new inputs')
    result=old.get('counter_exfil_hud_fit_result',{});source=old.get('counter_exfil_source_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_hud_fit_native_attempted')
            or not result.get('ok') or not result.get('local_authored')
            or result.get('candidate')!=old.get('source_checkpoint') or source.get('candidate')!=result.get('candidate')):
        raise Halt('Require the actual saved local HUD fit and unchanged acceptance/history')

class VerifyCounterHudFit(ProbeCounterExfil):
    def validate_recovery(self,old):
        validate_boundary(old);self.source=old['source_checkpoint']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_hud_fit_native_attempted=True,recovery_route='native-after-measured-local-armed-card-fit',
            recovery_change='Preserve original failed build and fifth-line geometry evidence. Run unchanged healthy inputs with a narrowly recognized actual Armed hint, then ordinary retrieval/F, unresolved escape and R. All physical, readability and original ending-content checks remain.')

if __name__=='__main__':raise SystemExit(main(VerifyCounterHudFit))
