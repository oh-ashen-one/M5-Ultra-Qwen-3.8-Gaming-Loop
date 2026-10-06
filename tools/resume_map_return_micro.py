#!/usr/bin/env python3
"""Keep the native-observed outward leg; ask local Qwen for three return durations."""
import json
import math
from resume_three_day_queue import main
from resume_map_walk_first import MapWalkFirst,CANDIDATE,ACCEPTED
from qualify_map_extension import MAP_TASK
from loop_controller.core import Halt,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.replay_contract import validate_submission
from loop_controller.runner import git

SOURCE='1c68cc752e653129196cfec1c2aa153d8445ca87'
ROUND='q0060-362ec8e6'
NATIVE=ROUND+'-prefix-1'
BLOCKER='Halt: Walking role no-submission; smaller role stop preserved'
SCENARIO_SHA='25f2118066bfdd01a8313f061f804d3fa1b2d408f712ae1991a82813e91dba86'


def validate_micro_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=11,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_prefix_budget_attempted=True,
        map_prefix_attempts=1,map_walking_prefix=None)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_return_micro_attempted'):
        raise Halt('Expected exact preserved second walking no-submission and first native rejection')


def compose_return(original,fields):
    durations=[fields[k] for k in ('north_seconds','west_seconds','south_seconds')]
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not .1<=v<=6 for v in durations):
        raise ValueError('Each measured axis movement must be a finite0.1..6seconds')
    kept=[dict(s,keys=list(s['keys'])) for s in original['steps'] if s['end']<=12.7]
    if len(kept)!=4 or kept[-1]['end']!=12.7:
        raise Halt('Expected the exact four observed outward/dwell intervals')
    cursor=12.7;captures=[6.5,11.3,12.3]
    for key,seconds in zip(('W','A','S'),durations):
        end=round(cursor+seconds,5);kept.append({'start':cursor,'end':end,'keys':[key]})
        cursor=end
        if key=='A':captures.append(round(cursor+.02,5))
    # Observable normal interaction; does not force or simulate a boarding state.
    cursor=round(cursor+.15,5);kept.append({'start':cursor,'end':round(cursor+.35,5),'keys':['E']})
    captures.append(round(cursor+.65,5))
    return validate_submission({'summary':fields['summary'],'duration':round(cursor+1,5),
        'input_steps':kept,'captures':captures},MAP_TASK)


class MapReturnMicro(MapWalkFirst):
    def validate_recovery(self,old):
        validate_micro_pause(old)
        if git(self.repo,'diff','--name-only',CANDIDATE,SOURCE,'--','game'):
            raise Halt('Preserve the same compiled local game candidate')
        self.original_scenario()

    def original_scenario(self):
        raw=(self.store.root/'evidence'/NATIVE/'captures/scenario.json').read_bytes()
        if sha(raw)!=SCENARIO_SHA:raise Halt('Observed outward replay changed')
        return json.loads(raw)

    def recovery_settings(self):
        return {'map_return_micro_attempted':True,'recovery_route':'changed-strategy',
            'recovery_change':'Local arithmetic for three scoped return segments; preserve verified outward inputs'}

    def local_prefix(self,ident,packet):
        original=self.original_scenario()
        self.c.update(output_tokens=2048,model_timeout_seconds=120)
        self.store.set(stage='local-three-return-durations');self.store.report()
        def finish(_,fields):
            result=compose_return(original,fields)
            self.store.event('local-return-durations-composed',native_prefix=NATIVE,
                scenario_sha256=SCENARIO_SHA,durations={k:fields[k] for k in ('north_seconds','west_seconds','south_seconds')},
                local_role='Qwen supplies arithmetic durations and concise diagnosis',
                cloud_role='Select measured-clear waypoints and compose ordinary input intervals',
                game_source_changed=False,native_pass_claimed=False)
            return result
        return self.model.session('replay-author',ident+'-three-durations',
            'Compute three axis-aligned walking durations and immediately call finish_task. No new plan.',
            'At t12.7 the native player is approximatelyX12.5333,Z11.0333. Walking speed is3.2m/s. '
            'The old A return atZ11 hits the pier base, so the selected bounded test returns viaZ17, '
            'clear of the measured dumpster and pier extents. Compute ONLY these three durations: '
            'north_seconds=(17-11.0333)/3.2 using W; west_seconds=(12.5333-2)/3.2 using A; '
            'south_seconds=(17-8)/3.2 using S. The controller preserves the already native-observed '
            'outward/dwell inputs, adds your three durations consecutively, then a normal E press near '
            'the actual car to test boarding. Required output: one finish_task tool call with '
            'north_seconds,west_seconds,south_seconds numeric seconds and summary (one sentence). '
            'Do not emit a whole replay, source, geometry search, or long explanation. Native physics '
            'will independently verify return and boarding; do not claim they passed.',
            [tool('finish_task','Submit only three numeric durations and one-sentence diagnosis.',
                {'north_seconds':{'type':'number'},'west_seconds':{'type':'number'},
                 'south_seconds':{'type':'number'},'summary':{'type':'string'}})],
            {'finish_task':finish},turns=1,reasoning_effort='low')


if __name__=='__main__':raise SystemExit(main(MapReturnMicro))
