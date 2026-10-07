#!/usr/bin/env python3
"""Seal scoped geometry evidence without rewriting the original generic red gate."""
from resume_camera_native_only import CameraNativeOnly
from preflight_counter_exfil import TASK,SOURCE
from resume_three_day_queue import main
from loop_controller.core import Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH

PRIOR='q0160-4244e2b1'

def union_support(point,inventory,radius=.38):
    x,_,z=point['position'];y=point['groundY']
    bounds=(x-radius,x+radius,z-radius,z+radius);rects=[]
    for obj in inventory['objects']:
        c,s=obj['boundsCenter'],obj['boundsSize']
        if obj['kind']!='renderer' or not obj['enabled'] or s[1]>=.6 or abs(c[1]+s[1]/2-y)>=.25:continue
        rect=(max(bounds[0],c[0]-s[0]/2),min(bounds[1],c[0]+s[0]/2),
              max(bounds[2],c[2]-s[2]/2),min(bounds[3],c[2]+s[2]/2))
        if rect[1]>rect[0] and rect[3]>rect[2]:rects.append((rect,obj['name']))
    xs=sorted({bounds[0],bounds[1]}|{v for r,_ in rects for v in r[:2]})
    zs=sorted({bounds[2],bounds[3]}|{v for r,_ in rects for v in r[2:]})
    uncovered=0
    for a,b in zip(xs,xs[1:]):
        for c,d in zip(zs,zs[1:]):
            px,pz=(a+b)/2,(c+d)/2
            if not any(r[0]<=px<=r[1] and r[2]<=pz<=r[3] for r,_ in rects):uncovered+=(b-a)*(d-c)
    return dict(position=point['position'],uncovered_square_metres=uncovered,passed=bool(point.get('ground')) and uncovered==0,
        renderers=sorted({name for _,name in rects}),scope='Union of actual thin renderer bounds; not mesh-triangle or driving proof')

def validate_evidence(gate,runtime,survey):
    if (gate.get('candidate_commit')!=SOURCE or gate.get('failure')!=['unchanging-captures']
            or gate.get('build_exit')!=0 or gate.get('compile_errors') or gate.get('player_exit')!=0
            or not gate.get('build_id') or not gate.get('scene_inventory',{}).get('passed')
            or runtime.get('errors')!=0 or not runtime.get('completed') or runtime.get('duration')!=78
            or runtime.get('capture_id')!=PRIOR+'-survey' or survey.get('time')!=77):
        raise Halt('Require actual completed error-free native geometry recording; preserve every other failure')

class SealCounterExfilPreflight(CameraNativeOnly):
    def validate_recovery(self,old):
        expected=dict(status='paused',controller_pid=None,owned_process=None,current_round=PRIOR,
            source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
            failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
            blocker="Halt: Native preflight prerequisite failed: ['unchanging-captures']")
        if any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_preflight_sealed'):
            raise Halt('Require the original static-ending capture prerequisite stop')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_preflight_sealed=True,recovery_route='scope-native-geometry-recording',
            recovery_change='Preserve generic red gate: two post-ending stationary images need not change for a read-only geometry survey. Use actual native completion/physics results and renderer-union analysis at pavement seams. No gameplay PASS or new engine run.')
    def work(self):
        ident=self.begin(TASK,'seal-native-counter-exfil-preflight')
        bundle=self.store.root/'evidence'/(PRIOR+'-survey');captures=bundle/'captures'
        gate=read_json(bundle/'gate.json');runtime=read_json(captures/'runtime-result.json')
        survey=read_json(captures/'counter-exfil-survey.json');inventory=read_json(captures/'scene-transforms.json')
        validate_evidence(gate,runtime,survey)
        for route in survey['routes']:
            route['renderedSupportUnion']=[union_support(p,inventory) for p in route['points']]
            route['groundedAndRenderedUnion']=all(p['passed'] for p in route['renderedSupportUnion'])
        central=next(r for r in survey['routes'] if r['name']=='central-westbound')
        if not all(central[k] for k in ('capsuleClear','coupeClear','groundedAndRenderedUnion')):
            raise Halt('Central geometry is not qualified; preserve measured obstruction or actual support gap')
        originals=[bundle/'gate.json',captures/'counter-exfil-survey.json',captures/'runtime-result.json',
            captures/'scene-transforms.json',captures/'trace.jsonl',*captures.glob('frame-*.png')]
        survey.update(candidate=SOURCE,build_id=gate['build_id'],evidence=bundle.name,gameplay_verified=False,
            original_gate_preserved=dict(passed=False,failure=gate['failure']),
            original_sha256={str(p.relative_to(bundle)):sha(p.read_bytes()) for p in originals},
            scoped_qualification='Native westbound clearance and renderer-bounds union only. Turning, driven traversal, activation and incident remain unverified.')
        atomic(self.store.root/'evidence'/(ident+'-counter-exfil-preflight.json'),survey)
        self.store.set(counter_exfil_preflight=survey);self.store.report()
        raise Halt('Native westbound geometry recorded; local Qwen must implement the one-incident parent contract')

if __name__=='__main__':raise SystemExit(main(SealCounterExfilPreflight))
