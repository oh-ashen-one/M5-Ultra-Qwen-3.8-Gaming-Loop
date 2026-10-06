#!/usr/bin/env python3
"""Qualify the saved map using Qwen's unchanged replay with recognized key casing."""
import json
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner,main
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK,qualify_one_extension
from loop_controller.core import Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.replay_contract import validate_submission
from loop_controller.runner import git

SOURCE='4918935c9989b942b4dff908dcc9dce6e376a584'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0055-72f3967e'
BLOCKER='Halt: Small-span map replay not submitted; saved source preserved'
RESPONSE_SHA='24133c401efb61ef6140e970a7e6ba2766577e12671fd61bcb5c787924a497fc'
SESSION=ROUND+'-map-replay'


def validate_replay_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=8,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,pavement_completion_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_replay_case_recovery_attempted'):
        raise Halt('Expected exact preserved map replay key-format stop')


def saved_replay(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Completed local replay proposal changed')
    value=json.loads(raw);choice=value['choices'][0];calls=choice['message'].get('tool_calls') or []
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='finish_task':
        raise Halt('Expected one complete local replay submission')
    fields=calls[0]['function']['arguments']
    if isinstance(fields,str):fields=json.loads(fields)
    result=validate_submission(fields,MAP_TASK)
    if not result['input_key_normalizations']:raise Halt('Expected diagnosed lowercase-key proposal')
    return result


class MapReplayCaseRecovery(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_replay_pause(old)
        saved_replay((self.store.root/'private/sessions'/SESSION/'response-001.json').read_bytes())

    def recovery_settings(self):return {'map_replay_case_recovery_attempted':True}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Saved map source changed before qualification')
        result=saved_replay((self.store.root/'private/sessions'/SESSION/'response-001.json').read_bytes())
        self.store.set(last_valid_replay=result['scenario'])
        self.store.event('normalize-saved-replay-key-spelling',original_session=SESSION,
            response_sha256=RESPONSE_SHA,normalizations=result['input_key_normalizations'],
            durations_and_capture_times_unchanged=True,game_source_unchanged=True,
            replay_author='local Qwen',normalization_author='cloud controller protocol adapter',
            native_pass_claimed=False)
        return result

    def work(self):
        self.machine.guard();self.store.set(task_design=NEXT_MAP)
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(MapReplayCaseRecovery))
