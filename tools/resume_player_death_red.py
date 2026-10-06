#!/usr/bin/env python3
"""Reproduce audited chapter death defects through declared native negative tests."""
import json
from resume_camera_native_only import CameraNativeOnly, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.player_death_checks import CASES, death_probe, inspect_player_death

TASK = dict(id='chapter-player-death-reproduction', phase='mission', visual_facing=False,
    outcome='Recorded zero-health handling at all chapter boundaries, attempted controls and ordinary reset')


class PlayerDeathRed(CameraNativeOnly):
    def validate_recovery(self, old):
        self.precision_recovery = old.get('current_round') == 'q0141-31af569a'
        if self.precision_recovery:
            self.validate_precision_recovery(old)
            return
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

    def validate_precision_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round='q0141-31af569a', source_checkpoint='8d23aed0e90336118ece640e5a4e0f092bda6bd0',
            last_playable_checkpoint=ACCEPTED, task_index=7, task_failures=24,
            failure_streak=1, diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
            player_death_red_attempted=True,
            blocker='Halt: Death diagnostic did not reach the intended live chapter; repair the test setup before game changes')
        if any(old.get(k) != v for k,v in expected.items()) or old.get('player_death_precision_recovered'):
            raise Halt('Require the exact relay float32 validator rejection, never an unrelated setup failure')
        prior = old.get('player_death_red_outcome', {}).get('cases', [])
        if [x.get('case') for x in prior] != list(CASES)[:4]:
            raise Halt('Require the four completed original native cases')
        self.reused = []; self.original_proof = {}
        for old_result in prior:
            bundle = self.store.root / 'evidence' / old_result['evidence']
            gate = read_json(bundle / 'gate.json')
            injection = read_json(bundle / 'captures/death-injection.json')
            if not gate.get('passed') or gate.get('candidate_commit') != expected['source_checkpoint']:
                raise Halt('Reuse requires clean original source-matched native execution')
            if old_result['case'] == 'relay-final':
                if (injection.get('time') != 59.599998474121094 or injection.get('healthBefore') != 44
                        or old_result.get('setup_passed') is not False):
                    raise Halt('Preserve a different injection setup failure')
            elif old_result.get('setup_passed') is not True:
                raise Halt('Preserve other chapter setup failures')
            rows = [json.loads(line) for line in (bundle / 'captures/trace.jsonl').read_text().splitlines()]
            result = inspect_player_death(rows, injection, old_result['case'])
            if not result['setup_passed']:
                raise Halt('Corrected float representation must establish every reused setup')
            result.update(candidate=expected['source_checkpoint'], build_id=gate['build_id'],
                evidence=bundle.name, original_native_evidence_reused=True)
            self.reused.append(result)
            for path in (bundle / 'gate.json', bundle / 'player-death-gate.json',
                         bundle / 'captures/trace.jsonl', bundle / 'captures/scenario.json',
                         bundle / 'captures/death-injection.json'):
                self.original_proof[str(path.relative_to(self.store.root))] = sha(path.read_bytes())
        self.source = old['source_checkpoint']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(player_death_red_attempted=True, player_death_precision_recovered=self.precision_recovery,
            recovery_route='native-chapter-death-reproduction',
            recovery_change='Reach chapters through the passing input prefix; inject zero health once in an external '
            'negative fixture, attempt real controls and simultaneous objective edges, then ordinary R reset. '
            'No game source edits or claimed natural-damage death proof.')

    def work(self):
        ident = self.begin(TASK, 'native-chapter-player-death-red')
        original = read_json(self.store.root / 'evidence/q0132-45fc0624-positive/captures/scenario.json')
        results = list(getattr(self, 'reused', []))
        if self.precision_recovery:
            for name, digest in self.original_proof.items():
                if sha((self.store.root / name).read_bytes()) != digest:
                    raise Halt('Original native evidence changed before precision reconciliation')
            atomic(self.store.root / 'evidence' / (ident + '-precision-reconciliation.json'),
                dict(original_files=self.original_proof, original_rejection_preserved=True,
                    changed_rule='Compare the declared Unity float32 boundary using its exact representable value',
                    repeated_native_runs=0, corrected_results=results))
        for case in CASES:
            if any(r['case'] == case for r in results):
                continue
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
