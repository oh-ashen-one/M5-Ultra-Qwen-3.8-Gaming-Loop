#!/usr/bin/env python3
"""One measured larger output allowance after the compact walking role exhausted 8192."""
from resume_three_day_queue import main
from resume_map_walk_first import MapWalkFirst,CANDIDATE,ACCEPTED
from loop_controller.core import Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='1c68cc752e653129196cfec1c2aa153d8445ca87'
ROUND='q0059-83da1884'
BLOCKER='Halt: Walking role no-submission; smaller role stop preserved'


def validate_budget_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=10,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_segment_recovery_attempted=True,
        map_prefix_attempts=0,map_walking_prefix=None)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_prefix_budget_attempted'):
        raise Halt('Expected exact compact walking-role output stop')


class PrefixBudgetRecovery(MapWalkFirst):
    def validate_recovery(self,old):
        validate_budget_pause(old)
        if git(self.repo,'diff','--name-only',CANDIDATE,SOURCE,'--','game'):
            raise Halt('Preserve the compiled local map candidate')

    def recovery_settings(self):
        return {'map_prefix_budget_attempted':True,'walking_prefix_output_tokens':16384,
            'recovery_route':'changed-strategy',
            'recovery_change':'Compact walking role retained; one larger16384output allowance after measured8192exhaustion'}


if __name__=='__main__':raise SystemExit(main(PrefixBudgetRecovery))
