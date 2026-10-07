"""A real early foot crossing cannot bank completion or duplicate the wave."""
from .counter_exfil_checks import chapter,horizontal
from .counter_exfil_success_checks import physical_pins,NAMES

def inspect_early_exit(rows,events):
    active=[r for r in rows if r.get('restarts')==0 and chapter(r).get('Active')]
    failures=[];crossing=None
    for before,row in zip(active,active[1:]):
        if (before.get('mode')==row.get('mode')=='foot' and before['player'][0]>3.2>=row['player'][0]
                and abs(row['player'][2]-16.0057)<=1.5 and row['health']>0
                and row['time']-before['time']<.2 and horizontal(before['player'],row['player'])<.5):
            actors=row['counterExfil']['actors'];pins={p['name'] for p in physical_pins(rows,events,row)}
            unresolved=[a['name'] for a in actors if a['alive'] and a['hp']>0 and a['name'] not in pins]
            if unresolved:crossing=dict(time=row['time'],player=row['player'],health=row['health'],unresolved=unresolved)
            break
    if crossing is None:failures.append('actual-unresolved-living-foot-crossing-not-established')
    if not active or any(chapter(r).get('Complete') or chapter(r).get('KilledCount')!=0 for r in active):
        failures.append('early-crossing-or-duplicate-F-awards-unearned-completion-or-score')
    spawned=[r for r in active if chapter(r).get('SpawnedCount')]
    identities={a['entityId'] for r in spawned for a in r['counterExfil']['actors']}
    if (len(identities)!=3 or any({a['name'] for a in r['counterExfil']['actors']}!=NAMES
            or sorted(a['hp'] for a in r['counterExfil']['actors'])!=[3,3,6] for r in spawned)):
        failures.append('duplicate-wave-or-unearned-target-damage')
    for start,end in [(99.3,99.6),(106,106.3)]:
        if not any(start<=r['time']<end and 'F' in r.get('keys',[]) for r in active):
            failures.append('ordinary-duplicate-F-input-not-observed')
    if crossing and not any(r['time']>crossing['time']+5 and r['player'][0]<3.2 for r in active):
        failures.append('west-side-observation-window-missing')
    reset=[r for r in rows if 120.4<=r['time']<=121.2 and r.get('restarts')==1]
    if len(reset)<4 or any(not chapter(r).get('Dormant') or r['counterExfil'].get('actors')
            or any(chapter(r).get(k) for k in ('Armed','Active','Complete','Failed','KilledCount','EscapedCount','ActiveTime')) for r in reset):
        failures.append('ordinary-R-did-not-clear-early-exit-attempt')
    return dict(passed=not failures,failure=sorted(set(failures)),early_crossing=crossing,
        scope='Ordinary unresolved foot exit, repeated F, no banked completion and R cleanup',final_game_accepted=False)
