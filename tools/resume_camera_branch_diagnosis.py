#!/usr/bin/env python3
"""Measure actual camera branches, obtain local diagnosis, then a cause-bound edit."""
import copy
import json
from resume_street_readability import StreetReadability, SECOND_TASK, ACCEPTED, validate_camera_span
from resume_three_day_queue import main
from repair_camera_clearance import CameraRepair
from continue_game_queue import ContinuousRunner, validate_scoped_review, review_evidence_seal
from qualify_map_extension import promote_qualified_extension
from loop_controller.camera_branch_probe import FIXTURE, SOURCE_SHA, equivalent_trace, changed_pixels
from loop_controller.camera_checks import inspect_target_transitions
from loop_controller.continuous_checks import MOTOR_PROBE
from loop_controller.continuous_tasks import TASKS
from loop_controller.core import Files, Halt, atomic, read_json, sha, verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.runner import git

SOURCE='0af5787bc2a1e57ff5e17bd2d0b984069a659380'
ROUND='q0089-58cdf873'
FRAME_SHA='c6b5b70e0055b242bf527e2f442aea4df020ca065f3edc13122135d77011de15'
TRACE_SHA='707e0e7a14ab2152dcf15c077b3008671e318ed6422c16558ad81ebdfdb7f838'
GATE_SHA='2cdfd4e8747b5992bbf18e830bf6ef60cd4af386e6254b6be8f833388bc4cab1'
PATH='Assets/Game/Bootstrap.cs'
SPANS={'segment':('            // Validate the ACTUAL smoothed segment','            // Final geometry-aware near-plane guard:'),
       'final-clearance':('            // Final geometry-aware near-plane guard:','            transform.position = pos;'),
       'look':('            // Look target:',None)}


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=23,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,street_camera_micro_attempted=True,
        blocker='Halt: Explicit controller stop')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_branch_diagnosis_attempted'):
        raise Halt('Expected exact preserved unchanged-return pause')


class CameraBranchDiagnosis(StreetReadability):
    def validate_recovery(self,old):
        validate_pause(old)
        prior=self.store.root/'evidence'/ROUND
        for path,digest in [('captures/frame-010.png',FRAME_SHA),('captures/trace.jsonl',TRACE_SHA),('gate.json',GATE_SHA)]:
            if sha((prior/path).read_bytes())!=digest:raise Halt('Preserved unchanged-return evidence changed')
        if sha((self.project/PATH).read_bytes())!=SOURCE_SHA:raise Halt('Exact measured camera source required')
        self.sealed_probe();self.accepted_probe()

    def recovery_settings(self):
        return dict(camera_branch_diagnosis_attempted=True,recovery_route='passive-camera-branches-local-cause-repair',
            recovery_change='Measure unchanged-source branch execution in a disposable build; local image/branch diagnosis before a minimal edit; changed clear return required')

    def diagnose(self,ident):
        probe=copy.deepcopy(self.sealed_probe());probe['fixture']=FIXTURE
        bundle=self.store.root/'evidence'/(ident+'-branch-diagnostic')
        self.store.set(stage='native-camera-branch-diagnostic');self.store.report()
        gate=self.engines.unity(self.project,bundle,probe,SOURCE)
        if not gate.get('passed'):raise Halt('Passive camera diagnostic failed native runtime')
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        old=[json.loads(x) for x in (self.store.root/'evidence'/ROUND/'captures/trace.jsonl').read_text().splitlines()]
        if not equivalent_trace(old,rows):raise Halt('Passive diagnostic changed physical/camera behavior; no gameplay diagnosis admitted')
        sample=min(rows,key=lambda r:abs(r['time']-50.49647));trace=sample.get('cameraGeometry',{}).get('branchTrace')
        if not trace or {p['name'] for p in trace.get('phases',[])}!={'desired','smoothed','after-segment','after-world-clearance','final'}:
            raise Halt('Camera diagnostic lacks actual branch observations')
        observed=dict(time=sample['time'],camera=sample['cameraGeometry'],source=SOURCE,
            passive_trace_equivalent=True,instrumentation=read_json(bundle/'camera-instrumentation.json'))
        atomic(bundle/'return-branch-observation.json',observed)
        self.store.set(camera_branch_observation=observed,stage='local-camera-cause-diagnosis');self.store.report()
        raw=(self.project/PATH).read_text();follow=raw[raw.index('    public class Follow'):]
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        def submit(_,f):
            if len(f['cause'])>1800 or len(f['minimal_change'])>1800:raise ValueError('Keep the diagnosis concise and operational')
            return dict(ok=True,**f)
        diagnosis=self.model.session('diagnosis',ident+'-cause-diagnosis',
            'You are local Qwen inspecting your actual return camera and measured branch execution. Return concise findings, not an implementation yet.',
            'The previous target-bounds guard produced byte-identical return pixels and pose. Inspect return.png and actual '
            'per-frame phases, segmentPulled, targetLifted, camera/renderer bounds. Distinguish body intersection from poor '
            'framing; do not assume the guard ran. Name the measured cause and one minimal repair span. '
            'Keep wall/near-plane clearance, ordinary target transitions, aim and controls. No mission or asset redesign. '
            'Submit a short observed cause and minimal action through submit_diagnosis; do not provide private reasoning. '
            '\nACTUAL RETURN OBSERVATIONS:\n'+json.dumps(observed)+'\nEXACT CURRENT FOLLOW:\n'+follow,
            [tool('submit_diagnosis','Record concise measured cause and the smallest camera repair scope.',
                {'cause':{'type':'string'},'span':{'type':'string','enum':list(SPANS)},'minimal_change':{'type':'string'}})],
            {'submit_diagnosis':submit},images=[('return.png ACTUAL unchanged diagnostic native return',bundle/'captures/frame-010.png')],
            turns=1,reasoning_effort='low')
        atomic(bundle/'local-cause-diagnosis.json',diagnosis)
        if not diagnosis.get('ok'):raise Halt('Local branch diagnosis supplied no complete findings; preserve observations before any edit')
        self.store.set(camera_local_cause_diagnosis=diagnosis)
        return diagnosis,observed

    def local_repair(self,ident,diagnosis,observed):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        start,end=SPANS[diagnosis['span']]
        if raw.count(start)!=1 or (end is not None and raw.count(end)!=1):raise Halt('Expected exact diagnosed camera span')
        first=raw.count('\n',0,raw.index(start))+1
        last=raw.count('\n',0,raw.index(end)) if end else len(raw.splitlines())
        edit=SelectedEdit(files,PATH,first,last,max_lines=90)
        def save(action,f):
            validate_camera_span(f['content']);return edit.apply(action,f['content'])
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='local-cause-based-camera-edit');self.store.report()
        self.model.session('builder',ident+'-cause-edit',
            'You are local Qwen implementing one minimal change justified by your measured camera diagnosis.',
            'Save only the selected span. Preserve all source outside it, public fields, renderer cache, target transitions, '
            'world collisions, near plane, aim and mission. No fixed replay times/coordinates, test hooks, asset changes or '
            'collider disabling. A changed clear return image, wall fixtures and every gameplay regression will be required. '
            'Submit edit_selected_span immediately; no replay authoring.\nYOUR CONCISE DIAGNOSIS:\n'+json.dumps(diagnosis)+
            '\nBRANCH PHASES:\n'+json.dumps(observed['camera']['branchTrace']['phases'])+
            '\nEXACT SELECTED SPAN:\n'+edit.old+'\nFULL FOLLOW CONTEXT:\n'+raw[raw.index('    public class Follow'):],
            [tool('edit_selected_span','Save only the measured cause-based camera correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if files.path(PATH).read_text()==raw:raise Halt('Cause-based local editor saved no correction')
        candidate=self.checkpoint_source('Local Qwen: repair measured return-camera branch and framing')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

    def native(self,task,ident,candidate,probe):
        bundle,gate=super().native(task,ident,candidate,probe)
        if task['id']!=SECOND_TASK['id'] or not gate.get('passed'):return bundle,gate
        before=self.store.root/'evidence'/ROUND/'captures/frame-010.png';after=bundle/'captures/frame-010.png'
        if sha(before.read_bytes())!=FRAME_SHA:raise Halt('Original camera comparison changed')
        if not changed_pixels(before,after):
            gate.update(passed=False,failure=['return-camera-pixels-unchanged'])
            atomic(bundle/'scoped-gate.json',gate);return bundle,gate
        digest=review_evidence_seal(bundle/'captures',candidate,task['id'])
        self.store.set(stage='local-before-after-return-review');self.store.report()
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        review=self.model.session('critic',ident+'-return-clarity',
            'You are a fresh local image critic judging one cause-based return-camera correction.',
            'before.png and after.png are actual native frames at the identical50.49647second return input point. '
            'Require a clearly improved readable car/route view without the old near-body obstruction or new geometry '
            'clipping. Mere changed pixels or passing wall tests are insufficient. Existing timeout/HUD styling is unchanged '
            'and outside this camera correction; do not claim mission completion. Cite both actual images. '
            'Return PASS only if the return view is clearly corrected; otherwise FIX with the concrete remaining defect.',
            [tool('submit_review','Judge actual return-camera clarity.',{'verdict':{'type':'string','enum':['PASS','FIX','UNVERIFIED']},
                'summary':{'type':'string'},'fixes':{'type':'array','items':{'type':'string'}}})],
            {'submit_review':lambda _,f:validate_scoped_review(f,['before.png','after.png'])},
            images=[('before.png ACTUAL prior obstructed return',before),('after.png ACTUAL new same-time return',after)],
            turns=1,reasoning_effort='low')
        verify_seal(bundle/'captures',digest);atomic(bundle/'return-camera-review.json',review)
        gate['return_camera_pixels_changed']=True;gate['return_camera_review']=review
        if not review.get('ok') or review.get('verdict')!='PASS':gate.update(passed=False,failure=['return-camera-clarity-not-qualified'])
        atomic(bundle/'scoped-gate.json',gate);return bundle,gate

    def work(self):
        ident=self.begin(SECOND_TASK,'native-branch-diagnosis')
        diagnosis,observed=self.diagnose(ident)
        candidate=self.local_repair(ident,diagnosis,observed)
        _,camera=CameraRepair.camera_probe(self,ident+'-camera-clearance',candidate)
        if not camera['passed']:raise Halt('Cause-based camera repair failed existing wall/near-plane contracts')
        motor,gate=ContinuousRunner.native(self,TASKS[1],ident+'-target-transitions',candidate,MOTOR_PROBE)
        rows=[json.loads(x) for x in (motor/'captures/trace.jsonl').read_text().splitlines()]
        transitions=inspect_target_transitions(rows);atomic(motor/'camera-target-contract.json',transitions)
        if not gate.get('passed') or not transitions['passed']:raise Halt('Cause-based camera repair failed actual target transitions')
        bundle,gate,failure=self.qualify(SECOND_TASK,ident,candidate,self.reuse_probe(candidate))
        if failure:
            self.record_rejection(SECOND_TASK,ident,candidate,failure)
            raise Halt('Cause-based camera/street correction did not qualify; preserve measured failure')
        if not gate.get('return_camera_pixels_changed') or gate.get('return_camera_review',{}).get('verdict')!='PASS':
            raise Halt('No visual promotion without changed clear return pixels')
        record=promote_qualified_extension(self,SECOND_TASK,bundle,gate,read_json(bundle/'critic.json'))
        return self.continue_after_street(record)


if __name__=='__main__':raise SystemExit(main(CameraBranchDiagnosis))
