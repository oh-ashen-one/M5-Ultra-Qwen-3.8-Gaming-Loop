#!/usr/bin/env python3
"""Close rejected courier art and continue the authorized connected-map scope."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import qualify_one_extension
from loop_controller.core import Halt, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='9062fb834071aa88fc374bce4181e48703a0f2ef'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
REJECTED='e45b26d6e84ac39f55a876e6aa43cddfec0c95d3'
ROUND='q0050-b46a1008'
BLOCKER='Halt: Repeated diagnosed blocker on chicago-polish-whole-route; failed source preserved and last playable state restored'


def validate_map_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=8,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,process_scan_recovery_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_after_courier_attempted'):
        raise Halt('Expected exact preserved courier rejection before the distinct map scope')


class MapAfterCourier(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_map_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Map extension requires exact accepted fallback game')
        gate=read_json(self.store.root/('evidence/'+ROUND+'-resumed-regression-combat-foot/combat-regression-gate.json'))
        if (gate.get('passed') is not False or gate.get('candidate_commit')!=REJECTED or
                gate.get('failure')!=['rival-damage-outside-visible-camera-aim']):
            raise Halt('Preserve the measured courier aim rejection')

    def recovery_settings(self):return {'map_after_courier_attempted':True}

    def work(self):
        self.machine.guard()
        self.store.set(task_design=NEXT_MAP,
            feedback={'closed_courier_candidate':REJECTED,'courier_accepted':False,
                      'next_required_milestone':NEXT_MAP})
        self.store.event('courier-scope-closed-map-prioritized',candidate=REJECTED,
            accepted_fallback=ACCEPTED,outcome='unaccepted',
            reason='Two shots damaged the rival while the camera ray missed its rendered bounds.',
            no_courier_retry=True,original_failure_counts_preserved=True)
        self.store.report()
        qualify_one_extension(self)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),
                      'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(MapAfterCourier))
