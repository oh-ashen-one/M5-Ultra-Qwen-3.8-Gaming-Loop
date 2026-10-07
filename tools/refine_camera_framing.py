#!/usr/bin/env python3
"""Use the second bounded local camera edit for the observed body-filling near view."""
from repair_camera_clearance import CameraRepair
from qualify_camera_repair import validate_qualification_pause
from resume_three_day_queue import main
from loop_controller.core import Halt,verify_seal,read_json,sha

SOURCE='f1169bd43c660511802cca5750b1b9d11e050971'
GUIDANCE=('Your first correction PASSES all three wall-clearance measurements, but actual near.png shows the camera '
    'at shin/waist height looking up under the player: the torso fills most of the image and the playable route disappears. '
    'This is not usable close-wall framing. This is the second and final bounded camera correction. Preserve the passing '
    'wall clearance while finding a safe higher/overhead or shoulder pose using real target renderer bounds and real geometry '
    'when space behind is very short. Keep the target identifiable and useful surrounding route visible. The 0.65m wall '
    'is a representative condition, not a special object to detect. Do not change normal unobstructed pose/aim. '
    'Also the current final check projects smoothed pos onto dir then raycasts dir, which is not the actual smoothed '
    'position direction after target rotation. Validate the actual final camera segment/clearance, not that projection; '
    'do not claim a fixed0.22 margin universally proves the near plane. Use compact geometry-aware code. '
    'The source restoration of pad/boarding is complete and frozen. Only Follow may change.')

def validate_refinement_pause(old):
    validate_qualification_pause(old)
    if old.get('source_checkpoint')!=SOURCE or old.get('camera_framing_refinement_attempted'):
        raise Halt('Expected the first measured camera correction; no extra retry budget')

class CameraFraming(CameraRepair):
    def validate_recovery(self,old):validate_refinement_pause(old)
    def recovery_settings(self):return {'camera_framing_refinement_attempted':True,'camera_repair_attempts':2}
    def work(self):
        contract=self.store.get('camera_after_probe');evidence=self.store.root/contract['evidence']
        verify_seal(evidence/'captures',self.store.get('camera_after_manifest'))
        if read_json(evidence/'camera-contract.json')!=contract:raise Halt('Preserve the measured first correction')
        self.store.set(camera_first_repair_probe=contract,camera_first_repair_manifest=self.store.get('camera_after_manifest'))
        self.store.event('cloud-camera-frame-review',candidate=SOURCE,frame_sha256=sha((evidence/'captures/frame-001.png').read_bytes()),
            observation='Clearance passes; near camera body fills the view and loses useful route framing',
            next_action='Second bounded local-Qwen camera edit',cloud_game_code=False)
        ident=self.store.get('camera_repair_id')+'-1'
        candidate=self.local_camera_edit(ident,evidence,contract,GUIDANCE)
        _,result=self.camera_probe(ident,candidate)
        if not result['passed']:raise Halt('Second local camera correction failed measured clearance; preserve source and stop')
        self.store.set(status='paused',stage='camera-clearance-qualified',
            blocker='Camera geometry passes; ordinary route and fresh visual qualification still required')
        self.store.report()

if __name__=='__main__':raise SystemExit(main(CameraFraming))
