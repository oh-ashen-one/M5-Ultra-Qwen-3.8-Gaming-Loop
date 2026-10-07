#!/usr/bin/env python3
"""Continue the preserved character work after measured official-runtime recovery."""
from resume_character_artifact import CharacterArtifact, SOURCE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR = 'q0128-3f59c879'
SESSION = PRIOR + '-complete-character-source'
RESPONSE = '16be12e21d2a53a75ef9a59af4b7c45f4b8b1bbd98a31a403338dd62ca9827a2'


def validate_boundary(old, response, digest, qualification):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
        current_round=PRIOR, task_index=7, task_failures=24, failure_streak=1,
        diagnosis_used=True, focused_character_attempted=True,
        overall_deadline_epoch=HARD_CAP_EPOCH, stage='local-focused-character-source')
    if any(old.get(k) != v for k, v in expected.items()) or old.get('runtime_character_recovery_attempted'):
        raise Halt('Preserve the exact second output-limit boundary and sole-owner history')
    if not old.get('blocker', '').startswith('Halt: Focused character source was not saved;'):
        raise Halt('Do not resume an unrelated or resource failure')
    choices = response.get('choices', [])
    if (digest != RESPONSE or len(choices) != 1 or choices[0].get('finish_reason') != 'length'
            or choices[0].get('message', {}).get('tool_calls')):
        raise Halt('Require the hash-pinned inspected non-artifact response')
    if (qualification.get('runtime') != '0.7.0' or qualification.get('passed') is not True
            or qualification.get('tool_correct') is not True or qualification.get('vision_correct') is not True
            or qualification.get('generation_tps', {}).get('text-160', 0) < 15):
        raise Halt('Require the measured same-model runtime qualification')


class RuntimeCharacter(CharacterArtifact):
    author_effort = 'low'

    def validate_recovery(self, old):
        self.prior_session = self.store.root / 'private/sessions' / SESSION
        path = self.prior_session / 'response-000.json'
        response = read_json(path)
        qualification = read_json(self.store.root / 'runtime-qualification.json')
        validate_boundary(old, response, sha(path.read_bytes()), qualification)
        self.retained_assistant = response['choices'][0]['message']
        self.prior_proof = {str(p.relative_to(self.store.root)): sha(p.read_bytes()) for p in
            (path, self.prior_session / 'history.json',
             self.store.root / 'evidence' / (PRIOR + '-character-author.json'))}
        self.before = self.store.root / 'evidence/q0126-657b9ebf-positive'
        prior = read_json(self.store.root / 'evidence/q0127-50cd61d4-prior-isolation-reevaluation.json')
        if not prior['result'].get('passed'):
            raise Halt('Preserve native baseline qualification')
        self.proof = prior['original_files']
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False
        self.c['runtime_performance_guard'] = dict(validated_text_tps=qualification['generation_tps']['text-160'])

    def recovery_settings(self):
        return dict(runtime_character_recovery_attempted=True,
            recovery_route='official-runtime-recovered-low-effort-retained-character',
            recovery_change='Preserve both failed responses and all source/counters. Use the second private '
            'response as retained local work, low effort, exact character source and actual/reference pixels; '
            'save one complete file, export, and capture natively with sustained-speed and request-wall bounds.')


if __name__ == '__main__':
    raise SystemExit(main(RuntimeCharacter))
