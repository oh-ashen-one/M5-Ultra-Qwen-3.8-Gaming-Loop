"""Read native geometry independently of the local decorative source author."""
from collections import Counter
import math

PREFIX='WorldCollision/EastStreetDetail/'

def inspect_details(before,after):
    failures=[]
    def static(obj):
        return obj['name'].split('/')[0] in ('WorldCollision','Street','Pavement','Props')
    def signature(obj):
        fields=('name','kind','enabled','position','lossyScale','up','forward','boundsCenter','boundsSize')
        return tuple((k,tuple(round(v,4) for v in obj[k]) if isinstance(obj.get(k),list) else obj.get(k)) for k in fields)
    old=Counter(signature(o) for o in before if static(o))
    retained=Counter(signature(o) for o in after if static(o) and not o['name'].startswith(PREFIX))
    if old!=retained:failures.append('existing-static-geometry-changed')
    added=[o for o in after if o['name'].startswith(PREFIX)]
    if not 100<=len(added)<=1200:failures.append('bounded-facade-detail-count')
    regions=set();families=set()
    for o in added:
        if o.get('kind')!='renderer' or not o.get('enabled'):failures.append('decorative-renderer-only');continue
        c=o.get('boundsCenter',[]);s=o.get('boundsSize',[])
        if len(c)!=3 or len(s)!=3 or not all(math.isfinite(v) for v in c+s) or min(s)<=0:
            failures.append('invalid-detail-bounds');continue
        lo=[c[i]-s[i]/2 for i in range(3)];hi=[c[i]+s[i]/2 for i in range(3)]
        region=o['name'][len(PREFIX):].split('/')[0].split('-')[0]
        if region not in ('South','North','East'):failures.append('unexpected-detail-region');continue
        regions.add(region)
        if lo[0]<21.9 or hi[0]>60.6 or lo[1]<-.1 or hi[1]>9.3 or lo[2]<7.4 or hi[2]>28.6:
            failures.append('detail-outside-building-envelope')
        if ((region=='South' and hi[2]>8.65) or (region=='North' and lo[2]<27.35)
                or (region=='East' and lo[0]<59.35)):
            failures.append('detail-in-drivable-interior')
        name=o['name'].rsplit('/',1)[-1]
        for family in ('win','door','cornice','pier'):
            if name.startswith(family):families.add(family)
    if regions!={'South','North','East'}:failures.append('three-facade-sides-unverified')
    if families!={'win','door','cornice','pier'}:failures.append('architectural-families-missing')
    return dict(passed=not failures,failure=sorted(set(failures)) or None,renderers=len(added),
                regions=sorted(regions),families=sorted(families),existing_static_geometry_unchanged=old==retained,
                scope='Decorative facade relief and original static geometry; visual readability still requires actual frame review.')
