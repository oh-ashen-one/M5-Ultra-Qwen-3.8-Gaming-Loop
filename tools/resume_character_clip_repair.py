#!/usr/bin/env python3
"""Finish the exact retained non-tool clip repair; never apply a partial file."""
from repair_character_clips import RepairCharacterClips,SOURCE,SCRIPT_SHA,ART,PRIOR,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

REPAIR_ROUND='q0194-959438ec'

class RetainedCharacterClipRepair(RepairCharacterClips):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=SOURCE,
            last_playable_checkpoint=ACCEPTED,current_round=REPAIR_ROUND,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            character_clip_repair_attempted=True,
            blocker='Halt: Only a completed public source artifact may be saved; no partial output')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('character_clip_retained_attempted'):
            raise Halt('Require the preserved clip repair output boundary and unchanged owner/history')
        self.export_path=self.store.root/'evidence'/(PRIOR+'-character-export.json')
        response=self.store.root/'private/sessions'/(REPAIR_ROUND+'-character-clip-repair')/'response-000.json'
        d=read_json(response);choices=d.get('choices',[])
        if (len(choices)!=1 or choices[0].get('finish_reason')!='length'
                or choices[0].get('message',{}).get('tool_calls')
                or d.get('usage',{}).get('completion_tokens')!=32768
                or sha((self.project/ART).read_bytes())!=SCRIPT_SHA):
            raise Halt('Require the exact bounded non-tool local response; no blind replay')
        self.retained=choices[0]['message'];self.response_sha=sha(response.read_bytes())
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_clip_retained_attempted=True,
            recovery_route='retained-local-clip-repair-complete-final-artifact',
            recovery_change='Preserve the32K output boundary, original source and failed export. Continue the exact private non-tool local response with direct final-Python submission. Same xhigh/model/guards; only a completed public artifact can save.',
            character_clip_retained_response_sha256=self.response_sha)

if __name__=='__main__':raise SystemExit(main(RetainedCharacterClipRepair))
