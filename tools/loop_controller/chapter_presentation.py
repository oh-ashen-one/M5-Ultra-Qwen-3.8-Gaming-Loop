"""Actual projected panel and marker geometry checks; no game state writes."""
import math

def rect(value):
    return isinstance(value,list) and len(value)==4 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in value) and value[2]>value[0] and value[3]>value[1]

def overlaps(a,b):
    return min(a[2],b[2])-max(a[0],b[0])>.003 and min(a[3],b[3])-max(a[1],b[1])>.003

def inspect_presentation(rows):
    failures=set();active=0;reset=0;first=None;examples=[]
    for row in rows:
        if row.get('time',0)<1:continue
        chapter=row.get('routeChapter',{});stage=chapter.get('stage')
        panels={p.get('name'):p for p in chapter.get('hudPanels',[])}
        if stage==0:
            current={n:panels.get(n,{}).get('textRect') for n in ('MissionHud','HudStatus')}
            if first is None:first=current
            if row.get('restarts',0)>0:
                reset+=1
                for n in current:
                    if not rect(current[n]) or not rect(first[n]):failures.add('legacy-reset-layout-unobserved')
                    # Text length/health changes after reset, so compare the
                    # upper anchor corner instead of the full content width.
                    elif abs(current[n][3]-first[n][3])>.008:failures.add('legacy-reset-layout-not-restored')
            continue
        if stage not in (1,2):continue
        active+=1;cards=[]
        for name,max_width in [('RouteHud',.56),('MissionHud',.43),('HudStatus',.36)]:
            panel=panels.get(name,{});t=panel.get('textRect');c=panel.get('cardRect')
            if not panel.get('visible') or not rect(t) or not rect(c):
                failures.add(name+'-visible-panel-unverified');continue
            if min(c[:2])<.015 or max(c[2:])>.985:failures.add(name+'-panel-offscreen')
            if c[2]-c[0]>max_width or c[3]-c[1]>.19:failures.add(name+'-panel-oversized')
            if t[0]<c[0]-.01 or t[1]<c[1]-.01 or t[2]>c[2]+.01 or t[3]>c[3]+.01:
                failures.add(name+'-text-outside-backing')
            if name=='RouteHud' and not .035<=t[3]-t[1]<=.17:failures.add('objective-text-size-unreadable')
            cards.append((name,c))
        for i,(name,a) in enumerate(cards):
            for other,b in cards[i+1:]:
                if overlaps(a,b):failures.add('overlapping-'+name+'-'+other)
        capture_cards=[]
        if not math.isclose(chapter.get('captureAspect',0),16/9,abs_tol=.001):
            failures.add('native-capture-projection-unverified')
        for name in ('RouteHud','MissionHud','HudStatus'):
            panel=panels.get(name,{});t=panel.get('captureTextRect');c=panel.get('captureCardRect')
            if not rect(t) or not rect(c):failures.add(name+'-capture-projection-missing');continue
            if min(c[:2])<.015 or max(c[2:])>.985:failures.add(name+'-capture-offscreen')
            if t[0]<c[0]-.01 or t[1]<c[1]-.01 or t[2]>c[2]+.01 or t[3]>c[3]+.01:
                failures.add(name+'-capture-text-outside-backing')
            capture_cards.append((name,c))
        for i,(name,a) in enumerate(capture_cards):
            for other,b in capture_cards[i+1:]:
                if overlaps(a,b):failures.add('capture-overlapping-'+name+'-'+other)
        center=chapter.get('cacheBoundsCenter');size=chapter.get('cacheBoundsSize')
        if not isinstance(center,list) or not isinstance(size,list) or len(center)!=3 or len(size)!=3 or not all(math.isfinite(v) for v in center+size):
            failures.add('cache-rendered-bounds-missing')
        else:
            if math.dist([center[0],center[2]],[50,18])>.15:failures.add('cache-rendered-center-misses-anchor')
            if abs(center[1]-size[1]/2-.14)>.04:failures.add('cache-rendered-base-not-grounded')
            if not all(.1<v<4 for v in size):failures.add('cache-rendered-size-unreasonable')
        if not isinstance(chapter.get('emissiveRenderers'),int) or not 0<=chapter['emissiveRenderers']<=1:
            failures.add('cache-emission-not-limited-to-accent')
        if len(examples)<2 or stage==2 and not any(x['stage']==2 for x in examples):
            examples.append(dict(time=row['time'],stage=stage,panels=panels,
                cache_bounds_center=center,cache_bounds_size=size,emissive_renderers=chapter.get('emissiveRenderers'),
                live_aspect=chapter.get('liveAspect'),capture_aspect=chapter.get('captureAspect')))
    if active<5:failures.add('active-chapter-presentation-unverified')
    if reset<3:failures.add('presentation-reset-unverified')
    return dict(passed=not failures,failure=sorted(failures) or None,active_samples=active,
        reset_samples=reset,examples=examples,scope='Live-window and native-capture UI geometry, physical cache bounds; actual pixel review remains required.')
