#!/usr/bin/env python3
"""Qualify a measured local camera repair against real route, regressions and images."""
import json
import time
import uuid
from continue_game_queue import ContinuousRunner,validate_scoped_review
from resume_three_day_queue import ThreeDayRunner,main
from repair_camera_clearance import ACCEPTED,PROBE,NEXT
from qualify_visual_replay import accepted_fixture,REGRESSIONS,SCENARIO_SHA
from loop_controller.core import Halt,atomic,now,read_json,seal,sha,verify_seal
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.model import tool
from loop_controller.review_summary import critic_evidence,require_combat_contracts
from loop_controller.aim_checks import require_aim_contracts
from loop_controller.runner import git

def validate_qualification_pause(old):
    expected=dict(last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=6,failure_streak=1,
        diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,camera_repair_attempted=True,
        blocker='Camera geometry passes; ordinary route and fresh visual qualification still required')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_qualification_attempted'):
        raise Halt('Expected the exact corrected-camera pause; preserve other faults')
    after=old.get('camera_after_probe',{})
    if (after.get('passed') is not True or after.get('candidate')!=old.get('source_checkpoint')
        or after.get('acceptance_fixture')!='camera-clearance' or not old.get('camera_after_manifest')):
        raise Halt('Ordinary qualification requires a sealed current-source camera clearance PASS')

def require_ordinary_qualification(gate,candidate):
    tests=gate.get('regressions',{}).get('regressions',[])
    if (not gate.get('passed') or gate.get('acceptance_fixture') or gate.get('candidate_commit')!=candidate
        or not gate.get('scoped_facts',{}).get('mission_anchors',{}).get('passed')
        or not gate.get('regressions',{}).get('passed') or {x['test'] for x in tests}!=REGRESSIONS
        or not all(x['gate'].get('passed') and x['gate'].get('candidate_commit')==candidate for x in tests)
        or not require_combat_contracts(gate) or not require_aim_contracts(gate)):
        raise Halt('Camera milestone requires the ordinary current-source route and every mechanics/aim contract')

class CameraQualification(ThreeDayRunner):
    def validate_recovery(self,old):validate_qualification_pause(old)
    def recovery_settings(self):return {'camera_qualification_attempted':True}
    def work(self):
        candidate=git(self.repo,'rev-parse','HEAD');camera=self.store.get('camera_after_probe')
        after_camera=self.store.root/camera['evidence']
        verify_seal(after_camera/'captures',self.store.get('camera_after_manifest'))
        if read_json(after_camera/'camera-contract.json')!=camera:raise Halt('Camera evidence changed')
        before_camera=self.store.root/PROBE
        verify_seal(before_camera/'captures',self.store.get('camera_before_manifest'))
        before,before_seal,probe=accepted_fixture(self,self.store.get('latest_visual_milestone'))
        if sha((before/'scenario.json').read_bytes())!=SCENARIO_SHA:raise Halt('Preserve exact accepted route')
        ident='q%04d-%s'%(self.store.get('rounds',0)+1,uuid.uuid4().hex[:8])
        self.store.set(current_round=ident,rounds=self.store.get('rounds',0)+1,
            current_task='Camera/beacon correction: ordinary route, all regressions, actual image comparison',
            stage='native-camera-ordinary-route');self.store.report()
        bundle,gate=ContinuousRunner.native(self,TASKS[6],ident,candidate,probe)
        if not gate.get('passed'):raise Halt('Camera correction ordinary route failed: '+str(gate.get('failure')))
        self.store.set(stage='camera-mechanics-regressions');self.store.report()
        regression=self.regress(TASKS[6],ident,candidate);gate['regressions']=regression
        if not regression['passed']:gate.update(passed=False,failure=regression['failure'])
        gate['camera_clearance']=camera;atomic(bundle/'scoped-gate.json',gate)
        require_ordinary_qualification(gate,candidate)
        captures=bundle/'captures';digest=seal(captures,{'candidate':candidate,'scope':'camera-beacon-improvement'})
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='fresh-camera-visual-comparison');self.store.report()
        names=['before-drive.png','after-drive.png','before-near.png','after-near.png','after-spawn.png']
        review=self.model.session('critic',ident+'-visual-critic',
            'You are a fresh local critic evaluating a bounded camera/beacon improvement from actual native images.',
            'Compare before-drive.png and after-drive.png at the identical accepted replay t15.5. '
            'The tall beacon should stop hiding the car. Compare before-near.png and after-near.png from the identical '
            'disposable close-wall fixture t6.5. Require a meaningful camera/visibility improvement without clipping, '
            'plus readable ordinary after-spawn.png. Camera geometry, ordinary route and all ten mechanics checks '
            'must pass independently; the fixture never accepts a game. This scope is camera/beacon, not final '
            'Chicago art or ten-minute pacing. Do not pass a still-wall-blocked or unusable view. '
            'Give3-5 prioritized remaining art-quality fixes. Prefer actor/car shape and scene composition over minor windows. '
            'Cite supplied actual filenames.\nNATIVE:'+json.dumps(critic_evidence(gate))+'\nCAMERA:'+json.dumps(camera),
            [tool('submit_review','Return the bounded actual-image verdict.',{
                'verdict':{'type':'string','enum':['PASS','FIX','UNVERIFIED']},'summary':{'type':'string'},
                'fixes':{'type':'array','items':{'type':'string'}}})],
            {'submit_review':lambda _,f:validate_scoped_review(f,names)},
            images=[('before-drive.png ACTUAL accepted t15.5',before/'frame-005.png'),
                    ('after-drive.png ACTUAL current t15.5',captures/'frame-005.png'),
                    ('before-near.png ACTUAL failing wall case t6.5',before_camera/'captures/frame-001.png'),
                    ('after-near.png ACTUAL corrected wall case t6.5',after_camera/'captures/frame-001.png'),
                    ('after-spawn.png ACTUAL current ordinary t3.2',captures/'frame-000.png')],
            turns=2,reasoning_effort='xhigh')
        verify_seal(before,before_seal);verify_seal(captures,digest)
        verify_seal(after_camera/'captures',self.store.get('camera_after_manifest'))
        atomic(bundle/'visual-critic.json',review);self.store.set(visual_focus_review=review)
        if not review.get('ok') or review.get('verdict')!='PASS':
            raise Halt('Camera/beacon visual improvement remains unaccepted; preserve actual criticism')
        record=dict(candidate=candidate,accepted_utc=now(),evidence=str(bundle.relative_to(self.store.root)),
            focus={'decision':'Measured camera collision repair and unobstructed beacon/car view'},review=review,
            capture_manifest_sha256=digest,camera_clearance=camera,final_game_accepted=False)
        path=self.project/'Notes'/('visual-'+ident+'.json');atomic(path,record)
        git(self.repo,'add','--',str(path.relative_to(self.repo)))
        git(self.repo,'-c','user.name=Evidence controller','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Record native camera and beacon improvement; final game remains pending')
        saved=git(self.repo,'rev-parse','HEAD')
        self.store.set(last_playable_checkpoint=saved,source_checkpoint=saved,latest_visual_milestone=record,
            last_verified_progress_epoch=time.time(),last_verified_progress_utc=now(),
            task_design=NEXT,feedback={'visual_review':review,'next_visible_focus':NEXT},stage='camera-milestone-qualified')
        task={**TASKS[6],'id':'camera-beacon-improvement','outcome':record['focus']['decision']}
        queue_milestone(self.store,'accepted-feature',task,bundle,gate,
            [captures/'frame-000.png',captures/'frame-005.png'],{'frame-000.png':3.2,'frame-005.png':15.5},review)
        self.store.event('camera-beacon-qualified',candidate=candidate,checkpoint=saved,
            evidence=record['evidence'],original_failure_counts_preserved=True,final_game_accepted=False)
        self.store.report()
        super().work()

if __name__=='__main__':raise SystemExit(main(CameraQualification))
