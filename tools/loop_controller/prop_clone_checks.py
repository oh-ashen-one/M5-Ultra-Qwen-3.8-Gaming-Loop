"""Compare native original/clone geometry; source comments cannot prove import parity."""
import math

CLONES=(('Props/alley_props/bollard01','WorldCollision/AlleyBollardS',(8,8.8)),
        ('Props/alley_props/bollard01','WorldCollision/AlleyBollardN',(8,19.65)),
        ('Props/alley_props/dumpster_a','WorldCollision/AlleyDumpster',(16,9.5)))


def inspect_door_layers(objects):
    """The cloned solid stone backing must not hide the original wood panel."""
    def one(name):
        found=[o for o in objects if o.get('name')==name and o.get('kind')=='renderer' and o.get('enabled',True)]
        return found[0] if len(found)==1 else None
    panel=one('WorldCollision/ServiceDoor');stone=one('WorldCollision/ServiceDoorSurround')
    if not panel or not stone:
        return dict(passed=False,failure=['missing-unique-door-renderers'])
    try:
        p=panel['boundsCenter'];s=stone['boundsCenter'];ps=panel['boundsSize'];ss=stone['boundsSize']
        finite=all(math.isfinite(v) for v in p+s+ps+ss) and min(ps+ss)>0
        front=(s[2]-ss[2]/2)-(p[2]-ps[2]/2)
        center=s[2]-p[2]
        passed=finite and .005<=front<=.02 and .065<=center<=.075 and abs(p[0]-s[0])<.005
    except (KeyError,IndexError,TypeError,ValueError):
        return dict(passed=False,failure=['invalid-door-native-bounds'])
    return dict(passed=passed,failure=[] if passed else ['wood-door-hidden-or-displaced'],
                wood_front_ahead_of_stone_m=front,wood_center_outward_offset_m=center,
                panel_bounds_center=p,stone_bounds_center=s,
                scope='Native geometry only; actual rendered door readability needs fresh visual review')


def inspect_alley_clones(objects):
    failures=[];facts=[]
    for original,clone,target in CLONES:
        def members(prefix):
            return {(o['name'][len(prefix):],o['kind']):o for o in objects
                    if o['name']==prefix or o['name'].startswith(prefix+'/')}
        source=members(original);copies=members(clone)
        if not source or source.keys()!=copies.keys():
            failures.append(clone+':missing-original-components')
        for key,src in source.items():
            dst=copies.get(key)
            if dst is None:continue
            a=src.get('boundsSize',[]);b=dst.get('boundsSize',[])
            sized=(len(a)==len(b)==3 and all(math.isfinite(v) and v>0 for v in a+b)
                   and all(abs(x-y)<=max(.005,.02*x) for x,y in zip(a,b)))
            oriented=True
            for axis in ('up','forward'):
                u=src.get(axis,[]);v=dst.get(axis,[])
                oriented &= len(u)==len(v)==3 and sum(x*y for x,y in zip(u,v))>.999
            if not sized:failures.append(clone+key[0]+':world-size')
            if not oriented:failures.append(clone+key[0]+':world-orientation')
            facts.append(dict(name=dst['name'],kind=dst['kind'],source_size=a,clone_size=b,
                              size_matches=sized,orientation_matches=oriented))
        renderers=[o for o in copies.values() if o['kind']=='renderer']
        if renderers:
            lo=[min(o['boundsCenter'][i]-o['boundsSize'][i]/2 for o in renderers) for i in range(3)]
            hi=[max(o['boundsCenter'][i]+o['boundsSize'][i]/2 for o in renderers) for i in range(3)]
            center=[(x+y)/2 for x,y in zip(lo,hi)]
            if abs(lo[1]-.14)>.02:failures.append(clone+':floor-placement')
            if math.hypot(center[0]-target[0],center[2]-target[1])>.05:
                failures.append(clone+':target-placement')
    return dict(passed=not failures,failure=failures,components=facts,
                scope='Native clone dimensions, world axes, component continuity and grounded placement only; visual quality needs rendered review')
