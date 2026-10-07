#!/usr/bin/env python3
"""Qualify one measured input composition, then continue the existing local game queue."""
import json
import uuid

from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from resume_cover_evidence import QUALIFIED, ACCEPTED
from loop_controller.aim_checks import inspect_aim_contract
from loop_controller.combat_checks import FOOT_PROBE, inspect_combat_contract
from loop_controller.continuous_checks import validate_proposed
from loop_controller.continuous_tasks import TASKS
from loop_controller.core import Halt, atomic, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.runner import git


BLOCKER = 'Halt: Repeated blocker diagnosis supplied no plan; preserve failure counters and source'


def validate_integrated_pause(old):
    expected = dict(source_checkpoint=QUALIFIED, last_playable_checkpoint=ACCEPTED,
                    task_index=6, task_failures=6, failure_streak=2, diagnosis_used=True,
                    overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
    if any(old.get(key) != value for key, value in expected.items()):
        raise Halt('Expected only the inspected q0034 replay/diagnosis stop; preserve unrelated faults')
    if old.get('integrated_recovery_attempted'):
        raise Halt('The bounded integrated replay recovery has already been attempted')


def integrated_probe(accepted_retry):
    """Keep proven firing and post-failure inputs; connect them with ordinary car controls."""
    retry = validate_proposed(accepted_retry, TASKS[3]['maximum'], TASKS[3]['coverage'])
    if retry['duration'] != 52 or not any(
            s == dict(start=32, end=32.3, keys=['R']) for s in retry['steps']):
        raise Halt('Expected the accepted 32-second failure/retry input sequence')
    steps = [dict(s, keys=list(s['keys'])) for s in FOOT_PROBE['steps']]
    # The observed firing pose is (0.96, 0.135, 5.86), with the coupe near
    # (3.36, -0.01, 7.96). This measured connector reaches its left rear side.
    # Acceptance must observe actual entry and sustained escape, never infer them.
    steps += [dict(start=9.8, end=10.55, keys=['W', 'D']),
              dict(start=10.8, end=11.05, keys=['E']),
              dict(start=11.2, end=23.4, keys=['W']),
              dict(start=24, end=24.3, keys=['E'])]
    steps += [dict(s, keys=list(s['keys'])) for s in retry['steps'] if s['start'] >= 32]
    return validate_proposed(dict(duration=52, steps=steps,
        captures=[3.2, 6.9, 7.55, 9.25, 11.1, 15.5, 18, 24.5, 31, 32.5, 39.9, 44.5, 47.2, 50.5]),
        TASKS[6]['maximum'], TASKS[6]['coverage'])


class IntegratedRouteResume(ThreeDayRunner):
    def validate_recovery(self, old):
        validate_integrated_pause(old)

    def recovery_settings(self):
        return {'integrated_recovery_attempted': True}

    def stop_failed_recovery(self, ident, candidate, feedback):
        self.store.set(integrated_recovery_result=feedback, feedback=feedback, stage='rejected')
        self.store.event('integrated-recovery-not-accepted', round=ident, candidate=candidate,
                         original_failure_counts_preserved=True, game_source_mutated=False)
        raise Halt('Bounded integrated replay recovery did not pass; preserve source, counters and evidence')

    def work(self):
        self.machine.guard()
        task = TASKS[6]
        candidate = git(self.repo, 'rev-parse', 'HEAD')
        if candidate != QUALIFIED:
            raise Halt('Integrated recovery requires the unchanged qualified thin-ray source')
        accepted = self.store.get('accepted_queue_features', {}).get('mission-failure-retry')
        if not accepted:
            raise Halt('Missing accepted failure/retry provenance')
        previous = self.store.root / accepted['evidence']
        prior_gate = read_json(previous / 'scoped-gate.json')
        if not prior_gate.get('passed') or prior_gate.get('candidate_commit') != accepted['candidate']:
            raise Halt('Accepted failure/retry record mismatch')
        probe = integrated_probe(read_json(previous / 'captures/scenario.json'))
        ident = 'q%04d-%s' % (self.store.get('rounds', 0) + 1, uuid.uuid4().hex[:8])
        self.store.set(current_round=ident, rounds=self.store.get('rounds', 0) + 1,
                       current_task=task['outcome'], phase=task['phase'], stage='native-integrated-recovery',
                       last_valid_replay=probe)
        self.store.event('integrated-replay-recovery', round=ident, source=candidate,
            author='cloud controller acceptance-input composition', game_source_mutated=False,
            provenance=['qualified FOOT_PROBE', accepted['evidence']],
            cause='q0033/q0034 fired while the camera ray missed the rival; bounded diagnosis returned no plan',
            original_failure_counts_preserved=True, extra_fixture=False)
        self.store.report()
        # Queue the milestone only after the added in-route checks and regressions;
        # the ordinary native wrapper queues earlier than this recovery's scope.
        bundle, gate = ContinuousRunner.native(self, task, ident, candidate, probe)
        if gate.get('passed'):
            rows = [json.loads(x) for x in (bundle / 'captures/trace.jsonl').read_text().splitlines()]
            events = [json.loads(x) for x in (bundle / 'captures/aim-shots.jsonl').read_text().splitlines()]
            drive = inspect_combat_contract(rows, 'driving')
            aim = inspect_aim_contract(events, 'aligned')
            gate.update(integrated_driving=drive, integrated_aim=aim)
            if not drive['passed'] or not aim['passed']:
                gate.update(passed=False, failure=(drive.get('failure') or []) + (aim.get('failure') or []))
        atomic(bundle / 'scoped-gate.json', gate)
        if not gate.get('passed'):
            self.stop_failed_recovery(ident, candidate, gate)
        self.store.set(stage='integrated-regressions'); self.store.report()
        regression = self.regress(task, ident, candidate)
        gate['regressions'] = regression
        if not regression['passed']:
            gate.update(passed=False, failure=regression['failure'])
        atomic(bundle / 'scoped-gate.json', gate)
        if not gate.get('passed'):
            self.stop_failed_recovery(ident, candidate, gate)
        self.store.set(stage='fresh-integrated-critique', latest_evidence=str(bundle.relative_to(self.store.root)))
        self.store.report()
        review = self.review(task, ident, bundle, gate)
        if not review.get('ok') or review.get('verdict') != 'PASS':
            self.stop_failed_recovery(ident, candidate, review)
        self.store.set(integrated_recovery_result={'passed': True, 'evidence': str(bundle.relative_to(self.store.root))})
        self.promote(task, candidate, bundle, gate, review)
        # Only genuine native/regression/fresh-local-review acceptance advances
        # the existing owner into substantial Chicago art and pacing work.
        return super().work()


if __name__ == '__main__':
    raise SystemExit(main(IntegratedRouteResume))
