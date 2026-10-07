#!/usr/bin/env python3
"""Carry forward the real bounded local physics draft into actual source submission."""
from repair_counter_exfil_propulsion import RepairCounterPropulsion,SOURCE,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0177-a89023b6'
RESPONSE_SHA='cc18693a7e7027494b4b483c61c91c92967244a5c73a6f5a4f5cc1c109d355ca'

class ResumeCounterPropulsion(RepairCounterPropulsion):
    source_context_tokens=98304
    source_output_tokens=32768
    retained_instruction=('The actual physical diagnosis and your bounded draft are retained. Finish that '
        'same focused solution now through finish_source: complete finite-propulsion Runner, selected '
        'SpawnOne method and genuinely shorter HudLine. No new design/planning or expanded comments. '
        'The next deliverable is actual saved source. Keep dynamic real contacts, free escape, gravity, '
        'death/reset and immediate separation clearing. The parked car must remain an actual physical '
        'obstacle after E, without freezing actors or altering the car/world. Same model/xhigh; '
        '32768output tokens are available within the unchanged600second request bound.')
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            counter_exfil_propulsion_repair_attempted=True,
            blocker='Halt: Preserve actual runner propulsion failure and local source; focused repair incomplete')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_propulsion_retained_attempted'):
            raise Halt('Require the exact output-boundary stop and unchanged source/history')
        path=self.store.root/'private/sessions'/(PRIOR+'-propulsion-source')/'response-000.json'
        if sha(path.read_bytes())!=RESPONSE_SHA:raise Halt('Original private propulsion draft changed')
        response=read_json(path);choice=response['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls') or response.get('usage',{}).get('completion_tokens')!=16384:
            raise Halt('Require the measured16384-token no-tool stop')
        self.retained_author=choice['message'];self.prior=old['counter_exfil_source_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_propulsion_retained_attempted=True,recovery_route='retained-finite-propulsion-source-submission',
            recovery_change='Keep the actual197.17second16384-token no-tool draft private and hash-sealed. '
            'Continue it with32768output/98304working tokens at unchanged model/xhigh,600second bound '
            'and original capacity/ownership/deadline guards. No model restart, counter reset or acceptance waiver.')

if __name__=='__main__':raise SystemExit(main(ResumeCounterPropulsion))
