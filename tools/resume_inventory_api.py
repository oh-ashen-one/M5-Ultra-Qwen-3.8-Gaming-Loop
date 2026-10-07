#!/usr/bin/env python3
"""Requalify the exact saved street after repairing the controller recorder API."""
import json
from resume_complete_inventory import CompleteInventory, CANDIDATE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git

SOURCE='fe8f342f77ac0bfa53beadb866adea84a030668f'
ROUND='q0084-b5d03d5d'
COMPILE_ROUND='q0083-a8af5ee5'
COMPILE_GATE_SHA='1aa6eb46024ac6e00732a4118295463882efda00c418d9e89d3bc0c17568f278'
EARLIER_SOURCE='1ebf314a8cbcb96e5615b065c82339ff2afbc447'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=22,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker='Halt: Explicit controller stop',
        street_native_probe_attempted=True,saved_door_accepted=False,second_street_attempts=3,
        complete_inventory_recovery_attempted=True,complete_inventory_native_attempts=1)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('inventory_api_recovery_attempted'):
        raise Halt('Expected exact recorder API pause with all local edits and counters preserved')


class InventoryApiRecovery(CompleteInventory):
    preserved_source=SOURCE
    native_attempt=2

    def validate_recovery(self,old):
        validate_pause(old)
        self.validate_recorded_fault()
        raw=(self.store.root/'evidence'/COMPILE_ROUND/'scoped-gate.json').read_bytes()
        if sha(raw)!=COMPILE_GATE_SHA:raise Halt('Original controller compile failure changed')
        gate=json.loads(raw)
        if (gate.get('candidate_commit')!=CANDIDATE or gate.get('passed') or
            not any('Assets/LoopHarness/LoopRuntime.cs' in line and 'GetInstanceID' in line
                    for line in gate.get('compile_errors',[]))):
            raise Halt('Expected the observed controller API failure')
        git(self.repo,'merge-base','--is-ancestor',EARLIER_SOURCE,SOURCE)

    def recovery_settings(self):
        return dict(inventory_api_recovery_attempted=True,
            recovery_route='native-entity-id-complete-inventory',
            recovery_change='Repair controller API and compile-fault routing; preserve both speculative local edits and unchanged source/replay/support/prop criteria')

    def after_native_failure(self):
        # The previous attempt was diverted by an infrastructure compile error.
        # Preserve its counter and permit one new local repair only after a
        # complete native observation establishes an actual game failure.
        self.store.event('complete-native-evidence-local-repair',previous_attempts=3,
            bounded_new_attempt=4,original_failure_history_preserved=True)
        return self.advance_second_street(start_attempt=4,last_attempt=4)


if __name__=='__main__':raise SystemExit(main(InventoryApiRecovery))
