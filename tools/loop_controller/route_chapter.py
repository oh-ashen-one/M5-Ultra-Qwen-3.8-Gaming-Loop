"""Additive chapter proof. Legacy courier and whole-game acceptance remain unchanged."""
import math

ANCHOR=[50,.14,18]

def point(value):
    return isinstance(value,list) and len(value)==3 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in value)

def distance(a,b):
    return math.dist([a[0],a[2]],[b[0],b[2]]) if point(a) and point(b) else float('inf')

def inspect_chapter(rows,require_complete=True,require_reset=True,expect_inactive=False):
    failures=set();activations=[];arrivals=[];exits=[];completions=[];resets=[]
    edges=[];prior_keys=set();previous=None;arrived=None;exited=None;activated=None
    last_restart=rows[0].get('restarts',0) if rows else 0
    pending_reset=None
    def fail(name):failures.add(name)
    def edge(key,t):return any(k==key and 0<=t-at<=.35 for at,k in edges)
    for row in rows:
        t=row.get('time',0);keys=set(row.get('keys',[]))
        edges.extend((t,k) for k in keys-prior_keys);prior_keys=keys
        if t<.5:continue
        obs=row.get('routeChapter',{})
        if not obs.get('present') or not obs.get('valid') or obs.get('componentCount')!=1:
            fail('chapter-component-observation-missing');continue
        stage=obs.get('stage');complete=obs.get('complete')
        if stage not in (0,1,2) or complete!=(stage==2):fail('chapter-state-invalid')
        if expect_inactive and (stage!=0 or complete):fail('chapter-activated-without-courier')
        restart=row.get('restarts',0)
        if restart!=last_restart:
            if not edge('R',t):fail('chapter-reset-without-R')
            pending_reset=t;last_restart=restart;arrived=exited=activated=None
        if pending_reset is not None:
            if stage==0 and not complete and not obs.get('cacheActive'):
                resets.append(t);pending_reset=None
            elif t-pending_reset>.35:fail('chapter-reset-not-cleared')
        if stage==0:
            if obs.get('cacheActive'):fail('chapter-cache-active-before-handoff')
        else:
            if not obs.get('cacheExists') or not point(obs.get('cachePosition')) or math.dist(obs['cachePosition'],ANCHOR)>.05:
                fail('chapter-fixed-anchor-missing-or-moved')
            if obs.get('actorChild'):fail('chapter-cache-follows-actor')
            if not obs.get('cacheActive') or obs.get('rendererCount',0)<1 or not obs.get('originalMeshReuse'):
                fail('chapter-original-visible-marker-missing')
            text=' '.join(row.get('visibleText') or []).lower()
            if 'dead-drop' not in text or not obs.get('objective'):fail('chapter-objective-presentation-missing')
        old_stage=previous.get('routeChapter',{}).get('stage') if previous else 0
        if stage==1 and old_stage==0:
            if row.get('mission')!='complete':fail('chapter-started-before-real-courier-ending')
            activated=t;activations.append(t)
        if stage==1 and activated is not None and row.get('mode')=='vehicle' and distance(row.get('vehicle'),ANCHOR)<=6.05:
            if arrived is None:arrived=t;arrivals.append(t)
        if previous and previous.get('mode')=='vehicle' and row.get('mode')=='foot' and arrived is not None:
            if not edge('E',t):fail('chapter-exit-without-normal-input')
            exited=t;exits.append(t)
        if stage==2 and old_stage!=2:
            if old_stage!=1 or activated is None:fail('chapter-premature-completion')
            if arrived is None or exited is None or not activated<=arrived<=exited<=t:
                fail('chapter-arrival-exit-sequence-missing')
            if row.get('mode')!='foot':fail('chapter-completed-in-wrong-mode')
            if distance(row.get('player'),ANCHOR)>1.55:fail('chapter-completed-away-from-cache')
            if not edge('F',t):fail('chapter-completed-without-fresh-F')
            completions.append(t)
        if stage==1 and complete:fail('chapter-early-ending')
        previous=row
    if not rows:fail('chapter-trace-missing')
    if pending_reset is not None:fail('chapter-reset-proof-truncated')
    if expect_inactive:
        if activations or completions:fail('chapter-inactive-red-case-failed')
    else:
        if not activations:fail('chapter-handoff-unverified')
        if require_complete and not completions:fail('chapter-real-completion-unverified')
        if not require_complete and completions:fail('chapter-unexpected-completion-in-activation-probe')
        if require_reset and not resets:fail('chapter-reset-unverified')
        if require_reset and require_complete and completions and not any(r>completions[0] for r in resets):
            fail('chapter-no-reset-after-completion')
    return dict(passed=not failures,failure=sorted(failures) or None,activations=activations,
        arrivals=arrivals,exits=exits,completions=completions,resets=resets,
        scope='inactive-red-case' if expect_inactive else ('chapter-completion' if require_complete else 'chapter-activation-reset'),
        final_game_accepted=False)
