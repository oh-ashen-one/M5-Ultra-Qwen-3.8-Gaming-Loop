#!/usr/bin/env python3
"""Review native-qualified death behavior and the observed late-HUD pixel defect."""
import json
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from resume_camera_native_only import ACCEPTED
from continue_game_queue import validate_scoped_review
from loop_controller.core import Halt, atomic, read_json, sha
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

    cloud_pixel_blockers=(
        "At interception-final/frame-001.png,75.65seconds, scene geometry obscures portions of "
        "the red death-message glyphs although the black card remains visible. Require the full "
        "message and R instruction to remain readable in this actual late-chapter camera view.",
    )

    def recovery_settings(self):
        return dict(player_death_review_attempted=True,recovery_route='native-qualified-death-pixel-review',
            recovery_change='Fresh local xhigh critic receives actual current-source early/late death, '
            'reset and healthy gameplay pixels plus Chicago target. No game-edit tools or checkpoint '
            'promotion. Preserve the observed late-view glyph obstruction even if the state trace '
            'reports visible text; record local criticism before the focused local rendering repair.')

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
            '\nACTUAL CAPTURE TIMES:'+json.dumps(times)+'\nCLOUD PIXEL OBSERVATION TO VERIFY:'+\
            json.dumps(self.cloud_pixel_blockers),
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
            scoped_accepted=False,cloud_pixel_blockers=list(self.cloud_pixel_blockers),
            final_game_accepted=False,known_limits=['Declared health injection is distinct from natural lethal damage.',
                'Current gameplay route is about75seconds;95second replay includes validation/reset.',
                'Art, lighting, audio and full ten-minute experience remain unfinished.'])
        atomic(self.store.root/'evidence'/(ident+'-death-review.json'),artifact)
        self.store.set(player_death_review_outcome=artifact);self.store.report()
        if not result.get('ok'):raise Halt('Death native proof and known pixel defect retained; local review needs bounded follow-up')
        raise Halt('Death mechanics pass; late HUD glyph obstruction requires focused local rendering repair before promotion')


if __name__=='__main__':raise SystemExit(main(ReviewDeath))
