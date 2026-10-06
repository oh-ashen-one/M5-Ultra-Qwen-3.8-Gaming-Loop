#!/usr/bin/env python3
"""Apply only the exact complete local final-answer ground patch, never reasoning."""
import json
import re
from resume_chapter_presentation import ChapterPresentation,PATH,ACCEPTED
from resume_measured_chapter_layout import GATE_SHA
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.small_edits import SelectedEdit

SOURCE='0eb5fb8f23c546104c6639383295070b0ffb29ef'
ROUND='q0104-1a943847'
RESPONSE_SHA='567946264ffeacbefecda185e4714f142578588700ed7a4f23ebe2ab6adf62a2'

def saved_patch(raw,expected):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original completed local response changed')
    choice=json.loads(raw)['choices'][0];message=choice['message']
    if choice.get('finish_reason')!='stop' or message.get('tool_calls'):
        raise Halt('Require the original complete final answer, not a truncated or tool response')
    # Only public final-answer content is inspected. Private reasoning is never
    # a source patch, and no generic marker/file replay is enabled.
    blocks=re.findall(r'```csharp\n(.*?)\n```',message.get('content') or '',re.S)
    if len(blocks)!=1 or blocks[0].rstrip('\n')!=expected.rstrip('\n'):
        raise Halt('Require exactly the already scoped seven-line correction, byte-for-byte')
    return blocks[0]+'\n'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,presentation_measured_repair_attempted=True,
        stage='local-cache-ground-offset',blocker='Halt: Local cache ground-offset correction was not saved')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('saved_ground_offset_recovered'):
        raise Halt('Require exact completed local ground response and unchanged current source')

class SavedGroundOffset(ChapterPresentation):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_prior()
        oldgate=self.store.root/'evidence/q0103-995b06ea/chapter-gate.json'
        if sha(oldgate.read_bytes())!=GATE_SHA:raise Halt('Preserve the original measured native rejection')
        _,expected=self.selected()
        saved_patch(self.response(),expected)

    def response(self):
        return (self.store.root/'private/sessions'/(ROUND+'-ground')/'response-000.json').read_bytes()

    def selected(self):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        first=raw.index('                // World offset: center X/Z -> anchor X/Z, min Y -> anchor.y + 0.14')
        last=raw.index('                c.position += delta;',first)+len('                c.position += delta;')
        edit=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last)+1,max_lines=9)
        expected=edit.old.replace('anchor.y + 0.14','anchor.y').replace('(aPos.y + 0.14f)','aPos.y')
        return edit,expected

    def recovery_settings(self):
        return {**super().recovery_settings(),'saved_ground_offset_recovered':True,
            'recovery_change':'Recover only the exact seven-line local final-answer patch; hash-bound selected edit, no private reasoning or regenerated source; native qualification unchanged.'}

    def source(self,ident):
        edit,expected=self.selected();content=saved_patch(self.response(),expected)
        edit.apply(ident+'-recover-ground-offset',content)
        candidate=self.checkpoint_source('Local Qwen: apply completed cache ground-offset correction')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        self.store.event('complete-local-ground-patch-recovered',candidate=candidate,
            original_response_sha256=RESPONSE_SHA,content_sha256=sha(content.encode()),
            source_surface='complete public final-answer code block',private_reasoning_used=False,
            original_no_tool_stop_preserved=True,local_game_author='Qwen',cloud_game_edits=False)
        return candidate

if __name__=='__main__':raise SystemExit(main(SavedGroundOffset))
