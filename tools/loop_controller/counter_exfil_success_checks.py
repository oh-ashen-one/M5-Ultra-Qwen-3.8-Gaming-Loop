"""Independent actual-contact, shot and crossing proof; never trusts Complete alone."""
import math
from .counter_exfil_checks import chapter,horizontal
from .aim_checks import inspect_aim_contract

NAMES={'CounterExfilRunner1','CounterExfilRunner2','CounterExfilRunner3'}

def physical_pins(rows,events,row):
    when=row['time'];contacts={};since={}
    for event in events:
        if event['time']>when+1e-4:continue
        if not event.get('otherIsVehicle'):continue
        actor=event['entityId'];other=event['otherId'];active=contacts.setdefault(actor,set())
        if event['kind']=='exit':
            active.discard(other)
            if not active:since.pop(actor,None)
        elif event['kind'] in ('enter','stay') and event.get('contacts'):
            if not active:since[actor]=event['time']
            active.add(other)
    pins=[]
    for actor in row.get('counterExfil',{}).get('actors',[]):
        ident=actor['entityId']
        if (not actor.get('alive') or actor.get('hp',0)<=0 or not actor.get('hasBody')
                or actor.get('kinematic') or not actor.get('colliderEnabled')
                or not contacts.get(ident) or when-since.get(ident,when)<.8-1e-4):continue
        older=[r for r in rows if r['time']<=when-.8 and r.get('restarts')==row.get('restarts')]
        if not older:continue
        start=older[-1];before=next((a for a in start.get('counterExfil',{}).get('actors',[]) if a['entityId']==ident),None)
        if before is None:continue
        duration=when-start['time'];speed=(before['position'][0]-actor['position'][0])/duration
        window=[r for r in rows if start['time']<=r['time']<=when and r.get('restarts')==row.get('restarts')]
        samples=[(r['time'],next((a for a in r.get('counterExfil',{}).get('actors',[]) if a['entityId']==ident),None)) for r in window]
        if any(a is None for _,a in samples):continue
        rates=[(a['position'][0]-b['position'][0])/(t1-t0) for (t0,a),(t1,b) in zip(samples,samples[1:]) if t1>t0]
        # An average can conceal a moving interval followed by a stop. Every
        # observed interval must be obstructed throughout the qualification span.
        if (duration>.95 or speed>.3 or not rates or max(rates)>.3001
                or not any(c.get('vehicle') for c in actor.get('contacts',[]))):continue
        pins.append(dict(name=actor['name'],entity_id=ident,continuous_contact_seconds=when-since[ident],
            measured_west_speed=speed,maximum_interval_west_speed=max(rates),
            measured_motion_seconds=duration,position=actor['position']))
    return pins

def inspect_success(rows,contact_events,shot_events):
    failures=[];facts={}
    active=[r for r in rows if r.get('restarts')==0 and chapter(r).get('Active')]
    completed=[r for r in active if chapter(r).get('Complete')]
    if not active:return dict(passed=False,failure=['real-activation-not-observed'],full_incident_success=False)
    onset=active[0]['time'];facts['activation_seconds']=onset
    spawned=[r for r in active if len(r.get('counterExfil',{}).get('actors',[]))==3]
    if not spawned or sorted(a['hp'] for a in spawned[0]['counterExfil']['actors'])!=[3,3,6]:
        failures.append('actual-three-starting-hp-not-established')
    identities={a['entityId'] for r in active for a in r.get('counterExfil',{}).get('actors',[])}
    names={a['name'] for r in active for a in r.get('counterExfil',{}).get('actors',[])}
    if len(identities)!=3 or names!=NAMES:failures.append('exact-stable-three-identities-not-established')
    shots=[e for e in shot_events if e.get('time',0)>=onset and e.get('restarts')==0]
    aim=inspect_aim_contract(shots,'aligned');facts['aim']=aim
    if not aim['passed']:failures.extend(aim['failure'] or [])
    lethal={};damage=[]
    for event in shots:
        hit=[t for t in event.get('targets',[]) if t.get('hpAfter',0)<t.get('hpBefore',0)]
        if len(hit)>1:failures.append('one-shot-damages-multiple-actors')
        for target in hit:
            if target['name'] not in NAMES:failures.append('new-incident-shooting-target-not-one-of-three');continue
            if target['hpAfter']!=target['hpBefore']-1:failures.append('non-unit-real-shot-damage')
            damage.append(dict(time=event['time'],name=target['name'],before=target['hpBefore'],after=target['hpAfter']))
            if target['hpBefore']>0 and target['hpAfter']<=0:
                if target['name'] in lethal:failures.append('same-actor-killed-twice')
                lethal[target['name']]=event['time']
    facts['actual_damage']=damage;facts['distinct_lethal_events']=lethal
    for row in active:
        state=chapter(row);actors=row.get('counterExfil',{}).get('actors',[])
        killed={a['name'] for a in actors if not a.get('alive') and a.get('hp',1)<=0}
        if state.get('KilledCount')!=len(killed):failures.append('kill-score-disagrees-with-distinct-actual-deaths')
        if any(lethal.get(name,float('inf'))>row['time']+1e-4 for name in killed):failures.append('death-without-actual-lethal-shot')
        if row.get('health',0)<=0 or state.get('Failed') or state.get('EscapedCount'):
            failures.append('death-or-escape-during-success-attempt')
    if not completed:failures.append('completion-not-reached')
    else:
        first=completed[0];pins=physical_pins(rows,contact_events,first)
        dead={a['name'] for a in first['counterExfil']['actors'] if not a['alive'] and a['hp']<=0}
        pinned={p['name'] for p in pins};facts['completion_seconds']=first['time'];facts['actual_live_pins_at_completion']=pins
        if dead|pinned!=NAMES or dead&pinned:failures.append('completion-without-three-distinct-real-resolutions')
        if len(dead)<1 or len(pinned)<1:failures.append('combined-real-shooting-and-live-pin-not-established')
        prior=[r for r in rows if r['time']<first['time'] and r.get('restarts')==0]
        previous=prior[-1] if prior else None
        if (previous is None or first['time']-previous['time']>.2 or previous.get('mode')!='foot' or first.get('mode')!='foot'
                or previous['player'][0]<=3.2 or first['player'][0]>3.2
                or abs(first['player'][2]-16.0057)>1.5 or horizontal(previous['player'],first['player'])>.5):
            failures.append('completion-without-actual-contiguous-western-foot-crossing')
        facts['crossing']={k:first[k] for k in ('time','mode','health','player','vehicle')}
    return dict(passed=not failures,failure=sorted(set(failures)),facts=facts,
        scope='Physical single-incident success only; current-source negatives, regressions and pixels remain separate',
        full_incident_success=not failures,final_game_accepted=False)
