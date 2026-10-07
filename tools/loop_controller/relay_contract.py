"""Immutable additive relay acceptance; normal input and observed game-owned state."""
import copy
import math
from .route_chapter import distance,point
from .continuous_checks import validate_proposed

ANCHORS=[[53,.2,27],[41,.2,9],[29,.2,27]]
DEADLINE=45

def scenarios(original):
    base=copy.deepcopy(original)
    steps=[s for s in base['steps'] if s['start']<33]
    # Cloud-authored acceptance inputs extend the proven local-game route.
    # Never move actors/props or count red-case waiting as mission duration.
    common=[(33.4,33.7,['F']),(34,35,['W']),(35.4,36.7,['D']),
        (37,38.25,['W']),(37,38.4,['F']),(38.55,38.85,['F'])]
    positive=common+[(39.2,40.2,['S']),(40.5,44.4,['A']),(44.7,48.7,['S']),
        (49,49.3,['F']),(49.8,51,['W']),(51.3,55.2,['A']),(55.5,59.3,['W']),
        (59.6,59.9,['F']),(80,80.3,['R']),(81,81.3,['F'])]
    wrong=common+[(39.2,40.2,['S']),(40.5,48.2,['A']),(48.5,49.5,['W']),
        (49.8,51.4,['F']),(78.2,78.5,['F']),(79,79.3,['R']),(80,80.3,['F'])]
    def make(extra,duration,captures):
        value=dict(duration=duration,steps=steps+[dict(start=a,end=b,keys=k) for a,b,k in extra],captures=captures)
        return validate_proposed(value,100,'mission-core')
    return {'positive':make(positive,83,[3.2,27.3234,32.55,38.3,38.7,49.15,59.75,78.6,80.6,82]),
        'wrong-timeout':make(wrong,82,[3.2,32.55,38.7,49.95,51.6,77.9,79.6,81]),
        'inactive':validate_proposed(dict(duration=18,steps=[dict(start=4,end=5,keys=['W']),
            dict(start=6,end=6.4,keys=['F']),dict(start=8,end=8.4,keys=['F'])],captures=[3.2,5.5,9,16]),100,'mission-core')}

def inspect_relay(rows,case):
    if case not in ('positive','wrong-timeout','inactive'):raise ValueError('Unknown relay proof case')
    failures=set();events=[];prior=None;prior_keys=set();edges=[];armed=None;reset_pending=None
    activations=[];completions=[];timeouts=[];wrong=[];resets=[];counts=[];active_samples=0;latched=False
    def fail(v):failures.add(v)
    def fresh(k,t):return any(key==k and 0<=t-at<=.35 for at,key in edges)
    for row in rows:
        t=row.get('time',0);keys=set(row.get('keys',[]));edges.extend((t,k) for k in keys-prior_keys);prior_keys=keys
        if t<.5:continue
        s=row.get('relay',{})
        if not s.get('present') or not s.get('valid') or s.get('componentCount')!=1:
            fail('relay-observer-or-component-missing');continue
        count=s.get('count');expected=s.get('expected');active=s.get('active');complete=s.get('complete');failed=s.get('failed')
        if count not in range(4) or expected!=count or complete!=(count==3) or (complete and failed):fail('relay-invalid-state')
        if case=='inactive' and (active or complete or failed or count or s.get('wrongOrders')):fail('relay-started-without-chapter')
        old=prior.get('relay',{}) if prior else {};old_count=old.get('count',0)
        restarted=prior and row.get('restarts',0)!=prior.get('restarts',0)
        if restarted:
            if not fresh('R',t):fail('relay-reset-without-R')
            reset_pending=t;armed=None
        if reset_pending is not None:
            if not any([active,complete,failed,count,s.get('wrongOrders')]) and not any(p.get('active') for p in s.get('sites',[])):
                resets.append(t);reset_pending=None
            elif t-reset_pending>.35:fail('relay-reset-not-cleared')
        if active and not old.get('active') and not restarted:
            chapter=row.get('routeChapter',{})
            if not chapter.get('complete') or chapter.get('stage')!=2:fail('relay-armed-before-east-cache')
            armed=t;activations.append(t)
        if active:
            active_samples+=1
            if not row.get('routeChapter',{}).get('complete'):fail('relay-mutated-prior-chapter')
            if row.get('mission')!='complete':fail('relay-mutated-legacy-mission')
            if not s.get('objective') or not s.get('hud',{}).get('visible'):fail('relay-objective-hidden')
            text=(s.get('hud',{}).get('text') or '').lower()
            if 'relay' not in text:fail('relay-text-missing')
            if complete and 'complete' not in text:fail('relay-ending-text-missing')
            if failed and 'failed' not in text:fail('relay-failure-text-missing')
            for k in ('textRect','cardRect','captureTextRect','captureCardRect'):
                rect=s.get('hud',{}).get(k)
                if not isinstance(rect,list) or len(rect)!=4 or not all(math.isfinite(x) for x in rect) or not (0<=rect[0]<rect[2]<=1 and 0<=rect[1]<rect[3]<=1):fail('relay-HUD-outside-'+k)
            sites=s.get('sites',[])
            if len(sites)!=3:fail('relay-three-physical-sites-missing')
            for i,p in enumerate(sites):
                if i>2:break
                if not p.get('exists') or not p.get('active') or p.get('actorChild') or not point(p.get('position')) or math.dist(p['position'],ANCHORS[i])>.03:fail('relay-anchor-invalid')
                if not p.get('originalMeshReuse') or p.get('rendererCount',0)<1:fail('relay-original-visible-mesh-missing')
                c,z=p.get('boundsCenter'),p.get('boundsSize')
                if not point(c) or not point(z) or any(v<=0 for v in z):fail('relay-render-bounds-missing');continue
                if abs(c[1]-z[1]/2-.2)>.02 or distance(c,ANCHORS[i])>.03 or not .65<=max(z)<=1.15:fail('relay-prop-not-grounded-or-sized')
                if p.get('colliderCount')!=1 or not point(p.get('colliderCenter')) or not point(p.get('colliderSize')):fail('relay-matching-solid-collider-missing')
                elif math.dist(c,p['colliderCenter'])>.04 or math.dist(z,p['colliderSize'])>.04:fail('relay-collider-does-not-match-visible-prop')
        elif any(p.get('active') for p in s.get('sites',[])):fail('relay-visible-before-activation-or-after-reset')
        if count!=old_count and not restarted and reset_pending is None:
            if count==old_count+1:
                if old_count not in range(3) or not active or old.get('failed') or old.get('complete') or row.get('mode')!='foot' or not fresh('F',t) or distance(row.get('player'),ANCHORS[old_count])>1.55:fail('relay-increment-without-ordered-fresh-near-foot-F')
                counts.append(count);events.append(dict(time=t,count=count,player=row.get('player')))
            elif not(count==0 and s.get('wrongOrders',0)==old.get('wrongOrders',0)+1):fail('relay-unexplained-progress-change')
        if s.get('wrongOrders',0)>old.get('wrongOrders',0) and not restarted:
            near=[i for i,a in enumerate(ANCHORS) if distance(row.get('player'),a)<=1.55]
            if s['wrongOrders']!=old.get('wrongOrders',0)+1 or not active or old.get('failed') or row.get('mode')!='foot' or not fresh('F',t) or len(near)!=1 or near[0]==old_count or count!=0:fail('relay-invalid-wrong-order-reset')
            wrong.append(t)
        if failed and not old.get('failed'):
            if armed is None or not 44.6<=t-armed<=45.4 or count==3 or not active:fail('relay-timeout-invalid')
            timeouts.append(t)
        if complete and not old.get('complete'):
            if count!=3 or old_count!=2 or armed is None or t-armed>45.4:fail('relay-invalid-completion')
            completions.append(t)
        if complete and not failed and armed is not None and t-armed>=45.5:latched=True
        if old.get('failed') and not restarted and (count!=old_count or s.get('wrongOrders')!=old.get('wrongOrders')):fail('relay-progress-after-timeout')
        prior=row
    if not rows:fail('relay-trace-missing')
    if reset_pending is not None:fail('relay-reset-truncated')
    if case!='inactive':
        if not activations or active_samples<5:fail('relay-activation-unverified')
        if not resets:fail('relay-reset-unverified')
    if case=='positive' and (counts!=[1,2,3] or len(completions)!=1 or wrong or timeouts):fail('relay-positive-sequence-unverified')
    if case=='positive' and not latched:fail('relay-completed-ending-after-deadline-unverified')
    if case=='wrong-timeout' and (counts!=[1] or len(wrong)!=1 or len(timeouts)!=1 or completions):fail('relay-wrong-order-or-timeout-unverified')
    return dict(passed=not failures,failure=sorted(failures) or None,case=case,activations=activations,
        ordered_interactions=events,wrong_orders=wrong,timeouts=timeouts,completions=completions,resets=resets,
        measured_relay_seconds=completions[0]-activations[0] if completions and activations else None,
        completion_latched_after_deadline=latched,
        final_game_accepted=False,red_waiting_is_not_mission_duration=True)
