#!/usr/bin/env python3
"""One coherent local character/camera pass with actual reference and native pixels."""
import json
import math
from resume_moving_encounter import MovingEncounter
from resume_interception_replay import SOURCE
from resume_combat_death import ACCEPTED
from resume_three_day_queue import main
from continue_game_queue import ReadBoundEdits,review_evidence_seal
from loop_controller.core import Files,Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.model import tool
from loop_controller.visual_context import TARGETS,contract,budget,visual_verdict
from loop_controller.interception_checks import inspect_interception
from loop_controller.continuous_tasks import TASKS
from qualify_moving_encounter import checked

ROUND='q0126-657b9ebf'
FAILURE='Halt: Moving encounter positive needs measured diagnosis: ["secondary-target-isolation-comparison-missing"]'
BOOT='Assets/Game/Bootstrap.cs';ART='Art/player.py';NEW='Assets/Game/CharacterPresentation.cs'
TASK=dict(id='reference-character-camera',phase='polish',polish=True,visual_facing=True,
          outcome='Readable third-person camera/aim and substantial original character anatomy, silhouette and materials')
S={'type':'string'}


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker=FAILURE)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('reference_visual_repair_attempted'):
        raise Halt('Require exact completed three-kill replay and unchanged history')


def validate_visual_source(path,content,original_boot):
    if path not in (BOOT,ART,NEW) or not isinstance(content,str) or len(content.encode())>48000 or len(content.splitlines())>900:
        raise ValueError('Save one bounded camera/presentation or original character source, at most48KB/900lines')
    if path==BOOT:
        marker='    public class Follow : MonoBehaviour'
        if marker not in content or content.split(marker)[0]!=original_boot.split(marker)[0]:
            raise ValueError('Preserve Bootstrap and Walker verbatim; only the Follow presentation class may change')
    if path.endswith('.cs'):
        for word in ('LoopRuntime','LoopAimObservation','LoopInterceptionObservation','LoopInput.Replay','GetCommandLineArgs','Time.timeScale'):
            if word in content:raise ValueError('Presentation must not depend on acceptance/replay implementation')
        # Existing Bootstrap legitimately initializes signals; no new signal writer.
        if content.count('LoopSignals.')>original_boot.count('LoopSignals.') and path==BOOT:
            raise ValueError('Keep existing signal ownership; camera presentation does not create gameplay outcomes')
    return content


def paired_positions(before,after,indices):
    result=[]
    for index in indices:
        a=read_json(before/'captures/scenario.json')['captures'][index]
        b=read_json(after/'captures/scenario.json')['captures'][index]
        def nearest(bundle,t):
            rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            return min(rows,key=lambda r:abs(r['time']-t))
        old,new=nearest(before,a),nearest(after,b)
        delta=math.dist(old['player'],new['player'])
        result.append(dict(index=index,before_seconds=a,after_seconds=b,player_distance=delta,
                           matched=abs(a-b)<.01 and delta<=.12))
    return result


class ReferenceVisuals(MovingEncounter):
    def validate_recovery(self,old):
        validate_pause(old)
        self.resume_capacity=False;self.priority_resume=False;self.transport_recovery=False;self.admission_recovery=False
        self.before=self.store.root/'evidence'/(ROUND+'-positive')
        self.escape=self.store.root/'evidence/q0125-2c1e6a12-exploration'
        raw=read_json(self.before/'gate.json');bad=read_json(self.before/'moving-encounter-gate.json')
        if not raw.get('passed') or raw.get('candidate_commit')!=SOURCE or bad.get('failure')!=['secondary-target-isolation-comparison-missing']:
            raise Halt('Preserve all other native or gameplay failures')
        self.proof={str(p.relative_to(self.store.root)):sha(p.read_bytes()) for root in (self.before,self.escape)
            for p in (root/'gate.json',root/'moving-encounter-gate.json',root/'captures/trace.jsonl',root/'captures/scenario.json')}

    def wait_for_capacity(self):self.capacity.wait('local-reference-character-camera')

    def recovery_settings(self):
        return dict(reference_visual_repair_attempted=True,recovery_route='reference-backed-original-visual-deliverable',
            recovery_change='Preserve three real moving kills and original failed validator. Compare actual pre/post living rivals. '
            'Local Qwen receives target/current PNG bytes, substantive budgets, complete source and Blender/Unity tools. '
            'Separate matched visual improvement, broader visual verdict and native gameplay qualification.')

    def images(self,broad=False,after=None):
        selected=TARGETS if broad else (TARGETS[0],TARGETS[2])
        images=[('AI-GENERATED TARGET '+name+'; aspiration, not native output',self.refs/name) for name in selected]
        roots=[('AFTER',after)] if broad else [('BEFORE',self.before)]+([('AFTER',after)] if after else [])
        for label,root in roots:
            for index in (0,2):
                t=read_json(root/'captures/scenario.json')['captures'][index]
                images.append((f'{label} ACTUAL NATIVE {root.name}/frame-{index:03d}.png; t={t}s',root/'captures'/f'frame-{index:03d}.png'))
        return images,contract(images,selected,2,broad=broad)

    def author(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files,polish=True)
        boot=files.path(BOOT).read_text();original_art=sha(files.path(ART).read_bytes());exported={};previews=[]
        fixed={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in (self.project/'Assets/Game').glob('*.cs') if p.name!='Bootstrap.cs'}
        def save(action,f):
            path=f['path'];content=validate_visual_source(path,f['content'],boot)
            if path==NEW and not files.path(path).exists():result=files.create(action,path,content)
            else:
                previous=edits.reads.get(path)
                if not previous:raise ValueError('Read the current source before saving; stale writes are rejected')
                result=files.edit(action,path,previous['sha256'],content=content);edits.reads.pop(path,None)
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: save reference-backed visual work'))
            return result
        def export(action,_):
            result=self.engines.blender(self.project,ART,action)
            if result.get('ok'):exported['sha256']=sha(files.path(ART).read_bytes())
            self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: export original character visual work'))
            return result
        def preview(action,_):
            if len(previews)>=2:raise ValueError('Two bounded native author previews; finish for full matched testing')
            if exported.get('sha256')!=sha(files.path(ART).read_bytes()):raise ValueError('Export the current character before native preview')
            candidate=self.checkpoint_source('Local Qwen: preserve native visual preview source')
            original=read_json(self.before/'captures/scenario.json')
            scenario=dict(id='visual-author-preview',coverage='foundation',duration=18,
                steps=[s for s in original['steps'] if s['end']<=18],captures=[3.2,10,17])
            bundle=self.store.root/'evidence'/(ident+'-author-preview-'+str(len(previews)))
            gate=self.engines.unity(self.project,bundle,scenario,candidate);previews.append(str(bundle.relative_to(self.store.root)))
            return {k:gate.get(k) for k in ('passed','failure','compile_errors','diagnostic','build_id')}
        def finish(_,f):
            if exported.get('sha256')!=sha(files.path(ART).read_bytes()) or exported['sha256']==original_art:
                raise ValueError('Save and export a substantive original character revision before finishing')
            if files.path(BOOT).read_text()==boot:raise ValueError('Complete the camera/aim readability change too')
            if any(sha(files.path(p).read_bytes())!=v for p,v in fixed.items()):raise Halt('Visual author changed protected gameplay source')
            return dict(ok=True,summary=f['summary'],preview_evidence=previews)
        images,required=self.images();budget(self.c)
        self.store.set(stage='local-reference-character-camera');self.store.report()
        result=self.model.session('builder',ident+'-coherent-visual-author',
            'You are local Qwen, sole original game/Blender author. Deliver a coherent substantial visual improvement.',
            'Inspect the supplied actual current native pixels and two reference targets. The real game is far below '
            'the target: its head and tall arm shapes dominate the lower center, aiming is crowded and no clear reticle '
            'is visible. Deliver readable third-person camera/aim plus a substantially improved ORIGINAL character '
            'silhouette, anatomy, joints, hands, clothing/material separation. A recolor of boxes is insufficient. '
            'Design and author tapered/rounded body and clothing forms, believable proportions, restrained detail and '
            'correct parent/pivot transforms. Existing player.py stacks parent-local offsets; assess the actual geometry. '
            'Use Blender original mesh construction, bevels/smooth normals and practical material values; preserve editable '
            'source/export. No downloaded assets, packages or external generators. This is one coherent deliverable; '
            'save complete related changes promptly rather than isolated cosmetic assignments. Output budget16384, '
            'thinking xhigh; you may save and continue via tools. No long essay is needed.\n'
            'Only Art/player.py, the Follow class in Bootstrap.cs and optional Assets/Game/CharacterPresentation.cs '
            'are writable. Bootstrap and Walker prefix stays verbatim, including physical movement, scene placement, '
            'scale, spawn, install APIs and imported visual correctionY=-0.79. Rival clones use that same asset correction. '
            'Ensure the exported visual fits the existing upright human collider, feet grounded and about1.8m tall. '
            'Preserve Combat ray/occlusion/health, all target colliders and mission state; no aim assist or wider casts. '
            'A reticle must mark the actual camera center ray and appear in Camera.Render, not uncaptured OnGUI. '
            'Retain geometry-aware camera wall/floor/near-plane protection and correct player/vehicle target changes. '
            'Do not solve crowding by hiding the entire character. Existing pivot names can remain for compatible '
            'animation; new visual animation must not change movement, hits or test signals. No cloud gameplay edits.\n'
            'Tools give full original Blender export and actual native Unity preview. read_file reports exact hashes '
            'and lines; save_source writes your complete source with stale-write protection. run_blender exports your '
            'latest character. run_native_preview gives compiler/runtime facts; a fresh critic sees the final matched '
            'native pixels after you finish. Two optional previews; no need to generate input scripts. Call finish_task '
            'after saved source and export. The existing ordinary-input replay, same-position captures, negative hit/cover '
            'tests and full gameplay suite gate promotion. The reference standard is not waived by a gameplay PASS.\n'
            'CURRENT BOOTSTRAP:\n'+boot+'\nCURRENT ORIGINAL CHARACTER:\n'+files.path(ART).read_text(),
            [tool('read_file','Read exact source; required before saving existing source.',{'path':S,'start_line':{'type':'integer'},'line_count':{'type':'integer'}},['path']),
             tool('save_source','Save one complete original camera/presentation or character source.',{'path':S,'content':S}),
             tool('run_blender','Export the latest original player.py through Blender; preserve .blend and FBX.',{}),
             tool('run_native_preview','Build and run a bounded actual Unity preview; return compiler/runtime facts.',{}),
             tool('finish_task','Finish the saved, exported coherent visual deliverable.',{'summary':S})],
            {'read_file':edits.read,'save_source':save,'run_blender':export,'run_native_preview':preview,'finish_task':finish},
            images=images,visual_contract=required,turns=16,reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-visual-author.json'),result)
        if not result.get('ok'):raise Halt('Reference-backed visual source saved incompletely; preserve progress and diagnose bounded continuation: '+json.dumps(result))

    def critique(self,ident,after,broad=False):
        images,required=self.images(broad,after);budget(self.c,broad)
        self.store.set(stage='broad-reference-visual-review' if broad else 'matched-character-camera-review');self.store.report()
        result=self.model.session('critic',ident+('-broad-critic' if broad else '-matched-critic'),
            'You are a fresh local visual critic. Judge actual pixels against the supplied target pixels.',
            ('All FIVE targets are supplied as aspirations. Assess the real overall visual gap honestly, including '
             'character anatomy/materials, camera/aim, street density/detail, lighting and consistency. Missing target '
             'locations/features remain missing. A gameplay PASS never implies visual acceptance. The game is unfinished.'
             if broad else 'Compare matched BEFORE/AFTER native views with neighborhood/combat target pixels. '
             'Require a substantial character silhouette/anatomy/material improvement AND readable third-person '
             'camera/aim with a center-ray reticle. Recoloring crude boxes, hiding the whole actor or HUD-only changes '
             'are insufficient. Do not exempt primitive art. Describe regressions honestly.')+
            ' Cite actual labels/times and visible evidence. Return PASS/FIX/UNVERIFIED and at most five prioritized '
            'specific fixes. No inferred animation, controls, combat success or ten-minute completion from stills.',
            [tool('submit_review','Return the independent visual verdict.',{'verdict':S,'summary':S,'fixes':{'type':'array','items':S}})],
            {'submit_review':lambda _,f:visual_verdict(f,broad)},images=images,visual_contract=required,turns=2,reasoning_effort='xhigh')
        atomic(after/('broad-visual-review.json' if broad else 'matched-visual-review.json'),result)
        return result

    def work(self):
        ident=self.begin(TASK,'local-reference-character-camera')
        for name,digest in self.proof.items():
            if sha((self.store.root/name).read_bytes())!=digest:raise Halt('Original replay evidence changed')
        rows=[json.loads(x) for x in (self.before/'captures/trace.jsonl').read_text().splitlines()]
        events=[json.loads(x) for x in (self.before/'captures/aim-shots.jsonl').read_text().splitlines()]
        corrected=inspect_interception(rows,events,'positive')
        atomic(self.store.root/'evidence'/(ident+'-prior-isolation-reevaluation.json'),
            dict(original_files=self.proof,original_failure_preserved=True,source=SOURCE,result=corrected))
        if not corrected['passed']:raise Halt('Preserve any genuine remaining prior encounter defect')
        self.author(ident)
        candidate=self.checkpoint_source('Local Qwen: reference-backed original character and camera')
        self.store.set(source_checkpoint=candidate,stage='native-reference-character-camera');self.store.report()
        after=self.store.root/'evidence'/(ident+'-positive')
        scenario=read_json(self.before/'captures/scenario.json')
        raw=self.engines.unity(self.project,after,scenario,candidate)
        if not raw.get('passed'):raise Halt('New visual candidate has a real compile/native fault; preserve source and diagnose')
        gate=checked(after,raw,'positive');pairs=paired_positions(self.before,after,(0,2))
        atomic(after/'matched-positions.json',pairs)
        seal=review_evidence_seal(after/'captures',candidate,'reference-character-camera')
        verdict=self.critique(ident,after)
        broad=self.critique(ident,after,True);verify_seal(after/'captures',seal)
        queue_milestone(self.store,'native-milestone',TASK,after,gate,
            [after/'captures/frame-000.png',after/'captures/frame-002.png'],
            {'frame-000.png':3.2,'frame-002.png':63.25},verdict)
        result=dict(candidate=candidate,evidence=str(after.relative_to(self.store.root)),
            targeted_gameplay_passed=gate.get('passed'),matched_positions=pairs,visual_review=verdict,
            broad_visual_review=broad,full_regressions='pending',final_game_accepted=False)
        atomic(after/'visual-deliverable.json',result);self.store.set(reference_visual_outcome=result);self.store.report()
        if not gate.get('passed') or not all(p['matched'] for p in pairs) or verdict.get('verdict')!='PASS':
            raise Halt('Actual visual comparison needs measured follow-up; no visual/gameplay promotion')
        # Full promotion checks run once after the targeted change actually works.
        self.store.set(stage='reference-visual-promotion-regressions');self.store.report()
        legacy=self.regress(TASKS[7],ident,candidate)
        result['full_regressions']=legacy;atomic(after/'visual-deliverable.json',result)
        self.store.set(reference_visual_outcome=result);self.store.report()
        if not legacy.get('passed'):raise Halt('Preserve the visual improvement but diagnose gameplay regression before promotion')
        raise Halt('Matched visual improvement and legacy regressions recorded; continue actual camera/encounter red cases and original environment quality')


if __name__=='__main__':raise SystemExit(main(ReferenceVisuals))
