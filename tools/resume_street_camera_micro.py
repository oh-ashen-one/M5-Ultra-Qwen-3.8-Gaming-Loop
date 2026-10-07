#!/usr/bin/env python3
"""Recover a camera output-limit stop with one small local bounds guard."""
import json
from resume_street_readability import StreetReadability, SOURCE, SECOND_TASK, ACCEPTED, validate_camera_span
from resume_three_day_queue import main
from repair_camera_clearance import CameraRepair
from qualify_map_extension import promote_qualified_extension
from loop_controller.core import Files, Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

ROUND='q0088-9a0ccd72'
RESPONSE_SHA='85aa572cecd2e7ca0c0cd014a2425956f4187dc84ba27a0ec8477c3d9e7f5fa0'
FENCE_ROUND='q0087-e949809e'
FENCE_GATE_SHA='c510e168d0924956529133fa5a9498b5a91f0997dcadc1ce2d2c521a8a2c93bb'
FENCE_DIAGNOSTIC_SHA='000a59757bed0e128d37dcf7cf895bab8309b1ece5d0a0aaaa04bb1a652a81b5'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,second_street_attempts=4,
        street_readability_recovery_attempted=True,saved_door_accepted=False,
        blocker='Halt: Focused local camera role saved no correction; preserve fence and evidence')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('street_camera_micro_attempted'):
        raise Halt('Expected exact no-edit camera output stop; preserve source and all earlier failures')


class StreetCameraMicro(StreetReadability):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-camera-span')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Original camera output-limit evidence changed')
        choice=json.loads(raw)['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls'):
            raise Halt('Expected no completed local camera tool call')
        bundle=self.store.root/'evidence'/FENCE_ROUND
        for name,expected in [('scoped-gate.json',FENCE_GATE_SHA),('fence-diagnostic.json',FENCE_DIAGNOSTIC_SHA)]:
            if sha((bundle/name).read_bytes())!=expected:raise Halt('Saved fence native evidence changed')
        gate=read_json(bundle/'scoped-gate.json');diagnostic=read_json(bundle/'fence-diagnostic.json')
        if (gate.get('candidate_commit')!=SOURCE or not gate.get('passed')
            or not gate.get('scene_inventory',{}).get('passed')
            or diagnostic.get('candidate')!=SOURCE
            or not diagnostic.get('traversal',{}).get('passed')
            or not diagnostic.get('support',{}).get('passed')):
            raise Halt('Require actual completed current-source fence traversal')
        self.sealed_probe();self.accepted_probe()

    def recovery_settings(self):
        return dict(street_camera_micro_attempted=True,recovery_route='local-camera-bounds-microedit',
            recovery_change='Preserve no-edit output exhaustion; one small local camera bounds guard, then existing native checks and sealed route')

    def camera_edit(self,ident):
        files=Files(self.project,self.store);path='Assets/Game/Bootstrap.cs';raw=files.path(path).read_text()
        needle='            pos.y = Mathf.Max(pos.y, floorY + 0.08f);'
        if raw.count(needle)!=1:raise Halt('Expected unique final floor-clamp insertion point')
        line=raw.count('\n',0,raw.index(needle))+1
        edit=SelectedEdit(files,path,line,line,max_lines=24)
        def save(action,fields):
            validate_camera_span(fields['content'])
            if needle.strip() not in fields['content']:raise ValueError('Preserve the existing floor clamp')
            return edit.apply(action,fields['content'])
        self.c.update(output_tokens=3072,model_timeout_seconds=180)
        self.store.set(stage='local-street-camera-bounds-microedit');self.store.report()
        self.model.session('builder',ident+'-camera-bounds-microedit',
            'You are local Qwen making one tiny C# camera edit. Submit edit_selected_span immediately; no redesign or replay.',
            'Keep the selected floor-clamp line and insert one compact own-target clearance guard after it. '
            'The next unchanged line assigns transform.position = pos. Existing wall/foreign-collider handling has already run. '
            'Observed defect: the return camera enters the coupe body because own target colliders are excluded. '
            'Use the existing cached Renderer[] rend and each active enabled renderer world bounds, expanded by the existing '
            'clearance margin, to detect whether pos lies within the followed target. If so, lift pos.y above existing '
            'world-space body top plus clearance and mark the existing cramped flag, so existing cramped look logic applies. '
            'When pos is already outside, preserve its normal pose. Keep the earlier wall loop, target cache, input, aim and '
            'mission unchanged. No hardcoded coordinates/times or new fields. At most24replacement lines. '
            'Available locals: Vector3 pos; float top (maximum world Y across target renderers), clearance=0.25f, floorY; '
            'bool cramped; Renderer[] rend. UnityEngine types are imported. Handle null renderers safely. '
            '\nEXACT SELECTED LINE:\n'+edit.old,
            [tool('edit_selected_span','Save the one compact local target-bounds guard.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if files.path(path).read_text()==raw:raise Halt('Tiny local camera edit saved no source; preserve both output-limit stops')
        candidate=self.checkpoint_source('Local Qwen: keep return camera above intersected target bounds')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        return candidate

    def work(self):
        ident=self.begin(SECOND_TASK,'local-camera-microedit-recovery')
        candidate=self.camera_edit(ident)
        _,camera=CameraRepair.camera_probe(self,ident+'-camera-clearance',candidate)
        if not camera['passed']:raise Halt('Local target-bounds guard failed existing camera wall contracts')
        bundle,gate,failure=self.qualify(SECOND_TASK,ident,candidate,self.reuse_probe(candidate))
        if failure:
            self.record_rejection(SECOND_TASK,ident,candidate,failure)
            raise Halt('Target-bounds camera/street qualification needs recorded correction; preserve accepted connector')
        record=promote_qualified_extension(self,SECOND_TASK,bundle,gate,read_json(bundle/'critic.json'))
        return self.continue_after_street(record)


if __name__=='__main__':raise SystemExit(main(StreetCameraMicro))
