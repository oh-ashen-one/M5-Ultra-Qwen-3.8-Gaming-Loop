#!/usr/bin/env python3
"""Save retained local C# work after one measured author output-limit stop."""
from implement_counter_exfil import ImplementCounterExfil,SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0162-7b7beb35'
RESPONSE_SHA='8bfde4ee41480c63f55f08d60b0be56bfac080af7cc1ddc7ee4ea40814ae8389'

def validate_boundary(old,response):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_source_attempted=True,
        blocker='Halt: Preserve usable local Counter-Exfil saves; complete source submission needs focused continuation')
    choice=response.get('choices',[{}])[0]
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_retained_source_attempted')
            or old.get('counter_exfil_source_outcome',{}).get('bounded_stop')!='output'
            or choice.get('finish_reason')!='length' or choice.get('message',{}).get('tool_calls')
            or not choice.get('message',{}).get('content')
            or response.get('usage',{}).get('completion_tokens')!=32768):
        raise Halt('Require the measured no-edit output-limit stop, preserved response and unchanged accepted source')

class RetainedCounterExfil(ImplementCounterExfil):
    retained_instruction=('Your previous bounded response used all32768output tokens before any tool call; '
        'NO game source file was saved. Use that retained implementation work now, without redesign or '
        'restating requirements. Make an ACTUAL create_file call for the first complete usable C# module '
        'as your next deliverable, then save the second module and exact HUD installation. Existing '
        'source remains byte-for-byte as supplied. Keep each new file under400lines/20KB. This is '
        'code submission, not another planning cycle. Thinking remains xhigh. Finish_task only after '
        'the actual tools have saved all required files; never claim a save that has not happened.')
    def validate_recovery(self,old):
        path=self.store.root/'private/sessions'/(PRIOR+'-counter-exfil-source')/'response-000.json'
        if sha(path.read_bytes())!=RESPONSE_SHA:raise Halt('Preserved private local implementation work changed')
        response=read_json(path);validate_boundary(old,response)
        self.retained_author=response['choices'][0]['message'];self.survey=old['counter_exfil_preflight']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_retained_source_attempted=True,recovery_route='retained-counter-exfil-code-save',
            retained_counter_exfil_response_sha256=RESPONSE_SHA,
            recovery_change='Preserve all32768private response tokens and exact stopped ledger. The original '
            '437.37second/77.64token-per-second request saved no code. Replace repeated per-point obstacle '
            'listings with their complete unique obstacle names/counts, retaining the full original survey. '
            'Provide exact install/Walker APIs with protected Follow available on demand; submit actual C# '
            'through tools now. Same model/xhigh,32768output/98304context,600second bound and guards; no restart.')

if __name__=='__main__':raise SystemExit(main(RetainedCounterExfil))
