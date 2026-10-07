#!/usr/bin/env python3
"""Qualify real aim/miss/cover behavior before continuing the existing rough route."""
import json
import shutil
import uuid
from resume_three_day_queue import ThreeDayRunner,main
from loop_controller.core import Files,Halt,atomic,read_json,sha,seal,verify_seal
from loop_controller.aim_checks import AIM_PROBES,inspect_aim_contract
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.review_summary import compact_rows
from continue_game_queue import validate_scoped_review
from loop_controller.continuous_tasks import TASKS

SOURCE='6102a3ce76e714c09998d8801b9e046ca0b0d520'
ACCEPTED='c32cfeb7c512a1ce231eb2c7c29d9738c92ab004'


def validate_aim_pause(old):
    if (old.get('source_checkpoint')!=SOURCE or old.get('last_playable_checkpoint')!=ACCEPTED
            or old.get('task_index')!=6 or old.get('task_failures')!=3 or old.get('failure_streak')!=1
            or old.get('overall_deadline_epoch')!=HARD_CAP_EPOCH or old.get('blocker')!='Halt: Requested stop'):
        raise Halt('Expected the inspected aim-assist boundary handoff; preserve other states')


class AimQualification(ThreeDayRunner):
    def validate_recovery(self,old):validate_aim_pause(old)
    def recovery_settings(self):return {'aim_qualification_pending':True}

    def measure(self,ident,candidate):
        results=[]
        for kind,probe in AIM_PROBES.items():
            bundle=self.store.root/'evidence'/(ident+'-'+kind)
            self.store.set(stage='native-aim-'+kind,aim_probe=str(bundle.relative_to(self.store.root)));self.store.report()
            gate=self.engines.unity(self.project,bundle,probe,candidate)
            if not gate.get('passed'):
                raise Halt('Aim diagnostic runtime failed: '+str(gate.get('failure'))+' '+str(gate.get('compile_errors')))
            events=[json.loads(x) for x in (bundle/'captures/aim-shots.jsonl').read_text().splitlines()]
            contract=inspect_aim_contract(events,kind)
            contract.update(candidate=candidate,build_id=gate['build_id'],evidence=str(bundle.relative_to(self.store.root)),
                            acceptance_fixture=probe.get('fixture'))
            atomic(bundle/'aim-contract.json',contract)
            seal(bundle/'captures',{'candidate':candidate,'scope':'aim-'+kind})
            self.store.event('aim-contract-observed',**contract)
            results.append(contract)
        return results

    def local_ray_repair(self,ident,before):
        files=Files(self.project,self.store);path='Assets/Game/Combat.cs'
        lines=files.path(path).read_text().splitlines()
        starts=[i for i,line in enumerate(lines) if '// Fair third-person aim:' in line]
        if len(starts)!=1:raise Halt('Expected the measured wide-cast source block')
        start=starts[0]
        ends=[i for i in range(start,min(len(lines),start+16)) if '~0, QueryTriggerInteraction.Ignore);' in lines[i]]
        if len(ends)!=1:raise Halt('Expected one complete wide-cast query')
        edit=SelectedEdit(files,path,start+1,ends[0]+1,max_lines=5)
        self.c.update(output_tokens=2048,model_timeout_seconds=180)
        self.store.set(stage='local-aim-geometry-repair');self.store.report()
        self.model.session('builder',ident+'-ray-repair',
            'You are the sole local Qwen gameplay author. Save one selected-span correction.',
            'Restore the accepted camera-forward Physics.RaycastAll query using existing origin, dir, FIRE_RANGE, '
            'all layers and QueryTriggerInteraction.Ignore. Remove the0.85m sphere radius and its inaccurate explanation. '
            'Keep the existing var hits name and every following nearest-hit, damage, tracer, collision and input rule. '
            'The accepted on-foot replay already hit the rival twice with the original thin ray. The failed new replay '
            'fired toward a barrier or ahead of a driving car while the rival was behind it; wider bullets are not a '
            'substitute for correct camera/target geometry. No target/collider growth or telemetry shortcuts. '
            'Measured current-source aim contracts:\n'+json.dumps(compact_rows(before))+
            '\nExact selected source span:\n'+edit.old,
            [tool('edit_selected_span','Replace only the selected query block.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if sha(files.path(path).read_bytes())==edit.before:raise Halt('Local Qwen saved no aim correction')
        candidate=self.checkpoint_source('Local Qwen: restore visible camera ray after measured off-aim hits')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        self.store.event('local-aim-correction-saved',candidate=candidate,game_author='local Qwen')
        return candidate

    def review_aim(self,ident,candidate,results):
        frames=[];seals=[]
        for result in results:
            if result['scope']=='wall':continue
            captures=self.store.root/result['evidence']/'captures'
            manifest=sha((captures/'manifest.json').read_bytes());verify_seal(captures,manifest)
            seals.append((captures,manifest))
            frames.append((result['scope']+'-frame-002.png; ACTUAL native capture; t='+
                           str(AIM_PROBES[result['scope']]['captures'][2]),captures/'frame-002.png'))
        names=[kind+'-frame-002.png' for kind in ('aligned','miss','near-cover')]
        self.c.update(output_tokens=6144,model_timeout_seconds=400)
        self.store.set(stage='fresh-aim-image-review');self.store.report()
        result=self.model.session('critic',ident+'-critic',
            'You are a fresh local visual critic of real aim, intentional miss and cover evidence.',
            'Judge only fair camera-aligned combat in this rough game. Require an actual centered target hit, '
            'deliberate off-target shots causing no rival damage, and nearer cover blocking a target behind it. '
            'The near-cover image is a labeled disposable validation obstacle, never a shipped art improvement. '
            'Pre-shot observations record the camera used by gameplay before Follow changes it in LateUpdate. '
            'Screenshots are actual scheduled frames after that update, so do not invent exact shot-frame identity. '
            'Review visible alignment and the independent measured events together. Do not accept a hit count alone. '
            'The target visual bounds and collider ray must both align for damage. No final art or audio claim. '
            'Give PASS, FIX or UNVERIFIED with concise explanation and at most five fixes; cite supplied image names. '
            '\nCANDIDATE:'+candidate+'\nACTUAL CONTRACTS:'+json.dumps(compact_rows(results)),
            [tool('submit_review','Return scoped verdict.',
                  {'verdict':{'type':'string','enum':['PASS','FIX','UNVERIFIED']},'summary':{'type':'string'},
                   'fixes':{'type':'array','items':{'type':'string'}}})],
            {'submit_review':lambda _,f:validate_scoped_review(f,names)},images=frames,turns=2,reasoning_effort='xhigh')
        for captures,expected in seals:verify_seal(captures,expected)
        atomic(self.store.root/'evidence'/(ident+'-review.json'),result)
        return result

    def work(self):
        ident='aim-qualification-'+uuid.uuid4().hex[:8]
        before=self.measure(ident+'-before',SOURCE)
        self.store.set(aim_before_contracts=before);self.store.report()
        candidate=SOURCE
        if not all(x['passed'] for x in before):
            candidate=self.local_ray_repair(ident,before)
            after=self.measure(ident+'-after',candidate)
        else:after=before
        atomic(self.store.root/'aim-qualification-result.json',dict(before=before,after=after,candidate=candidate))
        self.store.set(aim_after_contracts=after,aim_qualification_pending=False)
        if not all(x['passed'] for x in after):
            feedback={'failure':[f for x in after for f in (x.get('failure') or [])],'aim_contracts':after}
            self.reject_scoped(TASKS[6],ident,feedback,candidate)
            raise Halt('Measured aim or cover remains unqualified; preserve all observations')
        review=self.review_aim(ident,candidate,after)
        self.store.set(aim_review=review)
        if not review.get('ok'):
            raise Halt('Fresh aim review incomplete; preserve source and exact native contracts')
        feedback=self.store.get('feedback',{})
        feedback.update(aim_contracts=after,aim_review=review,
            route_instruction='Preserve the qualified thin camera ray and all accepted mechanics. Correct the ordinary-input route: use the accepted on-foot shot alignment before entering the vehicle; do not fire forward at a rival behind the car. Reuse measured pickup/delivery anchors and the known passing failure/retry inputs. Do not expand hit radii to rescue a replay.')
        self.store.set(feedback=feedback)
        if review.get('verdict')!='PASS':
            self.reject_scoped(TASKS[6],ident,feedback,candidate)
        self.store.event('aim-qualification-continuing-queue',candidate=candidate,scope='aim-only',
                         accepted_checkpoint_unchanged=ACCEPTED,review=review.get('verdict'))
        return super().work()


if __name__=='__main__':raise SystemExit(main(AimQualification))

