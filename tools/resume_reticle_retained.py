#!/usr/bin/env python3
"""Continue the high-effort local work with more submission room, preserving its failed attempt."""
from resume_reticle_source import ReticleSource, PRIOR
from resume_camera_native_only import SOURCE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

FAILED = 'q0135-8cd67cb5'
DIGEST = 'f52c4b83b58ffc91d703a62ef9764721593f9973b06af949b970cfebe95224d5'


class ReticleRetained(ReticleSource):
    reticle_output_tokens = 16384

    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=FAILED, source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, reticle_render_repair_attempted=True,
            blocker='Halt: No complete reticle source saved; preserve the bounded local response for diagnosis')
        if any(old.get(k) != v for k, v in expected.items()) or old.get('reticle_retained_attempted'):
            raise Halt('Require the exact high-effort output-limit stop; never an identical retry or unrelated fault')
        path = self.store.root / 'private/sessions' / (FAILED + '-reticle-source') / 'response-000.json'
        response = read_json(path)
        choice = response['choices'][0]
        if (sha(path.read_bytes()) != DIGEST or choice.get('finish_reason') != 'length'
                or choice['message'].get('tool_calls') or response.get('usage', {}).get('completion_tokens') != 8192):
            raise Halt('Require the complete preserved non-tool output-limit response')
        self.retained_assistant = choice['message']
        self.before = self.store.root / 'evidence' / PRIOR
        self.inspection = read_json(self.before / 'dual-render-pixel-inspection.json')
        receipt = read_json(self.before / 'dual-render-receipt.json')
        if not self.inspection.get('inspected_actual_pixels') or not receipt.get('native_passed'):
            raise Halt('Preserve the actual diagnostic evidence')
        for row in receipt['images']:
            if sha((self.before / 'captures' / row['file']).read_bytes()) != row['sha256']:
                raise Halt('Retained work must use identical inspected before pixels')
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(reticle_retained_attempted=True, recovery_route='retained-high-effort-reticle-submission',
            recovery_change='Preserve the 8192-token no-source stop. Retain that exact private local response, '
            'keep xhigh, and allow16384output tokens for one complete bounded rendering span. '
            'Same resident and memory/speed/wall guards; no partial-code extraction or automatic restart.')


if __name__ == '__main__':
    raise SystemExit(main(ReticleRetained))
