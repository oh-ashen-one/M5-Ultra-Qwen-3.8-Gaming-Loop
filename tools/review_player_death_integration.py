#!/usr/bin/env python3
"""Review the fully qualified local death repair and plan the next connected task."""
import json
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from resume_camera_native_only import ACCEPTED
from continue_game_queue import validate_scoped_review
from loop_controller.core import Halt, atomic, read_json, sha, now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.player_death_checks import CASES
from loop_controller.runner import git
from loop_controller.visual_context import TARGETS, contract

SOURCE='d4d13937c63b9e056d3c40bf72fbf02e63eb3990'
PRIOR='q0153-94519238'
REGRESSIONS={'walk','world','motor','courier','failure-retry','combat-foot',
    'combat-wall','combat-driving','aim-miss','aim-near-cover'}
TASK=dict(id='player-death-integration-review',phase='mission',visual_facing=True,
    outcome='Fresh actual-pixel review after all six death cases and healthy regressions')
S={'type':'string'}


def require_complete_native(result):
    cases=result.get('cases',[])
    positive=result.get('positive',{})
    regression=result.get('regressions',{})
    if (result.get('candidate')!=SOURCE or len(cases)!=len(CASES)
            or {x.get('case') for x in cases}!=set(CASES)
            or any(not x.get('passed') or not x.get('setup_passed') or x.get('failure')
                or x.get('candidate')!=SOURCE or not x.get('build_id') or not x.get('evidence') for x in cases)
            or not isinstance(positive,dict) or not positive.get('passed')
            or positive.get('candidate_commit')!=SOURCE or positive.get('acceptance_fixture')
            or not isinstance(regression,dict) or not regression.get('passed')):
        raise Halt('Require all six source-matched deaths plus real healthy gameplay; no fixture promotion')
    rows=regression.get('regressions',[])
    if (len(rows)!=len(REGRESSIONS) or {x.get('test') for x in rows}!=REGRESSIONS
            or any(not x.get('gate',{}).get('passed')
                or x['gate'].get('candidate_commit')!=SOURCE for x in rows)):
        raise Halt('Require all ten unchanged source-matched native regressions')


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        death_hud_recognition_recovered=True,
        blocker='Halt: Local death repair passes six zero-health boundaries and healthy gameplay; inspect native failure/reset images')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('player_death_review_attempted'):
        raise Halt('Require the exact completed native boundary with preserved history')
    require_complete_native(old.get('player_death_green_outcome',{}))


class ReviewDeath(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.native_result=old['player_death_green_outcome']
        path=self.store.root/'evidence'/(PRIOR+'-player-death-green.json')
        if read_json(path)!=self.native_result:raise Halt('Native ledger and immutable result differ')
        self.native_path=path
        self.native_sha=sha(path.read_bytes())
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(player_death_review_attempted=True,recovery_route='native-qualified-death-pixel-review',
            recovery_change='Fresh local xhigh critic receives actual current-source early/late death, '
            'reset and healthy gameplay pixels plus Chicago target. No game-edit tools. Only a scoped '
            'PASS may record a known-playable death checkpoint; preserve failure counters and queue '
            'position. Then local xhigh plans one meaningful next connected increment using current APIs.')

    def work(self):
        ident=self.begin(TASK,'fresh-local-death-visual-review')
        selected=[('courier-pickup',1),('relay-final',1),('interception-final',1),
            ('interception-final',3),('positive',7)]
        cases={x['case']:self.store.root/'evidence'/x['evidence'] for x in self.native_result['cases']}
        cases['positive']=self.store.root/'evidence'/(PRIOR+'-positive')
        images=[];times={};proof={}
        for name,index in selected:
            bundle=cases[name];path=bundle/'captures'/f'frame-{index:03d}.png'
            label=name+'/'+path.name
            times[label]=read_json(bundle/'captures/scenario.json')['captures'][index]
            images.append((f'ACTUAL NATIVE {label}; t={times[label]} seconds',path))
            for p in (path,bundle/'captures/scenario.json',bundle/'captures/trace.jsonl',bundle/'gate.json'):
                proof[p]=sha(p.read_bytes())
        images.append(('AI-GENERATED CHICAGO TARGET; aspiration, not native output',self.refs/TARGETS[0]))
        required=contract(images,[TARGETS[0]],5)
        self.c.update(working_context_tokens=81920,output_tokens=16384,model_timeout_seconds=600)
        facts=dict(candidate=SOURCE,all_six_declared_death_cases_passed=True,
            healthy_route_and_ten_regressions_passed=True,natural_damage_death_not_proven_by_injection=True,
            same_source_compile_clean=True,original_hud_false_negative_preserved=True,
            visual_quality_unfinished=True,ten_minute_route_not_proven=True)
        result=self.model.session('critic',ident+'-death-critic',
            'You are a fresh local visual critic. Judge supplied actual pixels, then submit a concise scoped verdict.',
            'Assess immediate readable health-depleted failure and explicit R restart instructions across '
            'early and late mission states; check ordinary R restores the living HUD without stale death text. '
            'Check the healthy ending is legible and camera/reticle remain readable. The external native '
            'suite establishes movement/fire/objective gating and ordinary reset; still images cannot '
            'independently prove animation, input or natural lethal damage. Return PASS/FIX/UNVERIFIED for '
            'this death/HUD scope, not overall art. Compare the reference honestly: rough primitive art, '
            'lighting and short mission remain unfinished and must not be accepted as final. Cite actual '
            'case/filename or timestamp. List at most five prioritized concrete fixes; distinguish '
            'blocking death/HUD issues from broader unfinished quality. No editing or source-completion '
            'claim is possible here. Call submit_review.\nNATIVE FACTS:'+json.dumps(facts)+
            '\nACTUAL CAPTURE TIMES:'+json.dumps(times),
            [tool('submit_review','Record the fresh scoped visual verdict.',
                {'verdict':S,'summary':S,'fixes':{'type':'array','items':S}})],
            {'submit_review':lambda _,f:validate_scoped_review(f,list(times),times)},
            images=images,visual_contract=required,turns=3,reasoning_effort='xhigh')
        if (any(sha(p.read_bytes())!=digest for p,digest in proof.items())
                or sha(self.native_path.read_bytes())!=self.native_sha
                or git(self.repo,'rev-parse','HEAD')!=SOURCE or git(self.repo,'status','--porcelain')):
            raise Halt('Source or external native evidence changed during read-only review')
        artifact=dict(candidate=SOURCE,native_result=self.native_path.name,
            native_result_sha256=self.native_sha,review=result,frames=required['records'],
            scoped_accepted=bool(result.get('ok') and result.get('verdict')=='PASS'),
            final_game_accepted=False,known_limits=['Declared health injection is distinct from natural lethal damage.',
                'Current gameplay route is about75seconds;95second replay includes validation/reset.',
                'Art, lighting, audio and full ten-minute experience remain unfinished.'])
        atomic(self.store.root/'evidence'/(ident+'-death-review.json'),artifact)
        self.store.set(player_death_review_outcome=artifact);self.store.report()
        if not artifact['scoped_accepted']:raise Halt('Death native proof is complete; follow the actual fresh local visual verdict')
        self.store.set(player_death_scoped_acceptance=dict(candidate=SOURCE,accepted_utc=now(),
            evidence=ident+'-death-review.json',scope='zero-health controls, chapter gating and failure/reset HUD',
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
            'Existing Chicago courier, dead drop, relay and moving interception now pass their healthy route '
            'and zero-health boundaries. Actual gameplay completion is about75seconds; the95second replay '
            'includes validation and reset. The target remains540..660seconds of varied playable action. '
            'Define one next substantial objective after interception using current exact APIs and existing '
            'original coupe/props, walking, driving and combat. Do not repeat the already implemented '
            'dead-drop/relay or add idle waits, empty laps or renamed F boxes. Core space is '
            'X-1..6/Z-2..30, alleyX6..22/Z8..20, east streetX22..60/Z8..28 with barriers. '
            'Use rendered connected space and measured collision; invisible ground and closed facades '
            'are not playable interiors. Specify activation, owned state, meaningful player choices, '
            'ordinary R and zero-health behavior, ending/failure, real positive and adverse input proof. '
            'No new assets/downloads or code edits in this planning step. Preserve current camera/reticle '
            'and verified contracts. Keep estimates distinct from measured play time and identify the '
            'remaining route/variation needed for ten minutes. Return concise user-facing final decisions '
            'through submit_plan, not hidden reasoning.\nCURRENT EXACT CHAPTER/DEATH APIs:\n'+context,
            [tool('submit_plan','Save one implementable connected gameplay scope.',{k:S for k in fields})],
            {'submit_plan':save},turns=3,reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-next-connected-plan.json'),result)
        self.store.set(next_connected_expansion=result);self.store.report()
        if not result.get('ok'):raise Halt('Death repair accepted; retain the bounded next-plan result for focused continuation')
        raise Halt('Death repair accepted and next local connected scope saved; seal acceptance and continue implementation')


if __name__=='__main__':raise SystemExit(main(ReviewDeath))
