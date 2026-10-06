#!/usr/bin/env python3
"""Capture the saved reticle through normal player and explicit camera render paths."""
import json

from resume_camera_native_only import CameraNativeOnly, SOURCE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR = 'q0132-45fc0624'
TASK = dict(id='reticle-dual-path-diagnostic', phase='polish', visual_facing=True,
    outcome='Source-matched actual normal game view and Camera.Render evidence before the local reticle repair')
SCENARIO = dict(id='reticle-dual-path', coverage='foundation', duration=8,
    steps=[dict(start=4, end=6, keys=['W'])], captures=[3.2, 6.5], screen_capture=True)


def capture_receipt(bundle, source, gate):
    captures = bundle / 'captures'
    rows = [json.loads(line) for line in (captures / 'capture-times.jsonl').read_text().splitlines()]
    expected = {kind + '-%03d.png' % index for kind in ('frame', 'screen') for index in range(2)}
    if {r['file'] for r in rows} != expected or len(rows) != len(expected):
        raise Halt('Both normal-screen and explicit-camera captures must be complete')
    result = dict(candidate=source, build_id=gate.get('build_id'), native_passed=gate.get('passed'),
        evidence=bundle.name, images=[], inspected_actual_pixels=False,
        reticle_verdict='pending actual pixel inspection', final_game_accepted=False)
    for row in rows:
        target = row['file'].startswith('frame-')
        if (row['cameraTargetTexture'] is not target or row['renderPath'] !=
                ('explicit-Camera.Render-target' if target else 'normal-player-screen')):
            raise Halt('Render path receipt does not match its actual camera target')
        raw = (captures / row['file']).read_bytes()
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
            raise Halt('Actual PNG capture missing')
        result['images'].append(dict(**row, sha256=sha(raw), bytes=len(raw)))
    return result


class ReticleDualCapture(CameraNativeOnly):
    def validate_recovery(self, old):
        recovery = old.get('current_round') == 'q0133-7016b97e'
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED, current_round=PRIOR,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, camera_native_only_attempted=True,
            blocker='Halt: Saved camera native checks complete with model unloaded; local visual criticism remains required')
        if recovery:
            expected.update(current_round='q0133-7016b97e', reticle_dual_before_attempted=True,
                blocker='Halt: Protected controller harness compilation failed; stop gameplay edits and repair infrastructure')
            failed = self.store.root / 'evidence/q0133-7016b97e'
            errors = read_json(failed / 'gate.json').get('compile_errors', [])
            if (not errors or any('ScreenCapture' not in e and 'Scripts have compiler errors' not in e for e in errors)
                    or (failed / 'captures').exists() or old.get('reticle_capture_module_recovered')):
                raise Halt('Require the exact preserved missing ScreenCapture module compiler failure')
        outcome = old.get('character_camera_outcome', {})
        if (any(old.get(k) != v for k, v in expected.items()) or (old.get('reticle_dual_before_attempted') and not recovery)
                or not outcome.get('native_gate', {}).get('passed')
                or not outcome.get('camera_clearance', {}).get('passed')
                or not outcome.get('full_regressions', {}).get('passed')):
            raise Halt('Require completed saved-camera native checks and preserved sole-owner history')
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False
        self.capture_module_recovery = recovery

    def recovery_settings(self):
        return dict(reticle_dual_before_attempted=True, reticle_capture_module_recovered=self.capture_module_recovery,
            recovery_route='reticle-dual-render-red-evidence',
            recovery_change='Capture actual normal player view and Camera.Render on identical saved source; '
            'keep inference unloaded and preserve prior full gameplay and clearance checks.')

    def work(self):
        ident = self.begin(TASK, 'native-reticle-dual-before')
        bundle = self.store.root / 'evidence' / ident
        gate = self.engines.unity(self.project, bundle, SCENARIO, SOURCE)
        if not gate.get('passed'):
            raise Halt('Dual-render native diagnostic failed; preserve compiler/runtime evidence')
        receipt = capture_receipt(bundle, SOURCE, gate)
        atomic(bundle / 'dual-render-receipt.json', receipt)
        self.store.set(reticle_dual_before=receipt); self.store.report()
        raise Halt('Reticle dual-render before evidence complete; inspect both actual render paths before local repair')


if __name__ == '__main__':
    raise SystemExit(main(ReticleDualCapture))
