#!/usr/bin/env python3
"""Resolve a pixel-review disagreement without changing working gameplay."""
import json
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from resume_camera_native_only import ACCEPTED
from review_player_death_integration import SOURCE, require_complete_native
from continue_game_queue import validate_scoped_review
from loop_controller.core import Halt, atomic, read_json, sha, now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.visual_context import TARGETS, contract

PRIOR='q0154-e7e1e7f0'
TASK=dict(id='death-pixel-evidence-resolution',phase='mission',visual_facing=True,
    outcome='Correct the disproven cloud obstruction claim and local reset-frame citation')
S={'type':'string'}
DEATH='interception-final/frame-001.png'
RESET='interception-final/frame-003.png'
HASHES={
    'q0152-4bb1d76f-courier-pickup/captures/frame-001.png':'0b8d5b29cb9b3fea3c09156c00b40d2f6b36a061dca3295484c63b78dee6d4a7',
    'q0153-94519238-interception-final/captures/frame-001.png':'694c2bd732bf9dd5174afae34eceeed439d4cece5d58f52383b9ff67578091e3',
    'q0153-94519238-interception-final/captures/frame-003.png':'3952655393706749a991cdae5ef0d62ae284b34095b9cad4b9ce28b6770b403d',
}


def compare_masks(first,second):
    from PIL import Image
    masks=[]
    for path in (first,second):
        im=Image.open(path).convert('RGB')
        if im.size!=(960,540):raise Halt('Expected original native960x540evidence')
        pixels=im.load()
        masks.append({(x,y) for y in range(30,124) for x in range(420,810)
            if pixels[x,y][0]>130 and pixels[x,y][0]>2*pixels[x,y][1]
            and pixels[x,y][0]>2*pixels[x,y][2]})
    a,b=masks
    return dict(region_xyxy=[420,30,810,124],criterion='R>130 and R>2G and R>2B, RGB8',
        first_red_pixels=len(a),second_red_pixels=len(b),matching=len(a&b),
        first_only=len(a-b),second_only=len(b-a),
        passed=len(a)==1831 and a==b)


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        player_death_review_attempted=True,
        blocker='Halt: Death mechanics pass; late HUD glyph obstruction requires focused local rendering repair before promotion')
    review=old.get('player_death_review_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('death_pixel_resolution_attempted')
            or review.get('candidate')!=SOURCE or review.get('scoped_accepted') is not False
            or not review.get('review',{}).get('ok') or review['review'].get('verdict')!='PASS'):
        raise Halt('Require the exact native-green/local-PASS disagreement without changing source/history')
    require_complete_native(old.get('player_death_green_outcome',{}))


def confirm_review(fields):
    checked=validate_scoped_review(fields,[DEATH,RESET],{DEATH:75.65,RESET:79.4})
    if checked['verdict']=='PASS' and (
            fields['death_frame']!=DEATH or fields['death_health']!=0
            or fields['reset_frame']!=RESET or fields['reset_health']!=100):
        raise ValueError('A PASS must identify the observed health values and correct actual frame labels')
    return checked


class ResolveDeathPixels(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.native_result=old['player_death_green_outcome']
        self.review_path=self.store.root/'evidence'/(PRIOR+'-death-review.json')
        if read_json(self.review_path)!=old['player_death_review_outcome']:
            raise Halt('Preserve the actual previous local review')
        self.proof={self.review_path:sha(self.review_path.read_bytes())}
        for name,digest in HASHES.items():
            path=self.store.root/'evidence'/name
            if sha(path.read_bytes())!=digest:raise Halt('Original actual pixel evidence changed')
            self.proof[path]=digest
        paths=list(HASHES)
        self.comparison=compare_masks(self.store.root/'evidence'/paths[0],self.store.root/'evidence'/paths[1])
        if not self.comparison['passed']:raise Halt('Do not retract the cloud suspicion without the exact foreground comparison')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(death_pixel_resolution_attempted=True,recovery_route='preserved-review-pixel-disagreement',
            recovery_change='The full1831pixel red glyph masks are identical in early/late death captures. '
            'Retract the cloud clipping suspicion, retain the original disagreement, and correct local '
            'frame attribution with two actual images. No game edits or native replay changes.')

    def work(self):
        ident=self.begin(TASK,'local-death-frame-attribution-review')
        before=self.store.root/'evidence/q0153-94519238-interception-final/captures'
        images=[('ACTUAL '+DEATH+';75.65seconds; before R',before/'frame-001.png'),
            ('ACTUAL '+RESET+';79.4seconds; after ordinary R',before/'frame-003.png'),
            ('CHICAGO TARGET; aspiration only',self.refs/TARGETS[0])]
        self.c.update(working_context_tokens=65536,output_tokens=16384,model_timeout_seconds=600)
        fields={'verdict':S,'summary':S,'fixes':{'type':'array','items':S},
            'death_frame':S,'death_health':{'type':'integer'},
            'reset_frame':S,'reset_health':{'type':'integer'}}
        result=self.model.session('critic',ident+'-frame-label-review',
            'You are a fresh local visual critic. Inspect the actual supplied pixels and identify their states precisely.',
            'Prior local criticism gave scoped PASS but mistakenly called the living reset image '
            'courier-pickup/frame-001.png at7.65seconds. That early image actually has HEALTH0. '
            'Here are ONLY the two relevant actual interception images, uniquely labeled: before R at75.65s '
            'and after ordinary R at79.4s. Read the health and mission panel from each; return exact labels '
            'and observed numeric health. Confirm whether the full death/R-restart text is readable and '
            'whether reset restores living objective text without stale death copy. Do not infer animations '
            'or ten-minute quality from stills. All six source-matched death cases, healthy route and ten '
            'regressions already pass. Direct comparison independently found identical1831pixel glyph '
            'foregrounds between early and late death images, so the cloud clipping suspicion is retracted. '
            'Judge the pixels yourself; this is a scoped attribution/readability check, not final art '
            'acceptance. Cite both actual filenames/times and submit_review. Original rough art remains unfinished.',
            [tool('submit_review','Correct actual frame attribution and return scoped verdict.',fields)],
            {'submit_review':lambda _,f:confirm_review(f)},images=images,
            visual_contract=contract(images,[TARGETS[0]],2),turns=3,reasoning_effort='xhigh')
        if (any(sha(p.read_bytes())!=h for p,h in self.proof.items())
                or git(self.repo,'rev-parse','HEAD')!=SOURCE or git(self.repo,'status','--porcelain')):
            raise Halt('Source or external proof changed during read-only resolution')
        outcome=dict(candidate=SOURCE,comparison=self.comparison,review=result,
            original_cloud_suspicion_preserved=True,cloud_obstruction_claim_retracted=True,
            original_local_review_preserved=True,game_source_changed=False,
            scoped_accepted=bool(result.get('ok') and result.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(self.store.root/'evidence'/(ident+'-pixel-resolution.json'),outcome)
        self.store.set(death_pixel_resolution_outcome=outcome);self.store.report()
        if not outcome['scoped_accepted']:raise Halt('Preserve corrected cloud finding; actual local attribution review needs follow-up')
        self.store.set(player_death_scoped_acceptance=dict(candidate=SOURCE,accepted_utc=now(),
            scope='zero-health controls, chapter gating and immediate failure/reset HUD',
            evidence=ident+'-pixel-resolution.json',native_evidence='q0153-94519238-player-death-green.json',
            prior_playable_checkpoint=ACCEPTED,final_game_accepted=False),last_playable_checkpoint=SOURCE)
        self.store.event('scoped-death-checkpoint-promoted',candidate=SOURCE,
            preserved_task_index=7,preserved_task_failures=24,preserved_failure_streak=1)
        self.store.report()
        self.next_plan(ident)

    def next_plan(self,ident):
        fields=['next_actions','exact_physical_scope','source_interfaces','failure_retry_and_ending',
            'native_acceptance','measured_pacing_limits']
        context='\n\n'.join(name+'\n'+(self.project/'Assets/Game'/name).read_text() for name in
            ['InterceptionMission.cs','RouteMission.cs','RelaySequence.cs','MissionDirectorHud.cs','DeathAuthority.cs'])
        def save(_,data):
            if set(data)!=set(fields) or any(not isinstance(x,str) or not 40<=len(x)<=2000 for x in data.values()):
                raise ValueError('Six concrete decision fields,40..2000characters each')
            return dict(ok=True,local_authored=True,**data)
        self.c.update(working_context_tokens=65536,output_tokens=16384,model_timeout_seconds=600)
        self.store.set(stage='local-next-connected-gameplay-plan');self.store.report()
        result=self.model.session('planner',ident+'-next-connected-plan',
            'You are local Qwen, the substantive game designer. Save one implementable next connected increment.',
            'Existing Chicago courier, dead drop, relay and moving interception pass their healthy route '
            'and zero-health boundaries. Actual gameplay completion is about75seconds; the95second replay '
            'includes validation/reset. The target remains540..660seconds of varied playable action. '
            'Define one next substantial objective after interception using current exact APIs and existing '
            'original coupe/props, walking, driving and combat. Do not repeat implemented dead-drop/relay '
            'or add idle waits, empty laps or renamed F boxes. Core space isX-1..6/Z-2..30, '
            'alleyX6..22/Z8..20, eaststreetX22..60/Z8..28 with barriers. Use rendered connected space and '
            'measured collision; invisible ground and closed facades are not playable interiors. Specify '
            'activation, owned state, meaningful player choices, ordinary R and zero-health behavior, '
            'ending/failure, real positive and adverse input proof. No new assets/downloads or code edits '
            'in this planning step. Preserve current camera/reticle and verified contracts. Keep estimates '
            'distinct from measured play time and identify remaining route/variation for ten minutes. '
            'Return concise user-facing final decisions through submit_plan, not hidden reasoning. '
            'Prior gameplay completions:'+json.dumps(self.native_result['positive'].get('interception',{}).get('completions',[]))+
            '\nCURRENT EXACT CHAPTER/DEATH APIs:\n'+context,
            [tool('submit_plan','Save one implementable connected gameplay scope.',{k:S for k in fields})],
            {'submit_plan':save},turns=3,reasoning_effort='xhigh',
            retained_assistant=getattr(self,'retained_plan',None))
        atomic(self.store.root/'evidence'/(ident+'-next-connected-plan.json'),result)
        self.store.set(next_connected_expansion=result);self.store.report()
        if not result.get('ok'):raise Halt('Death repair accepted; retain the bounded next-plan result for focused continuation')
        raise Halt('Death repair accepted and next local connected scope saved; seal acceptance and continue implementation')


if __name__=='__main__':raise SystemExit(main(ResolveDeathPixels))
