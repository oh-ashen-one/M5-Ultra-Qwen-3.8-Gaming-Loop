"""Scoped native queue contracts; none replaces final whole-game acceptance."""
import json
import math
from .core import read_json
from .mission_anchors import inspect_mission_anchors
from .mission_hud import inspect_courier_hud

KEYS={'W','A','S','D','E','R','F','Space','LeftShift','Mouse0','Mouse1','Escape'}


def scenario(duration,steps,captures,coverage='foundation'):
    return {'id':'continuous-'+coverage,'coverage':coverage,'duration':duration,
            'steps':[{'start':a,'end':b,'keys':k} for a,b,k in steps],'captures':captures}


WORLD_PROBE=scenario(26,[(4,16,['W']),(18,23,['A'])],[3.2,10,17,24])
MOTOR_PROBE=scenario(34,[(4,5.6,['W']),(5.6,6.6,['D']),(7.2,7.45,['E']),
    (8,18,['W']),(21,21.25,['E']),(24,24.25,['R']),(27,29,['W'])],
    [3.2,6.8,13,18.5,21.8,25,31],'driving')


def validate_proposed(value,maximum,coverage):
    if (not isinstance(value,dict) or not isinstance(value.get('duration'),(int,float))
            or not math.isfinite(value['duration']) or not 16<=value['duration']<=maximum):
        raise ValueError('Invalid bounded replay duration')
    steps=value.get('steps',[]);captures=value.get('captures',[])
    if not 1<=len(steps)<=160 or not 4<=len(captures)<=120:raise ValueError('Invalid replay step/capture count')
    for step in steps:
        if (set(step)!={'start','end','keys'} or not all(isinstance(step[k],(int,float)) and math.isfinite(step[k]) for k in ('start','end'))
                or not 4<=step['start']<step['end']<=value['duration']):
            raise ValueError('Invalid input interval')
        if not isinstance(step['keys'],list) or not step['keys'] or not set(step['keys'])<=KEYS:raise ValueError('Invalid replay keys')
    if not any('W' in s['keys'] for s in steps):raise ValueError('Replay must exercise movement')
    if any(not isinstance(t,(int,float)) or not math.isfinite(t) or not 0<=t<value['duration'] for t in captures):
        raise ValueError('Invalid capture time')
    if captures!=sorted(set(captures)):raise ValueError('Capture times must increase')
    return {'id':'observed-'+coverage,'coverage':coverage,**{k:value[k] for k in ('duration','steps','captures')}}


def window_motion(rows,key,start,end):
    values=[r[key] for r in rows if start<=r['time']<=end and len(r.get(key) or [])==3]
    return math.dist(values[0],values[-1]) if len(values)>=3 else None


def evaluate_step(task,bundle,base):
    if not base.get('passed'):
        trace=bundle/'captures/trace.jsonl'
        if trace.exists() and 'motor_reset' in task['checks']:
            rows=[json.loads(line) for line in trace.read_text().splitlines()]
            observations=[]
            for start,end,label in [(7.15,7.6,'first-entry'),(8,18,'intended-driving'),(21.5,23.5,'pre-reset-exit'),(25,26,'after-reset')]:
                selected=[r for r in rows if start<=r['time']<=end]
                observations.append({'window':label,'seconds':[start,end],'samples':len(selected),
                    'modes':sorted({r.get('mode','') for r in selected}),
                    'last_positions':{k:selected[-1].get(k) for k in ('player','vehicle','restarts')} if selected else None})
            return {**base,'input_observations':observations}
        return base
    rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
    objects=read_json(bundle/'captures/scene-transforms.json')['objects']
    failed=[];facts={}
    checks=task['checks']
    if 'world_collision' in checks:
        colliders=[o for o in objects if o['kind']!='renderer' and o.get('enabled')]
        facts['collider_count']=len(colliders)
        facts['forward_stop_motion']=window_motion(rows,'player',14.5,15.8)
        facts['side_stop_motion']=window_motion(rows,'player',21.5,22.8)
        if len(colliders)<6:failed.append('visible-world-colliders-missing')
        if any(facts[k] is None or facts[k]>.2 for k in ('forward_stop_motion','side_stop_motion')):
            failed.append('held-input-does-not-stop-at-world-obstacle')
        if not all(r.get('playerCollisionEnabled') for r in rows if r['time']>1):failed.append('player-collider-disabled')
        if max(r.get('playerPenetration',0) for r in rows if r['time']>1)>.15:failed.append('player-horizontal-penetration')
        if any(not -1.05<=r['player'][0]<=6.05 or not -2.05<=r['player'][2]<=30.05 for r in rows if r.get('player')):
            failed.append('player-left-bounded-pavement')
    if 'motor_reset' in checks:
        drive=[r for r in rows if r.get('mode')=='vehicle']
        early=[r for r in rows if 7.5<=r['time']<=8]
        exited=[r for r in rows if 21.5<=r['time']<=23.5]
        facts['entered_before_throttle']=bool(len(early)>=3 and all(r.get('mode')=='vehicle' for r in early))
        facts['grounded_exit_before_reset']=bool(len(exited)>=3 and all(r.get('mode')=='foot' and r.get('grounded') for r in exited))
        if not facts['entered_before_throttle']:failed.append('first-E-did-not-enter-before-throttle')
        if not facts['grounded_exit_before_reset']:failed.append('E-exit-not-grounded-before-reset')
        facts['vehicle_stop_motion']=window_motion(drive,'vehicle',16,17.8)
        if not drive or not all(r.get('vehicleCollisionEnabled') for r in drive):failed.append('vehicle-collider-missing')
        if facts['vehicle_stop_motion'] is None or facts['vehicle_stop_motion']>.2:failed.append('held-throttle-does-not-stop-at-boundary')
        if max([r.get('vehiclePenetration',0) for r in drive] or [999])>.15:failed.append('vehicle-horizontal-penetration')
        reset=[r for r in rows if 25<=r['time']<=26 and r.get('mode')=='foot' and r.get('grounded')]
        reset_ok=bool(reset and max(r.get('restarts',0) for r in reset)>=1
            and all(math.dist(r['player'],[0,.135,1.7])<.4 for r in reset)
            and all(len(r.get('vehicle') or [])==3 and math.dist(r['vehicle'],[3.6,0,8])<.4 for r in reset))
        facts['reset_positions_and_state']=reset_ok
        if not reset_ok:failed.append('reset-did-not-restore-grounded-player-and-car')
        if (window_motion(rows,'player',27,29) or 0)<1:failed.append('controls-not-restored-after-reset')
    mission_states={r.get('mission') for r in rows}
    if 'mission_complete' in checks:
        facts['mission_states']=sorted(str(x) for x in mission_states)
        if not {'active','complete'}<=mission_states:failed.append('connected-objective-ending-missing')
        if not any(r.get('visibleText') for r in rows):failed.append('objective-presentation-missing')
        anchors=inspect_mission_anchors(rows)
        facts['mission_anchors']=anchors
        if not anchors['passed']:failed.extend(anchors['failure'])
        if task['id']=='connected-mission':
            hud=inspect_courier_hud(rows)
            facts['courier_hud_states']=hud
            if not hud['passed']:failed.extend(hud['failure'])
        if task.get('polish'):
            primitives={'Cube','Cylinder','Sphere','Capsule','Plane','Quad'}
            if any(o.get('meshName') in primitives for r in rows for o in r.get('missionObjects',[])):
                failed.append('temporary-mission-world-primitives-require-Blender-replacement')
    if 'failure_retry' in checks:
        failed_rows=[r for r in rows if r.get('mission')=='failed' or r.get('health',100)<=0]
        reset=None;ending=None
        if not failed_rows:failed.append('actual-failure-branch-missing')
        else:
            first=failed_rows[0]
            reset=next((r for r in rows if r['time']>first['time']
                and r.get('restarts',0)>first.get('restarts',0) and r.get('mission')=='active'
                and any(first['time']<k['time']<=r['time'] and r['time']-k['time']<=.5
                        and 'R' in k.get('keys',[]) for k in rows)),None)
            if reset is None:failed.append('failure-retry-not-recoverable')
            else:
                ending=next((r for r in rows if r['time']>reset['time'] and r.get('mission')=='complete'
                             and r.get('restarts',0)==reset.get('restarts',0)),None)
        if ending is None:failed.append('retry-does-not-reach-ending')
        facts['failure_retry']={'failure_time':failed_rows[0]['time'] if failed_rows else None,
                                'reset_time':reset['time'] if reset else None,
                                'retry_completion_time':ending['time'] if ending else None}
    if 'combat' in checks:
        if not any('Mouse0' in r.get('keys',[]) for r in rows):failed.append('fire-input-missing')
        if max(r.get('shots',0) for r in rows)<1 or max(r.get('hits',0) for r in rows)<1:failed.append('actual-shot-and-hit-missing')
        if not any(o['kind']=='renderer' and any(n in o['name'].lower() for n in ('rival','enemy')) for o in objects):
            failed.append('no-rendered-combat-target')
    if 'pursuit' in checks:
        wanted=[r for r in rows if r.get('pursuit',0)>0]
        if not wanted or not any(r['time']>wanted[0]['time'] and r.get('pursuit')==0 for r in rows):
            failed.append('pursuit-start-and-escape-missing')
    if 'hud_audio' in checks:
        text=' '.join(t for r in rows for t in (r.get('visibleText') or [])).lower()
        if not all(word in text for word in ('health','wanted','objective')):failed.append('coherent-hud-fields-missing')
        facts['audio_peak_rms']=max(r.get('audioRms',0) for r in rows)
        if facts['audio_peak_rms']<.0001:failed.append('rendered-mixer-audio-unverified')
    if 'whole_route' in checks:
        if base.get('duration',0)<540:failed.append('whole-route-too-short')
        complete=[r for r in rows if r.get('mission')=='complete']
        if not complete or not 540<=complete[0]['time']<=660:failed.append('ten-minute-ending-timing-unverified')
    return {**base,'passed':not failed,'failure':failed or None,'scoped_checks':checks,'scoped_facts':facts,
            'scope':task['id'],'final_game_accepted':False}
