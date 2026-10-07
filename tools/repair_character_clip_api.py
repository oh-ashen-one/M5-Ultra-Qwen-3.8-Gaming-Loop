#!/usr/bin/env python3
"""Local two-span API repair after actual Blender5.2 keyframe failure."""
import ast
import json
from author_clothed_character import ACCEPTED,ART,TASK,validate_art
from qualify_qwen_capacity import CapacityAuthor
from repair_character_clips import PreviewRepairedCharacterClips
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='6c2fe9ee1bbe7f4ffa79768fca05b8ce774b76b6'
SCRIPT_SHA='9b7f71f92ce7c84733ef299e0f07266654902c3056d914a518013c66e02e4af4'
PRIOR='q0196-a855374b'
SAVED='Halt: Local exact Blender keyframe API repair saved; unload inference for fresh export and native inspection'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=SOURCE,
        last_playable_checkpoint=ACCEPTED,current_round=PRIOR,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Local clothed character export failed; preserve source and actual Blender diagnostic')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('character_clip_api_attempted'):
        raise Halt('Require the actual keyframe API error and preserved source/history')


def exact_spans(source):
    lines=source.splitlines(keepends=True);tree=ast.parse(source)
    keyrot=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='keyrot')
    tail=[n for n in tree.body if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=='ALLP'][-1]
    return [''.join(lines[n.lineno-1:n.end_lineno]) for n in (keyrot,tail)]


def apply_patches(source,response):
    choices=response.get('choices',[])
    if len(choices)!=1 or choices[0].get('finish_reason')!='stop':raise Halt('Require completed public API patches')
    message=choices[0].get('message',{})
    if message.get('tool_calls'):raise Halt('No partial tool replay in exact API artifact')
    content=message.get('content')
    if not isinstance(content,str) or len(content.encode())>14000:raise Halt('Require bounded public patch JSON')
    content=content.strip()
    if content.startswith('```json\n') and content.endswith('\n```'):content=content[8:-4]
    data=json.loads(content);patches=data.get('replacements',[]);spans=exact_spans(source)
    if len(patches)!=2 or {p.get('old') for p in patches}!=set(spans):
        raise Halt('Only the two exact API spans may change; geometry/poses are protected')
    changed=source
    for p in patches:
        if not isinstance(p.get('new'),str) or len(p['new'])>6000 or changed.count(p['old'])!=1:
            raise Halt('Require exact unique bounded source replacement')
        changed=changed.replace(p['old'],p['new'],1)
    return validate_art(changed)


class RepairCharacterClipAPI(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.failure_path=self.store.root/'evidence'/(PRIOR+'-character-export.json')
        d=read_json(self.failure_path)
        if (d.get('ok') or d.get('exit_code')!=7 or "unexpected keyword argument 'replace'" not in d.get('diagnostic','')
                or sha((self.project/ART).read_bytes())!=SCRIPT_SHA):raise Halt('Require the actual exact API defect')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_clip_api_attempted=True,recovery_route='local-two-span-blender-api-repair',
            recovery_change='Preserve repaired geometry/poses and actual Blender5.2 TypeError. Local Qwen edits only the keyframe helper and final action validation span using completed small JSON replacements. No whole-model rewrite or cloud source repair.')
    def work(self):
        ident=self.begin(TASK,'local-two-span-character-api-repair')
        files=Files(self.project,self.store);original=files.path(ART).read_text()
        spans=exact_spans(original)
        protected={p:sha(p.read_bytes()) for p in self.project.rglob('*.cs')}
        self.c.update(working_context_tokens=49152,output_tokens=16384,model_timeout_seconds=600)
        session=ident+'-character-api-repair'
        self.model.session('builder',session,
            'You are local Qwen. Make two tiny original Blender API corrections; return only completed JSON replacements.',
            'Actual Blender5.2 failure: bpy_struct.keyframe_insert got unexpected keyword argument replace. '
            'All repaired character geometry, side offsets, poses and clip ranges must remain byte-for-byte '
            'unchanged. Repair ONLY the two exact spans below. Do not reconsider the art or animation.\n'
            'For key insertion, use supported keyframe_insert parameters and preserve insertion of NEW '
            'keys as well as updating already existing keys at the same frame. A replace-only option would '
            'skip initial keys, so do not introduce it. Existing numeric pose/axis semantics stay intact.\n'
            'The final validation currently uses ob.action, which is not an Object property. The real action '
            'belongs to ob.animation_data.action. Blender5.2 uses layered actions and slots; do not assume '
            'a legacy Action.fcurves member. Installed official bpy_extras/anim_utils.py reads '
            'anim_data.action / anim_data.action_slot and iterates action.layers, layer.strips, '
            'strip.channelbag(slot) and channelbag.fcurves. However extrapolation here is OPTIONAL: all '
            'clip endpoints/gaps are already pinned, and exporter samples only frame1..279. A minimal valid '
            'action-presence check is enough; avoid adding unrelated curve traversal or dependencies. '
            'No added imports or file access. Preserve xhigh but finish this tiny repair promptly.\n'
            'Return exactly {"replacements":[{"old":<exact first span>,"new":<complete corrected first span>},'
            '{"old":<exact second span>,"new":<complete corrected second span>}]} as final JSON. '
            'No tools, prose, partials or full-file rewrite. Each old span must match the supplied text exactly.\n'
            'EXACT SPANS (JSON escaped for unambiguous newlines):\n'+json.dumps(spans),
            [],{},turns=1,reasoning_effort='xhigh',tool_choice='none')
        response=self.store.root/'private/sessions'/session/'response-000.json'
        source=apply_patches(original,read_json(response))
        if source==original or any(sha(p.read_bytes())!=h for p,h in protected.items()):raise Halt('Require actual scoped repair and unchanged C#')
        files.edit(ident+'-save-exact-api-repair',ART,SCRIPT_SHA,content=source)
        candidate=self.checkpoint_source('Local Qwen: fix Blender key insertion and action API usage')
        result=dict(candidate=candidate,prior_playable=ACCEPTED,repaired_prior_source=SOURCE,local_authored=True,
            script=ART,script_sha256=sha(source.encode()),response_sha256=sha(response.read_bytes()),
            failure_receipt_sha256=sha(self.failure_path.read_bytes()),native_verified=False,
            source_from='completed public two-span JSON artifact',reasoning_effort='xhigh')
        atomic(self.store.root/'evidence'/(ident+'-character-api-repair.json'),result)
        self.store.set(source_checkpoint=candidate,clothed_character_source_outcome=result,
            character_clip_api_source_outcome=result,stage='original-character-api-repair-source-saved')
        self.store.report();raise Halt(SAVED.removeprefix('Halt: '))


class PreviewCharacterClipAPI(PreviewRepairedCharacterClips):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker=SAVED,character_clip_api_attempted=True)
        result=old.get('character_clip_api_source_outcome',{})
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_clip_api_preview_attempted')
                or result.get('candidate')!=old.get('source_checkpoint') or result.get('repaired_prior_source')!=SOURCE):
            raise Halt('Require the saved local API repair and preserved accepted fallback')
        self.source=old['source_checkpoint'];self.source_result=result
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_clip_api_preview_attempted=True,recovery_route='fresh-api-repaired-character-native-preview',
            recovery_change='Inference unloaded; fresh original export, passive saved-pose inspection and native preview. Runtime motion and gameplay acceptance remain separate.')

if __name__=='__main__':raise SystemExit(main(RepairCharacterClipAPI))
