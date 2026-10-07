#!/usr/bin/env python3
"""Recover a completed 47-line local proposal, then correct its one measured lookup."""
import json
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import main
from resume_map_spans import MapSpanBuilder,PATH
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK,qualify_one_extension
from loop_controller.core import Files,Halt,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import typed_arguments,tool
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='506f55a795931abd7b42d0cbeeca2731a540c679'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0054-38aed712'
BLOCKER='Halt: Small map connected-pavement edit saved no change'
SESSION=ROUND+'-connected-pavement'
RESPONSE_SHA='256ddf337ab23e964af3894b86218a63a6e5094d0e8ba8f88b1cd436f201c36c'
PROPOSAL_SHA='f2acaa2b3c229d21ad474284cd913ee4b4d9a1488b0654df08519a58221255df'
SOURCE_SHA='c9d87c13062aa56496c732fd1c6f40f38b1e8e166df3c089c8828a152972bb88'


def validate_pavement_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=8,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_span_builder_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('pavement_completion_attempted'):
        raise Halt('Expected exact preserved pavement line-budget stop')


def completed_proposal(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Original local proposal response changed')
    value=json.loads(raw);choice=value['choices'][0];calls=choice['message'].get('tool_calls') or []
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1 or calls[0]['function']['name']!='edit_selected_span':
        raise Halt('Expected one completed local edit tool call')
    definition=tool('edit_selected_span','Original local edit.',{'content':{'type':'string'}})
    content=typed_arguments(calls[0]['function'],[definition])['content']
    if sha(content.encode())!=PROPOSAL_SHA or len(content.encode())>6000 or len(content.splitlines())!=47:
        raise Halt('Only the exact inspected 47-line local proposal can be recovered')
    return content


def pavement_lookup_span(raw):
    lines=raw.splitlines()
    starts=[i for i,line in enumerate(lines) if line.strip()=='Transform pv0 = null;']
    stops=[i for i,line in enumerate(lines) if line.strip()=='if (pv0 != null)']
    if len(starts)!=1 or len(stops)!=1 or not 0<stops[0]-starts[0]<=12:
        raise Halt('Expected one complete bounded pavement lookup before its whole-line guard')
    return starts[0]+1,stops[0]


class PavementCompletion(MapSpanBuilder):
    def validate_recovery(self,old):
        validate_pavement_pause(old)
        if sha((self.project/PATH).read_bytes())!=SOURCE_SHA:raise Halt('Saved opening source changed')
        completed_proposal((self.store.root/'private/sessions'/SESSION/'response-000.json').read_bytes())

    def recovery_settings(self):return {'pavement_completion_attempted':True}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        files=Files(self.project,self.store);path=files.path(PATH);raw=path.read_text()
        if sha(path.read_bytes())!=SOURCE_SHA:raise Halt('Do not apply the saved proposal twice')
        content=completed_proposal((self.store.root/'private/sessions'/SESSION/'response-000.json').read_bytes())
        first=next(i+1 for i,line in enumerate(raw.splitlines()) if '// 3) Understandable end barriers' in line)
        edit=SelectedEdit(files,PATH,first,first,max_lines=50)
        edit.apply(ident+'-recover-local-pavement-proposal',content)
        saved=self.checkpoint_source('Local Qwen: preserve completed 47-line pavement proposal')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        self.store.event('recover-completed-local-proposal',original_session=SESSION,
            original_response_sha256=RESPONSE_SHA,proposal_sha256=PROPOSAL_SHA,
            original_lines=47,previous_line_limit=45,recovery_line_limit=50,
            bytes_unchanged=True,original_rejection_preserved=True,game_author='local Qwen')
        raw=path.read_text()
        first,last=pavement_lookup_span(raw)
        bootstrap=files.path('Assets/Game/Bootstrap.cs').read_text()
        context=bootstrap[bootstrap.index('            Transform sw = null;'):bootstrap.index('            static GameObject Coupe()')]
        self.span(ident,'pavement-root-lookup',first,last,
            'Your completed pavement proposal was preserved exactly. One static lookup defect must be corrected: '
            'Bootstrap creates Pavement as its own scene-root GameObject; it is not a child of street, streetExt '
            'or props, which are the only roots passed to WorldColliders.Install. Replace ONLY this lookup span '
            'with a safe lookup of that existing scene object by its exact name Pavement, producing Transform pv0 '
            'or null if absent. Keep the later if(pv0!=null), geometry, materials, floor, fences and other source '
            'unchanged. At most4lines. Call edit_selected_span now; no new plan or full-file rewrite.',
            'ACTUAL PAVEMENT CREATION:\n'+context+'\nSUBMITTED PAVEMENT BLOCK:\n'+content,4)
        return self.propose_replay(task,ident)

    def work(self):
        self.machine.guard()
        self.store.set(task_design=NEXT_MAP)
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),
                      'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(PavementCompletion))
