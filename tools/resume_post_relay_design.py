#!/usr/bin/env python3
"""Continue the qualified relay with a bounded local pacing/HUD design."""
import json
from resume_ordered_relay import OrderedRelay
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

SOURCE='8ef71373663d49349ce8a74827b27e64036614e1'
ROUND='q0111-673150bb'
ACCEPTED='c9bbf1acc28a26c2a0d06a83da4d3b2b44cde188'
FIELDS=('next_playable_increment','fixed_physical_scope','actual_api_and_state','positive_and_red_proofs','consolidated_hud','pacing_dependencies')

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Relay qualification recorded; continue measured gameplay and broad visual work under existing authority')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('post_relay_design_attempted'):
        raise Halt('Require exact qualified relay checkpoint/history')
    if not old.get('relay_outcome',{}).get('accepted'):raise Halt('Preserve an unqualified relay outcome')

class PostRelayDesign(OrderedRelay):
    def validate_recovery(self,old):
        validate_pause(old)
        e=self.store.root/'evidence'/(ROUND+'-positive');g=read_json(e/'relay-gate.json')
        regs=g.get('regressions',{}).get('regressions',[])
        if not g.get('passed') or len(regs)!=10 or not all(v['gate'].get('passed') for v in regs):
            raise Halt('Require full current-source relay and regression proof')
        verify_seal(e/'captures',sha((e/'captures/manifest.json').read_bytes()))

    def recovery_settings(self):
        return dict(post_relay_design_attempted=True,recovery_route='local-next-gameplay-and-consolidated-HUD',
            recovery_change='Preserve qualified relay; local next measurable varied gameplay plan and one-primary-objective HUD. Shared M5 checks remain active; other authorized workloads untouched.')

    def work(self):
        task=dict(id='post-relay-design',phase='mission',checks=[],maximum=100,coverage='mission-core')
        ident=self.begin(task,'local-next-playable-increment');self.store.report()
        source='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in
            ['Assets/Game/RelaySequence.cs','Assets/Game/RelaySequence.Hud.cs','Assets/Game/Combat.cs','Assets/Game/Mission.cs'])
        self.c.update(output_tokens=6144,model_timeout_seconds=330)
        def submit(_,f):
            if set(f)!=set(FIELDS) or any(not isinstance(v,str) or not 30<=len(v)<=1500 for v in f.values()):
                raise ValueError('Return six concise implementable fields,30..1500characters each')
            return dict(ok=True,**f)
        plan=self.model.session('planner',ident+'-next-design',
            'You are local Qwen, substantive game designer. Submit one concrete next increment with actual APIs.',
            'The three-site relay is QUALIFIED. Actual ordinary-input whole progression ends59.633seconds; relay '
            'adds27.100seconds after east cache32.533seconds. Acceptance waited until83seconds only to test '
            'ending/reset; that waiting is NOT content. Need the next materially different playable objective '
            'toward540..660seconds, not another relabeled box/F sequence, idle timer or repeated empty lap. '
            'Propose one bounded objective with concrete actions, failure/retry, fixed physical anchors and '
            'game-owned observable progress. Actual connected space is coreX-1..6/Z-2..30, alleyX6..22/Z8..20, '
            'eaststreetX22..60/Z8..28; closed facade doors are not interiors. Existing original meshes may be '
            'reused; no downloaded assets or primitives. If expansion is needed, state its exact next rectangle, '
            'connection and walking/driving collision proof separately. Do not claim new enemies/doors/APIs '
            'exist; use provided source and mark exact new components/install hooks. Preserve all earlier '
            'game-state/reset contracts. No writes to protected legacy signals to fake outcomes. '
            'Also specify ONE primary objective panel plus separate health/wanted panel, replacing the current '
            'simultaneous delivery/cache/relay banners. It must show actual stage transitions and next action, '
            'readable distance/control hints, scoped endings/failure and correct reset. Compact completed-stage '
            'receipts may be a single footer; no four competing cards. Mechanics must remain unchanged for HUD '
            'work. Preserve the exact visible truths "grab", "parcel in hand", "delivery complete", "dead-drop" '
            'and "relay" in their appropriate phases; old presentation layout may be superseded by explicit '
            'new measured panel/legibility checks, not by hiding state errors. '
            'Do not claim unmeasured duration or route-choice variation. Give estimated increment duration as '
            'unmeasured and name the remaining physical/action dependencies needed for ten minutes. '
            'Write concise final decisions only; call submit_plan now.\nACTUAL SOURCE:\n'+source,
            [tool('submit_plan','Save the next gameplay and consolidated-HUD decision.',{k:{'type':'string'} for k in FIELDS})],
            {'submit_plan':submit},turns=1,reasoning_effort='low')
        e=self.store.root/'evidence'/ident;e.mkdir(exist_ok=True);atomic(e/'post-relay-plan.json',plan)
        self.store.set(post_relay_plan=plan,post_relay_plan_evidence=str(e.relative_to(self.store.root)));self.store.report()
        if not plan.get('ok'):raise Halt('Next playable design was not submitted')
        raise Halt('Next gameplay and HUD plan saved; continue authorized consolidated HUD implementation')

if __name__=='__main__':raise SystemExit(main(PostRelayDesign))
