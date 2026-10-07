#!/usr/bin/env python3
"""Parent-requested targeted cache/buffer correction, then native transition qualification."""
import json
import uuid
from qualify_camera_repair import CameraQualification
from repair_camera_clearance import CameraRepair,ACCEPTED
from resume_three_day_queue import main
from continue_game_queue import ContinuousRunner
from loop_controller.camera_checks import inspect_target_transitions
from loop_controller.continuous_checks import MOTOR_PROBE
from loop_controller.continuous_tasks import TASKS
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

SOURCE='1f3e41e764f1e6cf6d923b2014a9d6e1c1839e60'
BLOCKER='Halt: Camera milestone requires the ordinary current-source route and every mechanics/aim contract'

def validate_lifecycle_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
        task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        camera_qualification_attempted=True,blocker=BLOCKER)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_lifecycle_attempted'):
        raise Halt('Expected preserved q0045 near-cover stop; parent authorizes only targeted lifecycle corrections')

class CameraLifecycle(CameraQualification):
    def validate_recovery(self,old):validate_lifecycle_pause(old)
    def recovery_settings(self):return {'camera_lifecycle_attempted':True}

    def targeted_edit(self,ident,label,start_needle,end_needle,instruction):
        files=Files(self.project,self.store);path='Assets/Game/Bootstrap.cs';raw=files.path(path).read_text()
        if raw.count(start_needle)!=1 or raw.count(end_needle)!=1:raise Halt('Expected one exact lifecycle span')
        start=raw.index(start_needle);end=raw.index(end_needle,start)
        first=raw.count('\n',0,start)+1;last=raw.count('\n',0,end)
        edit=SelectedEdit(files,path,first,last,max_lines=90)
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='local-camera-'+label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are local Qwen making one targeted correction in your current Follow camera. Preserve unrelated code.',
            instruction+' Replace only the exact supplied span. Keep the public target interface and private Renderer[] rend '
            'field name for observation. No game/mission/boarding/aim redesign, no fixture-specific behavior. '
            'Call edit_selected_span once with the corrected block. The following line after this span stays unchanged: '+end_needle+
            '\nEXACT CURRENT SPAN:\n'+edit.old,
            [tool('edit_selected_span','Save the targeted local camera correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if files.path(path).read_text()==raw:raise Halt('Targeted local camera edit saved no change: '+label)

    def work(self):
        prior=read_json(self.store.root/'evidence/q0045-47f66fb4/scoped-gate.json')
        tests=prior.get('regressions',{}).get('regressions',[])
        bad=[x for x in tests if not x['gate'].get('passed')]
        if len(tests)!=10 or len(bad)!=1 or bad[0]['test']!='aim-near-cover':raise Halt('Preserve unexpected qualification failures')
        ident='camera-lifecycle-'+uuid.uuid4().hex[:8]
        self.store.set(camera_lifecycle_id=ident)
        others={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in (self.project/'Assets/Game').glob('*.cs') if p.name!='Bootstrap.cs'}
        self.targeted_edit(ident,'target-cache','        Renderer[] rend;','            var yaw =',
            'Bootstrap AddComponent<Follow>() invokes Awake BEFORE assigning target. The current cache stays null, and '
            'later player-to-car-to-player target changes cannot refresh it. Lazily refresh rend in LateUpdate whenever '
            'the actual Transform target changes or the cache is absent, including initial assignment. Remember which '
            'target the cache belongs to; clear/handle null safely. Preserve the LateUpdate method opening and return guard '
            'so the next existing var yaw line remains inside it. Do not change the camera algorithm.')
        self.targeted_edit(ident,'overlap-count','            for (int k = 0; k < 5 && Physics.OverlapSphereNonAlloc','            transform.position = pos;',
            'OverlapSphereNonAlloc leaves unused array slots containing stale colliders. In each of the existing at-most-five '
            'correction iterations, record the CURRENT returned count, break when zero, and inspect ONLY indices below that '
            'count. Preserve foreign/own filtering and the current bounded step toward the actor. Do not scan near.Length '
            'or clear unrelated data. The outer method already declares int n for ray hits; use a distinct count variable. '
            'Keep the next transform.position assignment outside the loop.')
        if any(sha((self.project/p).read_bytes())!=h for p,h in others.items()):raise Halt('Lifecycle correction changed unrelated gameplay')
        candidate=self.checkpoint_source('Local Qwen: refresh camera target cache and honor overlap result count')
        self.store.set(source_checkpoint=candidate)
        self.verify_and_continue(ident,candidate)

    def verify_and_continue(self,ident,candidate):
        bundle,camera=CameraRepair.camera_probe(self,ident+'-walls',candidate)
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        caches=[r.get('cameraGeometry',{}) for r in rows if r.get('time',0)>1]
        if not camera['passed'] or not caches or not all(o.get('rendererCacheMatchesTarget') is True for o in caches):
            raise Halt('Lifecycle camera failed near-wall geometry or actual initial target cache')
        self.store.set(stage='native-camera-target-transitions');self.store.report()
        motor,gate=ContinuousRunner.native(self,TASKS[1],ident+'-transitions',candidate,MOTOR_PROBE)
        if not gate.get('passed'):raise Halt('Lifecycle correction failed actual entry/drive/exit/reset')
        rows=[json.loads(x) for x in (motor/'captures/trace.jsonl').read_text().splitlines()]
        transitions=inspect_target_transitions(rows);transitions.update(candidate=candidate,build_id=gate['build_id'])
        atomic(motor/'camera-target-contract.json',transitions);self.store.set(camera_target_transitions=transitions)
        if not transitions['passed']:raise Halt('Actual player-car-player target cache transition failed')
        self.store.event('camera-lifecycle-qualified',candidate=candidate,wall_evidence=camera['evidence'],
            transition_evidence=str(motor.relative_to(self.store.root)),original_failure_counts_preserved=True)
        super().work()

if __name__=='__main__':raise SystemExit(main(CameraLifecycle))
