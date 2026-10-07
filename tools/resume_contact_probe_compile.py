#!/usr/bin/env python3
"""Repair the controller's obsolete identity API; keep gameplay/input unchanged."""
import json
from resume_vehicle_contact import VehicleContactRecovery,CANDIDATE,ACCEPTED,REPLAY
from resume_three_day_queue import main
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git


class ContactProbeCompile(VehicleContactRecovery):
    def validate_recovery(self,old):
        expected=dict(source_checkpoint='cd65b1cb702005da8ec9afb784b5fb94da460bf6',
            last_playable_checkpoint=ACCEPTED,current_round='q0068-3f122573-contact',
            task_index=7,task_failures=15,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,vehicle_contact_recovery_attempted=True,
            blocker='Halt: Contact diagnosis native execution failed')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('contact_probe_compile_recovery'):
            raise Halt('Expected exact preserved controller-probe compile error')
        if replay_identity(old['last_valid_replay'])!=REPLAY or len(old['map_traversal_strategies'])!=3:
            raise Halt('Preserve replay and exhausted strategy history')
        if git(self.repo,'diff','--name-only',CANDIDATE,old['source_checkpoint'],'--','game'):
            raise Halt('Diagnostic source must still match the local grounded candidate')
        gate=json.loads((self.store.root/'evidence'/old['current_round']/'scoped-gate.json').read_text())
        errors=gate.get('compile_errors',[])
        if gate.get('player_exit') is not None or not errors or any(
                'Object.GetInstanceID()' not in e and e!='Scripts have compiler errors.' for e in errors):
            raise Halt('Only the exact obsolete observation API is admitted')

    def recovery_settings(self):
        return {**super().recovery_settings(),'contact_probe_compile_recovery':True}


if __name__=='__main__':raise SystemExit(main(ContactProbeCompile))
