#!/usr/bin/env python3
"""Split the local replay problem: verify walk/boarding, then append local driving."""
import json
from resume_three_day_queue import main
from resume_map_traversal import MapTraversalRecovery,evidence_packet,CANDIDATE,ACCEPTED
from qualify_map_extension import MAP_TASK,inspect_extension,outside_distance
from loop_controller.core import Halt,atomic,now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import admit_strategy
from loop_controller.replay_contract import finish_tool,validate_submission
from loop_controller.runner import git

SOURCE='1c68cc752e653129196cfec1c2aa153d8445ca87'
ROUND='q0058-e3955810'
BLOCKER='Halt: Map recovery supplied no valid changed replay; explicit blocker report saved'


def validate_segment_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=10,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_traversal_recovery_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_segment_recovery_attempted'):
        raise Halt('Expected exact preserved no-submission map recovery stop')


def compact_packet(packet):
    return {'native_round':packet['native_round'],'failure':packet['failure'],
        'colliders':[{k:(list(map(lambda v:round(v,4),value)) if isinstance(value,list) else value)
                      for k,value in r.items()} for r in packet['colliders'] if r['name']!='GroundCollider'],
        'trace_samples':packet['trace_samples'][::3]}


def inspect_walking_prefix(rows,scenario):
    report=inspect_extension(rows)
    failure=[x for x in report['failure'] if x.startswith(('foot-','walking-'))]
    if not rows or rows[-1].get('mode')!='vehicle':failure.append('actual-boarding-missing')
    if not any(abs(r['time']-t)<=.25 and r.get('mode')=='foot' and
               outside_distance(r['player'])>=6 for t in scenario['captures'] for r in rows):
        failure.append('foot-outside-capture-missing')
    return {'passed':not failure,'failure':failure,'traversal':report['traversal']['foot'],
        'final_state':{k:rows[-1].get(k) for k in ('time','mode','player','vehicle','vehiclePenetration')} if rows else {},
        'scope':'Diagnostic walking roundtrip and boarding only; not connected-map acceptance'}


def combine_driving(prefix,fields):
    if any(s['start']<prefix['duration'] for s in fields['input_steps']):
        raise ValueError('Driving steps must begin after the unchanged verified walking-prefix duration')
    combined={**fields,'input_steps':prefix['steps']+fields['input_steps'],
        'captures':sorted(set(prefix['captures']+fields['captures']))}
    return validate_submission(combined,MAP_TASK)


class MapWalkFirst(MapTraversalRecovery):
    def validate_recovery(self,old):
        validate_segment_pause(old)
        if git(self.repo,'diff','--name-only',CANDIDATE,SOURCE,'--','game'):
            raise Halt('Expected the previously compiled local map candidate')

    def recovery_settings(self):
        return {'map_segment_recovery_attempted':True,'map_prefix_attempts':0,
            'recovery_route':'changed-strategy','map_walking_prefix':None,
            'recovery_change':'Smaller native-verified walking/boarding prefix, then local driving suffix'}

    def local_prefix(self,ident,packet):
        bootstrap=(self.project/'Assets/Game/Bootstrap.cs').read_text()
        walker=bootstrap[bootstrap.index('    public class Walker'):bootstrap.index('    public class Follow')]
        vehicle=(self.project/'Assets/Game/VehicleInteraction.cs').read_text()
        boarding=vehicle[vehicle.index('        void Update()'):vehicle.index('            // Driving:')]
        output_tokens=self.store.get('walking_prefix_output_tokens',8192)
        if output_tokens not in (8192,16384):raise Halt('Unqualified walking output budget')
        self.c.update(output_tokens=output_tokens,model_timeout_seconds=700 if output_tokens==16384 else 400)
        self.store.set(stage='local-walking-boarding-prefix');self.store.report()
        prompt=('Solve ONLY walking around the measured dumpster and then boarding. Do not plan driving yet. '
            'Submit finish_task promptly: summary (one-sentence cause/repair), duration16..45, input_steps '
            '[{start,end,keys}], captures. First4seconds stationary. Use uppercase WASD and one E press>=0.25s; '
            'no empty steps, R, teleport or code edits. At most12steps. Walk from actualspawnX0,Z1.7 '
            'through the opening X6,Z8..20 toX>=12, stay outside>=1s with a capture, return physically '
            'toX<=6, then approach the settled car nearX3.36,Z7.96 and actually board. Finish in vehicle mode '
            'at rest. Compute timings from world-space walking speed3.2m/s and collider extents. '
            'Earlier crossing atZ14.5 hit dumpster_b leftX4.875; use a clear route. Required floor X6..22,Z8..20. '
            'At least4captures include outside walking, return and after E. Never assume an E press worked. '
            'All required mechanics/geometry are attached; give one compact tool call, no broad plan.\n'
            'WALKER:\n'+walker+'\nBOARDING:\n'+boarding+'\nMEASURED EVIDENCE:\n'+json.dumps(compact_packet(packet)))
        def finish(_,fields):
            result=validate_submission(fields,MAP_TASK)
            if result['scenario']['duration']>45 or len(result['scenario']['steps'])>12:
                raise ValueError('Keep this walking/boarding prefix within45seconds and12steps')
            return result
        return self.model.session('replay-author',ident+'-walk-prefix',
            'You are local Qwen repairing only the walking/boarding prefix from real native evidence.',
            prompt,[finish_tool()],{'finish_task':finish},turns=2,reasoning_effort='low')

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        packet=evidence_packet(self.store.root/'evidence'/self.store.get('map_traversal_feedback_round'))
        prefix_record=self.store.get('map_walking_prefix')
        while not prefix_record:
            count=self.store.get('map_prefix_attempts',0)
            if count>=2:
                self.report_blocker('Two measured walking/boarding prefix attempts failed',ident)
                raise Halt('Walking prefix recovery exhausted; exact source/evidence preserved')
            label=ident+'-prefix-'+str(count+1)
            result=self.local_prefix(label,packet)
            if not result.get('scenario'):
                self.report_blocker('Smaller walking role submitted no replay: '+str(result.get('bounded_stop')),ident)
                raise Halt('Walking role no-submission; smaller role stop preserved')
            scenario=result['scenario'];self.store.set(map_prefix_attempts=count+1)
            candidate=git(self.repo,'rev-parse','HEAD')
            bundle,gate=self.native(task,label,candidate,scenario)
            if not gate.get('passed'):
                self.report_blocker('Walking diagnostic failed native build/runtime gate',label)
                raise Halt('Walking diagnostic native gate failed; no physical pass claimed')
            rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            walk=inspect_walking_prefix(rows,scenario);gate['walking_prefix']=walk
            atomic(bundle/'walking-prefix-gate.json',gate)
            if not walk['passed']:
                packet=evidence_packet(bundle);packet['failure']=walk['failure']
                self.store.set(task_failures=self.store.get('task_failures',0)+1,
                    stage='changed-strategy-recovery',feedback=walk)
                self.store.event('walking-prefix-rejected',round=label,failure=walk['failure'],
                    preserved_candidate=candidate,next_action='One changed local walking/boarding route')
                self.store.report();continue
            prefix_record={'candidate':candidate,'scenario':scenario,'native_round':label,'walk':walk}
            self.store.set(map_walking_prefix=prefix_record)
            self.store.event('walking-prefix-native-pass',round=label,candidate=candidate,
                final_game_accepted=False,map_extension_accepted=False,walking=walk)
        if git(self.repo,'rev-parse','HEAD')!=prefix_record['candidate']:
            raise Halt('Walking prefix cannot be reused across changed game source')
        prefix=prefix_record['scenario'];vehicle=(self.project/'Assets/Game/VehicleInteraction.cs').read_text()
        history=self.store.get('map_traversal_strategies',[])
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-driving-suffix');self.store.report()
        def finish(_,fields):
            result=combine_driving(prefix,fields)
            record=admit_strategy(result['scenario'],result['summary'],history)
            record.update(utc=now(),feedback_round=packet['native_round'],round=ident,
                source_checkpoint=self.store.get('source_checkpoint'),author='local Qwen')
            self.store.set(map_traversal_strategies=history+[record],last_valid_replay=result['scenario'])
            self.store.event('bounded-changed-map-strategy',**record)
            return result
        prompt=('A native-tested unchanged prefix has already walked outside, returned and boarded. '
            'Now supply ONLY the driving suffix in finish_task: summary with measured repair, overall duration<=150, '
            'input_steps occurring at or after '+str(prefix['duration'])+'seconds and >=4capture times after that. '
            'The controller prepends the exact verified prefix. At the boundary the car is stationary, vehicle '
            'mode is real, and its final position is attached. Drive through the actual opening toX>=12, '
            'remain outside>=1s with capture, then physically return toX<=6 and capture. No E/R, exit, reset '
            'or teleport. Use W/S throttle and A/D steering with exact VehicleInteraction physics. The car is '
            'about1.8mwide and4.3mlong; plan collision-free clearance around piers/dumpsters and finite alley '
            'boundaries. Preserve all source. Propose a compact practical suffix, not an entire new walk or '
            'design essay. It is unverified until native execution.\nVERIFIED PREFIX:\n'+json.dumps(prefix_record)+
            '\nMEASURED GEOMETRY/FAILED ROUTE:\n'+json.dumps(compact_packet(packet))+
            '\nEXACT VEHICLE MECHANICS:\n'+vehicle+'\nPRIOR STRATEGIES:\n'+json.dumps(history))
        result=self.model.session('replay-author',ident+'-driving-suffix',
            'You are local Qwen authoring one physical driving roundtrip after a verified boarding prefix.',
            prompt,[finish_tool()],{'finish_task':finish},turns=2,reasoning_effort='low')
        if not result.get('scenario'):
            self.report_blocker('Driving suffix role submitted no valid replay: '+str(result.get('bounded_stop')),ident)
            raise Halt('Driving suffix no-submission; verified walking prefix preserved')
        return result


if __name__=='__main__':raise SystemExit(main(MapWalkFirst))
