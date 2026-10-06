"""Observe one truthful objective panel plus health; never write game state.

This explicitly supersedes the old three-card presentation layout. Native
mission, chapter, relay, reset, physical-prop and regression contracts stay.
"""
import math
import re
from .chapter_presentation import rect,overlaps

def phase(row):
    intercept=row.get('interception',{})
    if intercept.get('active'):
        return 'interception-failed' if intercept.get('failed') else ('interception-complete' if intercept.get('complete') else 'interception')
    relay=row.get('relay',{});chapter=row.get('routeChapter',{})
    if relay.get('active'):
        return 'relay-failed' if relay.get('failed') else ('relay-complete' if relay.get('complete') else 'relay')
    if chapter.get('stage',0)>=1:return 'dead-drop'
    if row.get('mission')=='failed':return 'courier-failed'
    if row.get('mission')=='complete':return 'delivery-complete'
    carried=any(o.get('name')=='Parcel' and (o.get('playerChild') or o.get('vehicleChild')) for o in row.get('missionObjects',[]))
    return 'carrying' if carried else 'grab'

def inspect_hud(rows,required=()):
    failures=set();seen=set();examples=[];first_anchor=None;resets=0
    for row in rows:
        if row.get('time',0)<1:continue
        ch=row.get('routeChapter',{});panels={p.get('name'):p for p in ch.get('hudPanels',[])}
        p=panels.get('MissionBoard',{});h=panels.get('HudStatus',{});state=phase(row);seen.add(state)
        text=(p.get('text') or '').lower();lines=text.splitlines()
        if not p.get('visible') or not h.get('visible'):failures.add('primary-or-health-panel-hidden')
        if not 1<=len(lines)<=4 or any(len(line)>40 for line in lines):failures.add('objective-not-compact')
        if any(panels.get(n,{}).get('visible') or panels.get(n,{}).get('visibleRenderers',-1)!=0
               for n in ('MissionHud','RouteHud','RelayHud')):failures.add('competing-legacy-card-visible')
        if 'health' not in (h.get('text') or '').lower() or 'wanted' not in (h.get('text') or '').lower():
            failures.add('health-wanted-status-missing')
        if not math.isclose(ch.get('liveAspect',0),4/3,abs_tol=.002) or not math.isclose(ch.get('captureAspect',0),16/9,abs_tol=.002):
            failures.add('both-native-aspects-unobserved')
        for prefix in ('','capture'):
            tk='textRect' if not prefix else 'captureTextRect';ck='cardRect' if not prefix else 'captureCardRect'
            boxes=[]
            for name,pan in [('MissionBoard',p),('HudStatus',h)]:
                t=pan.get(tk);c=pan.get(ck)
                if not rect(t) or not rect(c):failures.add(name+'-projection-missing');continue
                if min(c[:2])<.015 or max(c[2:])>.985:failures.add(name+'-offscreen')
                if c[2]-c[0]>(.62 if name=='MissionBoard' else .36) or c[3]-c[1]>.24:
                    failures.add(name+'-oversized')
                if t[0]<c[0]-.005 or t[1]<c[1]-.005 or t[2]>c[2]+.005 or t[3]>c[3]+.005:
                    failures.add(name+'-text-outside-card')
                if name=='MissionBoard' and (t[3]-t[1])*540/max(1,len(lines))<12:
                    failures.add('objective-text-too-small')
                boxes.append(c)
            if len(boxes)==2 and overlaps(*boxes):failures.add('objective-health-overlap')
        t=p.get('textRect')
        if rect(t):
            if first_anchor is None:first_anchor=t[3]
            if abs(t[3]-first_anchor)>.008:failures.add('primary-panel-anchor-moves')
        if row.get('restarts',0)>0 and state=='grab':resets+=1
        expected={'grab':['grab'],'carrying':['parcel in hand'],'courier-failed':['failed','r'],
            'delivery-complete':['delivery complete'],'dead-drop':['dead-drop','delivery complete'],
            'relay':['relay','delivery complete','dead-drop complete'],
            'relay-complete':['relay complete','delivery complete','dead-drop complete'],
            'relay-failed':['relay failed','r','delivery complete','dead-drop complete'],
            'interception':['intercept','mouse0','relay complete','r reset'],
            'interception-complete':['interception complete','relay complete','r reset'],
            'interception-failed':['interception failed','relay complete','r reset']}[state]
        if any(term not in text for term in expected):failures.add('truthful-'+state+'-text-missing')
        if state=='grab' and any(term in text for term in ['parcel in hand','delivery complete','dead-drop complete','relay complete']):
            failures.add('premature-or-stale-receipt')
        if state=='carrying' and any(term in text for term in ['delivery complete','dead-drop complete','relay complete']):
            failures.add('premature-completion-receipt')
        if state=='relay':
            if str(row['relay'].get('count'))+'/3' not in text or 'f' not in text or not re.search(r'\d+\s*m\b',text):
                failures.add('relay-next-action-distance-or-progress-missing')
        if state.startswith('relay'):
            objective=(row.get('relay',{}).get('objective') or '').lower().splitlines()
            if not objective or lines[:len(objective)]!=objective:
                failures.add('relay-live-objective-not-rendered')
        if state.startswith('interception'):
            current=row['interception']
            if not current.get('valid') or text!=(current.get('objective') or '').lower():
                failures.add('interception-live-objective-not-rendered')
            if f"stopped {current.get('stopped')} / escaped {current.get('escaped')}" not in text:
                failures.add('interception-actual-counts-not-rendered')
        if ch.get('stage',0)>0:
            c=ch.get('cacheBoundsCenter');z=ch.get('cacheBoundsSize')
            if not isinstance(c,list) or not isinstance(z,list) or len(c)!=3 or len(z)!=3 or not all(math.isfinite(v) for v in c+z):
                failures.add('cache-physical-bounds-missing')
            elif math.dist([c[0],c[2]],[50,18])>.15 or abs(c[1]-z[1]/2-.14)>.04 or not all(.1<v<4 for v in z):
                failures.add('cache-physical-presentation-changed')
            if not isinstance(ch.get('emissiveRenderers'),int) or not 0<=ch['emissiveRenderers']<=1:
                failures.add('cache-accent-emission-changed')
        if not any(e['phase']==state for e in examples):examples.append(dict(time=row['time'],phase=state,panel=p,health=h))
    for state in set(required)-seen:failures.add('phase-unobserved-'+state)
    if not seen:failures.add('hud-trace-missing')
    return dict(passed=not failures,failure=sorted(failures) or None,phases=sorted(seen),reset_grab_samples=resets,
        examples=examples,layout='one primary objective panel plus health/wanted',pixel_review_required=True,
        final_game_accepted=False)
