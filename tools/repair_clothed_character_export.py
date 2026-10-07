#!/usr/bin/env python3
"""Local repair of the actual first export error and inspected transform defects."""
from author_character_plain_artifact import complete_source
from author_clothed_character import ACCEPTED, ART, TASK, SAVED
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='b628f6815287dc5c4c7b65d1a45614b61a6bb5b9'
SCRIPT_SHA='5391f2160871f981d8cb07d83afd94e96f15c6bfc45e55960a390fbf6cf954e8'
PRIOR='q0188-c0d67b71'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=PRIOR,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Local clothed character export failed; preserve source and actual Blender diagnostic')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('clothed_character_export_repair_attempted'):
        raise Halt('Require the first actual failed character export and preserved accepted fallback')


class RepairClothedExport(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.export_path=self.store.root/'evidence'/(PRIOR+'-character-export.json')
        self.failure=read_json(self.export_path)
        if (self.failure.get('ok') or self.failure.get('exit_code')!=7
                or "'Context' object has no attribute 'data'" not in self.failure.get('diagnostic','')
                or sha((self.project/ART).read_bytes())!=SCRIPT_SHA):
            raise Halt('Preserve any different export defect or changed local source')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(clothed_character_export_repair_attempted=True,
            recovery_route='local-focused-character-context-key-grounding-repair',
            recovery_change='Preserve first saved original model and real Blender AttributeError. Local Qwen repairs context/data access, consistent left/right pivot keys, actual foot lift after world-preserving parenting and right-hand weapon placement. Complete public source only; no cloud art edit or broad redesign.')

    def work(self):
        ident=self.begin(TASK,'local-clothed-character-export-repair')
        files=Files(self.project,self.store);original=files.path(ART).read_text()
        protected={p:sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        self.c.update(working_context_tokens=65536,output_tokens=16384,model_timeout_seconds=600)
        session=ident+'-character-export-repair'
        self.model.session('builder',session,
            'You are local Qwen, original Blender character author. Repair this saved artifact and return only the complete Python file.',
            'The early real Blender5.2 export failed immediately: AttributeError: Context object has no attribute data '
            'at SC.data.objects. Repair the execution/placement defects in the exact saved source below. Keep its '
            'original geometry/material design and articulation, no redesign or new feature.\n'
            '1. SC=bpy.context has no data: use the real bpy.data collection for initial object removal and final '
            'object count. Context collection/view_layer access remains on context.\n'
            '2. The loops bind sgn to l/r and s to numeric1/-1 but pivots are stored as sh[s],el[s],hip[s],kn[s]; '
            'later lookup uses l/r strings and fails. Make creation and lookup keys consistently l/r, retaining '
            'numeric side only for coordinates.\n'
            '3. The current root atZ=.79 combined with world-preserving parent inverse leaves actual mesh soles '
            'nearZ=0, contrary to the contract. Unity then subtracts .79 and buries the feet. Build the character '
            'with a zero root, parent world transforms once, then lift the completed presentation root by.79 so '
            'ACTUAL evaluated mesh soles in Blender world are near+.79 and top near2.6m. Correct misleading comments. '
            'Do not double any offsets or change Unity/collider.\n'
            '4. Right-hand weapon meshes currently use positiveX while the right forearm is on negativeX; attach '
            'and place the pistol beside the actual right hand so later elbow rotation carries it.\n'
            'Use supported bpy/bmesh/mathutils only. The adapter saves blend and exports FBX. Return the entire '
            'repaired source as plain final Python (one code fence allowed), no tools, prose or markers. Max240lines '
            '/16KB. Current full source follows; save the focused repair promptly rather than rethinking the art.\n'+original,
            [],{},turns=1,reasoning_effort='xhigh',tool_choice='none')
        response=self.store.root/'private/sessions'/session/'response-000.json'
        source=complete_source(read_json(response))
        if 'SC.data' in source or sha(source.encode())==SCRIPT_SHA:
            raise Halt('The actual context/data defect is not repaired')
        if any(sha(p.read_bytes())!=h for p,h in protected.items()):raise Halt('Protected C# changed')
        files.edit(ident+'-save-complete-export-repair',ART,SCRIPT_SHA,content=source)
        candidate=self.checkpoint_source('Local Qwen: repair original character export and pivot placement')
        result=dict(candidate=candidate,prior_playable=ACCEPTED,local_authored=True,script=ART,
            script_sha256=sha(source.encode()),native_verified=False,response_sha256=sha(response.read_bytes()),
            repaired_prior_source=SOURCE,original_export_sha256=sha(self.export_path.read_bytes()),
            source_from='complete public final content only',reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-character-export-repair.json'),result)
        self.store.set(source_checkpoint=candidate,clothed_character_source_outcome=result,
            stage='clothed-character-source-saved');self.store.report()
        raise Halt(SAVED.removeprefix('Halt: '))


if __name__=='__main__':raise SystemExit(main(RepairClothedExport))
