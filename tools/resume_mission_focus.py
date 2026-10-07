#!/usr/bin/env python3
"""Recover an evidenced replay-budget stop with three exact local-authored edits."""
import json

from recover_mission_replay import MissionRecovery
from resume_mission_fixture import main
from loop_controller.core import Files, Halt, sha
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from recover_mission_replay import MISSION
from loop_controller.replay_contract import finish_tool, validate_submission


def observed_route(previous):
    """Keep the native pickup/drive probe and append an observable ordinary R reset."""
    return {
        'summary': 'Previously observed pickup/drive inputs, delivery attempt, then ordinary R reset; success unverified.',
        'duration': 20,
        'input_steps': previous['steps'] + [{'start':17,'end':17.3,'keys':['R']}],
        'captures': [3.2,5.2,7.2,7.9,9.4,12.5,14.0,15.2,16.2,18.5],
    }


class MissionFocus(MissionRecovery):
    recovery_prefixes=('Halt: Replay-only role supplied no valid finish_task',
                       'Halt: Selected mission microtask saved no edit: compact-facing-hud')
    recovery_description='One-line local edits after the whole HUD block exhausted8192 tokens; same observed route'

    def line_edit(self,ident,label,needle,instruction):
        done=self.store.get('mission_line_edits',[])
        if label in done:return
        files=Files(self.project,self.store);lines=files.path(MISSION).read_text().splitlines()
        matches=[i+1 for i,line in enumerate(lines) if needle in line]
        if len(matches)!=1:raise Halt('Expected one exact local line: '+label)
        edit=SelectedEdit(files,MISSION,matches[0],matches[0],max_lines=3)
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='selected-mission-line',recovery_microtask=label);self.store.report()
        self.model.session('builder',ident+'-'+label,
            'You are the local Qwen C# author. Make one edit_selected_span call now. This is one mechanical line edit.',
            instruction+' Preserve indentation. Return only the replacement line through the tool.\nCURRENT LINE:\n'+edit.old,
            [tool('edit_selected_span','Replace this one exact source line.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1,reasoning_effort='low')
        if sha(files.path(MISSION).read_bytes())==edit.before:raise Halt('Selected mission line saved no edit: '+label)
        candidate=self.checkpoint_source('Local Qwen: mission line '+label)
        self.store.set(source_checkpoint=candidate,mission_line_edits=done+[label])
        self.store.event('selected-mission-edit-saved',microtask=label,candidate=candidate,game_author='local Qwen')
        self.store.report()

    def edit(self,task,ident):
        if task['id']!='connected-mission' or self.store.get('mission_focus_saved'):
            return super().edit(task,ident)
        # Instructions and exact source selection are supervision. All C# bytes
        # come from the authenticated local Qwen edit_selected_span response.
        for label,needle,instruction in [
            ('hud-facing','go.transform.localRotation = Quaternion.Euler',
             'Set the camera-child HUD localRotation to Quaternion.identity to remove the observed mirrored text.'),
            ('hud-character-size','tm.characterSize =',
             'Change only TextMesh characterSize from0.08 to0.008 to fit the three HUD lines in the native camera.'),
            ('hud-top-position','go.transform.localPosition = new Vector3(0f, 0.34f, 1.6f)',
             'Move this camera-child HUD local position up to Y0.70, preserving X0 and Z1.6.'),
            ('hud-card-height','card.transform.localScale =',
             'Shrink only the HUD backing card height from1.1 to0.28, preserving width1.7 and thickness0.01.'),
            ('fixed-pad-location','pad.transform.position =',
             'Place the stationary delivery pad at world X1, Y PAV_TOP+0.01, Z26. This is the reachable west loading bay on the existing pavement. Keep its real delivery reach unchanged.'),
            ('fixed-beacon-location','beaconGo.transform.position =',
             'Place the stationary beacon vertically above the delivery bay at world X1, Y PAV_TOP+3.5, Z26.'),
            ('actual-pad-position','padPos = new Vector3',
             'Set padPos to padRend.transform.position, the visible fixed destination already created in Build. Do not move actors or modify the real distance gate.')]:
            self.line_edit(ident,label,needle,instruction)
        self.store.set(mission_focus_saved=True)
        fixture=observed_route(self.store.get('last_valid_replay'))
        validate_submission(fixture,task)
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='submit-observed-replay');self.store.report()
        result=self.model.session('replay-author',ident+'-observed-fixture',
            'This is JSON serialization only. Immediately call finish_task copying the supplied object unchanged. '
            'Do not reason about routes or edit code. Native execution will determine whether it works.',
            'Success is unverified. Exact finish_task arguments:\n'+json.dumps(fixture),
            [finish_tool()],{'finish_task':lambda _,f:validate_submission(f,task)},turns=2,reasoning_effort='low')
        if not result.get('scenario'):raise Halt('Observed fixture not submitted; preserve focused edits')
        self.store.set(provided_fixture_pending=False,last_valid_replay=result['scenario'])
        self.store.event('replay-preflight-passed',source='observed input probe with normal R reset',
                         game_code_author='local Qwen',gameplay_success='unverified')
        return result


if __name__=='__main__':raise SystemExit(main(MissionFocus))
