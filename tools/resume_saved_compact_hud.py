#!/usr/bin/env python3
"""Recover the complete130-line local HUD tool proposal without regeneration."""
import json
from resume_chapter_presentation import ChapterPresentation,validate_visual_span,SOURCE,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,sha,read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH

ROUND='q0102-6057d9ec'
RESPONSE_SHA='7f76a495d73d8a5c98b4663ba7225eba15554d116d350961db59b6215221a62a'

def saved_proposal(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original complete HUD submission changed')
    choice=json.loads(raw)['choices'][0];calls=choice['message'].get('tool_calls',[])
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='edit_selected_span':
        raise Halt('Require exactly one complete local HUD tool call')
    fields=calls[0]['function']['arguments']
    if isinstance(fields,str):fields=json.loads(fields)
    if set(fields)!={'content'}:raise Halt('Require complete original content only')
    return validate_visual_span(fields['content'])

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,chapter_presentation_attempted=True,
        blocker='Halt: Local compact HUD edit was not saved')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('saved_compact_hud_recovered'):
        raise Halt('Require exact rejected compact HUD edit and unchanged source/history')

class SavedCompactHud(ChapterPresentation):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_prior()
        folder=self.store.root/'private/sessions'/(ROUND+'-hud')
        saved_proposal((folder/'response-000.json').read_bytes())
        results=[m for m in read_json(folder/'history.json') if m.get('role')=='tool']
        if len(results)!=1 or json.loads(results[0]['content'])!={'ok':False,'error':'Keep this exact visual span within its bounded edit size'}:
            raise Halt('Preserve the original measured line-limit rejection')

    def recovery_settings(self):
        return {**super().recovery_settings(),'saved_compact_hud_recovered':True,
            'recovery_change':'Accept only the exact complete130-line/4650byte local HUD proposal in the same visual span, bounded at140lines/6000bytes; no regeneration, gameplay or budget change.'}

    def hud_request(self,ident,hud,raw,save):
        path=self.store.root/'private/sessions'/(ROUND+'-hud')/'response-000.json'
        content=saved_proposal(path.read_bytes());save(ident+'-recover-hud',{'content':content})
        self.store.event('complete-compact-hud-recovered',original_response_sha256=RESPONSE_SHA,
            content_sha256=sha(content.encode()),lines=len(content.splitlines()),bytes=len(content.encode()),
            local_game_author='Qwen',cloud_game_edits=False,original_rejection_preserved=True)

if __name__=='__main__':raise SystemExit(main(SavedCompactHud))
