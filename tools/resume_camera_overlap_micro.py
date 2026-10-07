#!/usr/bin/env python3
"""One local micro-edit at the measured world-overlap lowering branch."""
import json
from resume_camera_completed_diagnosis import CompletedCameraDiagnosis, SOURCE, ACCEPTED
from resume_camera_branch_diagnosis import PATH
from resume_street_readability import validate_camera_span
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

ROUND='q0091-e1a25c20'
RESPONSE_SHA='7109f01647c7b8ad07f25adcddb369b0dfb23fc95b32c7c74293dca8c1d0d1f5'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,completed_camera_diagnosis_recovered=True,
        blocker='Halt: Cause-based local editor saved no correction')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_overlap_micro_attempted'):
        raise Halt('Expected exact no-edit cause-repair output stop')


class CameraOverlapMicro(CompletedCameraDiagnosis):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-cause-edit')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Original cause-editor exhaustion changed')
        choice=json.loads(raw)['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls'):
            raise Halt('Expected no completed camera edit; never apply partial output')
        self.saved_diagnosis();self.sealed_probe();self.accepted_probe()

    def recovery_settings(self):
        return dict(camera_overlap_micro_attempted=True,recovery_route='measured-overlap-height-and-framing-microedit',
            recovery_change='Preserve full-block output exhaustion; local edit of the exact lowering line, then all unchanged camera/street/image gates')

    def local_repair(self,ident,diagnosis,observed):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        needle='                candidate.y = Mathf.Max(candidate.y, floorY + 0.08f);'
        if raw.count(needle)!=1:raise Halt('Expected one exact world-overlap vertical correction line')
        line=raw.count('\n',0,raw.index(needle))+1
        edit=SelectedEdit(files,PATH,line,line,max_lines=8)
        def save(action,f):
            validate_camera_span(f['content']);return edit.apply(action,f['content'])
        self.c.update(output_tokens=2048,model_timeout_seconds=150)
        self.store.set(stage='local-measured-overlap-microedit');self.store.report()
        self.store.event('camera-repair-decomposed',reason='Full-block request exhausted output without any edit',
            observed_branch='world-overlap correction lowers camera while cramped remains false',
            source_author='local Qwen',cloud_role='scoped repair guidance and external acceptance only')
        self.model.session('builder',ident+'-overlap-microedit',
            'You are local Qwen authoring one tiny C# correction. Call edit_selected_span now; no redesign or replay.',
            'Your measured diagnosis identified poor framing above the rear deck, not a body intersection. '
            'The native world-overlap loop moves the camera toward its low pivot and lowers Y1.998 to1.769; cramped stays false. '
            'Replace only the selected line inside that already-active world-overlap correction. Preserve at least the intended '
            'camera height origin.y + camY as well as the existing floor minimum, and set the existing cramped flag so the '
            'existing close-space look mode is used after an actual correction. Keep horizontal collision steps and every '
            'other line unchanged. This is a proposed cause-based repair; near-wall, near-plane, target transitions, all '
            'mechanics and changed clear return pixels must still pass. Available locals: Vector3 candidate, origin; '
            'float camY, floorY; bool cramped. At most8lines. No helpers, fields, hardcoded replay times or coordinates. '
            '\nEXACT SELECTED LINE:\n'+edit.old,
            [tool('edit_selected_span','Save only the selected overlap height/framing correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if files.path(PATH).read_text()==raw:raise Halt('Measured overlap micro-edit saved no correction')
        candidate=self.checkpoint_source('Local Qwen: preserve camera height during world-overlap correction')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate


if __name__=='__main__':raise SystemExit(main(CameraOverlapMicro))
