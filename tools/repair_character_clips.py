#!/usr/bin/env python3
"""Local repair of measured animation export and inspected limb placement failures."""
from author_character_plain_artifact import complete_source
from author_clothed_character import ACCEPTED, ART, TASK
from qualify_qwen_capacity import CapacityAuthor
from preview_clothed_character import PreviewClothedCharacter
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='6ebecc05a460e75977414ae4e3ee4f28c7e24b91'
SCRIPT_SHA='30645121b9855cacc4a0d189c1c53f0c4eecf6cc82ead98b65c6fdb23958ddd7'
PRIOR='q0193-ca4cfa26'
SAVED='Halt: Local original clip execution and limb placement repair saved; unload inference for staged export and native inspection'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=PRIOR,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Local clothed character export failed; preserve source and actual Blender diagnostic')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('character_clip_repair_attempted'):
        raise Halt('Require the actual failed clip export and unchanged source/history')


class RepairCharacterClips(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.export_path=self.store.root/'evidence'/(PRIOR+'-character-export.json')
        failure=read_json(self.export_path)
        if (failure.get('ok') or failure.get('fresh_staged_export') or failure.get('exit_code')!=7
                or "NameError: name 'play' is not defined" not in failure.get('diagnostic','')
                or sha((self.project/ART).read_bytes())!=SCRIPT_SHA):
            raise Halt('Preserve any changed source or different Blender failure')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(character_clip_repair_attempted=True,
            recovery_route='local-exact-clip-execution-and-world-limb-placement-repair',
            recovery_change='Preserve failed export and prior asset hashes. Local Qwen defines the missing animation helper, positions limb lofts at their matching side pivots, verifies local rotation axes and pins clip endpoints. No new art redesign or cloud animation authorship.')

    def work(self):
        ident=self.begin(TASK,'local-character-clip-export-repair')
        files=Files(self.project,self.store);original=files.path(ART).read_text()
        protected={p:sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        self.c.update(working_context_tokens=98304 if getattr(self,'retained',None) else 65536,
            output_tokens=32768,model_timeout_seconds=600)
        session=ident+'-character-clip-repair'
        self.model.session('builder',session,
            'You are local Qwen, original Blender character and animation author. Repair this exact saved increment and return only complete Python source.',
            'The real Blender5.2 export failed with NameError: play is not defined at line212. '
            'Repair the following concrete defects in your saved source; preserve the original clothing design, '
            'materials, root lift, static facing correction, names, six clip ranges and protected Unity gameplay. '
            'Do not redesign the character or add features.\n'
            '1. Define the missing play helper before every call. Implement the intended dictionary of joint '
            'names and (frame, Euler angles) keys with real rotation_euler and keyframe_insert on the existing '
            'object actions. Verify all names exist and all six clips execute.\n'
            '2. Both sides of sleeves, forearms, thighs and shins currently use loft rings centered at X=0. '
            'PAR preserves world coordinates, so parenting does not place these meshes at their left/right '
            'joint pivots: they remain overlapping on the body midline. Position each limb loft at its actual '
            'matching side coordinates BEFORE world-preserving parenting. Retain connected joint endpoints '
            'and properly placed hands/shoes/weapon. Check evaluated rest world geometry, not just parent names.\n'
            '3. Verify rotation signs in the LOCAL joint basis. A root half-turn rotates both the character '
            'facing direction and limb bases; it does not by itself reverse local Euler semantics. FX=-1 '
            'solely because root.rotation_z=pi is suspect. Derive the correct signs from down-Z limbs and '
            'the model local forward +Y; preserve or repair your original poses accordingly, with a truthful '
            'comment. Aim must raise the pistol toward the FACE direction, with left-hand support. No root '
            'motion or Unity camera/controller changes.\n'
            '4. Pin participating channels at BOTH endpoints of each clip, including true rest channels, '
            'so neighboring clips do not interpolate into one another. Idle1..61, Walk71..101, Jog111..135, '
            'Aim145..175, Board185..209, Drive219..279 at30fps. Make loop endpoints consistent where applicable. '
            'Keep all active object actions on one timeline, no NLA, frame_start1/frame_end279 and finish at1. '
            'Ensure floor support and non-disconnected limbs through motion.\n'
            'Return the ENTIRE repaired Python source as final content now, optional one python fence; '
            'max460lines/30KB. No tools, XML, JSON, FILE markers, prose, filesystem I/O or export calls. '
            'Only bpy,bmesh,math,mathutils. Keep the bounded repair focused; the source will be saved, '
            'exported and inspected before separate local Unity integration.\nEXACT SOURCE:\n'+original,
            [],{},turns=1,reasoning_effort='xhigh',tool_choice='none',
            retained_assistant=getattr(self,'retained',None),
            retained_instruction='Continue the exact retained local repair without restarting analysis. Return the COMPLETE repaired Art/player.py as final Python NOW. The diagnosed execution, side placement, axis and endpoint issues are already covered. Preserve the existing original design; no new features, tools or prose. Save one bounded usable file promptly with the same xhigh setting.')
        response=self.store.root/'private/sessions'/session/'response-000.json'
        source=complete_source(read_json(response),max_lines=460,max_bytes=30000)
        if sha(source.encode())==SCRIPT_SHA:raise Halt('No local clip repair returned')
        if any(sha(p.read_bytes())!=h for p,h in protected.items()):raise Halt('Protected C# changed')
        files.edit(ident+'-save-complete-clip-repair',ART,SCRIPT_SHA,content=source)
        candidate=self.checkpoint_source('Local Qwen: repair original clip execution and side limb placement')
        result=dict(candidate=candidate,prior_playable=ACCEPTED,repaired_prior_source=SOURCE,
            local_authored=True,script=ART,script_sha256=sha(source.encode()),native_verified=False,
            response_sha256=sha(response.read_bytes()),original_export_sha256=sha(self.export_path.read_bytes()),
            source_from='complete public final content only',reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-character-clip-repair.json'),result)
        self.store.set(source_checkpoint=candidate,clothed_character_source_outcome=result,
            character_clip_repair_source_outcome=result,stage='original-character-clip-repair-source-saved')
        self.store.report();raise Halt(SAVED.removeprefix('Halt: '))


class PreviewRepairedCharacterClips(PreviewClothedCharacter):
    def observe_export(self,ident,candidate,exported):
        from pathlib import Path
        observer=Path(__file__).resolve().parents[1]/'controller/blender/observe_character.py'
        blend=self.project/'ArtSources/player/source.blend'
        output=self.store.root/'evidence'/(ident+'-character-rig')
        output.mkdir();report=output/'rig-observation.json'
        code=self.machine.execute('blender',[self.c['blender'],'--background','--disable-autoexec',str(blend),
            '--python-exit-code','7','--python',str(observer)],self.project,output,120,
            {'LOOP_RIG_OBSERVATION':str(report)},protected=[blend,observer],writable_roots=[output])
        receipt=dict(candidate=candidate,source_script_sha256=exported['script_sha256'],
            blend_sha256=sha(blend.read_bytes()),observer_sha256=sha(observer.read_bytes()),
            exit_code=code,report_sha256=sha(report.read_bytes()) if report.exists() else None,
            passively_evaluated_frames=True,authored_animation=False)
        atomic(output/'receipt.json',receipt)
        if code or not report.exists():raise Halt('Passive rig observation failed; preserve fresh asset and diagnostic')

    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker=SAVED,character_clip_repair_attempted=True)
        result=old.get('character_clip_repair_source_outcome',{})
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_clip_repair_preview_attempted')
                or result.get('candidate')!=old.get('source_checkpoint') or result.get('repaired_prior_source')!=SOURCE):
            raise Halt('Require the saved local clip repair and preserved accepted fallback')
        self.source=old['source_checkpoint'];self.source_result=result
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_clip_repair_preview_attempted=True,
            recovery_route='fresh-repaired-original-clip-export-and-native-preview',
            recovery_change='Inference unloaded; export locally repaired original character and clips into empty staging. Verify fresh bytes and actual native pixels/imported curves before runtime integration or acceptance.')


if __name__=='__main__':raise SystemExit(main(RepairCharacterClips))
