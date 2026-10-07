#!/usr/bin/env python3
"""Run ordinary inputs and prove original clip playback without promoting art."""
from pathlib import Path
from author_character_runtime import ACCEPTED,SOURCE,SAVED,TASK
from resume_camera_native_only import CameraNativeOnly
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.foot_animation_checks import assess


def scenario():
    return dict(id='original-character-foot-motion',coverage='foundation',duration=18,
        steps=[dict(start=1.8,end=3.0,keys=['Mouse1']),dict(start=4,end=5.1,keys=['S']),
            dict(start=5.5,end=7.1,keys=['W','D','LeftShift']),dict(start=7.4,end=7.7,keys=['F']),
            dict(start=8,end=9.2,keys=['W','Mouse1']),dict(start=9.5,end=9.8,keys=['E']),
            dict(start=10.2,end=12.3,keys=['W']),dict(start=12.3,end=13.3,keys=['S']),
            dict(start=16,end=16.1,keys=['R'])],
        captures=[1,1.2,1.4,1.6,2.1,2.22,2.34,2.46,4.3,4.42,4.54,4.66,
            6,6.12,6.24,6.36,8.3,8.42,8.54,8.66,9.7,11,16.5,17])


class PreviewCharacterFoot(CameraNativeOnly):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,last_playable_checkpoint=ACCEPTED,
            task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,blocker=SAVED,character_foot_runtime_attempted=True)
        result=old.get('character_foot_runtime_source_outcome',{})
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_foot_preview_attempted')
                or result.get('candidate')!=old.get('source_checkpoint') or result.get('prior_character_source')!=SOURCE):
            raise Halt('Require complete local importer/playback/installation and preserved fallback')
        for phase in result['phases']:
            if sha((self.project/phase['path']).read_bytes())!=phase['sha256']:
                raise Halt('Saved original presentation component changed')
        self.source=old['source_checkpoint'];self.source_result=result
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_foot_preview_attempted=True,recovery_route='native-original-foot-clip-articulation-proof',
            recovery_change='Inference unloaded. Original ordinary-input foot/aim/jog and brief existing vehicle/reset sequence with fresh frame bursts. Require actual local joint/clip progress and unchanged capsule/speed; no pose, art, vehicle or full gameplay acceptance is implied.')
    def work(self):
        import json
        ident=self.begin(TASK,'native-original-character-foot-motion')
        bundle=self.store.root/'evidence'/(ident+'-character-foot-motion');replay=scenario()
        gate=self.engines.unity(self.project,bundle,replay,self.source)
        result=dict(passed=False,failures=['native-build-or-runtime-failed'])
        if gate.get('passed'):
            rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            result=assess(rows,read_json(bundle/'build/character-import.json'))
            result.update(trace_sha256=sha((bundle/'captures/trace.jsonl').read_bytes()),
                imported_clips_sha256=sha((bundle/'build/character-import.json').read_bytes()),
                external_checks_sha256=sha((Path(__file__).parent/'loop_controller/foot_animation_checks.py').read_bytes()))
        atomic(bundle/'foot-animation-assessment.json',result)
        outcome=dict(candidate=self.source,prior_playable=ACCEPTED,base_native_gate=gate,
            motion_assessment=result,evidence=bundle.name,local_authored=True,
            visual_review='pending actual pixel and motion sequence inspection',
            known_blender_aim_defect='preserved for focused local repair',
            vehicle_presentation='not integrated',gameplay_promotion=False,final_character_accepted=False)
        atomic(bundle/'character-foot-preview.json',outcome)
        self.store.set(character_foot_native_outcome=outcome);self.store.report()
        frames=sorted((bundle/'captures').glob('frame-*.png'))
        if frames:
            queue_milestone(self.store,'native-milestone',TASK,bundle,
                dict(gate,passed=bool(gate.get('passed') and result['passed']),
                     foot_motion_failures=result['failures']),frames,
                {f'frame-{i:03d}.png':t for i,t in enumerate(replay['captures'])})
        if not gate.get('passed'):raise Halt('Original character foot preview failed native compile/runtime; preserve actual diagnostic')
        if not result['passed']:raise Halt('Original character foot animation evidence failed; preserve exact clip/joint observations')
        raise Halt('Original character foot playback measured; inspect native motion pixels before focused local pose/art and vehicle work')

if __name__=='__main__':raise SystemExit(main(PreviewCharacterFoot))
