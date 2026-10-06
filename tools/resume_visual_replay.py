#!/usr/bin/env python3
"""Recover the exact saved q0041 replay stop, then keep the sole queue advancing."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from qualify_visual_replay import qualify_saved_visual_candidate
from loop_controller.core import Halt
from loop_controller.continuous_tasks import TASKS
from loop_controller.delivery_policy import HARD_CAP_EPOCH

SOURCE = '932f4a8ad4bf9bb7662cbd4b888c19236fe94247'
ACCEPTED = '6abdc84913d5d23ffb0b9af45f69209ed47fb6a1'
ROUND = 'q0041-71098791'
BLOCKER = 'Halt: Replay-only role supplied no valid finish_task; required: summary, duration, input_steps, captures'


def validate_visual_replay_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
                    current_round=ROUND, task_index=7, task_failures=2, failure_streak=1,
                    diagnosis_used=False, overall_deadline_epoch=HARD_CAP_EPOCH, blocker=BLOCKER)
    if any(old.get(k) != v for k, v in expected.items()) or old.get('visual_replay_recovery_attempted'):
        raise Halt('Expected the exact unattempted q0041 replay-authoring pause; preserve other faults')


class VisualReplayResume(ThreeDayRunner):
    def validate_recovery(self, old):validate_visual_replay_pause(old)
    def recovery_settings(self):return {'visual_replay_recovery_attempted': True}

    def work(self):
        self.machine.guard()
        if not qualify_saved_visual_candidate(self, TASKS[7], ROUND, SOURCE):
            raise Halt('Saved q0041 no longer qualifies for visual-only replay reuse')
        return ContinuousRunner.work(self)


if __name__ == '__main__':raise SystemExit(main(VisualReplayResume))
