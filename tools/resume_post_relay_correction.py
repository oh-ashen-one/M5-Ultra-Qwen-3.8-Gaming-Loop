#!/usr/bin/env python3
"""Preserve the rejected local proposal; correct concrete API/pacing contradictions."""
import json
from resume_post_relay_design import PostRelayDesign,SOURCE,ACCEPTED,TASK,FIELDS
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

ROUND='q0112-b65a06fe'
RESPONSE_SHA='5e1fe3b6d4d9411abe3258a6397575d7b431facddbf62ec0caf6b0655f5f0fdb'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        post_relay_metadata_repaired=True,blocker='Halt: Next playable design was not submitted')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('post_relay_correction_attempted'):
        raise Halt('Require exact bounded proposal-validation stop and unchanged source/history')

def proposal(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original local proposal response changed')
    choice=json.loads(raw)['choices'][0];calls=choice['message'].get('tool_calls') or []
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='submit_plan':
        raise Halt('Require complete public local proposal tool arguments')
    value=calls[0]['function']['arguments'];value=json.loads(value) if isinstance(value,str) else value
    if set(value)!=set(FIELDS) or any(not isinstance(v,str) or len(v)>4500 for v in value.values()):
        raise Halt('Malformed original proposal')
    return value

class PostRelayCorrection(PostRelayDesign):
    def original(self):
        return (self.store.root/'private/sessions'/(ROUND+'-next-design')/'response-000.json').read_bytes()

    def validate_recovery(self,old):
        validate_pause(old);proposal(self.original())

    def recovery_settings(self):
        return dict(post_relay_correction_attempted=True,recovery_route='bounded-local-pacing-api-correction',
            recovery_change='Preserve rejected complete public proposal; correct duplicate timing, impossible runner duration, double fire/incorrect death target, reset gating and HUD interference before any encounter source.')

    def work(self):
        ident=self.begin(TASK,'local-corrected-next-gameplay-plan');e=self.store.root/'evidence'/ident
        atomic(e/'rejected-local-proposal.json',dict(accepted=False,response_sha256=RESPONSE_SHA,
            draft=proposal(self.original()),private_reasoning_used=False))
        self.c.update(output_tokens=3072,model_timeout_seconds=190)
        def submit(_,f):
            if set(f)!={'next_increment','implementation_dependencies'} or any(not isinstance(v,str) or not 30<=len(v)<=1400 for v in f.values()):
                raise ValueError('Two concise fields only, each30..1400characters')
            return dict(ok=True,**f,measured_current_route_seconds=59.633335114,
                measured_relay_seconds=27.100002289,proposed_increment_measured=False,implementation_approved=False)
        prompt=('Your complete moving-runner proposal was rejected by field-length validation and has these factual defects. '
            'Correct it in TWO short fields, each under1400characters. No code or long API listing. '
            'Measured current TOTAL59.633seconds already INCLUDES27.100seconds relay; do not add it again. '
            'Three simultaneous runners X24->58 at1.6m/s leak after21.25seconds, not60..110seconds. '
            'Keep one bounded moving-target encounter, report duration UNMEASURED, and do not pad with waits/waves '
            'or claim it approaches ten minutes. Scope east street X22..60/Z8..28; anchors require actual clearance. '
            'Actual Combat.HandleFire already damages ANY first-hit RivalAgent on each fresh Mouse0. Adding another '
            'fire handler would double damage. Its death branch currently disables the original rivalGo even if '
            'another RivalAgent was hit: this needs a scoped local-author repair plus original combat regressions '
            'BEFORE any multi-target implementation. Do not claim it is already reusable unchanged. '
            'Current source uses dynamic gravity Rigidbody, not your claimed byte-identical kinematic movement. '
            'New runner movement requires swept collision/grounding proof, not raw transform+= through props. '
            'R resets the WHOLE mission: new stage must clear/hide and wait for NEW RelaySequence.AllComplete, '
            'not immediately rearm. One authoritative damage owner; actualhp->0 only once incrementskill. '
            'New death handling, leak exclusion, wall/miss/held-fire, nohandoff and reset all need red proofs. '
            'HUD is separate first implementation: one MissionBoard plus existing HudStatus, selecting actual '
            'courier/cache/relay state. Do NOT clear other writers\' text or deactivate scripts: read their actual '
            'state/text, then suppress only their renderer cards after updates. Preserve truthful compact receipts. '
            'Call submit_plan NOW with next_increment (concrete actions, anchors, failure/reset, unmeasuredduration) '
            'and implementation_dependencies (realAPI repairs/proofs, HUD first, remaining ten-minute gap).')
        plan=self.model.session('planner',ident+'-corrected-plan',
            'You are local Qwen correcting your gameplay proposal. Be concise and submit the requested two-field decision.',
            prompt,[tool('submit_plan','Save a corrected concise next gameplay plan.',
                {k:{'type':'string'} for k in ['next_increment','implementation_dependencies']})],
            {'submit_plan':submit},turns=1,reasoning_effort='low')
        atomic(e/'corrected-pacing-plan.json',plan)
        self.store.set(corrected_post_relay_plan=plan,corrected_post_relay_plan_evidence=str(e.relative_to(self.store.root)))
        self.store.report()
        if not plan.get('ok'):raise Halt('Corrected local plan remains unsubmitted; preserve bounded response')
        raise Halt('Corrected next gameplay plan saved; continue authorized consolidated HUD implementation')

if __name__=='__main__':raise SystemExit(main(PostRelayCorrection))
