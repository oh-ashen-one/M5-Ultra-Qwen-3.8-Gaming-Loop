"""Compare native original/clone geometry; source comments cannot prove import parity."""
import math

CLONES=(('Props/alley_props/bollard01','WorldCollision/AlleyBollardS',(8,8.8)),
        ('Props/alley_props/bollard01','WorldCollision/AlleyBollardN',(8,19.65)),
        ('Props/alley_props/dumpster_a','WorldCollision/AlleyDumpster',(16,9.5)))


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
