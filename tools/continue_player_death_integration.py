#!/usr/bin/env python3
"""Finish local death integration after the verified concurrent install/walk task."""
from qualify_qwen_capacity import CapacityAuthor
from resume_player_death_focused import FocusedDeath, PHASES
from resume_camera_native_only import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE = 'dbfc89901b813ced826e976eb79c3370c95471b2'
PRIOR = 'q0147-d77ec817'
REMAINING = {'death-failure-and-reset-not-visible',
    'objective-progression-after-zero-health', 'player-can-fire-while-dead'}
CONTROLS = ('VehicleInteraction.cs', 'Combat.cs', 'Mission.cs')


def validate_boundary(old, native):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        current_round=PRIOR, source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        shared_workload_priority='simultaneous-no-default-priority',
        blocker='Halt: Local install/walk source passes healthy route and dead-walking/reset verification; full death integration remains pending')
    positive = native.get('positive', {})
    death = native.get('death_contract', {})
    if (any(old.get(k) != v for k,v in expected.items())
            or old.get('player_death_completion_attempted')
            or old.get('player_death_green_attempted')
            or old.get('capacity_trial_native_outcome') != native
            or native.get('candidate') != SOURCE or not native.get('model_unloaded')
            or not positive.get('passed') or positive.get('candidate_commit') != SOURCE
            or not positive.get('build_id') or death.get('build_id') != positive['build_id']
            or death.get('candidate') != SOURCE or not death.get('setup_passed')
            or set(death.get('failure', [])) != REMAINING
            or not native.get('walking', {}).get('passed')
            or not old.get('player_death_red_outcome', {}).get('all_setups_valid')
            or old.get('active_model_settings', {}).get('reasoning_effort') != 'xhigh'):
        raise Halt('Require the verified install/walk boundary, actual remaining death failures and unchanged history')


class CompleteDeath(CapacityAuthor):
    # Two bounded current-source contexts; every accepted edit is checkpointed.
    # Bootstrap (including Walker and Follow) and DeathAuthority remain read-only.
    phase_turns = 16
    phases = (
        ('remaining-controls', CONTROLS,
         'The installed DeathAuthority and zero-health Walker/reset behavior already pass native tests. '
         'Leave both intact. Integrate its actual IsDead API in VehicleInteraction, Combat and Mission: '
         'block player firing, courier pickup/delivery and vehicle throttle/steering/boarding/exiting '
         'immediately at zero health. Process ordinary R/reset edges before dead-input exits. Prevent '
         'residual horizontal vehicle velocity while dead without breaking gravity or living handling. '
         'Lethal rival damage in this update must prevent a later player shot. Preserve actual enemy '
         'damage, aim rays, collision, earned completion, timing, input bindings and ordinary reset. '
         'The latest real negative had three player shots and courier pickup after zero health; '
         'horizontal walking and whole reset already passed. No Bootstrap or authority edits.'),
        ('remaining-chapters', PHASES[2][1], PHASES[2][2] +
         ' Latest evidence:12early zero-health samples from7.633 to8.783seconds still displayed '
         'PARCEL IN HAND, although the9.9-second image eventually displayed failure. The existing '
         'MissionBoard must prioritize health-depleted failure and R retry immediately in every '
         'chapter, including simultaneous chapter input. Retain the current authority and controls.'),
    )

    def validate_recovery(self, old):
        native = read_json(self.store.root/'evidence'/(PRIOR+'-capacity-native.json'))
        validate_boundary(old, native)
        self.red = old['player_death_red_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(player_death_completion_attempted=True,
            recovery_route='verified-concurrent-source-complete-local-death',
            shared_workload_priority='simultaneous-no-default-priority',
            recovery_change='Retain qualified phase-aware runtime and exact xhigh model settings; finish '
            'remaining controls and chapters from current source with usable local checkpoints. Preserve '
            'Bootstrap/camera/reticle/Walker and authority. Then unload inference and run all six unchanged '
            'death cases, the healthy95-second route and all prior regressions before any promotion.')

    finish_author = FocusedDeath.finish_author


if __name__ == '__main__':raise SystemExit(main(CompleteDeath))
