#!/usr/bin/env python3
"""Complete retained death helpers with a larger bounded working context."""
import json
from resume_death_completed_controls import CompletedControls
from resume_death_context_boundary import BASELINE
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='8a9bf8e59e13d56e999a235e6ae3fd9556c2a4e2'
PRIOR='q0150-5c900be9'


def validate_boundary(old, result, budget):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        death_controls_result_recovered=True,shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Focused death route-relay-death incomplete; preserve source and diagnose changed continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('death_context_capacity_attempted')
            or old.get('player_death_green_attempted') or result.get('bounded_stop')!='context'
            or budget.get('session_id')!=PRIOR+'-death-route-relay-death'
            or budget.get('conservative_prompt_bound')!=34713
            or old.get('active_model_settings',{}).get('reasoning_effort')!='xhigh'):
        raise Halt('Require the measured context-only stop and exact preserved partial chapter source')


class DeathContextCapacity(CompletedControls):
    phase_context_tokens=65536
    phase_readonly={'interception-hud-death':('RouteMission.cs','RelaySequence.cs')}
    phases=(
        ('complete-route-relay',('RouteMission.cs','RelaySequence.cs'),
         'Continue the exact retained local death integration. The control gates are already complete. '
         'RouteMission and RelaySequence already have death-first checks and reset bookkeeping. Do not '
         'repeat those edits or restart the design. Finish their remaining helpers and inspect all '
         'Update/LateUpdate paths. Concrete saved-source findings: RelaySequence calls HoldForDeath and '
         'ReleaseDeath but defines neither yet. RouteMission defines those helpers but references '
         'undeclared DownColor and HudColor; complete the code using actual current APIs. Its FailureText '
         'currently emits literal backslash-n text: render real line breaks and clear R retry/reset '
         'wording. Preserve an actual prior timeout reason without inventing one, and keep earned '
         'receipts, healthy timings, activation/order behavior and ordinary R. Existing unified '
         'MissionDirectorHud receives final death priority in the following phase. Save only the '
         'remaining usable changes, then call finish_task. Do not edit controls, Bootstrap or authority.'),
        CompletedControls.phases[1],
    )

    def validate_recovery(self,old):
        row=self.store.db.execute("SELECT data FROM events WHERE kind='role-budget' ORDER BY id DESC LIMIT 1").fetchone()
        validate_boundary(old,read_json(self.store.root/'evidence'/(PRIOR+'-death-route-relay-death.json')),
            json.loads(row[0]) if row else {})
        names={'VehicleInteraction.cs','Combat.cs','Mission.cs','RouteMission.cs','RelaySequence.cs'}
        if set(git(self.repo,'diff','--name-only',BASELINE,SOURCE).splitlines())!={'game/Assets/Game/'+n for n in names}:
            raise Halt('Preserve the exact retained controls and partial chapters')
        self.red=old['player_death_red_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(death_context_capacity_attempted=True,recovery_route='retained-chapters-65536-context',
            recovery_change='The observed34713 conservative prompt plus16384 output exceeded49152 by1945. '
            'Increase this continuation working context to65536 within the unchanged262144 native window. '
            'Keep xhigh, output allowance, sampling, qualified resident, all real pressure/throughput guards '
            'and fixed cap. Complete retained helpers; expose new chapter APIs read-only to the final HUD '
            'phase. No synthetic benchmark or gameplay/harness substitution.')


if __name__=='__main__':raise SystemExit(main(DeathContextCapacity))
