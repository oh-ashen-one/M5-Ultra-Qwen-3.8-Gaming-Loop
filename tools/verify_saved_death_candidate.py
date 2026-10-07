#!/usr/bin/env python3
"""Test the exact local candidate from a preserved turn-budget boundary."""
from resume_player_death_green import PlayerDeathGreen
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='d4d13937c63b9e056d3c40bf72fbf02e63eb3990'
BASELINE='dbfc89901b813ced826e976eb79c3370c95471b2'
PRIOR='q0151-78c25268'
RESPONSE_SHA='0d40d5902b8e134e2c41efbac17908ceb29767ff86f278f2ef42a4909df17c7b'
NAMES={'Combat.cs','InterceptionMission.cs','Mission.cs','MissionDirectorHud.cs',
    'RelaySequence.cs','RouteMission.cs','VehicleInteraction.cs'}


def validate_boundary(old, route, partial, response):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        death_context_capacity_attempted=True,shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Focused death interception-hud-death incomplete; preserve source and diagnose changed continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('player_death_green_attempted')
            or not route.get('ok') or not route.get('local_authored')
            or set(route.get('changed_files',[]))!={'Assets/Game/RouteMission.cs','Assets/Game/RelaySequence.cs'}
            or partial.get('bounded_stop')!='turns' or sha(response)!=RESPONSE_SHA
            or old.get('active_model_settings',{}).get('reasoning_effort')!='xhigh'):
        raise Halt('Require the exact saved local candidate and preserved incomplete author boundary')


class SavedDeathCandidate(PlayerDeathGreen):
    def validate_recovery(self,old):
        root=self.store.root
        validate_boundary(old,read_json(root/'evidence'/(PRIOR+'-death-complete-route-relay.json')),
            read_json(root/'evidence'/(PRIOR+'-death-interception-hud-death.json')),
            (root/'private/sessions'/(PRIOR+'-death-interception-hud-death')/'response-015.json').read_bytes())
        changed=set(git(self.repo,'diff','--name-only',BASELINE,SOURCE).splitlines())
        if changed!={'game/Assets/Game/'+name for name in NAMES}:
            raise Halt('Saved candidate changed outside the seven local death-integration files')
        self.source=SOURCE
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(player_death_green_attempted=True,saved_death_candidate_tested=True,
            author_completion_claimed=False,
            recovery_route='native-qualification-of-preserved-local-candidate',
            recovery_change='Preserve the sixteen-turn author stop and saved source without inventing a '
            'finish_task result. Compile and exercise this exact candidate using the unchanged six death '
            'cases,95-second healthy route and ten regressions. Native evidence, then actual pixel review, '
            'determine acceptance; source saves alone never promote. Inference remains unloaded.')


if __name__=='__main__':raise SystemExit(main(SavedDeathCandidate))
