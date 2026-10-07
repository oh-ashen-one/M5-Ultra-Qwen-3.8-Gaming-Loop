#!/usr/bin/env python3
"""Finish retained local scope work with a measured larger output allowance."""
from refine_counter_exfil_scope import RefineCounterExfil, SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0158-1d99326d'
RESPONSE_SHA='8b6a23c9eca52342acde6d63a0c2afe2c539c7d4e73848b6f38add025d1ea556'


def validate_boundary(old,response):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_scope_review_attempted=True,
        blocker='Halt: Preserve original proposal and measured handoff; concise revised local scope not submitted')
    choice=response.get('choices',[{}])[0]
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_scope_retained_attempted')
            or old.get('counter_exfil_reviewed_plan',{}).get('bounded_stop')!='output'
            or choice.get('finish_reason')!='length' or choice.get('message',{}).get('tool_calls')
            or not choice.get('message',{}).get('content')
            or response.get('usage',{}).get('completion_tokens')!=16384):
        raise Halt('Require the exact measured planning-output stop and accepted source')


class RetainedScope(RefineCounterExfil):
    scope_context_tokens=98304
    scope_output_tokens=32768
    retained_instruction=('The previous response exhausted16384output tokens before submitting the revised '
        'scope. Use that retained work; do not repeat broad design or write code. Xhigh is unchanged and '
        'this bounded request has32768output tokens. Finish the six concise final fields with a real '
        'submit_plan call or complete JSON final content; do not merely claim the plan was saved.')

    def validate_recovery(self,old):
        p=self.store.root/'private/sessions'/(PRIOR+'-scope-refinement')/'response-000.json'
        if sha(p.read_bytes())!=RESPONSE_SHA:raise Halt('Preserved private scope work changed')
        response=read_json(p);validate_boundary(old,response)
        self.proposal=old['next_connected_expansion']
        self.retained_scope=response['choices'][0]['message']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(counter_exfil_scope_retained_attempted=True,recovery_route='retained-scope-larger-output',
            retained_scope_response_sha256=RESPONSE_SHA,
            recovery_change='Measured scope response used all16384tokens in201.59seconds at83.68decode '
            'tokens/second. Retain it and allow32768output within98304working/262144native context. '
            'Keep xhigh, sampling,600second request bound, qualified runtime/resource/ownership guards, '
            'accepted source, failure history and fixed cap. No game edits or synthetic benchmark.')


if __name__=='__main__':raise SystemExit(main(RetainedScope))
