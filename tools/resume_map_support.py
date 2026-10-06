#!/usr/bin/env python3
"""One diagnosed source/prefix repair; preserve all prior map attempts and gates."""
import json
import math
from resume_three_day_queue import main
from resume_map_traversal import MapTraversalRecovery, ACCEPTED
from resume_map_drive_micro import compose_maneuver
from qualify_map_extension import MAP_TASK
from loop_controller.core import Files, Halt, now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import admit_strategy
from loop_controller.replay_contract import validate_submission
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE = '1c68cc752e653129196cfec1c2aa153d8445ca87'
ROUND = 'q0065-21a6422f'
OBSERVED = 'q0063-6b7c8ebe'
PATH = 'Assets/Game/VehicleInteraction.cs'


def validate_support_pause(old):
    expected = dict(source_checkpoint=SOURCE, last_playable_checkpoint=ACCEPTED,
        current_round=ROUND, task_index=7, task_failures=13, failure_streak=2,
        diagnosis_used=True, overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Explicit controller stop', map_drive_exact_attempted=True)
    if any(old.get(k) != v for k, v in expected.items()) or old.get('map_support_repair_attempted'):
        raise Halt('Expected the exact owned stop after two pre-driving support rejections')
    history = old.get('map_traversal_strategies', [])
    if [r.get('round') for r in history] != [OBSERVED, 'q0064-fefd3c3e']:
        raise Halt('Preserve both native failures and their bounded strategy budget')


def ground_span(raw):
    lines = raw.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == '// Ground snap: raycast down skipping own collider']
    ends = [i for i, line in enumerate(lines) if line.strip() == 'if (e) Exit();']
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise Halt('Expected one complete ground-correction block before normal exit handling')
    return starts[0] + 1, ends[0]


def compose_clear_walk(fields):
    names = ('north_seconds', 'east_seconds', 'west_seconds', 'south_seconds')
    values = [fields[k] for k in names]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
           or not .1 <= v <= 6 for v in values):
        raise ValueError('Each local walking duration must be finite and within 0.1..6 seconds')
    cursor = 4.0; steps = []; captures = []
    for key, seconds in zip(('W', 'D', 'A', 'S'), values):
        end = round(cursor + seconds, 5)
        steps.append(dict(start=cursor, end=end, keys=[key])); cursor = end
        if key == 'W': captures.append(round(cursor - .2, 5))
        if key == 'D':
            captures.extend([round(cursor + .2, 5), round(cursor + 1, 5)])
            cursor = round(cursor + 1.2, 5)
        if key == 'A': captures.append(round(cursor + .02, 5))
    cursor = round(cursor + .15, 5)
    steps.append(dict(start=cursor, end=round(cursor + .35, 5), keys=['E']))
    captures.append(round(cursor + .65, 5))
    return validate_submission(dict(summary=fields['summary'], duration=round(cursor + 1, 5),
        input_steps=steps, captures=captures), MAP_TASK)


class MapSupportRepair(MapTraversalRecovery):
    def validate_recovery(self, old):
        validate_support_pause(old)
        gate = json.loads((self.store.root/'evidence'/OBSERVED/'scoped-gate.json').read_text())
        if gate.get('candidate_commit') != SOURCE or set(gate.get('failure', [])) != {
                'vehicle-rendered-support', 'rendered-pavement-support'}:
            raise Halt('Expected the observed source-matched support rejection')

    def recovery_settings(self):
        return dict(map_support_repair_attempted=True, recovery_route='changed-strategy',
            recovery_change='Local vehicle support edit and clear walking prefix; retain two old native failures')

    def edit(self, task, ident):
        if task['id'] != MAP_TASK['id']: return super().edit(task, ident)
        if git(self.repo, 'rev-parse', 'HEAD') != SOURCE:
            raise Halt('This exact source repair is admitted once only')
        files = Files(self.project, self.store); path = files.path(PATH); raw = path.read_text()
        first, last = ground_span(raw)
        edit = SelectedEdit(files, PATH, first, last, max_lines=16)
        self.c.update(output_tokens=2048, model_timeout_seconds=120)
        self.store.set(stage='local-vehicle-support-repair'); self.store.report()
        self.model.session('builder', ident+'-vehicle-support',
            'You are the sole local Qwen game coder. Submit one small exact source edit now.',
            'Native evidence: stationary car settles at rootY=-0.01 on pavement topY=0.14. '
            'Its BoxCollider centerY=0.75,sizeY=1.2, so its bottom is rootY+0.15. Gravity is enabled, '
            'Rigidbody is nonkinematic, X/Z rotations are frozen. Immediately after E boarding, '
            'BEFORE any throttle, current ground snap injects upward velocity and rootY reaches1.378. '
            'It compares ground height to ROOT instead of collider bottom. Repair only the selected '
            'ground-support block in at most16lines. Remove the redundant artificial lift if ordinary '
            'Rigidbody contact/gravity already supplies support, or correct the collider-bottom calculation '
            'without an upward launch. Preserve real physics, collisions, throttle/steering, exit/reset; '
            'no teleport, signal manipulation or disabling gravity. Do not rewrite the file or plan a route. '
            'Call edit_selected_span with content now. Exact selected block:\n'+edit.old,
            [tool('edit_selected_span', 'Replace only this bounded ground-support block.',
                  {'content': {'type': 'string'}})],
            {'edit_selected_span': lambda action, f: edit.apply(action, f['content'])},
            turns=1, reasoning_effort='low')
        if path.read_text() == raw:
            self.report_blocker('Exact vehicle support role supplied no source repair', ident)
            raise Halt('Small vehicle support repair not submitted; original source and attempts preserved')
        saved = self.checkpoint_source('Local Qwen: correct vehicle ground support after measured boarding launch')
        self.store.set(source_checkpoint=saved, candidate_commit=saved)
        self.store.event('local-vehicle-support-source-saved', candidate=saved,
            native_pass_claimed=False, prior_diagnostic_prefix_requires_requalification=True)
        self.store.set(stage='local-clear-walk-arithmetic'); self.store.report()
        def finish(_, fields):
            prefix = compose_clear_walk(fields)['scenario']
            # Reuse the first measured successful horizontal driving roundtrip.
            # This is a new proposal after source/prefix changes, never a cached pass.
            parameters = self.store.get('map_traversal_strategies')[0]['parameters']
            result = compose_maneuver(prefix, {**parameters, 'summary': fields['summary']})
            history = self.store.get('map_traversal_strategies')
            record = admit_strategy(result['scenario'], fields['summary'], history)
            record.update(utc=now(), round=ident, feedback_round=OBSERVED,
                source_checkpoint=saved, author='local Qwen source/arithmetic; disclosed cloud composition',
                parameters=parameters)
            self.store.set(map_traversal_strategies=history+[record],
                map_support_proposed_prefix=prefix, last_valid_replay=result['scenario'])
            self.store.event('support-repair-provenance', **record,
                cloud_role='Select clear Z17/X2/Z8 waypoints and compose ordinary keys; reuse observed driving proposal',
                local_role='Vehicle source repair and walking duration arithmetic',
                old_prefix_preserved_as_diagnostic=True, native_pass_claimed=False)
            return result
        result = self.model.session('replay-author', ident+'-clear-walk-durations',
            'Compute four simple durations and immediately call finish_task. No route planning.',
            'Compute only north_seconds=(17-1.7)/3.2; east_seconds=12.5333/3.2; '
            'west_seconds=(12.5333-2)/3.2; south_seconds=(17-8)/3.2. '
            'Return numeric seconds to five decimal places and a concise summary explaining the changed '
            'walking path crosses at Z17 because the old Z11 path steps onto the pier base. '
            'The controller composes W,D,1.2s released dwell,A,S,E; native tests decide whether this '
            'new prefix and the saved driving proposal pass. Never claim acceptance from arithmetic. '
            'One finish_task call now; no source, full replay or long explanation.',
            [tool('finish_task', 'Submit four walking durations and one sentence.',
                  {**{k: {'type': 'number'} for k in ('north_seconds','east_seconds','west_seconds','south_seconds')},
                   'summary': {'type': 'string'}})], {'finish_task': finish}, turns=1, reasoning_effort='low')
        if not result.get('scenario'):
            self.report_blocker('Four arithmetic walking fields not submitted; local source saved', ident)
            raise Halt('Clear walking arithmetic not submitted; source and all native failures preserved')
        return result


if __name__ == '__main__': raise SystemExit(main(MapSupportRepair))
