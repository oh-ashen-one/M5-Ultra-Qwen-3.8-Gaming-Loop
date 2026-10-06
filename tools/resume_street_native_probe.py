#!/usr/bin/env python3
"""Run a disclosed external acceptance probe after preserving local replay exhaustion."""
import copy
import json
from resume_saved_door import SavedDoor, ACCEPTED
from resume_three_day_queue import main
from resume_alley_presentation import REPLAY
from loop_controller.core import Halt, sha
from loop_controller.continuous_checks import validate_proposed
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import replay_identity

SOURCE='6f9244b9045039e0749cd85489e55114b345e448'
ROUND='q0080-35287f55'
RESPONSE_SHA='7fc117d58452e7c82ca6461a5113d5351fa4aa5c3d9607a3faf534996574b784'
BLOCKER='Halt: Second-street replay supplied no complete bounded tool submission'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=20,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,
        street_submission_recovered=True,saved_door_accepted=False,second_street_attempts=1)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('street_native_probe_attempted'):
        raise Halt('Expected exact saved street source and exhausted replay stop')


def retimed_probe(accepted):
    if replay_identity(accepted)!=REPLAY:raise Halt('Require the immutable native-passing alley input sequence')
    probe=copy.deepcopy(accepted)
    # Extend the existing straight movement intervals; preserve approach,
    # boarding, steering and coasting. These are external test inputs, not
    # gameplay code or a claim that the new route has already succeeded.
    # Observed walker speed is3.2m/s. Vehicle limits are8m/s forward and3m/s
    # reverse, so1.5s additional full throttle needs4s additional reverse.
    extensions=[(accepted['steps'][1]['end'],5.0),(accepted['steps'][2]['end'],5.0),
                (accepted['steps'][7]['end'],1.5),(accepted['steps'][8]['end'],4.0)]
    def shifted(t):return round(t+sum(extra for boundary,extra in extensions if t>=boundary-1e-7),5)
    for before,after in zip(accepted['steps'],probe['steps']):
        after['start']=shifted(before['start']);after['end']=shifted(before['end'])
    probe['captures']=[shifted(t) for t in accepted['captures']]
    probe['duration']=shifted(accepted['duration'])
    return validate_proposed(probe,150,'foundation')


class StreetNativeProbe(SavedDoor):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-street-replay')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Preserve original replay exhaustion')
        choice=json.loads(raw)['choices'][0]
        if choice.get('finish_reason')!='length' or choice['message'].get('tool_calls'):
            raise Halt('Expected no executable submission from the original replay role')
        retimed_probe(self.accepted_probe())

    def recovery_settings(self):
        return dict(street_native_probe_attempted=True,street_native_probe_pending=True,
            recovery_route='saved-local-street-external-native-probe',
            recovery_change='Disclosed controller-authored acceptance timings derived from the proven local alley replay; no gameplay source changes')

    def local_street_source(self,ident):
        if self.store.get('street_native_probe_pending'):
            self.store.event('test-saved-local-street-without-regeneration',candidate=SOURCE,
                source_author='local Qwen',test_author='disclosed cloud controller',native_pass_claimed=False)
            return SOURCE
        return super().local_street_source(ident)

    def local_street_replay(self,ident):
        if self.store.get('street_native_probe_pending'):
            scenario=retimed_probe(self.accepted_probe())
            self.store.set(street_native_probe_pending=False)
            self.store.event('external-street-probe-composed',candidate=SOURCE,scenario=scenario,
                physical_input_base=REPLAY,test_author='disclosed cloud controller',
                local_gameplay_source_unchanged=True,local_replay_exhaustion_preserved=True,
                inputs='Normal W/A/S/D/E only; longer straight outward/return legs, no reset or teleport',
                expected_outcome='Foot/car beyond both old regions and physical return; unverified until native gate')
            return scenario
        return super().local_street_replay(ident)

    def work(self):
        self.store.set(saved_door_probe=self.accepted_probe())
        return self.advance_second_street()


if __name__=='__main__':raise SystemExit(main(StreetNativeProbe))
