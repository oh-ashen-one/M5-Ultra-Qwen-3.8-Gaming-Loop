#!/usr/bin/env python3
"""Local diagnosis and up to three changed native routes on the existing map candidate."""
import json
from continue_game_queue import ContinuousRunner,failure_key
from resume_three_day_queue import ThreeDayRunner,main
from resume_map_spans import PATH
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK,qualify_one_extension
from loop_controller.core import Halt,atomic,now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.recovery_policy import admit_strategy,recovery_route,replay_identity
from loop_controller.replay_contract import finish_tool,validate_submission
from loop_controller.runner import git

SOURCE='f0ab973030062d378c7f5672985a6494cf83814f'
CANDIDATE='b54e706eff48db2ac454a91a89a61e6f34589776'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0057-fdbb23a9'
BLOCKER='Halt: Repeated diagnosed blocker on connected-map-extension; failed source preserved and last playable state restored'


def validate_traversal_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=10,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_compile_recovery_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_traversal_recovery_attempted'):
        raise Halt('Expected exact preserved native map traversal rejection')


def evidence_packet(bundle):
    gate=json.loads((bundle/'scoped-gate.json').read_text())
    objects=json.loads((bundle/'captures/scene-transforms.json').read_text())['objects']
    colliders=[{k:r[k] for k in ('name','kind','boundsCenter','boundsSize','enabled') if k in r}
               for r in objects if r['kind']!='renderer']
    rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
    scenario=json.loads((bundle/'captures/scenario.json').read_text())
    # Endpoint, collision and boarding observations; never substitute simulated positions.
    times=sorted(set([4,8,11.5,13.5,17.5,20,20.4,23.5,27.5,28.5,33]+[r['time'] for r in rows[::30]]))
    samples=[]
    for t in times:
        row=min(rows,key=lambda r:abs(r['time']-t))
        samples.append({k:row.get(k) for k in ('time','keys','mode','player','vehicle','grounded',
            'playerPenetration','vehiclePenetration')})
    return {'native_round':bundle.name,'candidate':gate['candidate_commit'],
        'failure':gate.get('failure'),'facts':gate.get('scoped_facts'),
        'colliders':colliders,'trace_samples':samples,'failed_scenario':scenario}


class MapTraversalRecovery(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_traversal_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Expected exact accepted fallback')
        gate=json.loads((self.store.root/'evidence'/ROUND/'scoped-gate.json').read_text())
        if gate['candidate_commit']!=CANDIDATE or recovery_route(gate,0)!='changed-strategy':
            raise Halt('Expected the verified recoverable native traversal failure')

    def recovery_settings(self):
        return {'map_traversal_recovery_attempted':True,'map_traversal_strategies':[],
            'map_traversal_feedback_round':ROUND,'recovery_route':'changed-strategy',
            'recovery_limit':3,'recovery_authorization':'Owner-directed bounded diagnosis after q0057'}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        history=self.store.get('map_traversal_strategies',[])
        if not history:
            if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Initial fallback changed')
            git(self.repo,'restore','--source='+CANDIDATE,'--','game/'+PATH)
            original=self.checkpoint_source('Recover compiled local map candidate for measured route repair')
            self.store.set(source_checkpoint=original,candidate_commit=original)
            self.store.event('restore-local-map-candidate',candidate=CANDIDATE,
                cloud_game_code_authored=False,accepted_checkpoint_unchanged=True)
        bundle=self.store.root/'evidence'/self.store.get('map_traversal_feedback_round')
        packet=evidence_packet(bundle)
        source='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in
            (PATH,'Assets/Game/VehicleInteraction.cs'))
        source+='\nBOOTSTRAP AND WALKER:\n'+(self.project/'Assets/Game/Bootstrap.cs').read_text().split('    public class Follow')[0]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-map-geometry-diagnosis',recovery_route='changed-strategy');self.store.report()
        original_scenario=packet['failed_scenario']
        original_identity=replay_identity(original_scenario)
        def finish(_,fields):
            result=validate_submission(fields,task)
            if replay_identity(result['scenario'])==original_identity:
                raise ValueError('This is the replay that just failed; change the physical route using the trace')
            record=admit_strategy(result['scenario'],result['summary'],history)
            record.update(utc=now(),feedback_round=bundle.name,round=ident,
                source_checkpoint=self.store.get('source_checkpoint'),author='local Qwen')
            self.store.set(map_traversal_strategies=history+[record],last_valid_replay=result['scenario'])
            self.store.event('bounded-changed-map-strategy',**record)
            return result
        prompt=('Diagnose the failed traversal from the actual collider bounds, trace and current source, then '
            'repair only its normal-input replay. No new source/art is needed before testing a route around the '
            'existing visible obstacles. Explain the concrete cause and changed route briefly in summary; '
            'call finish_task with summary,duration,input_steps,captures. Every step is {start,end,keys}. '
            'Use uppercase W/A/S/D/E, no empty steps, first4seconds input-free, duration16..150, >=4 increasing '
            'captures. E must last>=0.25s and must occur within the actual source boarding range. '
            'The old accepted rectangle is X-1..6,Z-2..30. New floor is X6..22,Z8..20. First walk toX>=12, '
            'remain outside>=1second and capture, then physically walk back inside. Board the actual car, '
            'drive toX>=12, remain>=1second and capture, then physically drive back inside. No resets or '
            'teleports. Respect actual turn-rate, acceleration, vehicle dimensions and collision geometry. '
            'Previous route stopped atX4.535/Z14.5; dumpster_b bounds leftX4.875 with player radius/skin '
            'accounting for the gap. At previous E the player was approximately3.85m from the car and '
            'never entered vehicle mode. Do not assume intended keys caused driving. Find a physically '
            'clear crossing/approach using ALL collider bounds, including piers and car extents. '
            'Preserve collision tests; never remove obstacles or alter controls just to fit a replay. '
            'This role must submit an actual changed strategy, not another reading/planning loop. '
            'Your summary is a concise user-facing diagnosis, not private reasoning.\n'
            'NATIVE EVIDENCE:\n'+json.dumps(packet)+'\nCURRENT SOURCE:\n'+source+
            '\nALREADY ATTEMPTED STRATEGIES:\n'+json.dumps(history))
        result=self.model.session('replay-author',ident+'-geometry-replay',
            'You are local Qwen diagnosing and repairing real input-driven native game traversal.',
            prompt,[finish_tool()],{'finish_task':finish},turns=2,reasoning_effort='low')
        if not result.get('scenario'):
            self.report_blocker('Local geometry/replay role submitted no valid changed strategy',ident)
            raise Halt('Map recovery supplied no valid changed replay; explicit blocker report saved')
        return result

    def report_blocker(self,reason,ident):
        report={'utc':now(),'round':ident,'reason':reason,'recovery_route':'report-blocker',
            'attempts':self.store.get('map_traversal_strategies',[]),
            'accepted_checkpoint':self.store.get('last_playable_checkpoint'),
            'source_checkpoint':self.store.get('source_checkpoint'),
            'hard_cap_epoch':HARD_CAP_EPOCH,'approval_wait':False,
            'delivery_status':'pending-existing-parent-oversight','no_duplicate_schedule':True}
        atomic(self.store.root/'RECOVERY-BLOCKER.json',report)
        self.store.set(recovery_route='report-blocker',recovery_blocker_report='RECOVERY-BLOCKER.json')
        self.store.event('bounded-recovery-blocker-reported',**report);self.store.report()

    def reject_scoped(self,task,ident,feedback,candidate):
        if task['id']!=MAP_TASK['id']:return super().reject_scoped(task,ident,feedback,candidate)
        count=len(self.store.get('map_traversal_strategies',[]))
        if recovery_route(feedback,count)!='changed-strategy':
            self.report_blocker('Bounded map recovery exhausted or requires a different diagnosed repair',ident)
            return super().reject_scoped(task,ident,feedback,candidate)
        key=failure_key({k:feedback[k] for k in ('failure','compile_errors','verdict','fixes') if k in feedback})
        streak=self.store.get('failure_streak',0)+1 if key==self.store.get('failure_key') else 1
        self.store.set(feedback=feedback,failure_key=key,failure_streak=streak,
            task_failures=self.store.get('task_failures',0)+1,stage='changed-strategy-recovery',
            map_traversal_feedback_round=ident,recovery_route='changed-strategy')
        self.store.event('recoverable-native-failure-routed',candidate=candidate,
            task=task['id'],attempts=count,maximum=3,failure=feedback.get('failure'),
            counters_preserved=True,next_action='Local Qwen diagnoses this trace and changes normal-input route')
        self.store.report()

    def work(self):
        self.machine.guard();self.store.set(task_design=NEXT_MAP)
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,recovery_route='accepted',
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(MapTraversalRecovery))
