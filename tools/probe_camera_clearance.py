#!/usr/bin/env python3
"""Run the requested close-wall cases on the naturally paused current game, once."""
import json
import uuid
from resume_three_day_queue import ThreeDayRunner, main
from loop_controller.camera_checks import CAMERA_PROBE, inspect_camera
from loop_controller.core import Halt, atomic, read_json, seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='6fe8ed8a721a89822f4ecddf055996855f73fed6'
ACCEPTED='6abdc84913d5d23ffb0b9af45f69209ed47fb6a1'
BLOCKER='Halt: Repeated blocker diagnosis supplied no plan; preserve failure counters and source'


def validate_camera_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
        task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_probe_attempted'):
        raise Halt('Expected the exact unattempted q0044 diagnosis stop; preserve other faults')


class CameraProbe(ThreeDayRunner):
    def validate_recovery(self,old):validate_camera_pause(old)
    def recovery_settings(self):return {'camera_probe_attempted':True}
    def work(self):
        ident='camera-clearance-'+uuid.uuid4().hex[:8]
        self.store.set(stage='native-camera-clearance',camera_diagnostic_id=ident);self.store.report()
        bundle=self.store.root/'evidence'/ident
        gate=self.engines.unity(self.project,bundle,CAMERA_PROBE,SOURCE)
        if not gate.get('passed'):raise Halt('Camera diagnostic runtime failed: '+str(gate.get('failure')))
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        contract=inspect_camera(rows);contract.update(candidate=SOURCE,build_id=gate['build_id'],
            evidence=str(bundle.relative_to(self.store.root)),acceptance_fixture=CAMERA_PROBE['fixture'])
        atomic(bundle/'camera-contract.json',contract)
        digest=seal(bundle/'captures',{'candidate':SOURCE,'scope':'camera-clearance-diagnostic'})
        self.store.set(camera_before_probe=contract,camera_before_manifest=digest,
            latest_evidence=str(bundle.relative_to(self.store.root)),status='paused',
            blocker='Scoped camera close-wall evidence recorded; original full-route stop preserved')
        self.store.event('camera-close-wall-measured',**contract);self.store.report()


if __name__=='__main__':raise SystemExit(main(CameraProbe))
