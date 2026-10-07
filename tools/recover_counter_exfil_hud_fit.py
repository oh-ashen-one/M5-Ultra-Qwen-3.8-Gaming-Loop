#!/usr/bin/env python3
"""Save exact completed local HUD fields after a trailing-newline guard error."""
import json
from repair_counter_exfil_hud_fit import RepairCounterHudFit,SOURCE,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0172-a300c2d0'
RESPONSE_SHA='cb573bd02a92697ff97671e864ad2938656cd6edddef30946290bf93396b8dc0'

class RecoverCounterHudFit(RepairCounterHudFit):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_hud_fit_attempted=True,
            blocker='Halt: Preserve local source and the measured Armed HUD fit failure')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_hud_fit_final_recovered'):
            raise Halt('Require the exact completed local HUD submission and unchanged stopped history')
        response=self.store.root/'private/sessions'/(PRIOR+'-hud-fit-source')/'response-002.json'
        if sha(response.read_bytes())!=RESPONSE_SHA:raise Halt('Completed local HUD response changed')
        choice=read_json(response)['choices'][0];calls=choice['message'].get('tool_calls',[])
        if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='finish_source':
            raise Halt('Require one complete actual final source tool call')
        fields=calls[0]['function']['arguments'];fields=json.loads(fields) if isinstance(fields,str) else fields
        if set(fields)!={'hud_source','hint_property'}:raise Halt('Unexpected source submission fields')
        self.recovered_fields=fields;self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_hud_fit_final_recovered=True,recovery_route='exact-final-local-hud-newline-normalization',
            recovery_change='The third local source tool submission fits both bounds and preserves all protected helpers, lacking only EOF newline. Perform existing newline normalization before the exact tail check and recover those same source fields without new inference; preserve all original rejections.')

if __name__=='__main__':raise SystemExit(main(RecoverCounterHudFit))
