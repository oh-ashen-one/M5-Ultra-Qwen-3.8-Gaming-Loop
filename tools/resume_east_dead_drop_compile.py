#!/usr/bin/env python3
"""Repair one measured local chapter compile error, then continue its unchanged gates."""
import json
from resume_east_dead_drop import EastDeadDrop, PATH, BOOT, TASK, SOURCE as BEFORE, ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit

SOURCE='15179c556344b121295a856aafe8e8b05305020c'
ROUND='q0094-43a4dcac'
SOURCE_SHA='819c8212d0d506e237019aef12dc84cce7efeb4c6408ff7ba55af7e699614f11'
GATE_SHA='2d9aa0d88e2d0aa763e765105806dd8617dba0bc9ab7db5c511548a226f39a4a'

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,east_dead_drop_implementation_attempted=True,
        blocker='Halt: Saved chapter failed additive native activation/reset gate')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('east_dead_drop_compile_repair_attempted'):
        raise Halt('Expected exact preserved local chapter compile failure')

class ChapterCompileRepair(EastDeadDrop):
    def validate_recovery(self,old):
        validate_pause(old)
        raw=(self.store.root/'evidence'/(ROUND+'-activation')/'chapter-gate.json').read_bytes()
        if sha(raw)!=GATE_SHA or sha((self.project/PATH).read_bytes())!=SOURCE_SHA:
            raise Halt('Preserve original chapter compiler evidence and source')
        gate=json.loads(raw)
        specific=[e for e in gate.get('compile_errors',[]) if 'error CS' in e]
        if not specific or any("RouteMission.cs(133,42): error CS1503" not in e for e in specific):
            raise Halt('Only the measured Transform-parent API compile failure is in scope')

    def recovery_settings(self):
        return dict(east_dead_drop_compile_repair_attempted=True,
            recovery_route='single-local-chapter-parent-type-repair',
            recovery_change='Preserve the failed native build; local edit of its one wrong parent argument; unchanged chapter and legacy gates')

    def source(self,ident):
        files=Files(self.project,self.store)
        raw=(self.project/PATH).read_text()
        needle='                var c = Instantiate(src, anchor).transform;'
        if raw.count(needle)!=1:raise Halt('Expected exact measured clone-parent line')
        line=raw.count('\n',0,raw.index(needle))+1
        edit=SelectedEdit(files,PATH,line,line,max_lines=1)
        def save(action,f):
            if len(f['content'].splitlines())!=1:raise ValueError('Change only the parent API argument')
            return edit.apply(action,f['content'])
        self.c.update(output_tokens=1536,model_timeout_seconds=120)
        self.store.set(stage='local-chapter-compile-repair');self.store.report()
        self.model.session('builder',ident+'-parent-type',
            'You are local Qwen repairing one compiler-proven API mismatch in your chapter.',
            'Unity rejects the second Instantiate argument because src is a Transform and anchor is a GameObject. '
            'Use the Transform parent from anchor while preserving the cloned source and c type. Replace only this line. '
            'No other game or harness edits.\n'+edit.old,
            [tool('edit_selected_span','Save the one-line parent API correction.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},turns=1,reasoning_effort='low')
        if (self.project/PATH).read_text()==raw:raise Halt('Local chapter compiler repair saved no edit')
        saved=self.checkpoint_source('Local Qwen: repair chapter clone parent type')
        self.store.set(source_checkpoint=saved,candidate_commit=saved);return saved

if __name__=='__main__':raise SystemExit(main(ChapterCompileRepair))

