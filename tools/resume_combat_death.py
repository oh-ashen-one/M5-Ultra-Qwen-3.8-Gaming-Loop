#!/usr/bin/env python3
"""Continue the same queue with actual lethal-hit/reset evidence."""
import json
from resume_hud_presentation_polish import HudPresentationPolish
from resume_hud_live_objective import ACCEPTED
from resume_three_day_queue import main
from loop_controller.combat_death_checks import DEATH_PROBE, inspect_death
from loop_controller.core import Halt, atomic
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE = '32149663ae0fab28aad2c7f566ec6ef4fbc7086c'
ROUND = 'q0121-98837c39'
TASK = dict(id='combat-lethal-reset', phase='mission', checks=[], maximum=30, coverage='mission-core',
    outcome='Three actual first-hit shots kill the struck rival; ordinary R restores the encounter')


def validate_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=ROUND,
        task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='combat-hit-target-original-regressions',
        blocker='Halt: Local hit-target dependency and original regressions complete; next qualify the planned moving encounter')
    prep = old.get('combat_hit_target_preparation', {})
    if (any(old.get(k) != v for k,v in expected.items()) or old.get('combat_death_attempted')
        or prep.get('candidate') != SOURCE or not prep.get('original_regressions_passed')):
        raise Halt('Require exact completed local hit-target regression boundary and preserved history')


class CombatDeath(HudPresentationPolish):
    def validate_recovery(self, old):
        validate_pause(old)
        self.resume_capacity = False; self.priority_resume = False; self.transport_recovery = False

    def wait_for_capacity(self): self.capacity.wait('native-combat-lethal-reset')

    def recovery_settings(self):
        return dict(combat_death_attempted=True, recovery_route='actual-lethal-hit-reset',
            recovery_change='Extend the original ordinary-input two-shot test to three shots and R reset. '
            'Observe actual target HP, enabled renderers/collider and reset state. No gameplay edits or '
            'secondary-target qualification claim until the moving encounter proves it.')

    def work(self):
        ident = self.begin(TASK, 'native-combat-lethal-reset')
        bundle = self.store.root / 'evidence' / ident
        gate = self.engines.unity(self.project, bundle, DEATH_PROBE, SOURCE)
        if gate.get('passed'):
            rows = [json.loads(x) for x in (bundle / 'captures/trace.jsonl').read_text().splitlines()]
            events = [json.loads(x) for x in (bundle / 'captures/aim-shots.jsonl').read_text().splitlines()]
            gate['death_reset'] = inspect_death(rows, events)
            gate.update(passed=gate['death_reset']['passed'], failure=gate['death_reset']['failure'])
        atomic(bundle / 'combat-death-gate.json', gate)
        self.store.set(combat_death_outcome=dict(candidate=SOURCE, evidence=str(bundle.relative_to(self.store.root)),
            passed=gate.get('passed'), secondary_target_isolation_qualified=False, final_game_accepted=False))
        self.store.report()
        if not gate.get('passed'): raise Halt('Actual lethal-hit/reset needs measured diagnosis: ' + json.dumps(gate.get('failure')))
        raise Halt('Actual lethal-hit/reset qualified; continue local moving-target encounter implementation')


if __name__ == '__main__': raise SystemExit(main(CombatDeath))
