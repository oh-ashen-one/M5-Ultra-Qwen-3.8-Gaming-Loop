#!/usr/bin/env python3
"""One exact local steering calculation, then single-parameter native corrections."""
import json
from resume_three_day_queue import main
from resume_map_drive_micro import MapDriveMicro,compose_maneuver,driving_feedback,LIMITS,SOURCE,ACCEPTED,PREFIX
from qualify_map_extension import MAP_TASK
from loop_controller.core import Halt,now
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.recovery_policy import admit_strategy
from loop_controller.runner import git

ROUND='q0062-c575829a'
BLOCKER='Halt: Small driving field submission failed; prefix and explicit blocker preserved'


def validate_exact_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=11,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_drive_micro_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_drive_exact_attempted'):
        raise Halt('Expected the exact preserved four-field output stop')
    prefix=old.get('map_walking_prefix') or {}
    if prefix.get('candidate')!=SOURCE or prefix.get('native_round')!=PREFIX or not prefix.get('walk',{}).get('passed'):
        raise Halt('Preserve the native-passing walking and boarding prefix')


class MapDriveExact(MapDriveMicro):
    def validate_recovery(self,old):
        validate_exact_pause(old)
        scenario=json.loads((self.store.root/'evidence'/PREFIX/'captures/scenario.json').read_text())
        if scenario!=old['map_walking_prefix']['scenario']:raise Halt('Verified prefix changed')

    def recovery_settings(self):
        return {'map_drive_exact_attempted':True,'recovery_route':'changed-strategy',
            'recovery_change':'One steering arithmetic value; subsequent correction changes only one parameter'}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        prefix=self.store.get('map_walking_prefix')['scenario']
        if git(self.repo,'rev-parse','HEAD')!=SOURCE:raise Halt('Exact native prefix source changed')
        history=self.store.get('map_traversal_strategies',[])
        initial=not history
        previous=history[-1]['parameters'] if history else dict(approach_seconds=.75,turn_seconds=1.444444,out_seconds=.8,reverse_seconds=5.5)
        feedback=driving_feedback(self.store.root/'evidence'/self.store.get('map_traversal_feedback_round')) if history else None
        self.c.update(output_tokens=1024 if initial else 2048,model_timeout_seconds=120)
        self.store.set(stage='local-single-driving-parameter');self.store.report()
        def finish(_,fields):
            parameters={**previous,fields['parameter']:fields['seconds']}
            result=compose_maneuver(prefix,{**parameters,'summary':fields['summary']})
            record=admit_strategy(result['scenario'],result['summary'],history)
            record.update(utc=now(),round=ident,feedback_round=feedback['round'] if feedback else PREFIX,
                source_checkpoint=SOURCE,author='local Qwen',parameters=parameters)
            self.store.set(map_traversal_strategies=history+[record],last_valid_replay=result['scenario'])
            self.store.event('bounded-changed-map-strategy',**record)
            self.store.event('single-drive-field-provenance',local_parameter=fields['parameter'],
                local_value=fields['seconds'],cloud_role='Maneuver structure and initial approach/out/reverse test values',
                game_source_changed=False,native_pass_claimed=False)
            return result
        if initial:
            prompt=('Compute only (100-30)/90 + 2/3 seconds, to four decimal places. '
                'Call finish_task with parameter="turn_seconds", seconds=that number, and a one-sentence '
                'summary explaining this computes a100degree steering interval after an initial30degrees. '
                'Do not design a route or inspect geometry. This arithmetic parameter goes into a normal-input '
                'native diagnostic; physics will independently decide whether the route works.')
        else:
            prompt=('Choose only ONE numeric adjustment to the last measured driving maneuver. Return finish_task '
                'with parameter,seconds,summary. Do not generate a full route or source. Existing sequence: '
                'W approach; coast1.5; W+D turn; W out; coast2.2; S reverse; coast1.2. '
                'Opening is X6,Z8..20. Target is X>=12 then return X<=6. Lower approach turns earlier; '
                'higher approach turns later. Lower turn rotates less clockwise; higher turn rotates more. '
                'Vehicle speeds max8forward/3reverse; steering about90deg/s once moving. '
                'If outside succeeded but return fell short, adjust only reverse duration. Otherwise adjust '
                'only the parameter responsible for the measured missed opening/obstacle. '
                'Use a short diagnosis and call the tool promptly. Current parameters:'+json.dumps(previous)+
                '\nAllowed ranges:'+json.dumps(LIMITS)+'\nMeasured endpoints:'+json.dumps(feedback))
        fields={'parameter':{'type':'string','enum':['turn_seconds'] if initial else list(LIMITS)},
            'seconds':{'type':'number'},'summary':{'type':'string'}}
        result=self.model.session('replay-author',ident+'-one-drive-parameter',
            'Return one small numeric tool result. No broad plan or long explanation.',
            prompt,[tool('finish_task','Submit one numeric maneuver parameter and a short explanation.',fields)],
            {'finish_task':finish},turns=2,reasoning_effort='low')
        if not result.get('scenario'):
            self.report_blocker('Single-parameter driving role supplied no valid result: '+str(result.get('bounded_stop')),ident)
            raise Halt('Single-parameter driving submission exhausted; explicit blocker and native prefix preserved')
        return result


if __name__=='__main__':raise SystemExit(main(MapDriveExact))
