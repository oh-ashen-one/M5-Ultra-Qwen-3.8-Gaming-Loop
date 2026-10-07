#!/usr/bin/env python3
"""Finish preserved local export repair after a plain-response output boundary."""
from repair_clothed_character_export import RepairClothedExport,SOURCE,SCRIPT_SHA,PRIOR
from author_clothed_character import ACCEPTED,ART
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

REPAIR_ROUND='q0189-e9223bd2'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=REPAIR_ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Only a completed public source artifact may be saved; no partial output',
        clothed_character_export_repair_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('character_export_retained_attempted'):
        raise Halt('Require unchanged source and the preserved bounded plain repair response')


class RetainedCharacterExport(RepairClothedExport):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.export_path=self.store.root/'evidence'/(PRIOR+'-character-export.json')
        self.failure=read_json(self.export_path)
        response=self.store.root/'private/sessions'/(REPAIR_ROUND+'-character-export-repair')/'response-000.json'
        data=read_json(response);choices=data.get('choices',[])
        if (len(choices)!=1 or choices[0].get('finish_reason')!='length'
                or choices[0].get('message',{}).get('tool_calls')
                or data.get('usage',{}).get('completion_tokens')!=16384
                or sha((self.project/ART).read_bytes())!=SCRIPT_SHA):
            raise Halt('No blind replay: require the actual bounded non-tool response and exact source')
        self.retained=choices[0]['message'];self.response_sha=sha(response.read_bytes())
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False

    def recovery_settings(self):
        return dict(character_export_retained_attempted=True,
            recovery_route='retained-local-export-repair-final-artifact',
            recovery_change='Preserve the16K output boundary and source. Continue the exact returned non-tool local message privately, with explicit final-Python submission and unchanged xhigh. Save only a completed public source through the existing hash-bound edit; no partial application or private-reasoning extraction.',
            character_export_retained_response_sha256=self.response_sha)


if __name__=='__main__':raise SystemExit(main(RetainedCharacterExport))
