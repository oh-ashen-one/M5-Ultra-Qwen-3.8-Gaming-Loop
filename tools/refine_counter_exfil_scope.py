#!/usr/bin/env python3
"""Ground the next local objective in measured handoff and corridor evidence."""
import json
import math
from qualify_qwen_capacity import CapacityAuthor
from finalize_connected_plan import FIELDS,validate_plan,final_text_plan
from resolve_death_pixel_review import SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,atomic
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

PRIOR='q0157-fa2b8a3b'
TASK=dict(id='counter-exfil-scope-review',phase='mission',visual_facing=False,
    outcome='One grounded first counter-exfil incident with explicit handoff and unpadded pacing')


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        connected_plan_final_attempted=True,
        blocker='Halt: Death repair accepted and next local connected scope saved; seal acceptance and continue implementation')
    plan=old.get('next_connected_expansion',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_scope_review_attempted')
            or not plan.get('ok') or not plan.get('local_authored')):
        raise Halt('Require the concrete saved local proposal on the accepted unchanged game')
    validate_plan({k:plan.get(k) for k in FIELDS})


class RefineCounterExfil(CapacityAuthor):
    scope_context_tokens=65536
    scope_output_tokens=16384
    def validate_recovery(self,old):
        validate_boundary(old)
        self.proposal=old['next_connected_expansion']
        saved=read_json(self.store.root/'evidence'/(PRIOR+'-final-connected-plan.json'))
        if saved!=self.proposal:raise Halt('Original concrete proposal and ledger differ')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(counter_exfil_scope_review_attempted=True,recovery_route='measured-counter-exfil-scope',
            recovery_change='Preserve the first local proposal. Review its twelve-wave pacing, health/car '
            'handoff, unqualified lane assumptions and old completion contracts using actual existing '
            'native records. Local xhigh revises only the concise final plan; game edits remain unavailable.')

    def work(self):
        ident=self.begin(TASK,'local-grounded-counter-exfil-scope')
        bundle=self.store.root/'evidence/q0153-94519238-positive'
        gate=read_json(bundle/'gate.json')
        if not gate.get('passed') or gate.get('candidate_commit')!=SOURCE:
            raise Halt('Measured handoff requires current accepted-source native evidence')
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        end=min(rows,key=lambda x:abs(x['time']-77))
        crossings=[]
        for x in (6,22):
            for a,b in zip(rows,rows[1:]):
                if a.get('restarts',0) or b.get('restarts',0):continue
                if a.get('vehicle') and b.get('vehicle') and a['vehicle'][0]<x<=b['vehicle'][0]:
                    crossings.append(dict(gate_x=x,time=b['time'],vehicle=b['vehicle'],
                        mode=b['mode'],penetration=b.get('vehiclePenetration')));break
        facts=dict(source=SOURCE,time=end['time'],health=end['health'],player=end['player'],
            vehicle=end['vehicle'],mode=end['mode'],
            player_to_coupe_metres=math.dist(end['player'],end['vehicle']),vehicle_crossings=crossings,
            other_lanes='not yet qualified by actual swept physics/driving')
        atomic(self.store.root/'evidence'/(ident+'-handoff-facts.json'),facts)
        context='\n\n'.join(name+'\n'+(self.project/'Assets/Game'/name).read_text() for name in
            ['Combat.cs','VehicleInteraction.cs','InterceptionMission.cs','MissionDirectorHud.cs','DeathAuthority.cs'])
        self.c.update(working_context_tokens=self.scope_context_tokens,
            output_tokens=self.scope_output_tokens,model_timeout_seconds=600)
        result=self.model.session('planner',ident+'-scope-refinement',
            'You are local Qwen. Revise your selected counter-exfil proposal using concrete review findings.',
            'Keep the chosen counter-exfil concept and return only the same six concise final fields '
            '(300..600characters each, under4000characters total). A real submit_plan call or complete '
            'JSON final content is required, not a saved-claim. Do not write code or repeat broad design. '
            'Four prioritized review constraints: '
            '(1) Qualify ONE complete counter-exfil incident first, using your one lead/two standards and '
            'pin/shoot/foot-exfil choices. Twelve repetitions of three lanes do not establish varied '
            'ten-minute content. Keep540..660seconds as the eventual whole-game target, not a claimed '
            'duration from multiplication; further distinct actions remain future work. '
            '(2) Actual handoff has28health and the coupe about20metres away. Specify a reachable, '
            'input-driven handoff and when pressure begins, preserving genuine health/damage and avoiding '
            'a forced unobserved loss while retrieving the car. Do not grant a hidden heal or teleport. '
            '(3) Only central vehicle crossings have direct current-source proof. Specify exact first '
            'incident paths and live sweep/collision checks before assuming other lanes are traversable; '
            'empty400x400ground is not rendered route proof. Preserve all existing environment geometry. '
            '(4) Keep old interception completion/receipt, ordinary reset and six death contracts intact. '
            'Specify armed/active/complete state and ordinary activation so the previous healthy ending '
            'remains a real observable result, and define new HUD priority without rewriting old success '
            'counters or hiding old regressions. Use actual APIs: CurrentHealth is a method. '
            'No assets, source edits or inferred physics PASS.\nYOUR ORIGINAL FINAL PROPOSAL:\n'+
            json.dumps(self.proposal)+'\nACTUAL NATIVE FACTS:\n'+json.dumps(facts)+
            '\nCURRENT EXACT CONTROL/CHAPTER APIs:\n'+context,
            [tool('submit_plan','Save the reviewed final first-incident scope.',{k:{'type':'string'} for k in FIELDS})],
            {'submit_plan':lambda _,f:validate_plan(f)},turns=2,reasoning_effort='xhigh',
            retained_assistant=getattr(self,'retained_scope',None),
            retained_instruction=getattr(self,'retained_instruction',None))
        if not result.get('ok') and set(result)=={'summary'}:
            try:
                result=final_text_plan(result['summary']);result['submission_route']='strict-final-json-content'
            except (ValueError,TypeError):pass
        atomic(self.store.root/'evidence'/(ident+'-counter-exfil-reviewed-plan.json'),result)
        self.store.set(counter_exfil_reviewed_plan=result);self.store.report()
        if not result.get('ok'):raise Halt('Preserve original proposal and measured handoff; concise revised local scope not submitted')
        raise Halt('Reviewed local counter-exfil scope saved; implement and qualify the first complete incident')


if __name__=='__main__':raise SystemExit(main(RefineCounterExfil))
