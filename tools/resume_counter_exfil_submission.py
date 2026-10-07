#!/usr/bin/env python3
"""Save the retained runner correction, then finish the untouched HUD integration."""
from submit_counter_exfil_parts import SubmitCounterExfil
from finish_counter_exfil_parts import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='7d70b70ef43f60d93afdd6524c479d1d30e43ff9'
PRIOR='q0166-6dae1501'
RESPONSE_SHA='6c09d7f2cf63ac0c3d603c285d8bb24736263fb28e1670a7201b9ddc5b332e99'

class RetainedCounterSubmission(SubmitCounterExfil):
    part_labels=('runner','hud')
    source_context_tokens=98304
    source_output_tokens=32768
    retained_instruction=('The previous runner correction used all16384tokens without a source-save call. '
        'Use that retained work. The required changes are already fully specified: immediate real coupe '
        'collision-exit reset/death gate, and the exact piecewise LaneZ. Now submit the complete corrected '
        'CounterExfilRunner.cs through finish_source. Do not redesign, add features, restate the brief, '
        'or claim the file was saved. The actual finish_source call is the next deliverable. Same xhigh '
        'quality;32768output tokens are available within the fixed bounded request.')
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_direct_submission_attempted=True,counter_exfil_current_part='runner',
            blocker='Halt: Preserve saved local source; direct runner submission incomplete: output')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_submission_retained_attempted'):
            raise Halt('Require the saved crossing and exact incomplete runner output boundary')
        path=self.store.root/'private/sessions'/(PRIOR+'-runner-source')/'response-000.json'
        if sha(path.read_bytes())!=RESPONSE_SHA:raise Halt('Retained private runner work changed')
        response=read_json(path);choice=response['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls') or response.get('usage',{}).get('completion_tokens')!=16384:
            raise Halt('Require the measured no-tool runner output stop')
        self.initial_parts=old.get('counter_exfil_direct_parts',[])
        if len(self.initial_parts)!=1 or self.initial_parts[0].get('candidate')!=SOURCE or not self.initial_parts[0].get('ok'):
            raise Halt('Preserve the actual successful crossing source submission')
        self.retained_parts={'runner':choice['message']}
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_submission_retained_attempted=True,recovery_route='retained-runner-source-then-hud',
            recovery_change='Keep the successful crossing and untouched old HUD. Retain the exact16384-token '
            'runner response, then submit actual corrected source with32768output/98304working context. '
            'Same model/xhigh,600second bound, resident, pressure/ownership guards and fixed cap; no restart.')

if __name__=='__main__':raise SystemExit(main(RetainedCounterSubmission))
