#!/usr/bin/env python3
"""Recover an evidenced replay-budget stop with three exact local-authored edits."""
import json

from recover_mission_replay import MissionRecovery
from resume_mission_fixture import main
from loop_controller.core import Halt
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
    def edit(self,task,ident):
        if task['id']!='connected-mission' or self.store.get('mission_focus_saved'):
            return super().edit(task,ident)
        # Instructions and exact source selection are supervision. All C# bytes
        # come from the authenticated local Qwen edit_selected_span response.
        self.selected(ident,'compact-facing-hud','void BuildHud()',
            'Correct the observed backwards, oversized native HUD. Camera-child TextMesh should face the camera '
            'without the current Y180 mirror. Use identity local rotation, compact character size about .008 '
            'and a narrow dark backing at positive local Z behind the text. Position near the top of the '
            'view, keep the three lines inside a normal camera view, and leave most of the game unobscured. '
            'Keep LegacyRuntime.ttf, actual RefreshHud stage logic and the same controls. Only replace this block.',45)
        self.selected(ident,'reachable-delivery-location','void Build()',
            'The current destination is obstructed on the east side. Native ordinary driving reaches the paved '
            'west loading area around X.48,Z25.0; the visible pavement is X-1..6,Z-2..30. Place a distinct '
            'stationary delivery bay centered at X1,Z26, with the existing pad wholly on that pavement and '
            'the beacon vertically above the same world point. This is a persistent human-playable location, '
            'never conditional on a replay or clock. Preserve laneX3.6 and the parcel X3.6,Z3.2, missionRoot, '
            'materials and other setup. Do not alter vehicle physics, spawn or the real2.6m delivery radius.',100)
        self.selected(ident,'destination-from-world-pad','void Start()',
            'Initialize padPos from the actual fixed padRend.transform.position created by Build, so the '
            'delivery proximity checks the visible destination rather than the old laneX/Z27.5 coordinates. '
            'Preserve lastRestarts. Do not move the pad or change gameplay signals.',12)
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
