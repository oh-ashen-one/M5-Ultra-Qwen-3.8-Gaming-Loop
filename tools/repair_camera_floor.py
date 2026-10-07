#!/usr/bin/env python3
"""Correct the measured camera-to-floor collapse without changing route mechanics."""
import uuid
from repair_camera_lifecycle import CameraLifecycle,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='e29fa2552a7d9c2a4f7b82f747e0d2c53be9bf6e'
def validate_floor_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
        task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        camera_observer_recovery_attempted=True,blocker='Halt: Requested stop')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_floor_repair_attempted'):
        raise Halt('Expected the measured camera-floor boundary stop; preserve other faults')
    if old.get('camera_target_transitions',{}).get('passed') is not True:
        raise Halt('Preserve the actual passing player-car-player cache transition proof')

class CameraFloor(CameraLifecycle):
    def validate_recovery(self,old):validate_floor_pause(old)
    def recovery_settings(self):return {'camera_floor_repair_attempted':True}
    def work(self):
        request=read_json(self.store.root/'camera-framing-stop-request.json')
        if request.get('candidate')!=SOURCE or request.get('stop_file_text')!='cloud-camera-visible-floor-stop-e29fa25\n':
            raise Halt('Expected the exact measured-framing intervention')
        ident='camera-floor-'+uuid.uuid4().hex[:8];self.store.set(camera_floor_id=ident)
        self.targeted_edit(ident,'safe-final-pose','            // Validate the ACTUAL smoothed segment','        }\n    }\n}',
            'The actual 0.65m-wall camera collapses to position(0,0.1063,1.7049), while the player root is '
            '(0,0.135,1.7) and floor top is0.14. No actor bounds sample is in frame; the image is an upward ground/body view. '
            'Cache transitions now pass and must stay unchanged. The current final validation segment begins at the '
            'ground-level target root; its overlap correction also steps toward that root by a fixed0.25m even when '
            'less than0.25m remains, allowing overshoot below the floor. Repair ONLY this final collision/framing block. '
            'Use an above-ground actor-centered collision pivot based on actual bounds. Validate the actual candidate '
            'and final lens clearance against foreign geometry, exclude own actor, honor returned hit counts, and '
            'never step beyond the remaining safe segment or force the camera into the floor. Preserve normal unobstructed '
            'camera pose/aim. In cramped space keep some identifiable actor and the route visible, not an upward view '
            'through the body. The existing final LookAt block is included so it can follow the corrected actual pose. '
            'Do not hardcode a diagnostic wall, change colliders, mission anchors, boarding, input, HP or asset geometry. '
            'Keep this compact (at most90 lines/6000bytes); no new planner or redesign.')
        candidate=self.checkpoint_source('Local Qwen: keep final camera collision correction above the floor')
        self.store.set(source_checkpoint=candidate)
        self.verify_and_continue(ident,candidate)

if __name__=='__main__':raise SystemExit(main(CameraFloor))
