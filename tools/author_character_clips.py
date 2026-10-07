#!/usr/bin/env python3
"""Use inspected native pixels for original clothing/facing and Blender clips."""
from author_character_plain_artifact import complete_source
from author_clothed_character import ACCEPTED,ART,TASK
from qualify_qwen_capacity import CapacityAuthor
from preview_clothed_character import PreviewClothedCharacter
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.visual_context import TARGETS,contract

SOURCE='7209c867297a5f6cbdaa142c508808a50234940a'
PRIOR='q0191-5bf45f93'
SAVED='Halt: Local character facing/clothing and Blender clip source saved; unload idle inference and export/native-preview before runtime integration'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=PRIOR,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Clothed character exported and early native preview saved; inspect actual pixels then author runtime animation')
    preview=old.get('clothed_character_preview_outcome',{})
    review=old.get('clothed_character_cloud_pixel_review',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_blender_clips_attempted')
            or preview.get('candidate')!=SOURCE or not preview.get('native_gate',{}).get('passed')
            or not preview.get('export',{}).get('fresh_staged_export')
            or review.get('candidate')!=SOURCE or review.get('verdict')!='FIX'):
        raise Halt('Require the fresh native character preview and actual-pixel findings before clips')


class CharacterClips(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.before=self.store.root/'evidence'/(PRIOR+'-character-preview')
        self.review=read_json(self.before/'cloud-pixel-review.json')
        if not self.review.get('inspected_actual_pixels') or self.review.get('candidate')!=SOURCE:
            raise Halt('Require source-matched actual pixel review')
        for frame in self.review['frames']:
            if sha((self.before/'captures'/frame['name']).read_bytes())!=frame['sha256']:
                raise Halt('Inspected native pixels changed')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(character_blender_clips_attempted=True,
            recovery_route='native-pixel-backed-original-facing-cloth-and-blender-clips',
            recovery_change='The early fresh export/native preview is preserved and unaccepted. Local Qwen improves connected clothing, corrects reversed visual facing and authors actual original Blender keyframes on the existing articulated rig. Complete public source save precedes staged export/native preview; C# and all accepted gameplay remain protected.')

    def work(self):
        ident=self.begin(TASK,'local-character-facing-cloth-and-clips')
        files=Files(self.project,self.store);original=files.path(ART).read_text();preimage=sha(original.encode())
        protected={p:sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        images=[('AI-GENERATED CHARACTER TARGET '+name+'; aspiration not native output',self.refs/name)
            for name in (TARGETS[0],TARGETS[2])]
        for index,t in ((0,1),(2,6.3)):
            images.append((f'ACTUAL CURRENT NATIVE {PRIOR}/frame-{index:03d}.png at{t}s',
                self.before/'captures'/f'frame-{index:03d}.png'))
        packet=contract(images,[TARGETS[0],TARGETS[2]],2)
        self.c.update(working_context_tokens=98304,output_tokens=32768,model_timeout_seconds=600)
        session=ident+'-original-blender-clips'
        self.model.session('builder',session,
            'You are local Qwen, original Blender character and animation author. Save one complete usable increment as final Python source.',
            'The early export is real and grounded, but actual images show a stiff faceted barrel torso, shoulder '
            'caps and primitive clothing, and the FACE points toward the trailing camera. Compare the attached '
            'neighborhood/alley targets. Deliver the next bounded original Art/player.py increment now, using '
            'the exact source below. All Unity C#, camera, reticle, capsule, movement/aim and missions are protected.\n'
            'A. Improve the visibly clothed human silhouette at this camera scale: connected tapered jacket '
            'torso/shoulders/sleeves instead of cylindrical tube plus prominent balls, readable collar/hem/cuffs, '
            'restrained zipper/placket/pockets/seams and trouser shape, believable hands/head/shoes. Use original '
            'shaped mesh rings/lofts and useful smooth/beveled shading; no external assets/textures. Keep grounded '
            '1.8m proportions and the existing width envelope (about.61m); avoid tiny detail that cannot read. '
            'This is one coherent improvement, not a complete character production overhaul.\n'
            'B. Correct presentation facing: in current Unity frames the face looks toward the behind-player '
            'camera instead of movement/aim direction. Apply the needed static half-turn to the visual export '
            'around its vertical axis, with a precise comment about the native conversion. Do not move or rotate '
            'the real player/controller or camera. Keep the tested root lift+.79 and correct world-preserving '
            'parenting, bpy.data access and l/r dictionary keys.\n'
            'C. Author ORIGINAL Blender keyframe motion on the articulated shoulder/elbow/hip/knee/head pivots, '
            'with a torso/spine pivot if useful. Put ALL active object actions on ONE scene timeline at30fps: '
            'Idle1..61, Walk71..101, Jog111..135, Aim145..175, Board185..209, Drive219..279. Key all participating '
            'joint channels at clip endpoints and intermediate poses, with deliberate rest states between clips '
            'so no state bleeds into another. Idle has subtle breathing/weight/head motion; walk and jog have '
            'opposing leg/arm cycles, knee flex and natural connected joints; aim raises the right hand weapon '
            'forward with left-hand support and restrained breathing; boarding bends/reaches into the vehicle; '
            'driving has seated knees/arms toward the wheel and small natural upper-body motion. Keep the root '
            'presentation transform static throughout: no root motion or animated actor translation. Do not '
            'pretend a static stance proves animation. Pose the meshes/handgun together coherently.\n'
            'The fixed adapter exports the current combined timeline with bake_anim=True, '
            'bake_anim_use_all_actions=False and bake_anim_use_nla_strips=False. Do not create NLA strips or '
            'unassigned alternative actions. Use keyframe_insert on the current object actions; document the '
            'six frame ranges in source. Set scene.frame_start=1, frame_end=279, fps=30 and return to frame1 '
            'at the end. A separate LOCAL-authored Unity importer/runtime increment will split these ranges '
            'and play them; do not add C# or files here. Walking/jogging are presentation clips; current on-foot '
            'speed3.2m/s stays unchanged. Visual boarding/driving must not delay existing E behavior.\n'
            'Return ONLY complete Python final content, optional single python fence, max440lines/28KB. '
            'No tools/XML/JSON/FILE markers or essay. The prior successful public-source save path avoids large '
            'tool envelopes. Use supported xhigh and32768tokens to produce this saved artifact promptly. '
            'Only bpy,bmesh,math,mathutils APIs; no file I/O or export calls. Retain source attribution and '
            'incremental work; code will be exported and viewed before any acceptance.\nEXACT CURRENT SOURCE:\n'+original,
            [],{},images=images,turns=1,reasoning_effort='xhigh',visual_contract=packet,tool_choice='none')
        response=self.store.root/'private/sessions'/session/'response-000.json'
        source=complete_source(read_json(response),max_lines=440,max_bytes=28000)
        if sha(source.encode())==preimage:raise Halt('No original character/clip increment saved')
        if any(sha(p.read_bytes())!=h for p,h in protected.items()):raise Halt('Protected C# changed')
        files.edit(ident+'-save-complete-original-clips',ART,preimage,content=source)
        candidate=self.checkpoint_source('Local Qwen: original character facing clothing and Blender clips')
        outcome=dict(candidate=candidate,prior_playable=ACCEPTED,prior_character_source=SOURCE,
            local_authored=True,script=ART,script_sha256=sha(source.encode()),response_sha256=sha(response.read_bytes()),
            source_from='complete public final content only',reasoning_effort='xhigh',native_verified=False,
            runtime_animation='pending local Unity integration and measured native motion')
        atomic(self.store.root/'evidence'/(ident+'-character-clips-source.json'),outcome)
        self.store.set(source_checkpoint=candidate,clothed_character_source_outcome=outcome,
            character_blender_clips_source_outcome=outcome,stage='original-character-clips-source-saved');self.store.report()
        raise Halt(SAVED.removeprefix('Halt: '))


class PreviewCharacterClips(PreviewClothedCharacter):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker=SAVED,character_blender_clips_attempted=True)
        result=old.get('character_blender_clips_source_outcome',{})
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_blender_clips_preview_attempted')
                or result.get('candidate')!=old.get('source_checkpoint') or result.get('prior_character_source')!=SOURCE):
            raise Halt('Require the newly saved original Blender clips and preserved fallback')
        self.source=old['source_checkpoint'];self.source_result=result
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_blender_clips_preview_attempted=True,
            recovery_route='early-native-character-facing-cloth-and-clip-export',
            recovery_change='Inference unloaded; fresh staged original Blender export and native pixel preview. This checks visual/import progress only; local runtime clip integration and actual motion proof remain mandatory.')


if __name__=='__main__':raise SystemExit(main(CharacterClips))
