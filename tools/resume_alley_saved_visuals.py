#!/usr/bin/env python3
"""Qualify saved local lighting/props after an optional detail role exhausted output."""
import json
from resume_three_day_queue import main
from resume_alley_readability import AlleyReadability, add_junction_captures, ROUND as PRIOR_ROUND
from resume_map_traversal import ACCEPTED
from resume_alley_presentation import REPLAY
from qualify_map_extension import MAP_TASK
from loop_controller.core import Halt, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git

SOURCE='8439ae8789793a881c51003cad94e39fc7210c01'
ROUND='q0073-0d2c6d2f'
RESPONSE_SHA='cfa108b38944e3c585f198bde98491fbdb0d9d3b53a5ade654c4a7b77f6b9d7f'


def validate_saved_visual_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=17,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,alley_readability_recovery_attempted=True,
        blocker='Halt: Scoped readability edit not saved; prior local source preserved')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('alley_saved_visuals_attempted'):
        raise Halt('Expected exact preserved partial visual source, not a different failure')
    if replay_identity(old['last_valid_replay'])!=REPLAY:raise Halt('Preserve proven physical inputs')


class SavedVisuals(AlleyReadability):
    def validate_recovery(self,old):
        validate_saved_visual_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-service-door-detail')/'response-000.json').read_bytes()
        if sha(raw)!=RESPONSE_SHA:raise Halt('Original output-limit record changed')
        c=json.loads(raw)['choices'][0]
        if c.get('finish_reason')!='length' or c['message'].get('tool_calls'):
            raise Halt('Expected no complete door edit; never recover truncated output')

    def recovery_settings(self):
        return dict(alley_saved_visuals_attempted=True,recovery_route='qualify-saved-visual-progress',
            recovery_change='Native proof of saved local lighting/props; optional door edit remains deferred',
            deferred_visual_detail='Service-door role exhausted4096tokens without a tool call; no door code saved')

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Preserve saved local source')
        probe=self.store.get('last_valid_replay')
        if replay_identity(probe)!=REPLAY:raise Halt('Preserve physical inputs')
        bundle=self.store.root/'evidence'/PRIOR_ROUND
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        scenario=add_junction_captures(probe,rows)
        self.store.set(last_valid_replay=scenario,stage='qualify-saved-local-lighting-props')
        self.store.event('saved-local-visuals-native-qualification',candidate=SOURCE,
            unchanged_game_source=True,physical_inputs_unchanged=True,
            door_detail_saved=False,output_limit_preserved=True,
            all_ten_and_fresh_critic_required=True,cloud_game_code_authored=False)
        return dict(ok=True,scenario=scenario)


if __name__=='__main__':raise SystemExit(main(SavedVisuals))
