#!/usr/bin/env python3
"""Recover complete final local C# through the original validated source-save path."""
from submit_counter_exfil_parts import SubmitCounterExfil,final_source_parameter
from finish_counter_exfil_parts import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='7d70b70ef43f60d93afdd6524c479d1d30e43ff9'
PRIOR='q0167-981c0b36'
RESPONSE_SHA='fb03a69b2fe9b63b2466c380a76124b79a5ce15757f82fd9d65cf351ebd4922a'

class RecoverCounterRunner(SubmitCounterExfil):
    part_labels=('runner','hud')
    source_context_tokens=98304
    source_output_tokens=32768
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_submission_retained_attempted=True,counter_exfil_current_part='runner',
            blocker='Halt: Preserve saved local source; direct runner submission incomplete: no source tool')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_runner_final_recovered'):
            raise Halt('Require the exact stopped final-parameter response and unchanged accepted source/history')
        path=self.store.root/'private/sessions'/(PRIOR+'-runner-source')/'response-000.json'
        if sha(path.read_bytes())!=RESPONSE_SHA:raise Halt('Original final local runner response changed')
        content=final_source_parameter(read_json(path))
        self.recovered_parts={'runner':dict(content=content,response_sha256=RESPONSE_SHA)}
        self.initial_parts=old.get('counter_exfil_direct_parts',[])
        if len(self.initial_parts)!=1 or self.initial_parts[0].get('candidate')!=SOURCE or not self.initial_parts[0].get('ok'):
            raise Halt('Keep the actual successful crossing submission')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_runner_final_recovered=True,recovery_route='strict-final-local-code-recovery-then-hud',
            recovery_change='The normal-stop response contains complete final C# in one content parameter, '
            'separate from reasoning. Recover only those exact source bytes through the original scoped '
            'hash-checked validator/save path, preserving the raw response and prior no-tool stop. '
            'No cloud code substitution. Then local Qwen finishes HUD; native proof remains pending.')

if __name__=='__main__':raise SystemExit(main(RecoverCounterRunner))
