#!/usr/bin/env python3
"""Attempt a measured physical pin, actual aimed shots and ordinary foot exit."""
import json
from probe_counter_exfil_driving import ProbeCounterDriving,SOURCE,ACCEPTED,TASK
from resume_three_day_queue import main
from loop_controller.core import Halt,read_json,atomic
from loop_controller.delivery_policy import HARD_CAP_EPOCH,queue_milestone
from loop_controller.counter_exfil_checks import chapter,values

PRIOR='q0175-1c1bc798'

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
        source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Ordinary Counter-Exfil driving and contact diagnostic preserved; inspect physical evidence before route continuation')
    result=old.get('counter_exfil_driving_outcome',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_success_probe_attempted')
            or result.get('candidate')!=SOURCE or not result.get('native',{}).get('passed')):
        raise Halt('Require the actual current-source driving/contact measurements and unchanged history')

def success_attempt(original):
    scenario=dict(original,id='counter-exfil-physical-pin-shoot-foot-exit-attempt',duration=124,
        captures=[.6,98.5,101.8,105.4,106.8,109,112,114,119,123])
    scenario['steps']=[dict(s) for s in original['steps'] if s['start']<100]
    sequence=[(100.2,100.3,['E']),(100.4,101.5,['S']),(101.6,103.9,['D']),
        (104,104.55,['W']),(104.7,104.8,['A']),
        (107.2,108.3,['S']),(108.4,111.02,['A']),(111.2,112.3,['W']),
        (112.5,113.7,['A']),(118,118.1,['R']),(120,121,['W'])]
    sequence += [(105.2+.2*i,105.28+.2*i,['Mouse0']) for i in range(9)]
    scenario['steps'] += [dict(start=a,end=b,keys=k) for a,b,k in sequence]
    scenario['steps'].sort(key=lambda s:s['start'])
    return scenario

class ProbeCounterSuccess(ProbeCounterDriving):
    def validate_recovery(self,old):
        validate_boundary(old);self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_success_probe_attempted=True,recovery_route='native-measured-pin-shoot-foot-exit-attempt',
            recovery_change='Reuse the physically measured car approach. Exit with E, walk around the real body, fire actual camera rays at the two following runners, then walk the western exit while a real lead pin must remain. Preserve all failures; claimed completion alone cannot pass independent contact/shot/crossing acceptance.')
    def work(self):
        ident=self.begin(TASK,'native-counter-exfil-success-route-attempt')
        original=read_json(self.store.root/'evidence'/(PRIOR+'-maneuver')/'captures/scenario.json')
        scenario=success_attempt(original);bundle=self.store.root/'evidence'/(ident+'-success-attempt')
        raw=self.engines.unity(self.project,bundle,scenario,SOURCE)
        path=bundle/'captures/trace.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
        completions=[r for r in rows if r.get('restarts')==0 and chapter(r).get('Complete')]
        failures=[r for r in rows if r.get('restarts')==0 and chapter(r).get('Failed')]
        selected=[]
        for t in [100.3,105.4,106.8,109,112,114,119]:
            if not rows or rows[-1]['time']<t:continue
            r=min(rows,key=lambda x:abs(x['time']-t));ce=r.get('counterExfil',{})
            selected.append(dict(time=r['time'],health=r['health'],mode=r['mode'],player=r['player'],vehicle=r['vehicle'],
                shots=r['shots'],hits=r['hits'],chapter=values(ce.get('chapter')),actors=ce.get('actors')))
        result=dict(candidate=SOURCE,native=raw,evidence=bundle.name,
            reported_completion_time=completions[0]['time'] if completions else None,
            reported_failure_time=failures[0]['time'] if failures else None,measurements=selected,
            independent_success_acceptance='pending actual contact/shot/crossing inspection',
            known_hud_failure_preserved=True,full_incident_success=False,final_game_accepted=False)
        atomic(bundle/'success-attempt.json',result);self.store.set(counter_exfil_success_outcome=result);self.store.report()
        frames=sorted((bundle/'captures').glob('frame-*.png'))
        if frames:queue_milestone(self.store,'native-milestone',TASK,bundle,{**raw,'passed':False,'diagnostic_only':True},frames,
            {f'frame-{i:03d}.png':t for i,t in enumerate(scenario['captures'])})
        raise Halt('Counter-Exfil physical success attempt recorded; independent contact, shot and crossing proof required')

if __name__=='__main__':raise SystemExit(main(ProbeCounterSuccess))
