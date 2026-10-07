#!/usr/bin/env python3
"""A diagnosed incomplete 16K tool response gets one bounded 32K artifact save."""
from author_clothed_character import ClothedCharacter, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt, read_json, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR = 'q0185-47b1c305'


def validate_boundary(old, response, speed):
    expected = dict(status='paused', controller_pid=None, owned_process=None,
        source_checkpoint=ACCEPTED, last_playable_checkpoint=ACCEPTED,
        current_round=PRIOR, task_index=7, task_failures=24, failure_streak=1,
        diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker="KeyError: 'choices'", clothed_character_author_attempted=True)
    if (any(old.get(k) != v for k, v in expected.items()) or old.get('clothed_character_budget_attempted')
            or response.get('error', {}).get('code') != 'incomplete_tool_call' or response.get('choices')
            or speed.get('status') != 'finished' or not speed.get('samples')
            or speed['samples'][-1]['generated_tokens'] < 16000):
        raise Halt('Require the exact incomplete-output fault, no source save, and advancing generation evidence')


class ClothedCharacterBudget(ClothedCharacter):
    response_tokens = 32768

    def validate_recovery(self, old):
        session = self.store.root/'private/sessions'/(PRIOR+'-clothed-character')
        response = read_json(session/'response-000.json')
        speed = read_json(session/'speed-watch-000.json')
        validate_boundary(old, response, speed)
        self.preserved = {name: sha((session/name).read_bytes())
            for name in ('response-000.json', 'history.json', 'speed-watch-000.json', 'request-000-settings.json')}
        self.resume_capacity = self.priority_resume = self.transport_recovery = self.admission_recovery = False

    def recovery_settings(self):
        return dict(clothed_character_budget_attempted=True,
            recovery_route='diagnosed-incomplete-tool-output-32K-character-save',
            recovery_change='Original16K request generated steadily to the output boundary but server returned incomplete_tool_call with no choices/source. Preserve exact error/history privately; no partial tool replay. Same original art task/model/xhigh/images with32K output inside98K working context,600second request cap and unchanged resource/deadline guards.',
            clothed_character_original_fault=dict(round=PRIOR, files=self.preserved, no_source_saved=True))


if __name__ == '__main__':
    raise SystemExit(main(ClothedCharacterBudget))
