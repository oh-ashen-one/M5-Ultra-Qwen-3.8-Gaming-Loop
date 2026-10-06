#!/usr/bin/env python3
"""Reproduce audited chapter death defects through declared native negative tests."""
import json
from resume_camera_native_only import CameraNativeOnly, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.player_death_checks import CASES, death_probe, inspect_player_death

TASK = dict(id='chapter-player-death-reproduction', phase='mission', visual_facing=False,
    outcome='Recorded zero-health handling at all chapter boundaries, attempted controls and ordinary reset')


class PlayerDeathRed(CameraNativeOnly):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
            failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
            reticle_native_attempted=True,
            blocker='Halt: Local reticle native evidence complete; inspect actual dual-render pixels before scoped acceptance')
        outcome = old.get('reticle_native_outcome', {})
        if (any(old.get(k) != v for k, v in expected.items()) or old.get('player_death_red_attempted')
                or outcome.get('candidate') != old.get('source_checkpoint')
                or not outcome.get('route_passed') or not outcome.get('camera_clearance_passed')):
            raise Halt('Require the preserved local reticle native boundary and original history')
        inspection = read_json(self.store.root / 'evidence' / outcome['evidence'] / 'dual-render-pixel-inspection.json')
        if (not inspection.get('inspected_actual_pixels') or not inspection.get('offscreen_reticle_visible')
                or not inspection.get('normal_screen_reticle_visible') or inspection.get('candidate') != old['source_checkpoint']):
            raise Halt('Complete actual dual-render reticle inspection before the next integration defect')
        self.source = old['source_checkpoint']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(player_death_red_attempted=True, recovery_route='native-chapter-death-reproduction',
            recovery_change='Reach chapters through the passing input prefix; inject zero health once in an external '
            'negative fixture, attempt real controls and simultaneous objective edges, then ordinary R reset. '
            'No game source edits or claimed natural-damage death proof.')

    def work(self):
        ident = self.begin(TASK, 'native-chapter-player-death-red')
        original = read_json(self.store.root / 'evidence/q0132-45fc0624-positive/captures/scenario.json')
        results = []
        for case in CASES:
            bundle = self.store.root / 'evidence' / (ident + '-' + case)
            native = self.engines.unity(self.project, bundle, death_probe(original, case), self.source)
            if not native.get('passed'):
                raise Halt('Death diagnostic compile/runtime prerequisite failed: ' + case)
            captures = bundle / 'captures'
            rows = [json.loads(line) for line in (captures / 'trace.jsonl').read_text().splitlines()]
            result = inspect_player_death(rows, read_json(captures / 'death-injection.json'), case)
            result.update(candidate=self.source, build_id=native['build_id'], evidence=bundle.name)
            atomic(bundle / 'player-death-gate.json', result)
            results.append(result)
            summary = dict(candidate=self.source, cases=results, all_setups_valid=all(r['setup_passed'] for r in results),
                all_cases_complete=len(results)==len(CASES), source_changed=False, final_game_accepted=False)
            atomic(self.store.root / 'evidence' / (ident + '-player-death-red.json'), summary)
            self.store.set(player_death_red_outcome=summary); self.store.report()
            if not result['setup_passed']:
                raise Halt('Death diagnostic did not reach the intended live chapter; repair the test setup before game changes')
        raise Halt('Chapter zero-health reproduction complete; local authoritative death-gating repair is next')


if __name__ == '__main__':
    raise SystemExit(main(PlayerDeathRed))
