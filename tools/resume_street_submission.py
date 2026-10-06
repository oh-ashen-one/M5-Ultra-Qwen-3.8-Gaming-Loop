#!/usr/bin/env python3
"""Recover a complete local source submission rejected by an ambiguous path contract."""
import json
from resume_second_street import SecondStreet, SOURCE, ACCEPTED
from resume_saved_door import PATH
from resume_three_day_queue import main
from loop_controller.core import Files, Halt, sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

ROUND='q0079-ff33490c'
RESPONSE_SHA='0ae7fb563a104059206b71adaed9d5e3f10cf3bf9cacd04d3d9c44bae0e497c1'
HELPER='Assets/Game/ConnectedStreet.cs'
BLOCKER='Halt: Second-street role saved no source; no native expansion claim'


def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=20,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,
        door_fix_deferred_for_street=True,saved_door_accepted=False,second_street_attempts=1)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('street_submission_recovery_attempted'):
        raise Halt('Expected exact untouched street source/path stop')


def completed_submission(raw):
    if sha(raw)!=RESPONSE_SHA:raise Halt('Complete original street submission changed')
    choice=json.loads(raw)['choices'][0];calls=choice['message'].get('tool_calls',[])
    if choice.get('finish_reason')!='tool_calls' or len(calls)!=1:
        raise Halt('Only a complete original tool call can be recovered')
    function=calls[0]['function'];fields=function['arguments']
    fields=json.loads(fields) if isinstance(fields,str) else fields
    if function['name']!='create_file' or set(fields)!={'path','content'} or fields['path']!='ConnectedStreet.cs':
        raise Halt('Recovery maps one known basename only; no fuzzy paths or other actions')
    content=fields['content']
    if len(content.splitlines())!=124 or len(content.encode())!=6971:
        raise Halt('Expected reviewed compact original helper')
    return content


def selected_span(raw,label):
    lines=raw.splitlines()
    needles={
        'wall-api':('static void AddWall(',1),
        'fence-api':('static void PlaceFence(',2),
        'open-old-collider':('AddWall(go, new Vector3(AX1 + WALL_T * 0.5f,',2),
        'open-old-fence':('PlaceFence(fenceSourcePrefab, go, new Vector3(AX1 - 0.3f,',2),
    }
    if label in needles:
        needle,count=needles[label];found=[i for i,l in enumerate(lines) if l.strip().startswith(needle)]
        if len(found)!=1:raise Halt('Selected integration boundary is ambiguous: '+label)
        start=found[0]
    elif label=='open-old-visible-wall':
        starts=[i for i,l in enumerate(lines) if 'var names = new[] { "AlleySouthWall", "AlleyNorthWall", "AlleyEndWall" }' in l]
        if len(starts)!=1:raise Halt('Expected original alley wall array')
        start=next((i for i in range(starts[0],len(lines)) if lines[i].strip()=='for (int i = 0; i < 3; i++)'),None)
        if start is None:raise Halt('Expected visible wall loop')
        count=1
    elif label=='install-street':
        found=[i for i,l in enumerate(lines) if '// North (forward, +Z) end: fence runs across pavement width.' in l]
        if len(found)!=1:raise Halt('Expected original final core fences')
        start=found[0]-2;count=3
        if lines[start].strip()!='if (fenceSourcePrefab != null)' or lines[start+1].strip()!='{':
            raise Halt('Preserve final core fence conditional')
    else:raise Halt('Unknown integration edit')
    return start+1,start+count


class StreetSubmission(SecondStreet):
    def validate_recovery(self,old):
        validate_pause(old)
        completed_submission(self.original_response())
        if (self.project/HELPER).exists():raise Halt('Never overwrite an existing helper')
        self.accepted_probe()

    def original_response(self):
        return (self.store.root/'private/sessions'/(ROUND+'-street-source')/'response-000.json').read_bytes()

    def recovery_settings(self):
        return dict(street_submission_recovery_attempted=True,recovery_route='complete-local-submission-and-small-integration',
            recovery_change='Map one exact rejected basename to its allowed path; preserve complete local code and request six bounded integration edits')

    def local_street_source(self,ident):
        if self.store.get('street_submission_recovered'):return super().local_street_source(ident)
        files=Files(self.project,self.store);content=completed_submission(self.original_response())
        files.create(ident+'-recover-complete-local-module',HELPER,content)
        saved=self.checkpoint_source('Preserve complete local-Qwen street module after exact path correction')
        self.store.set(source_checkpoint=saved,candidate_commit=saved,street_submission_recovered=True)
        self.store.event('complete-local-source-submission-recovered',original_response_sha256=RESPONSE_SHA,
            original_path='ConnectedStreet.cs',actual_project_path=HELPER,content_sha256=sha(content.encode()),
            original_lines=124,recovery_line_budget=160,original_rejections_preserved=True,
            cloud_game_code_authored=False,native_validation_pending=True)
        tasks=[
            ('wall-api','Expose only this existing static AddWall helper publicly so your new module can call it; keep parameters and body unchanged.'),
            ('fence-api','Expose only this existing static PlaceFence helper publicly so your new module can call it; preserve both header lines and parameters.'),
            ('open-old-collider','Remove only this two-line AddWall call for the old east alley boundary atX22.25. Your new street now closes its outer east edge atX60.25. Preserve all other colliders.'),
            ('open-old-fence','Remove only this two-line PlaceFence call crossing the old east junction. Keep every other fence and its collision.'),
            ('open-old-visible-wall','Change only this visible-wall loop to instantiate its first TWO entries, preserving AlleySouthWall and AlleyNorthWall and omitting the obsolete AlleyEndWall. Leave the arrays and bodies unchanged.'),
            ('install-street','Insert the call to ConnectedStreet.Install(go, fenceSourcePrefab) immediately BEFORE the selected if statement. Preserve the if, brace and existing core-fence comment. Your helper must run once regardless of the fence argument being null.'),
        ]
        for label,instruction in tasks:
            raw=files.path(PATH).read_text();start,end=selected_span(raw,label)
            edit=SelectedEdit(files,PATH,start,end,max_lines=8)
            self.c.update(output_tokens=2048,model_timeout_seconds=120)
            self.store.set(stage='local-street-integration-'+label);self.store.report()
            self.model.session('builder',ident+'-'+label,
                'You are the local Qwen author finishing your saved street helper. Submit only the selected tiny integration edit.',
                instruction+' Use edit_selected_span now. No unrelated changes, assets, mission or replay. '
                'An empty replacement removes the selected obsolete call.\nEXACT SELECTED OLD SPAN:\n'+edit.old+
                '\nEXACT CURRENT WorldColliders:\n'+raw+'\nYOUR SAVED ConnectedStreet:\n'+content,
                [tool('edit_selected_span','Save only this selected integration span.',{'content':{'type':'string'}})],
                {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
            if files.path(PATH).read_text()==raw:raise Halt('Local street integration did not save '+label+'; preserve completed source')
            saved=self.checkpoint_source('Local Qwen: connect street / '+label)
            self.store.set(source_checkpoint=saved,candidate_commit=saved)
        return self.store.get('source_checkpoint')


if __name__=='__main__':raise SystemExit(main(StreetSubmission))
