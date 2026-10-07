#!/usr/bin/env python3
"""Complete the retained importer and continue the same local presentation scope."""
from author_character_runtime import CharacterRuntime,SOURCE,PRIOR,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

FAILED_ROUND='q0199-cb2cf8f4'

class RetainedCharacterRuntime(CharacterRuntime):
    response_tokens=32768
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=SOURCE,
            last_playable_checkpoint=ACCEPTED,current_round=FAILED_ROUND,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            character_foot_runtime_attempted=True,
            blocker='Halt: C# source requires a completed public response; no partial application')
        if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_foot_runtime_retained_attempted')
                or old.get('character_runtime_saved_phases')):
            raise Halt('Require the original bounded importer response and no applied partial components')
        path=self.store.root/'private/sessions'/(FAILED_ROUND+'-importer')/'response-000.json'
        data=read_json(path);choices=data.get('choices',[])
        if (len(choices)!=1 or choices[0].get('finish_reason')!='length'
                or choices[0].get('message',{}).get('tool_calls')
                or data.get('usage',{}).get('completion_tokens')!=16384):
            raise Halt('Require the actual non-tool response boundary; no blind retry')
        self.retained_by_phase={'importer':choices[0]['message']};self.response_sha=sha(path.read_bytes())
        self.bundle=self.store.root/'evidence'/(PRIOR+'-character-preview')
        self.imported=read_json(self.bundle/'build/character-import.json')
        self.review=read_json(self.bundle/'cloud-pixel-review.json')
        if not self.review.get('inspected_actual_pixels') or self.review.get('candidate')!=SOURCE:
            raise Halt('Require the preserved actual native/art review')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_foot_runtime_retained_attempted=True,recovery_route='retained-original-importer-final-component',
            recovery_change='Preserve the16K importer response and unchanged game. Continue its exact private non-tool local output with direct completed C# submission. Use32K for subsequent substantive components within96K working context; same xhigh/model/guards and small independent saved files.',
            character_foot_runtime_retained_response_sha256=self.response_sha)

if __name__=='__main__':raise SystemExit(main(RetainedCharacterRuntime))
