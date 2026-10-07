#!/usr/bin/env python3
"""Recover one hash-pinned, complete final local source submission."""
import re
from repair_counter_exfil_propulsion import RepairCounterPropulsion,SOURCE,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0178-5de66f1f'
RESPONSE_SHA='f8f8ce179cffbcd5e401b34edae9dca048425bee6e8779027b3edbae29a3a347'

def final_fields(response):
    choices=response.get('choices',[])
    if len(choices)!=1:raise ValueError('Require one completed source response')
    choice=choices[0];message=choice.get('message',{})
    if choice.get('finish_reason')!='stop' or message.get('tool_calls') or not message.get('reasoning_content'):
        raise ValueError('Require complete final content separate from private reasoning')
    pattern=(r'<invoke name="finish_source">\s*'
        r'<parameter name="runner_source">(?P<runner_source>[\s\S]+?)</parameter>\s*'
        r'<parameter name="spawn_method">(?P<spawn_method>[\s\S]+?)</parameter>\s*'
        r'<parameter name="hint_property">(?P<hint_property>[\s\S]+?)</parameter>\s*</invoke>')
    match=re.fullmatch(pattern,message.get('content','').strip())
    if not match:raise ValueError('Require only all three exact completed final source fields')
    return match.groupdict()

class RecoverCounterPropulsion(RepairCounterPropulsion):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_propulsion_repair_attempted=True,counter_exfil_propulsion_retained_attempted=True,
            blocker='Halt: Preserve actual runner propulsion failure and local source; focused repair incomplete')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_propulsion_final_recovered'):
            raise Halt('Require exact completed no-tool submission and unchanged stopped history')
        path=self.store.root/'private/sessions'/(PRIOR+'-propulsion-source')/'response-000.json'
        if sha(path.read_bytes())!=RESPONSE_SHA:raise Halt('Completed local source response changed')
        self.recovered_fields=final_fields(read_json(path));self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_propulsion_final_recovered=True,recovery_route='exact-final-local-propulsion-fields',
            recovery_change='Recover only three complete final C# fields from the hash-pinned stopped response through the original bounded hash-checked save tools. Preserve the no-tool stop and private reasoning. This does not qualify source or native behavior; focused material API and terminal-stop review corrections remain required.')

if __name__=='__main__':raise SystemExit(main(RecoverCounterPropulsion))
