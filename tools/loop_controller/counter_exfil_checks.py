"""Independent native observations for the first chapter's entry/escape/reset."""
import math
import re

def values(entries):
    result={}
    for item in entries or []:
        name,kind,value=item['name'],item['type'],item['value']
        if kind=='Boolean':value={'True':True,'False':False}[value]
        elif kind=='Int32':value=int(value)
        elif kind in ('Single','Double'):
            value=float(value)
            if not math.isfinite(value):raise ValueError('Non-finite native chapter observation')
        result[name]=value
    return result

def chapter(row):
    data=row.get('counterExfil') or {}
    if not data.get('available'):return {}
    raw=values(data.get('chapter'))
    if not {'armed','active','complete','failed'}<=set(raw):return {}
    return dict(Dormant=not raw['armed'],Armed=raw['armed'] and not raw['active'],Active=raw['active'],
        Complete=raw['complete'],Failed=raw['failed'],SpawnedCount=len(data.get('actors') or []),
        KilledCount=raw.get('killedCount'),EscapedCount=raw.get('escapedCount'),ActiveTime=raw.get('activeTime'),
        FailReason=raw.get('failReason'),
        # This initial probe never pins. Any accumulated qualification is a real
        # raw-field anomaly, not a getter invocation by the observer.
        PinnedNow=sum(values(a.get('state')).get('hold',0)>=.8 for a in data.get('actors',[]) if a.get('alive')))

def horizontal(a,b):return math.hypot(a[0]-b[0],a[2]-b[2])

def old_ending_with_armed_hint(row,text):
    """Only the authorized fifth line may augment a genuinely completed ending."""
    state=chapter(row);old=row.get('interception',{})
    if (not state.get('Armed') or any(state.get(k) for k in ('Active','Complete','Failed','SpawnedCount'))
            or not old.get('valid') or not old.get('complete') or old.get('failed')
            or old.get('stopped')!=3 or old.get('escaped')!=0 or row.get('health',0)<=0):return False
    original=(old.get('objective') or '').lower();text=text.lower()
    if not original or not text.startswith(original+'\n'):return False
    hint=text[len(original)+1:]
    if ('\n' in hint or len(hint)>40 or not hint.startswith('exfil')
            or not all(re.search(r'\b'+word+r'\b',hint) for word in ('coupe','e','f'))):return False
    distance=re.search(r'\b(\d+)\s*m\b',hint)
    actor=row.get('vehicle') if row.get('mode')=='vehicle' else row.get('player')
    car=row.get('vehicle')
    return bool(distance and actor and car and abs(int(distance[1])-horizontal(actor,car))<=1)

def inspect_activation_escape(rows,exit_x=3.2):
    failure=[];facts={}
    if not rows or any(not chapter(r) for r in rows if r['time']>.5):
        return dict(passed=False,failure=['chapter-observation-missing'],full_incident_success=False)
    before=[r for r in rows if 77.1<=r['time']<84.5 and r['restarts']==0]
    handoff=min(rows,key=lambda r:abs(r['time']-77))
    facts['handoff']={k:handoff[k] for k in ('time','health','player','vehicle','mode')}
    if (handoff['health']!=28 or handoff['mode']!='foot'
            or horizontal(handoff['player'],[28.187391,0,13.939845])>.05
            or horizontal(handoff['vehicle'],[47.605087,0,17.460318])>.05):
        failure.append('measured-old-handoff-changed')
    if not before or any(not chapter(r).get('Armed') or chapter(r).get('Active')
            or chapter(r).get('SpawnedCount')!=0 or r['counterExfil'].get('actors')
            or r['health']>28 or horizontal(r['vehicle'],handoff['vehicle'])>.05 for r in before):
        failure.append('retrieval-or-foot-F-starts-new-pressure-or-moves-car')
    active=[r for r in rows if r['restarts']==0 and chapter(r).get('Active')]
    if not active:
        failure.append('ordinary-seated-F-activation-not-reached')
    else:
        first=active[0];velocity=first.get('vehiclePhysics',{}).get('velocity') or [999,999,999]
        facts['activation']=dict(time=first['time'],mode=first['mode'],health=first['health'],velocity=velocity)
        if not 85.2-1e-4<=first['time']<=85.4+1e-4 or first['mode']!='vehicle' or math.sqrt(sum(x*x for x in velocity))>.25:
            failure.append('activation-without-declared-stationary-seated-F')
    spawned=[r for r in active if len(r['counterExfil'].get('actors') or [])==3]
    if not spawned:
        failure.append('exact-three-physical-runners-not-observed')
    else:
        first=spawned[0];actors=first['counterExfil']['actors'];native={r['name']:r for r in first.get('rivals',[])}
        hp=sorted(native.get(a['name'],{}).get('hp',-1) for a in actors)
        facts['first_spawn']=dict(time=first['time'],hp=hp,actors=[a['name'] for a in actors])
        if hp!=[3,3,6] or any(not a.get('hasBody') or a.get('kinematic') or not a.get('colliderEnabled') for a in actors):
            failure.append('runner-hp-or-solid-dynamic-body-contract')
        identities={a['entityId'] for r in active for a in r['counterExfil'].get('actors',[])}
        if len(identities)!=3:failure.append('runner-replenishment-or-identity-change')
    failed=[r for r in active if chapter(r).get('Failed')]
    if not failed:
        failure.append('unresolved-western-escape-not-observed')
    else:
        first=failed[0];state=chapter(first)
        candidates=[a for a in first['counterExfil'].get('actors',[]) if a['position'][0]<=exit_x
            and a.get('alive') and values(a.get('state')).get('hold',0)<.8]
        facts['escape_failure']=dict(time=first['time'],reason=state.get('FailReason'),actual_crossers=[a['name'] for a in candidates])
        if (not candidates or state.get('EscapedCount',0)<1 or not state.get('FailReason')
                or first['health']<=0 or any(chapter(r).get('Complete') for r in active)):
            failure.append('failure-without-genuine-unresolved-crossing')
    old=[r for r in rows if 77.1<=r['time']<136 and r['restarts']==0]
    if not old or any(not r.get('interception',{}).get('complete') or r['interception'].get('stopped')!=3
            or r['interception'].get('escaped')!=0 for r in old):
        failure.append('prior-interception-history-changed')
    reset=[r for r in rows if 136.4<=r['time']<=137.2 and r['restarts']==1]
    if not reset or any(r['health']!=100 or r['mode']!='foot' or r['counterExfil'].get('actors')
            or not chapter(r).get('Dormant') or any(chapter(r).get(k) for k in
                ('Armed','Active','Complete','Failed','SpawnedCount','KilledCount','EscapedCount','PinnedNow','ActiveTime')) for r in reset):
        failure.append('ordinary-R-did-not-clear-chapter')
    return dict(passed=not failure,failure=sorted(set(failure)),facts=facts,
        scope='Ordinary retrieval/explicit activation/physical unresolved escape/reset only',
        full_incident_success=False,shoot_pin_foot_exit='not tested',death_negatives='not tested',final_game_accepted=False)
