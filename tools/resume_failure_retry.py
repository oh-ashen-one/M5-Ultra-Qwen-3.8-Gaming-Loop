#!/usr/bin/env python3
"""Recover the observed directory-read fault with local-authored mission micro-edits."""
from pathlib import Path

from loop_controller.core import Halt
from loop_controller.continuous_checks import validate_proposed
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from resume_mission_review import verified_probe
from resume_three_day_queue import ThreeDayRunner, main

PAUSED_SOURCE='8bdb22671553e53a2a203675765b71c105553eb9'
ACCEPTED_COURIER='ca12a184f01a0d7222b3d8d577783c9a41c06b9c'


def validate_failure_pause(state,project):
    expected="IsADirectoryError: [Errno 21] Is a directory: "+repr(str(Path(project)/'Notes'))
    if (state.get('task_index')!=3 or state.get('blocker')!=expected
            or state.get('source_checkpoint')!=PAUSED_SOURCE
            or state.get('last_playable_checkpoint')!=ACCEPTED_COURIER
            or state.get('overall_deadline_epoch')!=HARD_CAP_EPOCH):
        raise Halt('Preserve any pause other than the inspected failure/retry directory-read fault')


def failure_probe(previous,task,deadline=45):
    """Wait for the real deadline, then R and the observed successful route."""
    offset=deadline+2
    value={'duration':previous['duration']+offset,
        'steps':[{'start':offset,'end':offset+.3,'keys':['R']}]+[
            {**step,'start':step['start']+offset,'end':step['end']+offset} for step in previous['steps']],
        'captures':[3.2,deadline-.5,deadline+1,offset+.5]+[offset+t for t in [5.2,7.9,12.5,15.2,18.5]]}
    return validate_proposed(value,task['maximum'],task['coverage'])


class FailureRetryRunner(ThreeDayRunner):
    def validate_recovery(self,old):validate_failure_pause(old,self.project)

    def recovery_settings(self):
        return {'failure_retry_recovery_pending':True}

    def edit(self,task,ident):
        if not self.store.get('failure_retry_recovery_pending'):return super().edit(task,ident)
        if task['id']!='mission-failure-retry':raise Halt('Failure recovery cannot edit another task')
        for label,needle,instruction in [
            ('failure-start-timer','padPos = padRend.transform.position;',
             'Preserve this Start assignment. Add initialization of the existing float missionStartTime to Time.time.'),
            ('failure-reset-timer','stage = 0;',
             'This is Respawn, reached after the existing physical R reset. Preserve stage zero and reset the existing '
             'missionStartTime to Time.time. Change no other state or timer threshold.'),
            ('failure-deadline-latch','// Animate parcel when in world.',
             'Replace this Update comment with at most three compact lines, after the existing Restarts/Respawn handling. '
             'For stages zero or one, if elapsed Time.time minus missionStartTime reaches existing DEADLINE, latch stage '
             'three, use the existing Set helper to set Mission to failed and MissionComplete to false. If stage three, '
             'call RefreshHud and return from Update, preventing all parcel/F interaction until R. Preserve the comment '
             'as the final line. Do not change the deadline or actors and do not inspect the replay.'),
            ('failure-visible-reason','if (hud == null) return;',
             'Preserve the null guard. Add a compact early stage-three branch setting hud.text to three short lines: '
             'DELIVERY FAILED, Delivery window expired, R to retry. Use escaped newline characters and return afterward. '
             'Stages zero/one/two must continue through their existing HUD paths.'),
            ('failure-pickup-countdown','"OBJECTIVE: reach the parcel  ("',
             'Preserve the exact objective, distance and newline concatenation in this HUD expression. Append a compact '
             'remaining-seconds countdown before its newline, using the existing DEADLINE and missionStartTime, Time.time, '
             'Mathf.Max with zero and Mathf.CeilToInt. Keep this one source line and the same three HUD lines.'),
            ('failure-carry-countdown','"OBJECTIVE: drive to the GREEN pad  ("',
             'Preserve the exact objective, distance and newline concatenation in this HUD expression. Append a compact '
             'remaining-seconds countdown before its newline, using the existing DEADLINE and missionStartTime, Time.time, '
             'Mathf.Max with zero and Mathf.CeilToInt. Keep this one source line and the same three HUD lines.')]:
            self.line_edit(ident,label,needle,instruction)
        previous,evidence=verified_probe(self.store.root,task)
        probe=failure_probe(previous,task)
        self.store.set(failure_retry_recovery_pending=False,last_valid_replay=probe)
        self.store.event('failure-retry-recovery-probe',prior_passing_route=evidence,
            real_failure_wait_seconds=47,ordinary_reset=True,success_claimed=False,
            game_code_author='local Qwen',probe_author='cloud acceptance controller',
            retry_counters_changed=False)
        return {'ok':True,'scenario':probe}


if __name__=='__main__':raise SystemExit(main(FailureRetryRunner))
