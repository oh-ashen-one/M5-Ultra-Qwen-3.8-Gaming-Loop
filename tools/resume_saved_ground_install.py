#!/usr/bin/env python3
"""Apply the exact completed local two-line ground installation submission."""
import json
import re
from resume_street_ground import StreetGround,INSTALL,PATH,ACCEPTED,validate_module
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.small_edits import SelectedEdit

SOURCE='4695512c642431177d5490660323bed7c545f3fd'
ROUND='q0106-966250e2'
RESPONSE_SHA='6ea29794a0a94cb38c23754cc74d5097a281c79209b25bd2e5e36025eca5b4f4'

def saved_install(raw,old):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original completed installation response changed')
    choice=json.loads(raw)['choices'][0];m=choice['message'];content=m.get('content') or ''
    expected=re.sub(r'\s+','',old)+'EastStreetGround.Install(parent);'
    if choice.get('finish_reason')!='stop' or m.get('tool_calls') or re.sub(r'\s+','',content)!=expected:
        raise Halt('Require only the exact completed local two-statement installation')
    return content

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,street_ground_attempted=True,
        blocker='Halt: Saved street-ground module has no install')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('saved_ground_install_recovered'):
        raise Halt('Require the exact saved ground module and unexecuted local installation')

class SavedGroundInstall(StreetGround):
    def selected(self):
        files=Files(self.project,self.store);raw=files.path(INSTALL).read_text()
        rows=[(i,t) for i,t in enumerate(raw.splitlines(),1) if 'EastStreetDetail.Install(parent);' in t]
        if len(rows)!=1 or 'EastStreetGround.Install(' in raw:raise Halt('Preserve unique unmodified installation site')
        line,_=rows[0];return SelectedEdit(files,INSTALL,line,line,max_lines=3)

    def response(self):return (self.store.root/'private/sessions'/(ROUND+'-install')/'response-000.json').read_bytes()

    def validate_recovery(self,old):
        validate_pause(old);self.verify_presentation()
        validate_module((self.project/PATH).read_text())
        saved_install(self.response(),self.selected().old)
        if not old.get('chapter_presentation_outcome',{}).get('accepted'):
            raise Halt('Preserve the qualified prior presentation scope')

    def recovery_settings(self):
        return {**super().recovery_settings(),'saved_ground_install_recovered':True,
            'recovery_change':'Recover only the hash-pinned complete two-line local installation via current-file-bound tool; no private reasoning or regenerated code; unchanged native curb and regression gates.'}

    def source(self,ident):
        edit=self.selected();content=saved_install(self.response(),edit.old)
        edit.apply(ident+'-recover-ground-install',content)
        candidate=self.checkpoint_source('Local Qwen: apply completed east street ground installation')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        self.store.event('complete-ground-install-recovered',candidate=candidate,
            original_response_sha256=RESPONSE_SHA,content_sha256=sha(content.encode()),
            source_surface='complete public final-answer code',private_reasoning_used=False,
            original_no_tool_stop_preserved=True,local_game_author='Qwen',cloud_game_edits=False)
        return candidate

if __name__=='__main__':raise SystemExit(main(SavedGroundInstall))
