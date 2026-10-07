"""Immutable ground geometry and ordinary-input curb traversal acceptance."""
from collections import Counter
import copy
import math

PREFIX='WorldCollision/EastStreetGround/'
SURFACES={
    'SidewalkSouth':([41,.17,9],[38,.06,2]),
    'SidewalkNorth':([41,.17,27],[38,.06,2]),
    'CurbSouth':([41,.17,10],[38,.06,.12]),
    'CurbNorth':([41,.17,26],[38,.06,.12]),
}

def probe(original):
    result=copy.deepcopy(original)
    # Preserve the entire real mission through completion. These additional
    # walkovers are acceptance work, not new ten-minute gameplay content.
    result['steps']=[s for s in result['steps'] if s['start']<34]
    result['steps'] += [dict(start=a,end=b,keys=keys) for a,b,keys in [
        (34,35,['W']),(35.4,36.7,['D']),(37,38.6,['W']),
        (39.6,45.25,['S']),(46,49.4,['W']),(50,50.3,['R']),(51,51.3,['F'])]]
    result['captures']=sorted(set([t for t in result['captures'] if t<34]+[35.2,38.8,41.5,45.5,47,50.6,52]))
    result.update(duration=53,id='east-street-ground-curb-walkovers')
    return result

def signature(obj):
    fields=('name','kind','enabled','position','lossyScale','up','forward','boundsCenter','boundsSize')
    return tuple((k,tuple(round(v,4) for v in obj[k]) if isinstance(obj.get(k),list) else obj.get(k)) for k in fields)

def inspect_geometry(before,after):
    failures=[]
    def static(o):return o['name'].split('/')[0] in ('WorldCollision','Street','Pavement','Props')
    old=Counter(signature(o) for o in before if static(o))
    retained=Counter(signature(o) for o in after if static(o) and not o['name'].startswith(PREFIX))
    if old!=retained:failures.append('existing-ground-wall-facade-geometry-changed')
    added=[o for o in after if o['name'].startswith(PREFIX)]
    for name,(center,size) in SURFACES.items():
        for kind in ('renderer','BoxCollider'):
            found=[o for o in added if o['name']==PREFIX+name and o['kind']==kind]
            if len(found)!=1 or not found[0].get('enabled'):
                failures.append(name+'-'+kind+'-missing');continue
            o=found[0]
            for field,want in [('boundsCenter',center),('boundsSize',size)]:
                v=o.get(field,[])
                if len(v)!=3 or not all(math.isfinite(x) for x in v) or max(abs(v[i]-want[i]) for i in range(3))>.012:
                    failures.append(name+'-'+kind+'-'+field+'-mismatch')
    dashes=[o for o in added if o['name'].rsplit('/',1)[-1].startswith('LaneDash')]
    if len(dashes)!=9:failures.append('nine-original-mesh-lane-dashes-required')
    for o in dashes:
        c=o.get('boundsCenter',[]);s=o.get('boundsSize',[])
        if o['kind']!='renderer' or not o.get('enabled') or len(c)!=3 or len(s)!=3:
            failures.append('decorative-only-dash-unverified');continue
        if not all(math.isfinite(v) for v in c+s) or not(24<=c[0]<=59 and abs(c[1]-.142)<.004 and abs(c[2]-18)<.02):
            failures.append('dash-not-flush-on-road')
        if max(abs(s[i]-[2.4,.002,.10][i]) for i in range(3))>.012:failures.append('dash-scale-mismatch')
    if len(added)!=17:failures.append('unexpected-ground-components')
    return dict(passed=not failures,failure=sorted(set(failures)) or None,added_components=len(added),
        old_static_geometry_unchanged=old==retained,sidewalk_top_y=.20,road_top_y=.14,curb_step_m=.06,
        scope='Matching raised sidewalk/curb renderers and colliders; original road geometry retained.')

def inspect_walkovers(rows):
    groups={'road':[],'north':[],'south':[]};bad=[]
    for r in rows:
        t=r.get('time',0);p=r.get('player') or []
        if not 34<=t<49.9 or len(p)!=3:continue
        if r.get('mode')!='foot' or not r.get('playerCollisionEnabled') or r.get('playerPenetration',999)>.15:
            bad.append(t)
        if not 52.5<=p[0]<=54.5 or not r.get('grounded'):continue
        region='north' if 26.5<=p[2]<=27.35 else 'south' if 8.65<=p[2]<=9.5 else 'road' if 11<=p[2]<=25 else None
        if region:
            top=.14 if region=='road' else .20
            if abs(p[1]-top)>.012:bad.append(t)
            groups[region].append(dict(time=t,position=p))
    failures=[]
    if bad:failures.append('curb-crossing-collision-or-grounding-failed')
    if any(len(v)<5 for v in groups.values()):failures.append('both-raised-sidewalks-and-road-unverified')
    if groups['north'] and groups['south'] and groups['north'][0]['time']>=groups['south'][0]['time']:
        failures.append('normal-input-north-then-south-crossing-unverified')
    return dict(passed=not failures,failure=failures or None,samples={k:len(v) for k,v in groups.items()},
        first_observations={k:v[0] if v else None for k,v in groups.items()},bad_times=bad[:6],
        scope='Real on-foot crossings of both6cm curbs after the unchanged chapter; not mission pacing duration.')
