"""Independent real-input moving-target, isolation, escape and reset contracts."""
import math
from .aim_checks import inspect_aim_contract
from .continuous_checks import validate_proposed
from .counter_exfil_checks import old_ending_with_armed_hint

NAMES = {'InterceptRunner1','InterceptRunner2','InterceptRunner3'}


def probes(original):
    prefix=[s for s in original['steps'] if s['end']<=60]
    movement=[(60.3,60.8,['D']),(60.9,62.15,['S']),(62.3,62.5,['A']),
              (64.8,66.05,['S']),(66.2,66.35,['A']),
              (70.8,72.05,['S']),(72.2,72.35,['A'])]
    taps=[63.2,63.5,63.8,64.1,69,69.2,69.4,69.6,69.8,70,70.2,70.4,75,75.2,75.4,75.6,75.8,76]
    extra=movement+[(t,t+.09,['Mouse0']) for t in taps]+[(90,90.3,['R']),(92,93,['W'])]
    positive=validate_proposed(dict(duration=95,steps=prefix+[dict(start=a,end=b,keys=k) for a,b,k in extra],
        captures=[3.2,59.75,63.25,64.25,69.45,70.5,75.45,77,90.6,94]),100,'mission-core')
    inactive=validate_proposed(dict(duration=18,steps=[dict(start=4,end=5,keys=['W']),
        dict(start=7,end=7.2,keys=['F'])],captures=[3.2,6,10,16]),100,'mission-core')
    return dict(positive=positive,inactive=inactive)


def inspect_interception(rows,events,case):
    if case not in ('positive','escape','inactive'): raise ValueError('Unknown interception case')
    failures=set(); activations=[]; completions=[]; escapes=[]; resets=[]; deaths={}; spans={}; prior=None
    original_visibility=[]; actual_shots=[]; pending_reset=None; after_reset=[]
    def fail(reason): failures.add(reason)
    for row in rows:
        t=row.get('time',0)
        if t<.5: continue
        s=row.get('interception',{}); old=prior.get('interception',{}) if prior else {}
        if not s.get('present') or not s.get('valid') or s.get('componentCount')!=1:
            fail('interception-state-observer-missing'); prior=row; continue
        targets={v.get('name'):v for v in s.get('targets',[])}
        if len(targets)!=len(s.get('targets',[])) or not set(targets)<=NAMES: fail('target-identities-invalid')
        for key in ('stopped','escaped','spawned'):
            if not isinstance(s.get(key),int) or not 0<=s[key]<=3: fail('interception-count-invalid')
        if s.get('complete') and s.get('failed'): fail('simultaneous-ending-and-failure')
        restarted=prior and row.get('restarts')!=prior.get('restarts')
        if restarted:
            recent=[r for r in rows if 0<=t-r.get('time',0)<=.35]
            if not any('R' in r.get('keys',[]) for r in recent): fail('reset-without-ordinary-R')
            pending_reset=t; deaths={}
        if pending_reset is not None:
            clean=not any([s.get('active'),s.get('complete'),s.get('failed'),s.get('stopped'),s.get('escaped'),s.get('spawned'),targets])
            if clean:
                if not resets: resets.append(t)
                after_reset.append(t)
            elif t-pending_reset>.35: fail('whole-reset-not-cleared-or-stage-rearmed')
        if s.get('active') and not old.get('active') and not restarted:
            if not row.get('relay',{}).get('complete') or row.get('mission')!='complete' or not row.get('routeChapter',{}).get('complete'):
                fail('interception-started-without-real-prior-completion')
            activations.append(t)
        if case=='inactive' and (s.get('active') or targets or any(s.get(k) for k in ('stopped','escaped','spawned','complete','failed'))):
            fail('interception-active-without-handoff')
        if s.get('active'):
            if not row.get('relay',{}).get('complete') or row.get('mission')!='complete': fail('interception-mutated-prior-state')
            panels={p.get('name'):p for p in row.get('routeChapter',{}).get('hudPanels',[])}
            text=panels.get('MissionBoard',{}).get('text','')
            if not s.get('objective') or (text!=s['objective'] and not old_ending_with_armed_hint(row,text)):
                fail('actual-interception-objective-not-rendered')
            if 'R reset' not in text or 'relay complete' not in text.lower(): fail('interception-receipt-or-reset-hint-missing')
        for name,v in targets.items():
            pos=v.get('position',[])
            if len(pos)!=3 or not all(isinstance(x,(float,int)) and math.isfinite(x) for x in pos):
                fail('invalid-target-position'); continue
            if v.get('hp')==0 and v.get('alive') is False:
                deaths.setdefault(name,t)
                if v.get('renderers')!=0 or v.get('colliderEnabled') is not False: fail('actual-dead-target-not-hidden-and-nonsolid')
            if v.get('alive') and v.get('colliderEnabled') and not s.get('failed') and not s.get('complete'):
                points=spans.setdefault(name,[]);points.append((t,pos))
                if not v.get('dynamicBody') or not v.get('gravity'): fail('live-target-not-dynamic-and-gravity-driven')
                if not 23.4<=pos[0]<=58.3 or not 8.3<=pos[2]<=27.7: fail('target-left-rendered-physical-street')
                age=t-points[0][0]
                if age>.5 and (not v.get('groundCollider') or not -.06<=v.get('footGap',999)<=.12):
                    fail('live-target-grounding-not-established')
                if v.get('renderers',0)<1: fail('live-target-invisible')
        if s.get('stopped',0)>len(deaths): fail('stop-count-exceeds-actual-distinct-deaths')
        if old.get('stopped',0)>s.get('stopped',0) and not restarted: fail('stopped-count-decreased-without-reset')
        if s.get('escaped',0)>old.get('escaped',0) and not restarted:
            eligible=[v for v in targets.values() if v.get('alive') and v.get('hp',0)>0 and
                len(v.get('position',[]))==3 and v['position'][0]>=58 and v.get('renderers')==0 and v.get('colliderEnabled') is False]
            if s['escaped']!=old.get('escaped',0)+1 or not eligible or not s.get('failed'):
                fail('escape-not-a-real-live-boundary-crossing')
            escapes.append(dict(time=t,names=[v['name'] for v in eligible],stopped=s.get('stopped')))
        if s.get('failed') and not old.get('failed'):
            if not(s.get('escaped',0)>0 or row.get('health',100)<=0): fail('failure-without-escape-or-player-death')
        if s.get('complete') and not old.get('complete'):
            if s.get('stopped')!=3 or set(deaths)!=NAMES or s.get('escaped')!=0 or row.get('health',0)<=0:
                fail('completion-without-three-real-stops')
            completions.append(t)
        if (old.get('complete') or old.get('failed')) and not restarted:
            if any(s.get(k)!=old.get(k) for k in ('complete','failed','stopped','escaped')):
                fail('resolved-encounter-state-not-latched')
        prior=row
    onset=activations[0] if activations else float('inf')
    relevant=[e for e in events if e.get('time',0)>=onset and e.get('restarts')==0]
    if case=='positive':
        aim=inspect_aim_contract(relevant,'aligned')
        if not aim['passed']: failures.update(aim['failure'])
        lethal=[]
        for e in relevant:
            changes=[v for v in e.get('targets',[]) if v.get('hpAfter',0)<v.get('hpBefore',0)]
            if len(changes)>1: fail('one-shot-damaged-multiple-targets')
            for target in changes:
                if target.get('hpAfter')!=target.get('hpBefore')-1: fail('shot-damage-not-one-real-hit')
                if target.get('name') in NAMES:
                    actual_shots.append(dict(time=e['time'],target=target['name'],before=target['hpBefore'],after=target['hpAfter']))
                    if target['hpAfter']==0:
                        lethal.append(target['name'])
                        # Inspect other living actors immediately after this shot.
                        sample=next((r for r in rows if r.get('restarts')==e.get('restarts') and 0<=r['time']-e['time']<=.25),None)
                        if sample is None: fail('lethal-shot-post-state-missing'); continue
                        before=next((r for r in reversed(rows) if r.get('restarts')==e.get('restarts') and 0<e['time']-r['time']<=.25),None)
                        if before is None: fail('lethal-shot-pre-state-missing'); continue
                        expected={v['name']:v for v in before.get('rivals',[]) if v.get('name')!=target['name'] and v.get('alive') and v.get('hp',0)>0}
                        after={v['name']:v for v in sample.get('rivals',[])}
                        living=[after[name] for name in expected if name in after]
                        original_visibility.extend(dict(time=sample['time'],name=v['name'],renderers=v.get('renderers'),collider=v.get('colliderEnabled')) for v in living)
                        # The final living rival has no comparator. Earlier real
                        # comparisons remain mandatory, including the original rival.
                        if any(name not in after or not after[name].get('alive') or
                               after[name].get('hp')!=v.get('hp') for name,v in expected.items()):
                            fail('lethal-hit-changed-another-live-rival')
                        if any(v.get('renderers',0)<1 or v.get('colliderEnabled') is not True for v in living):
                            fail('lethal-hit-hid-or-disabled-another-live-rival')
        if set(lethal)!=NAMES or len(lethal)!=3 or len(actual_shots)!=9: fail('three-actual-moving-target-kills-unverified')
        if len(completions)!=1 or escapes: fail('positive-encounter-ending-unverified')
        if not any(v['name']=='Rival' for v in original_visibility): fail('original-rival-isolation-unverified')
    elif case=='escape':
        if not escapes or completions: fail('actual-escape-failure-unverified')
        if any(e.get('hitsAfter',0)>e.get('hitsBefore',0) for e in relevant): fail('escape-proof-includes-target-damage')
        if any(e['stopped'] for e in escapes): fail('escaped-live-target-counted-as-stop')
    movement={name:round(max(math.dist(p[1],points[0][1]) for p in points),3) for name,points in spans.items()}
    if case!='inactive':
        if len(activations)!=1: fail('one-real-activation-unverified')
        if not resets or not after_reset or max(after_reset)-min(after_reset)<2: fail('reset-persistence-unverified')
        if set(movement)!=NAMES or any(v<1 for v in movement.values()): fail('three-actual-moving-bodies-unverified')
    if not rows: fail('native-trace-missing')
    return dict(passed=not failures,failure=sorted(failures) or None,case=case,activations=activations,
        completions=completions,escapes=escapes,resets=resets,movement_metres=movement,
        actual_new_target_damage=actual_shots,other_live_rivals_after_lethal=original_visibility,
        secondary_target_isolation_qualified=case=='positive' and not failures,
        final_game_accepted=False,validation_wait_is_not_mission_duration=True)
