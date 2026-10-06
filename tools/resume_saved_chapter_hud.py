#!/usr/bin/env python3
"""Recover the exact complete HUD proposal; locally fix its measured panel depth."""
import json
from resume_chapter_hud_route import ChapterHudMeasuredRoute,validate_hud,PATH,SOURCE,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

ROUND='q0097-6acaea0f'
RESPONSE_SHA='24e266a1ab559e9fd93c17c342b7fdcd0732ffde41176235e637e06db7f4a64e'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,chapter_hud_measured_route_attempted=True,
        chapter_route_pilot_attempts=0,blocker='Halt: HUD correction supplied no saved edit')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('chapter_saved_hud_recovered'):
        raise Halt('Expected exact rejected complete HUD submission, never a partially generated edit')

def saved_proposal(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original HUD submission changed')
    c=json.loads(raw)['choices'][0];calls=c['message'].get('tool_calls',[])
    if c.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='edit_selected_span':
        raise Halt('Only one complete original HUD tool submission may be recovered')
    fields=calls[0]['function']['arguments']
    if isinstance(fields,str):fields=json.loads(fields)
    if set(fields)!={'content'}:raise Halt('Expected the complete original HUD content')
    return validate_hud(fields['content'])

class SavedChapterHud(ChapterHudMeasuredRoute):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'private/sessions'/(ROUND+'-hud')/'response-000.json').read_bytes()
        saved_proposal(raw)

    def recovery_settings(self):
        return dict(chapter_saved_hud_recovered=True,
            recovery_route='exact-complete-local-hud-proposal-recovery',
            recovery_change='Allow only the new card to hide while inactive, keep legacy receipt protected; preserve original rejection; local panel-depth micro-edit before unchanged native gates')

    def source(self,ident):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        first=raw.index('        void BuildHud()');last=raw.index('        void Update()')
        edit=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last),max_lines=85)
        original=(self.store.root/'private/sessions'/(ROUND+'-hud')/'response-000.json').read_bytes()
        proposal=saved_proposal(original)
        edit.apply(ident+'-recover-complete-hud',proposal)
        recovered=self.checkpoint_source('Recover complete local-Qwen chapter HUD proposal')
        self.store.set(source_checkpoint=recovered,candidate_commit=recovered)
        self.store.event('complete-hud-tool-recovered',original_response_sha256=RESPONSE_SHA,
            original_rejection_preserved=True,content_sha256=sha(proposal.encode()),local_game_author='Qwen',
            cloud_change='Accept own-card visibility in the external edit guard; no rewritten gameplay')
        raw=files.path(PATH).read_text()
        first=raw.index('                    card.localPosition =')
        last=raw.index('                    card.localScale =')
        start_line=raw.count('\n',0,first)+1;end_line=raw.count('\n',0,last)+1
        panel=SelectedEdit(files,PATH,start_line,end_line,max_lines=5)
        def save(action,f):return panel.apply(action,validate_hud(f['content']))
        self.c.update(output_tokens=1536,model_timeout_seconds=120)
        self.store.set(stage='local-chapter-hud-panel-depth');self.store.report()
        self.model.session('builder',ident+'-panel-depth',
            'You are local Qwen correcting only the cloned UI backing before native render verification.',
            'Your recovered backing clones the existing unit Cube HudCard. Its proposed thickness0.32 and centerZ0.02 '
            'put its front face atZ-0.14, in front of the text planeZ0. Keep it safely behind: centerZ0.025 and '
            'thickness0.01. The upper-centered three-line text extends downward; use backing centerX0,Y-0.11, '
            'width2.2,height0.34. Preserve identity rotation. Disable any Collider on this NEW card clone so UI cannot '
            'affect actor physics; never alter the original card or any world collider. At most5replacement lines. '
            'Call edit_selected_span now.\n'+panel.old,
            [tool('edit_selected_span','Save the small backing layout correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if files.path(PATH).read_text()==raw:raise Halt('Local HUD panel-depth correction supplied no edit')
        saved=self.checkpoint_source('Local Qwen: size and place the chapter HUD backing behind text')
        self.store.set(source_checkpoint=saved,candidate_commit=saved);return saved

if __name__=='__main__':raise SystemExit(main(SavedChapterHud))
