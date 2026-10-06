#!/usr/bin/env python3
"""Verify local reticle source with inference unloaded and both actual render paths."""
from resume_camera_native_only import CameraNativeOnly, ACCEPTED
from resume_reticle_dual_capture import SCENARIO, capture_receipt
from resume_three_day_queue import main
from repair_camera_clearance import CameraRepair
from qualify_moving_encounter import checked
from loop_controller.core import Halt, atomic, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR = 'q0136-d3f42928'
TASK = dict(id='reticle-native-verification', phase='polish', visual_facing=True,
    outcome='Both reticle render paths, unchanged input-driven route and camera clearance')


class ReticleNative(CameraNativeOnly):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=PRIOR, last_playable_checkpoint=ACCEPTED,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, reticle_render_repair_attempted=True,
            blocker='Halt: Local reticle source saved; unload the idle model deliberately before dual-render native verification')
        authored = old.get('reticle_source_outcome', {})
        if (any(old.get(k) != v for k, v in expected.items()) or old.get('reticle_native_attempted')
                or authored.get('candidate') != old.get('source_checkpoint')
                or authored.get('round') != PRIOR or not authored.get('local_authored')):
            raise Halt('Require the complete local reticle source checkpoint and preserved sole-owner history')
        receipt = read_json(self.store.root / 'private/sessions' / (PRIOR + '-reticle-source') / 'request-000-visual.json')
        if not receipt.get('verified') or receipt.get('reasoning_effort') != 'xhigh' or receipt.get('image_count') != 3:
            raise Halt('Require the actual high-reasoning image request receipt')
        result = read_json(self.store.root / 'evidence' / (PRIOR + '-reticle-author.json'))
        if not result.get('ok'):
            raise Halt('Require a usable complete source save, never a truncated response')
        self.source = old['source_checkpoint']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(reticle_native_attempted=True, recovery_route='local-reticle-native-both-paths',
            recovery_change='Keep inference deliberately unloaded. Check real screen/target PNGs, the prior 95-second '
            'input-driven mission and wall/near-plane clearance without changing any acceptance requirement.')

    def work(self):
        ident = self.begin(TASK, 'native-reticle-dual-after')
        bundle = self.store.root / 'evidence' / (ident + '-dual')
        gate = self.engines.unity(self.project, bundle, SCENARIO, self.source)
        if not gate.get('passed'):
            raise Halt('Local reticle native compile/render failed; preserve source and evidence')
        result = capture_receipt(bundle, self.source, gate)
        atomic(bundle / 'dual-render-receipt.json', result)
        self.store.set(reticle_native_outcome=result); self.store.report()
        self.store.set(stage='native-reticle-route-regression'); self.store.report()
        scenario = read_json(self.store.root / 'evidence/q0132-45fc0624-positive/captures/scenario.json')
        positive = self.store.root / 'evidence' / (ident + '-positive')
        raw = self.engines.unity(self.project, positive, scenario, self.source)
        gameplay = checked(positive, raw, 'positive') if raw.get('passed') else raw
        result['route_passed'] = gameplay.get('passed')
        result['route_evidence'] = positive.name
        if gameplay.get('passed'):
            _, clearance = CameraRepair.camera_probe(self, ident + '-camera-clearance', self.source)
            result['camera_clearance_passed'] = clearance.get('passed')
        atomic(bundle / 'dual-render-receipt.json', result)
        self.store.set(reticle_native_outcome=result); self.store.report()
        if not result.get('route_passed') or not result.get('camera_clearance_passed'):
            raise Halt('Reticle source failed current-source route or camera-clearance regression')
        raise Halt('Local reticle native evidence complete; inspect actual dual-render pixels before scoped acceptance')


if __name__ == '__main__':
    raise SystemExit(main(ReticleNative))
