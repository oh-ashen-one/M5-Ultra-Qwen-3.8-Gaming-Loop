#!/usr/bin/env python3
"""Keep saved control gates and finish death integration in smaller contexts."""
from continue_player_death_integration import CompleteDeath, SOURCE as BASELINE, CONTROLS
from resume_player_death_focused import FocusedDeath, PHASES
from resume_three_day_queue import main
from resume_camera_native_only import ACCEPTED
from loop_controller.core import Halt, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='0e2f64f4c48a55eb7d1ababc2b658b0eabb9eddb'
PRIOR='q0148-4c9406cf'


def validate_boundary(old, result):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        player_death_completion_attempted=True,shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Focused death remaining-controls incomplete; preserve source and diagnose changed continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('death_context_recovery_attempted')
            or old.get('player_death_green_attempted') or result.get('bounded_stop')!='context'
            or old.get('active_model_settings',{}).get('reasoning_effort')!='xhigh'):
        raise Halt('Require the exact saved-controls context boundary; never reset failures or repeat a resource fault')


class DeathContextRecovery(CompleteDeath):
    allow_unchanged_phases=('verify-retained-controls',)
    phases=(
        ('verify-retained-controls',CONTROLS,
         'The previous local task already saved death gates in all three current files before its '
         'context budget ended during inspection. VehicleInteraction keeps ordinary R first and gates '
         'doors/throttle/steering with horizontal stopping; Combat.HandleFire now checks IsDead after '
         'real rival damage; CourierMission checks IsDead before pickup/delivery. Inspect the exact '
         'current code for completeness against that requirement. Keep usable edits; do not repeat them '
         'or refactor. If correct, call finish_task immediately with a concise confirmation; this retained '
         'phase explicitly allows no additional edit. If an actual missing control path exists, make '
         'only that focused repair and finish. Preserve gravity, living input, reset and earned history.'),
        ('route-relay-death',('RouteMission.cs','RelaySequence.cs'),PHASES[2][2]+
         ' This phase edits only RouteMission and RelaySequence. Interception and the unified HUD '
         'follow in their own short context. Existing controls are already saved; do not repeat them.'),
        ('interception-hud-death',('InterceptionMission.cs','MissionDirectorHud.cs'),PHASES[2][2]+
         ' This phase edits only InterceptionMission and MissionDirectorHud. Route and relay gates '
         'are already saved. Prioritize same-frame health-depleted failure/R retry on MissionBoard; '
         'the previous12early dead samples incorrectly retained the PARCEL IN HAND objective.'),
    )

    def validate_recovery(self,old):
        validate_boundary(old,read_json(self.store.root/'evidence'/(PRIOR+'-death-remaining-controls.json')))
        changed=set(git(self.repo,'diff','--name-only',BASELINE,SOURCE).splitlines())
        if changed!={'game/Assets/Game/'+name for name in CONTROLS}:
            raise Halt('Retained source must contain only the three saved local control integrations')
        self.red=old['player_death_red_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(death_context_recovery_attempted=True,
            recovery_route='preserve-saved-controls-smaller-chapter-contexts',
            recovery_change='Preserve q0148 controls and its33822-token conservative bound plus16384 output '
            'exceeding49152 working context. Keep the same healthy resident, xhigh and output allowance. '
            'Confirm retained controls without requiring gratuitous edits, then use two-file chapter '
            'contexts. All source, acceptance history, counters and the fixed cap remain preserved.')

    def finish_author(self,ident,result):
        result['retained_control_source']=SOURCE
        result['retained_control_round']=PRIOR
        result['changed_files']=sorted(set(result['changed_files'])|{'Assets/Game/'+name for name in CONTROLS})
        FocusedDeath.finish_author(self,ident,result)


if __name__=='__main__':raise SystemExit(main(DeathContextRecovery))
