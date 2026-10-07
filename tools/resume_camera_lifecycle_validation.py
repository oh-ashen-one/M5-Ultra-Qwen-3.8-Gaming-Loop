#!/usr/bin/env python3
"""Resume saved local camera code after fixing the observer's obsolete Unity API."""
from repair_camera_lifecycle import CameraLifecycle,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE='e29fa2552a7d9c2a4f7b82f747e0d2c53be9bf6e'
def validate_observer_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,
        task_failures=6,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        camera_lifecycle_attempted=True,blocker='Halt: Camera repair native runtime failed: compile-build')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('camera_observer_recovery_attempted'):
        raise Halt('Expected the exact saved-source observer compile stop; preserve other faults')

class ObserverRecovery(CameraLifecycle):
    def validate_recovery(self,old):validate_observer_pause(old)
    def recovery_settings(self):return {'camera_observer_recovery_attempted':True}
    def work(self):
        ident=self.store.get('camera_lifecycle_id')
        gate=read_json(self.store.root/'evidence'/(ident+'-walls')/'gate.json')
        errors=gate.get('compile_errors','')
        text=str(errors)
        if gate.get('failure')!='compile-build' or 'LoopCameraObservation.cs' not in text or 'GetInstanceID' not in text:
            raise Halt('Expected the diagnosed observer API error; do not bypass another compile fault')
        self.store.event('observer-api-recovery',saved_candidate=SOURCE,game_edits_repeated=False,
            preserved_failure_evidence='evidence/'+ident+'-walls')
        self.verify_and_continue(ident+'-observer-fixed',SOURCE)

if __name__=='__main__':raise SystemExit(main(ObserverRecovery))
