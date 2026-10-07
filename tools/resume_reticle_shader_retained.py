#!/usr/bin/env python3
"""Submit the retained local shader work without repeating its initial analysis."""
from resume_reticle_shader import ReticleShader, SOURCE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR = 'q0137-e28946db'
DIGEST = '133cc6939a9a1d044579d9b98e4b58de0b59fbbfb2aa88976141dec44ec35c64'


class ReticleShaderRetained(ReticleShader):
    def validate_recovery(self, old):
        expected = dict(status='paused', controller_pid=None, owned_process=None,
            current_round=PRIOR, source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
            task_index=7, task_failures=24, failure_streak=1, diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH, reticle_shader_attempted=True,
            blocker='Halt: Local reticle shader source incomplete; preserve the bounded response and files')
        if any(old.get(k) != v for k, v in expected.items()) or old.get('reticle_shader_retained_attempted'):
            raise Halt('Require the exact shader output-limit stop with unchanged source and counters')
        path = self.store.root / 'private/sessions' / (PRIOR + '-reticle-source') / 'response-000.json'
        response = read_json(path); choice = response['choices'][0]
        if (sha(path.read_bytes()) != DIGEST or choice.get('finish_reason') != 'length'
                or choice['message'].get('tool_calls') or response.get('usage', {}).get('completion_tokens') != 16384):
            raise Halt('Require the preserved complete non-tool local shader response')
        self.retained_assistant = choice['message']
        self.api_review = read_json(self.store.root / 'evidence/q0136-d3f42928-reticle-api-review.json')
        self.before = self.store.root / 'evidence/q0134-e549c186'
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(reticle_shader_retained_attempted=True, recovery_route='retained-local-shader-submission',
            recovery_change='Preserve the16384-token no-source attempt. Retain that exact private work and ask '
            'for the complete two-file submission with xhigh and all original bounds; no identical fresh retry.')


if __name__ == '__main__':
    raise SystemExit(main(ReticleShaderRetained))
