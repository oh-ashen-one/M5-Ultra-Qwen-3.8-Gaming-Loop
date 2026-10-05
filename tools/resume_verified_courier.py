#!/usr/bin/env python3
"""Restore the measured accepted courier geometry after a natural replay-budget stop."""
import re

from loop_controller.core import Files,Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from recover_mission_replay import MISSION
from resume_failure_retry import ACCEPTED_COURIER,failure_probe
from resume_mission_review import verified_probe
from resume_three_day_queue import ThreeDayRunner,main

PAUSED_SOURCE='59aedf617e987820fd0c5d7431d717f14eb74911'


def validate_geometry_pause(state):
    if (state.get('task_index')!=3 or state.get('source_checkpoint')!=PAUSED_SOURCE
            or state.get('last_playable_checkpoint')!=ACCEPTED_COURIER
            or not state.get('blocker','').startswith('Halt: Replay-only role supplied no valid finish_task')
            or state.get('task_failures')!=5 or state.get('failure_streak')!=1
            or state.get('diagnosis_used') is not True or state.get('overall_deadline_epoch')!=HARD_CAP_EPOCH):
        raise Halt('Preserve any stop other than the inspected q0022 replay-budget stop')


def current_deadline(source):
    matches=re.findall(r'const\s+float\s+DEADLINE\s*=\s*(\d+(?:\.\d+)?)[fF]\s*;',source)
    if len(matches)!=1 or not 10<=float(matches[0])<=120:
        raise Halt('Expected one bounded current mission deadline; do not invent a wait')
    return float(matches[0])


class VerifiedCourierRunner(ThreeDayRunner):
    def validate_recovery(self,old):validate_geometry_pause(old)

    def recovery_settings(self):return {'verified_courier_recovery_pending':True}

    def restore_pad(self,ident):
        label='verified-west-bay-pad'
        if label in self.store.get('mission_line_edits',[]):return
        files=Files(self.project,self.store);lines=files.path(MISSION).read_text().splitlines()
        found=[i for i,line in enumerate(lines) if 'pad.transform.position =' in line]
        if len(found)!=1:raise Halt('Expected one real pad assignment')
        i=found[0]
        if i<3 or not all(line.strip().startswith('//') for line in lines[i-3:i]):
            raise Halt('Expected the inspected three obsolete pad comments')
        edit=SelectedEdit(files,MISSION,i-2,i+1,max_lines=4)
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='selected-mission-line',recovery_microtask=label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are the local Qwen game author. Make one edit_selected_span call for the exact four-line span.',
            'Restore the previously native-verified west loading bay: pad world X1, Y PAV_TOP+0.01f, Z26. '
            'Replace the three obsolete comments with one accurate short comment. Actual accepted F delivery was '
            'at vehicle X0.486,Z24.925, 1.19m from this pad. Moving the pad to X3.6 produced a measured3.22m gap '
            'at F. This restores proven geometry, not a new guessed target. Preserve all other source.\n'+edit.old,
            [tool('edit_selected_span','Replace only the exact selected span.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if sha(files.path(MISSION).read_bytes())==edit.before:raise Halt('Local Qwen did not save the scoped pad repair')
        candidate=self.checkpoint_source('Local Qwen: restore verified west bay pad')
        self.store.set(source_checkpoint=candidate,mission_line_edits=self.store.get('mission_line_edits',[])+[label])
        self.store.event('selected-mission-edit-saved',microtask=label,candidate=candidate,game_author='local Qwen')

    def edit(self,task,ident):
        if not self.store.get('verified_courier_recovery_pending'):return super().edit(task,ident)
        if task['id']!='mission-failure-retry':raise Halt('Courier recovery cannot edit another task')
        self.restore_pad(ident)
        self.line_edit(ident,'verified-original-delivery-reach','if (dz <=',
            'Restore the original actual-distance delivery condition to2.6 metres. Preserve the if statement and '
            'braces below it. Do not widen acceptance, alter actors or change mission signals.')
        self.line_edit(ident,'verified-beacon-over-pad','beaconGo.transform.position =',
            'Align the visual beacon directly over the restored verified pad: world X1, Y PAV_TOP+3.5f, Z26. '
            'This makes the existing HUD distance and marker refer to the real destination. Preserve all other values.')
        deadline=current_deadline(Files(self.project,self.store).path(MISSION).read_text())
        previous,evidence=verified_probe(self.store.root,task)
        probe=failure_probe(previous,task,deadline)
        self.store.set(verified_courier_recovery_pending=False,last_valid_replay=probe)
        self.store.event('verified-courier-recovery-probe',accepted_route=evidence,current_deadline_seconds=deadline,
            reset_seconds=deadline+2,actual_failure_still_required=True,success_claimed=False,
            retry_counters_changed=False,game_source_author='local Qwen',probe_author='cloud acceptance controller')
        return {'ok':True,'scenario':probe}


if __name__=='__main__':raise SystemExit(main(VerifiedCourierRunner))
