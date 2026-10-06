#!/usr/bin/env python3
"""Accept one complete pinned local entrance edit with two formatting lines of headroom."""
import json
from resume_alley_presentation import AlleyPresentation,PATH,ACCEPTED,REPLAY
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import replay_identity
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='73f8efb81a173ea4f7f5fdb19f363c4db4d63ba6'
ROUND='q0071-a3f56a74'
SESSION=ROUND+'-visible-entrance'
RESPONSE_SHA='425d141acd2f371f89a7a97d301487d386a2c12f53d3981265163ee8b7098644'
PROPOSAL_SHA='6d59104f9fe96ba61ae9d2ee62bb15f7bcf1e61463128df36264b40ba7f062c3'


def completed_entrance(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original local response changed')
    d=json.loads(raw);c=d['choices'][0];calls=c['message'].get('tool_calls',[])
    if c.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='edit_selected_span':
        raise Halt('Expected exactly one complete source tool submission')
    content=json.loads(calls[0]['function']['arguments'])['content']
    if sha(content.encode())!=PROPOSAL_SHA or len(content.splitlines())>18:
        raise Halt('Expected the exact16-line/789-byte local proposal')
    return content


class AlleyCompleted(AlleyPresentation):
    def validate_recovery(self,old):
        expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
            task_index=7,task_failures=16,failure_streak=1,diagnosis_used=True,
            overall_deadline_epoch=HARD_CAP_EPOCH,alley_presentation_recovery_attempted=True,
            blocker='Halt: Scoped alley presentation edit not submitted; physics candidate preserved')
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('alley_completed_recovery_attempted'):
            raise Halt('Expected exact preserved complete entrance proposal rejection')
        if replay_identity(old['last_valid_replay'])!=REPLAY:raise Halt('Preserve the native-passing replay')
        completed_entrance((self.store.root/'private/sessions'/SESSION/'response-000.json').read_bytes())

    def recovery_settings(self):
        return dict(alley_completed_recovery_attempted=True,recovery_route='completed-proposal-recovery',
            recovery_change='Keep saved asphalt; accept exact16-line local entrance at18-line bound; then local walls')

    def prepare_source(self):
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Preserve saved local asphalt source')

    def selected(self,ident,label,needle,instruction,max_lines):
        if label=='matching-asphalt':return
        if label!='visible-entrance':return super().selected(ident,label,needle,instruction,48)
        content=completed_entrance((self.store.root/'private/sessions'/SESSION/'response-000.json').read_bytes())
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        lines=[i+1 for i,line in enumerate(raw.splitlines()) if line.strip()==needle]
        if len(lines)!=1:raise Halt('Expected the unchanged exact insertion comment')
        edit=SelectedEdit(files,PATH,lines[0],lines[0],max_lines=18)
        edit.apply(ident+'-pinned-entrance',content)
        saved=self.checkpoint_source('Local Qwen: preserve completed alley entrance proposal')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        self.store.event('completed-local-entrance-recovered',response_sha256=RESPONSE_SHA,
            proposal_sha256=PROPOSAL_SHA,original_line_limit=14,scoped_line_limit=18,
            local_content_changed=False,candidate=saved,native_pass_claimed=False)


if __name__=='__main__':raise SystemExit(main(AlleyCompleted))
