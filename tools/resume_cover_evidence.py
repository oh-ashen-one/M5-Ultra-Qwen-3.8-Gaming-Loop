#!/usr/bin/env python3
"""Supply the missing cover views using an immutable copy of the qualified game."""
import json
import shutil
import uuid
from resume_aim_qualification import AimQualification,ACCEPTED
from resume_three_day_queue import ThreeDayRunner,main
from loop_controller.core import Halt,atomic,read_json,sha,seal,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.aim_checks import AIM_PROBES,inspect_aim_contract
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.review_summary import compact_rows
from continue_game_queue import validate_scoped_review

QUALIFIED='1295417194c0f2cdf9716982df06afebd6336c57'
PREFIX='aim-qualification-5c2a0076-after-'


def validate_cover_pause(old):
    if (old.get('last_playable_checkpoint')!=ACCEPTED or old.get('task_index')!=6
            or old.get('task_failures')!=4 or old.get('failure_streak')!=2
            or old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH or old.get('blocker')!='Halt: Requested stop'
            or old.get('aim_review',{}).get('verdict')!='UNVERIFIED'):
        raise Halt('Expected the preserved cover-image handoff; do not clear unrelated faults')


class CoverEvidenceResume(ThreeDayRunner):
    def validate_recovery(self,old):validate_cover_pause(old)
    def recovery_settings(self):return {'cover_evidence_pending':True}

    def work(self):
        ident='aim-cover-evidence-'+uuid.uuid4().hex[:8]
        original=self.store.root/'evidence'/(PREFIX+'aligned')/'project'
        snapshot=self.store.root/'private'/ident
        shutil.copytree(original,snapshot,ignore=shutil.ignore_patterns('Library','Temp','obj','Logs','UserSettings','.git'))
        copied_harness=snapshot/'Assets/LoopHarness'
        if not copied_harness.is_dir():raise Halt('Expected only the copied external harness')
        shutil.rmtree(copied_harness)
        # The source under review is the already qualified candidate, even if
        # the interrupted route role saved later source. Do not overwrite it.
        for p in (snapshot/'Assets/Game').glob('*.cs'):
            expected=git(self.repo,'show',QUALIFIED+':game/Assets/Game/'+p.name)
            if p.read_text().rstrip()!=expected.rstrip():raise Halt('Immutable qualification source mismatch')
        probe=AIM_PROBES['near-cover']
        bundle=self.store.root/'evidence'/ident
        self.store.set(stage='native-cover-visible-edge');self.store.report()
        gate=self.engines.unity(snapshot,bundle,probe,QUALIFIED)
        if not gate.get('passed'):raise Halt('Cover evidence runtime failed: '+str(gate.get('failure')))
        events=[json.loads(x) for x in (bundle/'captures/aim-shots.jsonl').read_text().splitlines()]
        contract=inspect_aim_contract(events,'near-cover')
        contract.update(candidate=QUALIFIED,evidence=str(bundle.relative_to(self.store.root)),
                        build_id=gate['build_id'],acceptance_fixture=probe['fixture'])
        atomic(bundle/'aim-contract.json',contract)
        seal(bundle/'captures',{'candidate':QUALIFIED,'scope':'near-cover-visible-edge'})
        if not contract['passed']:raise Halt('Reframed cover must still block actual shots: '+str(contract['failure']))
        results=[read_json(self.store.root/'evidence'/(PREFIX+kind)/'aim-contract.json')
                 for kind in ('aligned','miss','wall')]+[contract]
        frames=[];names=[];seals=[]
        selections=[('aligned',self.store.root/'evidence'/(PREFIX+'aligned'),2,7.55),
                    ('miss',self.store.root/'evidence'/(PREFIX+'miss'),2,8.65),
                    ('wall',self.store.root/'evidence'/(PREFIX+'wall'),2,8.0),
                    ('near-cover-before',bundle,1,6.9),('near-cover-after',bundle,2,7.55)]
        for name,parent,index,seconds in selections:
            captures=parent/'captures';digest=sha((captures/'manifest.json').read_bytes())
            verify_seal(captures,digest);seals.append((captures,digest))
            label=name+'-frame-'+str(index).zfill(3)+'.png';names.append(label)
            frames.append((label+'; ACTUAL native capture at t='+str(seconds),captures/('frame-'+str(index).zfill(3)+'.png')))
        cover_events={}
        for name,parent in [('wall',self.store.root/'evidence'/(PREFIX+'wall')),('near-cover',bundle)]:
            cover_events[name]=[json.loads(x) for x in (parent/'captures/aim-shots.jsonl').read_text().splitlines()]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='fresh-complete-cover-review');self.store.report()
        result=self.model.session('critic',ident+'-critic',
            'You are a fresh local visual critic of actual camera aim, misses and cover.',
            'The earlier review lacked the wall frame and the near cover filled the view. This packet supplies the '
            'missing actual wall image, a visible near-cover edge, a pre-cover control view, and per-shot geometry/HP. '
            'Reassess from this evidence; PASS, FIX or UNVERIFIED are all allowed. Do not infer success from counts alone. '
            'The opaque cover should hide the part of the rival behind it; use the open control view and actual '
            'first-ray collider/target intersection to assess occlusion. Both cover fixtures are disposable external '
            'test objects, not shipped game art. The source under review remains unchanged1295417. The harness records '
            'camera position/forward before gameplay, excludes only the shooter hierarchy and current vehicle, and '
            'records target HP after the shot. No actor or camera is moved by this observation. '
            'Judge aligned real damage, deliberate misses, nearer wall and near-origin cover. Rough art and audio '
            'quality remain outside this scope. Cite supplied image names and give up to five fixes only if needed. '
            '\nCONTRACTS:'+json.dumps(compact_rows(results))+'\nEXACT COVER SHOTS:'+json.dumps(compact_rows(cover_events)),
            [tool('submit_review','Return scoped evidence verdict.',
                {'verdict':{'type':'string','enum':['PASS','FIX','UNVERIFIED']},'summary':{'type':'string'},
                 'fixes':{'type':'array','items':{'type':'string'}}})],
            {'submit_review':lambda _,f:validate_scoped_review(f,names)},images=frames,turns=2,reasoning_effort='xhigh')
        for captures,digest in seals:verify_seal(captures,digest)
        atomic(bundle/'critic.json',result)
        self.store.set(cover_evidence_pending=False,aim_cover_evidence=str(bundle.relative_to(self.store.root)),
                       aim_complete_review=result)
        feedback=self.store.get('feedback',{})
        feedback.update(aim_contracts=results,aim_review=result,
            route_instruction='Cover imagery was an external evidence issue, now separately reviewed. Preserve the qualified camera ray. Finish the ordinary-input route using accepted on-foot firing geometry and measured pickup, driving, failure/retry and ending inputs. Do not alter hit radius or mission geometry to compensate for a missed replay.')
        self.store.set(feedback=feedback);self.store.report()
        if not result.get('ok'):raise Halt('Complete cover review remained incomplete; preserve original and new evidence')
        self.store.event('cover-evidence-review-complete',candidate=QUALIFIED,review=result.get('verdict'),
                         original_review_preserved=True,counters_preserved=True,source_overwritten=False)
        return super().work()


if __name__=='__main__':raise SystemExit(main(CoverEvidenceResume))

