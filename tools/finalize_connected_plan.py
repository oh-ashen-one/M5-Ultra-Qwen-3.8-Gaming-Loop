#!/usr/bin/env python3
"""Save an actual final local design, rejecting a bare claim that it was saved."""
import json
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from resolve_death_pixel_review import SOURCE
from loop_controller.core import Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

PRIOR='q0156-d1f986e9'
RESPONSE_SHA='aa06d07f6a15e04c35a2208428546a587600add0b281c02861e91a1e0879ca46'
FIELDS=['next_actions','exact_physical_scope','source_interfaces','failure_retry_and_ending',
    'native_acceptance','measured_pacing_limits']
TASK=dict(id='connected-plan-final-submission',phase='mission',visual_facing=False,
    outcome='Save concrete final local design fields from retained private work')


def validate_plan(data):
    if (not isinstance(data,dict) or set(data)!=set(FIELDS)
            or any(not isinstance(x,str) or not 40<=len(x)<=2000 for x in data.values())):
        raise ValueError('Return exactly six concrete final decision fields,40..2000characters each')
    return dict(ok=True,local_authored=True,**data)


def final_text_plan(text):
    return validate_plan(json.loads(text))


def validate_boundary(old,response):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        connected_plan_retained_attempted=True,
        blocker='Halt: Death repair accepted; retain the bounded next-plan result for focused continuation')
    value=old.get('next_connected_expansion',{})
    choice=response.get('choices',[{}])[0];message=choice.get('message',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('connected_plan_final_attempted')
            or set(value)!={'summary'} or not value['summary'].startswith('Plan saved:')
            or choice.get('finish_reason')!='stop' or message.get('tool_calls')
            or message.get('content')!=value['summary']):
        raise Halt('Require the exact non-tool completion claim; no existing concrete plan may be overwritten')


class FinalConnectedPlan(CapacityAuthor):
    def validate_recovery(self,old):
        p=self.store.root/'private/sessions'/(PRIOR+'-next-connected-plan')/'response-000.json'
        if sha(p.read_bytes())!=RESPONSE_SHA:raise Halt('Prior private local work changed')
        response=read_json(p);validate_boundary(old,response)
        self.retained=response['choices'][0]['message']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(connected_plan_final_attempted=True,recovery_route='actual-final-design-not-completion-claim',
            recovery_change='Preserve the prior217character saved-claim and its private retained work. '
            'Ask for six actual concise final decision fields, accepting either a real submit_plan tool '
            'or strict complete JSON final content. Reject bare saved claims and partial JSON. Same '
            'xhigh/model/budgets/guards; no game-edit tools or invented planning result.')

    def work(self):
        ident=self.begin(TASK,'local-final-connected-design')
        context='\n\n'.join(name+'\n'+(self.project/'Assets/Game'/name).read_text() for name in
            ['InterceptionMission.cs','RouteMission.cs','RelaySequence.cs','MissionDirectorHud.cs','DeathAuthority.cs'])
        self.c.update(working_context_tokens=65536,output_tokens=16384,model_timeout_seconds=600)
        result=self.model.session('planner',ident+'-final-design',
            'You are local Qwen. Deliver the actual final design as six concise user-facing decision fields.',
            'Your retained design concerns one post-interception counter-exfil objective using the original '
            'coupe and measured east/alley/core corridors, pin/block collision, combat and foot western-line '
            'completion. Keep that selected concept; do not design another mission or write implementation '
            'code now. No structured plan or tool submission was actually saved by the last response. '
            'Its statement "Plan saved" was only text and did not save a plan. Supply the actual six '
            'fields listed in the submit_plan schema. Aim for300..600characters per field and under4000 '
            'characters total. Return either a real submit_plan call OR one complete JSON object in your '
            'final content, without code fences or surrounding prose. Do not merely assert completion. '
            'Separate exact measured facts from estimates. Current gameplay is about75seconds;95second '
            'replay includes reset, and540..660seconds remains the goal. Use only current rendered space '
            '(coreX-1..6/Z-2..30, alleyX6..22/Z8..20, eastX22..60/Z8..28), actual collision and existing '
            'original actors/props. Preserve death/R, camera/reticle and old objective contracts. No '
            'new assets/downloads or game edits. Final decisions only, no private reasoning in fields. '
            '\nCURRENT EXACT APIs:\n'+context,
            [tool('submit_plan','Save the actual final six-field design.',{k:{'type':'string'} for k in FIELDS})],
            {'submit_plan':lambda _,f:validate_plan(f)},turns=2,reasoning_effort='xhigh',
            retained_assistant=self.retained,
            retained_instruction='No actual plan was saved: the prior final content was only a completion claim. '
                'Use your retained work without repeating the design. Thinking remains xhigh. NOW deliver '
                'the six concise final fields through a real submit_plan call or one complete final JSON '
                'object. Do not say the plan was saved and do not write code.')
        if not result.get('ok') and set(result)=={'summary'}:
            try:
                parsed=final_text_plan(result['summary'])
                parsed['submission_route']='strict-final-json-content'
                result=parsed
            except (ValueError,TypeError):
                pass
        atomic(self.store.root/'evidence'/(ident+'-final-connected-plan.json'),result)
        self.store.set(next_connected_expansion=result);self.store.report()
        if not result.get('ok'):raise Halt('Concrete local next-design submission still missing; preserve drafts and diagnose the real format failure')
        raise Halt('Death repair accepted and next local connected scope saved; seal acceptance and continue implementation')


if __name__=='__main__':raise SystemExit(main(FinalConnectedPlan))

