#!/usr/bin/env python3
"""Four local maneuver parameters followed by native proof and bounded correction."""
import json
import math
from resume_three_day_queue import main
from resume_map_traversal import MapTraversalRecovery,CANDIDATE,ACCEPTED
from qualify_map_extension import MAP_TASK
from loop_controller.core import Halt,now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import admit_strategy
from loop_controller.replay_contract import validate_submission
from loop_controller.runner import git

SOURCE='1c68cc752e653129196cfec1c2aa153d8445ca87'
ROUND='q0061-22c8f22d'
PREFIX='q0061-22c8f22d-prefix-2'
BLOCKER='Halt: Driving suffix no-submission; verified walking prefix preserved'
LIMITS={'approach_seconds':(.3,1.25),'turn_seconds':(.8,1.9),
        'out_seconds':(.3,2),'reverse_seconds':(3,8)}


def validate_drive_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=11,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_return_micro_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_drive_micro_attempted'):
        raise Halt('Expected exact preserved driving no-submission stop')
    prefix=old.get('map_walking_prefix') or {}
    if prefix.get('candidate')!=SOURCE or prefix.get('native_round')!=PREFIX or not prefix.get('walk',{}).get('passed'):
        raise Halt('A real source-matched walking-return-boarding prefix is required')


def compose_maneuver(prefix,fields):
    for key,(low,high) in LIMITS.items():
        value=fields[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ValueError(key+' must remain within the bounded maneuver range')
    steps=[dict(s,keys=list(s['keys'])) for s in prefix['steps']]
    captures=list(prefix['captures']);cursor=round(prefix['duration']+.8,5)
    def press(keys,duration):
        nonlocal cursor
        end=round(cursor+duration,5);steps.append({'start':cursor,'end':end,'keys':keys});cursor=end
    press(['W'],fields['approach_seconds'])
    cursor=round(cursor+1.5,5)  # Release all keys so normal deceleration settles speed.
    press(['W','D'],fields['turn_seconds'])
    press(['W'],fields['out_seconds'])
    captures.extend([round(cursor+.4,5),round(cursor+1.4,5),round(cursor+2.1,5)])
    cursor=round(cursor+2.2,5)
    press(['S'],fields['reverse_seconds'])
    captures.append(round(cursor+.85,5))
    return validate_submission({'summary':fields['summary'],'duration':round(cursor+1.2,5),
        'input_steps':steps,'captures':sorted(set(captures))},MAP_TASK)


def driving_feedback(bundle):
    gate=json.loads((bundle/'scoped-gate.json').read_text())
    scenario=json.loads((bundle/'captures/scenario.json').read_text())
    rows=[json.loads(l) for l in (bundle/'captures/trace.jsonl').read_text().splitlines()]
    times=sorted(set([s[k] for s in scenario['steps'] for k in ('start','end') if s[k]>=22]+scenario['captures'][-4:]))
    samples=[]
    for t in times:
        row=min(rows,key=lambda r:abs(r['time']-t))
        samples.append({k:row.get(k) for k in ('time','mode','vehicle','keys','vehiclePenetration')})
    return {'round':bundle.name,'failure':gate.get('failure'),
        'map':gate.get('scoped_facts',{}).get('map_extension'),'samples':samples}


class MapDriveMicro(MapTraversalRecovery):
    def validate_recovery(self,old):
        validate_drive_pause(old)
        if git(self.repo,'diff','--name-only',CANDIDATE,SOURCE,'--','game'):
            raise Halt('Keep the exact compiled local game source')
        gate=json.loads((self.store.root/'evidence'/PREFIX/'walking-prefix-gate.json').read_text())
        scenario=json.loads((self.store.root/'evidence'/PREFIX/'captures/scenario.json').read_text())
        if gate.get('candidate_commit')!=SOURCE or not gate.get('walking_prefix',{}).get('passed') or scenario!=old['map_walking_prefix']['scenario']:
            raise Halt('Verified walking prefix evidence differs from saved state')

    def recovery_settings(self):
        return {'map_drive_micro_attempted':True,'recovery_route':'changed-strategy',
            'recovery_change':'Four numeric local maneuver parameters; immediate native feedback and at most three changed strategies'}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        prefix_record=self.store.get('map_walking_prefix');prefix=prefix_record['scenario']
        if git(self.repo,'rev-parse','HEAD')!=prefix_record['candidate']:
            raise Halt('Do not reuse walking evidence after changing game source')
        history=self.store.get('map_traversal_strategies',[])
        feedback=driving_feedback(self.store.root/'evidence'/self.store.get('map_traversal_feedback_round')) if history else None
        self.c.update(output_tokens=2048,model_timeout_seconds=120)
        self.store.set(stage='local-four-driving-parameters');self.store.report()
        def finish(_,fields):
            result=compose_maneuver(prefix,fields)
            record=admit_strategy(result['scenario'],result['summary'],history)
            record.update(utc=now(),round=ident,feedback_round=feedback['round'] if feedback else PREFIX,
                source_checkpoint=SOURCE,author='local Qwen',parameters={k:fields[k] for k in LIMITS})
            self.store.set(map_traversal_strategies=history+[record],last_valid_replay=result['scenario'])
            self.store.event('bounded-changed-map-strategy',**record)
            self.store.event('micro-drive-authorship',local_role='Choose numeric durations and diagnose observed motion',
                cloud_role='Scope maneuver structure and compose normal W/D/S intervals with unchanged native walking prefix',
                game_source_changed=False,native_pass_claimed=False)
            return result
        prompt=('Return one finish_task tool call with FOUR durations and one-sentence summary. No full replay or broad plan. '
            'Walking outside/return/boarding is already native-proven and stays unchanged. Car starts stationary at '
            'X3.359,Z7.963, heading approximately10degrees left of north (inferred from accepted native forward motion). '
            'Measured accepted straight W: after1.0s car(2.838,10.860); after1.53s(2.151,14.679). '
            'Selected small normal-input maneuver: W approach_seconds; coast1.5s; W+D turn_seconds; W out_seconds; '
            'coast2.2s; S reverse_seconds; coast1.2s. Your task is only choosing the four numeric durations. '
            'Goal: drive through opening X6,Z8..20 toX>=12, remain outside>=1s, then physically reverse toX<=6. '
            'Car width1.8,length4.3. Floor endsX22/Z20. Pier base X4..7,Z9.5..12.5; dumpster X4.875..6.125,Z12.4..14.8. '
            'A northward approach followed by a clockwise turn above the obstacles is the scoped strategy. '
            'Mechanics: acceleration6m/s2, max8forward/3reverse, coasting decel4m/s2. Steering90deg/s*min(abs(speed)/4,1), '
            'reversed when backing. From rest W+D turns30degrees in the first2/3second, then90deg/s. '
            'Useful initial calculation: approach0.75s thencoast travels about4.22m; a100degree turn takes about1.444s; '
            'outward0.8s thencoast may stop at the actual outer barrier; reverse5.5s travels about15.75m from rest. '
            'These are unverified starting estimates, not a physical pass. Choose/correct within approach0.3..1.25, '
            'turn0.8..1.9, out0.3..2, reverse3..8. On a retry change the diagnosed maneuver using actual endpoints; '
            'do not repeat the same timings. All other controls/source remain unchanged.\n'
            'PRIOR PARAMETERS:'+json.dumps([r.get('parameters') for r in history])+
            '\nACTUAL LATEST NATIVE FEEDBACK:'+json.dumps(feedback))
        fields={k:{'type':'number'} for k in LIMITS};fields['summary']={'type':'string'}
        result=self.model.session('replay-author',ident+'-four-drive-parameters',
            'You are local Qwen choosing four bounded physical maneuver durations; call the tool promptly.',
            prompt,[tool('finish_task','Submit four numeric durations and a concise measured diagnosis.',fields)],
            {'finish_task':finish},turns=2,reasoning_effort='low')
        if not result.get('scenario'):
            self.report_blocker('Four-field driving role produced no valid changed maneuver: '+str(result.get('bounded_stop')),ident)
            raise Halt('Small driving field submission failed; prefix and explicit blocker preserved')
        return result


if __name__=='__main__':raise SystemExit(main(MapDriveMicro))
