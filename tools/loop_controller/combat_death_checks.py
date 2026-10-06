"""Actual ordinary-input lethal hit and whole-reset proof; no gameplay writes."""
import math
from .continuous_checks import scenario
from .aim_checks import inspect_aim_contract

DEATH_PROBE = scenario(22, [(4,5.6,['W']), (5.6,5.9,['D']), (6.3,6.6,['S']),
    (7.5,7.8,['Mouse0']), (9.2,9.5,['Mouse0']), (10.9,11.2,['Mouse0']),
    (14,14.3,['R']), (18,19,['W'])], [3.2,7.55,9.25,10.95,12,14.5,19.5], 'mission-core')
DEATH_PROBE['id'] = 'actual-rival-lethal-hit-and-reset'


def inspect_death(rows, events):
    failed = []; facts = {}; aim = inspect_aim_contract(events, 'aligned')
    if not aim['passed']: failed += aim['failure']
    shots = [e for e in events if e.get('restarts') == 0 and 'Mouse0' in e.get('keys', [])
             and e.get('shotsAfter', 0) == e.get('shotsBefore', 0) + 1]
    hits = [(e, t) for e in shots for t in e.get('targets', []) if t.get('hpAfter', 0) < t.get('hpBefore', 0)]
    chain = [(t.get('hpBefore'), t.get('hpAfter')) for e,t in hits if t.get('name') == 'Rival']
    if len(shots) != 3 or len(hits) != 3 or chain != [(3,2),(2,1),(1,0)]:
        failed.append('three-real-first-hit-damage-events-not-established')
    if any(e.get('hitsAfter') != e.get('hitsBefore', 0) + 1 for e,t in hits):
        failed.append('hit-counter-does-not-match-actual-damage')
    dead = [(r,v) for r in rows if 11.3 <= r.get('time',0) <= 13.8 and r.get('restarts') == 0
            for v in r.get('rivals',[]) if v.get('name') == 'Rival']
    if len(dead) < 10 or any(v.get('alive') or v.get('hp') != 0 or v.get('renderers') != 0
                            or v.get('colliderEnabled') is not False for r,v in dead):
        failed.append('struck-rival-death-render-collider-not-established')
    after = [(r,v) for r in rows if 14.4 <= r.get('time',0) <= 17.5 and r.get('restarts') == 1
             for v in r.get('rivals',[]) if v.get('name') == 'Rival']
    if len(after) < 10 or any(v.get('alive') is not True or v.get('hp') != 3 or v.get('renderers',0) < 1
        or v.get('colliderEnabled') is not True or math.dist(v.get('position',[999]*3), [2,.14,-.5]) > .15
        or r.get('health') != 100 or r.get('hits') != 0 or r.get('shots') != 0 or r.get('pursuit') != 0
        for r,v in after):
        failed.append('whole-reset-rival-health-position-counters-not-established')
    if not any('R' in r.get('keys',[]) for r in rows): failed.append('ordinary-reset-input-missing')
    facts.update(shot_count=len(shots), damage_chain=chain, dead_samples=len(dead), reset_samples=len(after),
                 actual_damage=aim['facts']['damage_events'])
    return dict(passed=not failed, failure=failed or None, facts=facts,
                secondary_target_isolation_qualified=False, final_game_accepted=False)
