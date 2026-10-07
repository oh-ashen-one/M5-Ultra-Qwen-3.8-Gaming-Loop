#!/usr/bin/env python3
"""Measure an ordinary-input westbound maneuver and actual obstruction/release."""
import json
from resume_camera_native_only import CameraNativeOnly
from implement_counter_exfil import TASK
from finish_counter_exfil_parts import ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,atomic
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.counter_exfil_checks import values

SOURCE='9df6c96af1ccd25d3115a44434a23aec0537d273'
PRIOR='q0174-7bbb3098'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: First Counter-Exfil native recordings preserved; inspect actual activation/escape/reset before success route')
    result=old.get('counter_exfil_probe_outcome',{}).get('activation_escape',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_driving_probe_attempted')
            or not result.get('native',{}).get('passed') or not result.get('semantic',{}).get('passed')
            or result.get('semantic',{}).get('candidate')!=SOURCE):
        raise Halt('Require the actual current-source activation/escape/reset evidence and unchanged history')

def maneuver(original):
    scenario=dict(original,id='counter-exfil-normal-driving-obstruction-release',duration=127,
        captures=[.6,84.8,88.9,92.3,94.2,98.5,106,112,117,125])
    scenario['steps']=[dict(s) for s in original['steps'] if s['start']<85]
    # Cloud-authored acceptance inputs, derived from actual unchanged throttle,
    # steering and braking APIs. No state injections, transforms or collision edits.
    scenario['steps'] += [dict(start=a,end=b,keys=keys) for a,b,keys in (
        (85.2,88.1,['S','D']), (89.1,89.75,['W','D']),
        (89.75,90.1,['W']), (90.1,90.42,['W','A']), (90.42,91.75,['S']),
        (92.4,92.5,['F']), (92.7,96.6,['W']), (96.6,97.94,['S','D']),
        (115,116.6,['S']), (123,123.1,['R']))]
    return scenario

class ProbeCounterDriving(CameraNativeOnly):
    def validate_recovery(self,old):
        validate_boundary(old);self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_driving_probe_attempted=True,recovery_route='native-ordinary-driving-obstruction-diagnostic',
            recovery_change='Keep the known one-character HUD failure red. Measure actual reverse turn, westbound travel, coupe obstruction and release through ordinary keys. No promotion, forced mission state, altered collision or new model request.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-driving-diagnostic')
        original=read_json(self.store.root/'evidence'/(PRIOR+'-activation-escape')/'captures/scenario.json')
        scenario=maneuver(original);bundle=self.store.root/'evidence'/(ident+'-maneuver')
        raw=self.engines.unity(self.project,bundle,scenario,SOURCE)
        path=bundle/'captures/trace.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
        samples=[]
        for t in [84.8,88.9,92.3,94.2,98.5,106,112,117,125]:
            if not rows or rows[-1]['time']<t:continue
            row=min(rows,key=lambda r:abs(r['time']-t));ce=row.get('counterExfil',{})
            samples.append(dict(time=row['time'],mode=row['mode'],health=row['health'],player=row['player'],
                vehicle=row['vehicle'],vehicle_physics=row.get('vehiclePhysics'),vehicle_penetration=row.get('vehiclePenetration'),
                chapter=values(ce.get('chapter')),actors=ce.get('actors')))
        result=dict(candidate=SOURCE,native=raw,evidence=bundle.name,measurements=samples,
            known_hud_failure_preserved=True,physical_pin_independent_check='pending',
            full_incident_success=False,final_game_accepted=False)
        atomic(bundle/'driving-diagnostic.json',result);self.store.set(counter_exfil_driving_outcome=result);self.store.report()
        frames=sorted((bundle/'captures').glob('frame-*.png'))
        if frames:queue_milestone(self.store,'native-milestone',TASK,bundle,{**raw,'passed':False,'diagnostic_only':True},frames,
            {f'frame-{i:03d}.png':t for i,t in enumerate(scenario['captures'])})
        raise Halt('Ordinary Counter-Exfil driving and contact diagnostic preserved; inspect physical evidence before route continuation')

if __name__=='__main__':raise SystemExit(main(ProbeCounterDriving))
