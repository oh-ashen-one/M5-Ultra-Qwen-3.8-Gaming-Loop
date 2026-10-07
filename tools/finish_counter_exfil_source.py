#!/usr/bin/env python3
"""Finish existing local chapter modules in a fresh exact-source context."""
from implement_counter_exfil import ImplementCounterExfil,SOURCE as ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='87a9438808887207f98350da55d31b31b67bb71e'
PRIOR='q0163-2b785ac6'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_retained_source_attempted=True,
        blocker='Halt: Preserve usable local Counter-Exfil saves; complete source submission needs focused continuation')
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_finish_source_attempted')
            or old.get('counter_exfil_source_outcome',{}).get('bounded_stop')!='context'):
        raise Halt('Require the saved two-module context boundary without changing accepted source or failure history')

class FinishCounterExfil(ImplementCounterExfil):
    author_context_tokens=65536
    author_output_tokens=16384
    focused_instruction=('FOCUSED CODE CONTINUATION: Both new files already exist and are supplied in full below. '
        'The retained draft successfully saved them, then reached its context bound. Use read/replace_text '
        'to finish these existing modules; do not re-create them or repeat the design. Five concrete tasks: '
        '(1) Remove the invalid placeholder lambda assignment to run.Coupe in SpawnOne, retaining the '
        'actual Transform assignment, and finish compiling source. '
        '(2) Install the chapter once through the actual existing MissionDirectorHud.Install and integrate '
        'its real board API. Keep the old ending visible while Armed with compact E/F guidance. Preserve '
        'the existing death text/colour/camera/reticle and specific failure priority; do not crowd the '
        'small board with two full objectives. Read exact current spans before replacements. '
        '(3) Physical separation currently lacks OnCollisionExit and can retain credit for0.12seconds. '
        'Clear the current-car contact and uninterrupted hold immediately on its real collision exit; '
        'a lost contact must restart the entire0.8second qualification. Do not count pins after death. '
        '(4) FootAtWestExit currently tests only standing beyond the line and accepts a wide unqualified '
        'Z band. Require an actual living on-foot east-to-west crossing in the validated central exit '
        'region after all three are killed or currently pinned. Reset prior-crossing samples on R; '
        'standing beyond the exit before resolution must not fabricate a crossing. '
        '(5) The actual qualified central path is PIECEWISE: X47.605/Z17.4603 to X22/Z16.5738 to '
        'X6/Z16.0057 to X3/Z16.0057. The saved straight endpoint interpolation is not that exact '
        'surveyed path. Make the runner lane honor those existing waypoints, keep physical collision '
        'and gravity, and correct source comments that claim the old rival is necessarily live (the '
        'measured healthy handoff killed it). Preserve genuine old source/health/counters. '
        'No broad planning or extra features. Submit actual usable code edits now, then finish_task.')
    def validate_recovery(self,old):
        validate_boundary(old);self.survey=old['counter_exfil_preflight']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_finish_source_attempted=True,recovery_route='fresh-exact-source-finish-counter-exfil',
            recovery_change='Keep the two local source modules and all prior private work. Fresh scoped '
            'context fixes the concrete placeholder/contact/crossing/path findings and finishes HUD '
            'installation. Same model/xhigh and measured guard policy; native proof remains required.')

if __name__=='__main__':raise SystemExit(main(FinishCounterExfil))
