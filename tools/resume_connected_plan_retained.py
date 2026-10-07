#!/usr/bin/env python3
"""Retain the actual capped local design response and request its final plan."""
from resolve_death_pixel_review import ResolveDeathPixels, SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0155-e2ac2964'
RESPONSE_SHA='b77da7046b70544861dc32516858f2bc15944d5062c882e0649f93f93d4f79e8'
TASK=dict(id='retained-connected-objective-plan',phase='mission',visual_facing=False,
    outcome='Submit the already-developed local next-objective design without repeating its analysis')


def validate_boundary(old,response):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        death_pixel_resolution_attempted=True,
        blocker='Halt: Death repair accepted; retain the bounded next-plan result for focused continuation')
    result=old.get('next_connected_expansion',{})
    accepted=old.get('player_death_scoped_acceptance',{})
    choice=response.get('choices',[{}])[0]
    message=choice.get('message',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('connected_plan_retained_attempted')
            or result.get('bounded_stop')!='output' or accepted.get('candidate')!=SOURCE
            or choice.get('finish_reason')!='length' or message.get('role')!='assistant'
            or not message.get('content') or message.get('tool_calls')
            or response.get('usage',{}).get('completion_tokens')!=16384):
        raise Halt('Require the exact accepted source and no-tool planning output boundary')


class RetainedConnectedPlan(ResolveDeathPixels):
    def validate_recovery(self,old):
        path=self.store.root/'private/sessions'/(PRIOR+'-next-connected-plan')/'response-000.json'
        if sha(path.read_bytes())!=RESPONSE_SHA:raise Halt('Retained private plan response changed')
        response=read_json(path);validate_boundary(old,response)
        self.retained_plan=response['choices'][0]['message']
        self.native_result=old['player_death_green_outcome']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(connected_plan_retained_attempted=True,recovery_route='retained-local-next-design',
            retained_plan_response_sha256=RESPONSE_SHA,
            recovery_change='The actual xhigh planner used16384output tokens without a tool submission. '
            'Preserve its response privately and reuse it in the next context. The continuation asks '
            'for submit_plan, not nonexistent source-edit tools. Model, xhigh, output budget, sampling, '
            'resource/ownership guards, accepted checkpoint, counters and cap are unchanged.')

    def work(self):
        ident=self.begin(TASK,'local-retained-next-connected-plan')
        self.next_plan(ident)


if __name__=='__main__':raise SystemExit(main(RetainedConnectedPlan))
