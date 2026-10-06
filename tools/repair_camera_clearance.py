#!/usr/bin/env python3
"""Bounded local-Qwen repair of measured camera defects, preserving the stopped ledger."""
import json
import time
import uuid
from continue_game_queue import ContinuousRunner, validate_scoped_review
from resume_three_day_queue import ThreeDayRunner, main
from resume_visual_focus import changed_span
from probe_camera_clearance import SOURCE, ACCEPTED
from qualify_visual_replay import accepted_fixture, REGRESSIONS, SCENARIO_SHA
from loop_controller.camera_checks import CAMERA_PROBE, inspect_camera
from loop_controller.core import Files, Halt, atomic, now, read_json, seal, sha, verify_seal
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH, queue_milestone
from loop_controller.model import tool
from loop_controller.review_summary import critic_evidence, require_combat_contracts
from loop_controller.aim_checks import require_aim_contracts
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

S={'type':'string'}
RESTORE='1e0c6ac3943be16e3148b441a2bc93caabbce907'
PROBE='evidence/camera-clearance-b8c84a72'
BUILD='445f84ba32f50f2613f4fcc0bfed3a853131593c0441e31c99d6b4392ef47583'
NEXT=('Choose one substantial visible actor/car shape or street-composition improvement from the actual images. '
      'Preserve the newly verified camera, thin-ray combat, objective anchors and controls. No more minor facade windows. '
      'Use one existing original Blender asset, native comparisons and fresh criticism; final ten-minute quality is pending.')

def validate_repair_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
        task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Scoped camera close-wall evidence recorded; original full-route stop preserved')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_repair_attempted'):
        raise Halt('Expected the exact measured camera stop; preserve other faults and failure counters')
    before=old.get('camera_before_probe',{})
    if (before.get('candidate')!=SOURCE or before.get('build_id')!=BUILD or before.get('evidence')!=PROBE
        or before.get('passed') is not False or set(before.get('failure',[]))!={'near-camera-crosses-obstacle','endpoint-camera-crosses-obstacle'}):
        raise Halt('Repair requires the exact native measured camera failures')

def validate_follow_replacement(content):
    if not isinstance(content,str) or len(content.encode())>20000 or len(content.splitlines())>260:
        raise ValueError('Keep the Follow replacement under20KB/260lines')
    if not content.lstrip().startswith('public class Follow : MonoBehaviour') or content.count('class Follow')!=1:
        raise ValueError('Replace only the supplied Follow class and enclosing namespace closing brace')
    if any(x in content for x in ['LoopCamera','LoopInput','LoopSignals','CameraClearanceWall','Destroy(','.enabled = false','.enabled=false']):
        raise ValueError('No fixture/replay branches, signal writes or collider disabling')
    if 'public Transform target' not in content or 'public Vector3 offset' not in content:
        raise ValueError('Preserve the existing Follow target and offset interface')

class CameraRepair(ThreeDayRunner):
    def validate_recovery(self,old):validate_repair_pause(old)
    def recovery_settings(self):return {'camera_repair_attempted':True}

    def restore_unaccepted_route_changes(self,ident):
        files=Files(self.project,self.store)
        for name in ['Mission.cs','VehicleInteraction.cs']:
            path='Assets/Game/'+name;accepted=git(self.repo,'show',RESTORE+':game/'+path)+'\n'
            change=changed_span(files.path(path).read_text(),accepted)
            if not change:continue
            start,end,replacement=change;edit=SelectedEdit(files,path,start,end,max_lines=140)
            def restore(action,fields):
                if fields['content'].rstrip()!=replacement.rstrip():raise ValueError('Use the exact earlier local source span')
                return edit.apply(action,fields['content'])
            self.c.update(output_tokens=4096,model_timeout_seconds=240)
            self.store.set(stage='local-preserve-route-mechanics');self.store.report()
            self.model.session('builder',ident+'-restore-'+name,
                'You are local Qwen restoring your own earlier route mechanics without redesign.',
                'q0044 moved the delivery pad fromX1 toX3.6 and widened boarding while its replay still failed. '
                'Prior accepted native evidence completed the X1 route. Restore exactly this supplied earlier span; '
                'retain q0042 thin beacon geometry. No new logic. Call edit_selected_span. PATH:'+path+
                '\nCURRENT:\n'+edit.old+'\nEARLIER LOCAL REPLACEMENT:\n'+replacement,
                [tool('edit_selected_span','Restore the earlier local source span.',{'content':S})],
                {'edit_selected_span':restore},turns=1,reasoning_effort='low')
            if files.path(path).read_text().rstrip()!=accepted.rstrip():raise Halt('Local route restoration incomplete: '+name)
        self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: preserve proven route anchors and boarding'))

    def local_camera_edit(self,ident,evidence,contract,guidance=''):
        files=Files(self.project,self.store);path='Assets/Game/Bootstrap.cs'
        raw=files.path(path).read_text();marker='    public class Follow : MonoBehaviour'
        if raw.count(marker)!=1:raise Halt('Expected one exact Follow source span')
        prefix,old=raw.split(marker);old=marker+old;before=sha(raw.encode())
        others={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in (self.project/'Assets/Game').glob('*.cs') if p.name!='Bootstrap.cs'}
        def replace(action,fields):
            content=fields['content'];validate_follow_replacement(content)
            if not content.endswith('\n'):content+='\n'
            return files.edit(action,path,before,old=old,new=content)
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-measured-camera-repair');self.store.report()
        result=self.model.session('builder',ident+'-camera-editor',
            'You are the sole local Qwen camera-code author. Fix measured defects using ordinary geometry, never test-specific behavior.',
            'Actual Unity evidence below proves the camera passes beyond a0.65m wall and sits inside an endpoint wall. '
            'The old Max(1.4,hit-.45) can exceed a close hit. Adding dir*.5 after a .45 margin can cross the endpoint. '
            'The old full-hit<1.5 predicate measures proximity to the desired endpoint, not actor visibility. '
            'Replace only Follow, preserving target/offset, normal unobstructed pose and look direction, controls, source outside this span. '
            'Use geometry-safe candidate AND final smoothed positions with camera/near-plane clearance; no minimum that exceeds available space. '
            'Exclude own target colliders appropriately. Handle close walls and transitions without clipping. '
            'Frame the actual target when cramped; do not claim endpoint distance measures actor visibility. '
            'Any crowding/framing rule should use actual target bounds/view/occlusion or honestly be just collision response. '
            'Preserve ordinary thin-ray shooting semantics as far as possible; no aim, mission, collider or asset edits. '
            'Keep compact. Submit the complete supplied Follow span including its final namespace closing brace through replace_follow. '
            'Do not include Bootstrap or Walker. Save once; then finish.\nCURRENT REVIEW GUIDANCE:'+guidance+'\nMEASURED:'+json.dumps(contract)+
            '\nEXACT CURRENT SPAN:\n'+old,
            [tool('replace_follow','Replace only the supplied exact Follow class span.',{'content':S}),
             tool('finish_task','Finish after saving the camera correction.',{'summary':S})],
            {'replace_follow':replace,'finish_task':lambda _,f:{'ok':True,**f}},
            images=[('near.png ACTUAL current close-wall camera',evidence/'captures/frame-001.png'),
                    ('endpoint.png ACTUAL endpoint wall',evidence/'captures/frame-003.png')],turns=3,reasoning_effort='low')
        changed=files.path(path).read_text()
        if changed==raw:raise Halt('Local camera request saved no correction: '+str(result.get('bounded_stop','no edit')))
        if not changed.startswith(prefix) or any(sha(files.path(p).read_bytes())!=h for p,h in others.items()):
            raise Halt('Camera repair exceeded its exact source scope')
        candidate=self.checkpoint_source('Local Qwen: measured close-wall camera correction')
        self.store.set(source_checkpoint=candidate);return candidate

    def camera_probe(self,ident,candidate):
        bundle=self.store.root/'evidence'/ident
        self.store.set(stage='native-camera-repair-validation');self.store.report()
        gate=self.engines.unity(self.project,bundle,CAMERA_PROBE,candidate)
        if not gate.get('passed'):raise Halt('Camera repair native runtime failed: '+str(gate.get('failure')))
        contract=inspect_camera([json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()])
        contract.update(candidate=candidate,build_id=gate['build_id'],evidence=str(bundle.relative_to(self.store.root)),acceptance_fixture='camera-clearance')
        atomic(bundle/'camera-contract.json',contract);digest=seal(bundle/'captures',{'candidate':candidate,'scope':'camera-clearance-diagnostic'})
        self.store.set(camera_after_probe=contract,camera_after_manifest=digest,latest_evidence=contract['evidence']);self.store.report()
        return bundle,contract

    def work(self):
        before=self.store.root/PROBE
        verify_seal(before/'captures',self.store.get('camera_before_manifest'))
        old_contract=read_json(before/'camera-contract.json')
        if old_contract!=self.store.get('camera_before_probe'):raise Halt('Measured camera evidence changed')
        ident='camera-repair-'+uuid.uuid4().hex[:8]
        self.store.set(camera_repair_id=ident)
        self.restore_unaccepted_route_changes(ident)
        evidence,contract=before,old_contract
        for attempt in range(2):
            candidate=self.local_camera_edit(ident+'-'+str(attempt),evidence,contract)
            evidence,contract=self.camera_probe(ident+'-'+str(attempt),candidate)
            if contract['passed']:break
        if not contract['passed']:raise Halt('Two local camera corrections failed the same measured clearance cases; preserve evidence')
        self.store.set(status='paused',stage='camera-clearance-qualified',
            blocker='Camera geometry passes; ordinary route and fresh visual qualification still required')
        self.store.event('camera-clearance-corrected',candidate=candidate,evidence=contract['evidence'],
            original_failure_counts_preserved=True,final_game_accepted=False);self.store.report()

if __name__=='__main__':raise SystemExit(main(CameraRepair))
