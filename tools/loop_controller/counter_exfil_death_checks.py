"""Declared negative-only health injection; freeze new state at the actual edge."""
from .player_death_checks import death_probe,inspect_player_death
from .counter_exfil_checks import chapter

CASES={'armed-start':(85.2,'F',False,0),'active-receipt':(86.55,'',True,0),
       'active-runners':(88,'',True,3),'failed-escape':(110,'',True,3)}

def contract(case):
    at,key,_,_=CASES[case]
    return at,key,dict(interceptionComplete=True,stopped=3,spawned=3,escaped=0)

def probe(original,case):
    return death_probe(original,'counter-exfil-'+case,contract(case))

def inspect_frozen(rows,injection,case):
    at,_,active,count=CASES[case];reset=at+3.5;failures=[]
    initial=injection.get('counterBefore') or {};before=chapter(dict(counterExfil=initial))
    actors={a['entityId']:a for a in initial.get('actors',[])}
    if (not before or before.get('Active')!=active or before.get('SpawnedCount')!=count
            or not (before.get('Armed') or active) or before.get('Complete')
            or (case=='failed-escape' and (not before.get('Failed') or not before.get('FailReason')))):
        return dict(passed=False,failure=['actual-counter-state-before-death-not-established'])
    dead=[r for r in rows if injection['time']-1e-4<=r['time']<reset-.01 and r.get('restarts')==0 and r.get('health')==0]
    if len(dead)<10:failures.append('counter-zero-health-observation-window-missing')
    for row in dead:
        state=chapter(row);current={a['entityId']:a for a in row.get('counterExfil',{}).get('actors',[])}
        if (not state or state.get('Active')!=before.get('Active') or state.get('Complete')
                or any(state.get(k)!=before.get(k) for k in ('SpawnedCount','KilledCount','EscapedCount','ActiveTime'))
                or set(current)!=set(actors)):
            failures.append('counter-activation-spawn-progress-or-score-after-death')
        for ident,actor in current.items():
            old=actors.get(ident)
            if old is None or any(actor.get(k)!=old.get(k) for k in ('hp','alive')):
                failures.append('counter-target-damage-or-identity-change-after-death')
        if before.get('FailReason'):
            board=next((p for p in row.get('routeChapter',{}).get('hudPanels',[]) if p.get('name')=='MissionBoard'),{})
            if state.get('FailReason')!=before['FailReason'] or before['FailReason'] not in board.get('text',''):
                failures.append('specific-counter-failure-lost-on-death')
    after=[r for r in rows if reset+.4<=r['time']<=reset+1.2 and r.get('restarts')==1]
    if len(after)<4:failures.append('counter-reset-window-missing')
    for row in after:
        state=chapter(row)
        if (not state.get('Dormant') or row.get('counterExfil',{}).get('actors')
                or any(state.get(k) for k in ('Armed','Active','Complete','Failed','SpawnedCount','KilledCount','EscapedCount','ActiveTime','FailReason'))):
            failures.append('counter-state-or-actors-survive-R')
    return dict(passed=not failures,failure=sorted(set(failures)),zero_health_samples=len(dead),reset_samples=len(after),
        actual_counter_before_death=before)

def inspect(rows,injection,case):
    legacy=inspect_player_death(rows,injection,'counter-exfil-'+case,contract(case))
    counter=inspect_frozen(rows,injection,case)
    return dict(passed=legacy['passed'] and counter['passed'],case=case,
        failure=sorted(set(legacy['failure']+counter['failure'])),old_controls_and_reset=legacy,counter=counter,
        intervention='External declared health=0 injection only; real input prefix and all game state transitions preserved.',
        natural_damage_death_proven=False,final_game_accepted=False)
