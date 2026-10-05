"""Limited, evidence-backed subfeatures remain separate from final game acceptance."""
import json
import time
from .core import Halt, now, read_json


def pavement_coverage(bundle, radius=.32):
    objects=read_json(bundle/'captures/scene-transforms.json')['objects']
    surfaces=[]
    for obj in objects:
        if obj['kind']!='renderer' or not obj.get('enabled',False):continue
        if not any(word in obj['name'].lower() for word in ('sidewalk','pavement','road')):continue
        center,size=obj['boundsCenter'],obj['boundsSize']
        if not 0<size[1]<=.35 or min(size[0],size[2])<1:continue
        surfaces.append({'name':obj['name'],'min':[center[i]-size[i]/2 for i in range(3)],
                         'max':[center[i]+size[i]/2 for i in range(3)]})
    rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
    rows=[r for r in rows if r['time']>=.5 and r.get('player') and r.get('mode')=='foot']
    missed=[]
    for row in rows:
        x,y,z=row['player']
        covered=all(any(s['min'][0]<=x+dx<=s['max'][0] and s['min'][2]<=z+dz<=s['max'][2]
                        and abs(s['max'][1]-y)<.12 for s in surfaces)
                    for dx in (-radius,0,radius) for dz in (-radius,0,radius))
        if not covered:missed.append({'time':row['time'],'player':row['player']})
    return {'passed':len(rows)>=20 and bool(surfaces) and not missed,'samples':len(rows),
            'uncovered_samples':len(missed),'first_uncovered':missed[:3],
            'radius_m':radius,'surfaces':surfaces,
            'scope':'Flat rendered-surface bounds support the route; actual frame review is also required.'}


def accept_subfeature(store, feature, candidate, evidence, gate, review, coverage=None):
    if not gate.get('passed') or not review.get('ok') or review.get('verdict')!='PASS':
        raise Halt('Subfeature needs native success and independent scoped PASS')
    if feature=='foundation-short-walk':
        if (not gate.get('stationary_grounded') or gate.get('frame_count',0)<4
                or gate.get('player_displacement',0)<17 or not coverage or not coverage.get('passed')):
            raise Halt('Foundation milestone requires grounding, full route and rendered surface coverage')
        if not all(review.get(k) is True for k in ('camera_readable','car_visible','continuous_paving')):
            raise Halt('Foundation milestone requires observed camera, car and continuous paving')
    elif feature=='vehicle-entry-drive-exit':
        if gate.get('vehicle_displacement',0)<3 or gate.get('coverage')!='driving':
            raise Halt('Vehicle milestone requires the driving native gate')
    else:raise Halt('Unknown bounded subfeature')
    features=store.get('accepted_subfeatures',{})
    if feature in features:raise Halt('A repeated feature cannot reset the progress clock')
    record={'candidate':candidate,'evidence':evidence,'accepted_utc':now(),
            'scope':feature,'final_game_accepted':False,'review':review,
            'remaining':'Chicago target quality, final HUD/audio/performance, combat and complete ten-minute mission remain separate.'}
    features[feature]=record
    store.set(accepted_subfeatures=features,last_verified_progress_epoch=time.time(),
              last_verified_progress_utc=now())
    store.event('subfeature-accepted',**record)
    return record
