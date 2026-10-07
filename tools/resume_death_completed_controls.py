#!/usr/bin/env python3
"""Recover the inspected local controls conclusion and author only pending chapters."""
from resume_death_context_boundary import DeathContextRecovery, SOURCE, BASELINE
from resume_player_death_focused import PHASES
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

PRIOR='q0149-9d0c5516'
RESPONSE_SHA='9eafd5fea158d8515d7ff76252e637569ec8d7e474c5269ec4af13d3d3e54055'


def validate_boundary(old, response_bytes, saved):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        death_context_recovery_attempted=True,player_death_completion_attempted=True,
        shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Focused death verify-retained-controls incomplete; preserve source and diagnose changed continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('death_controls_result_recovered')
            or old.get('player_death_green_attempted') or sha(response_bytes)!=RESPONSE_SHA):
        raise Halt('Require the exact unchanged controls and inspected terminal local response')
    import json
    choice=json.loads(response_bytes)['choices'][0];message=choice['message']
    content=message.get('content','')
    if (choice.get('finish_reason')!='stop' or message.get('tool_calls')
            or saved.get('summary')!=content
            or not content.startswith('Verified all three saved gates directly in current source')
            or not content.endswith('No missing control path within the stated scope, so I made no edit, as this phase permits.')):
        raise Halt('Local controls conclusion is incomplete or changed; never invent a finish result')


class CompletedControls(DeathContextRecovery):
    phases=DeathContextRecovery.phases[1:]
    allow_unchanged_phases=()

    def validate_recovery(self,old):
        response=self.store.root/'private/sessions'/(PRIOR+'-death-verify-retained-controls')/'response-002.json'
        saved=read_json(self.store.root/'evidence'/(PRIOR+'-death-verify-retained-controls.json'))
        validate_boundary(old,response.read_bytes(),saved)
        changed=set(git(self.repo,'diff','--name-only',BASELINE,SOURCE).splitlines())
        if changed!={'game/Assets/Game/'+n for n in ('VehicleInteraction.cs','Combat.cs','Mission.cs')}:
            raise Halt('Preserve the exact three retained source edits')
        self.red=old['player_death_red_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(death_controls_result_recovered=True,
            recovery_route='reuse-completed-local-controls-confirmation',
            recovered_controls_response_sha256=RESPONSE_SHA,
            recovered_controls_scope='Local source inspection only; native qualification still required.',
            recovered_controls_correction='The final answer overstates no object creation: Install creates '
            'the authority host, while the decision method creates no presentation. This does not alter '
            'the verified three control gates or claim native success.',
            recovery_change='Preserve q0149 plain final response unchanged and recover its inspected '
            'controls confirmation without another model request. Continue only the pending two-file '
            'route/relay and interception/HUD contexts with the same healthy resident and xhigh settings.')


if __name__=='__main__':raise SystemExit(main(CompletedControls))
