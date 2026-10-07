"""Camera-aligned hit, deliberate miss and real cover checks from pre-shot observations."""
from .combat_checks import FOOT_PROBE,WALL_PROBE
from .continuous_checks import scenario

AIM_PROBES={
    'aligned':{**FOOT_PROBE,'id':'aim-aligned-hit','captures':[3.2,6.9,7.55,9.25,14]},
    'miss':scenario(16,[(4,6,['S']),(6.2,7.6,['W','D']),(7.8,8.1,['F']),
        (8.2,12.5,['S']),(8.6,8.9,['Mouse0']),(9.4,9.7,['Mouse0']),
        (10.2,10.5,['Mouse0']),(11,11.3,['Mouse0'])],[3.2,7.8,8.65,9.5,11.2,14],'mission-core'),
    'wall':WALL_PROBE,
    'near-cover':{**FOOT_PROBE,'id':'aim-near-cover','fixture':'combat-near-cover',
                  'captures':[3.2,6.9,7.55,9.25,14]},
}


def inspect_aim_contract(events,kind):
    failed=[];valid=[e for e in events if 'Mouse0' in e.get('keys',[])
        and e.get('shotsAfter',0)>e.get('shotsBefore',0)]
    if not valid:failed.append('actual-shot-observations-missing')
    damage=[];off_aim=[];misses=[];blocked=[]
    for e in valid:
        targets=e.get('targets',[])
        for t in targets:
            if t.get('hpAfter',0)<t.get('hpBefore',0):
                fact=dict(time=e['time'],target=t['name'],first_ray_collider=e.get('firstRayCollider'),
                    hp_before=t['hpBefore'],hp_after=t['hpAfter'],
                    viewport_contains_center=t.get('viewportContainsCenter'),visual_bounds_ray_hit=t.get('visualBoundsRayHit'))
                damage.append(fact)
                if not all(t.get(k) for k in ('colliderRayHit','visualBoundsRayHit','viewportContainsCenter','firstRayTarget')):
                    off_aim.append(fact)
        if targets and not any(t.get('colliderRayHit') or t.get('viewportContainsCenter') for t in targets):
            misses.append(e)
        wall='CombatNearCover' if kind=='near-cover' else 'CombatValidationWall'
        if e.get('firstRayCollider')==wall and any(t.get('colliderRayHit') for t in targets):
            blocked.append(e)
    if off_aim:failed.append('rival-damage-outside-visible-camera-aim')
    if kind=='aligned':
        if not damage:failed.append('aligned-rival-damage-not-demonstrated')
    elif kind=='miss':
        if len(misses)<2:failed.append('intentional-off-target-shots-not-demonstrated')
        if damage or any(e['hitsAfter']!=e['hitsBefore'] for e in valid):
            failed.append('intentional-miss-causes-damage')
    elif kind in ('wall','near-cover'):
        if not blocked:failed.append('aimed-rival-behind-cover-not-demonstrated')
        if any(e['hitsAfter']!=e['hitsBefore'] or any(t['hpAfter']<t['hpBefore'] for t in e['targets']) for e in blocked):
            failed.append('shot-damages-through-nearer-cover')
        if kind=='near-cover' and not any('CombatNearCover' in e.get('originOverlaps085',[]) for e in blocked):
            failed.append('near-origin-cover-not-exercised')
    else:raise ValueError('Unknown aim contract')
    facts={'shot_count':len(valid),'damage_events':damage,'off_aim_damage':off_aim,
           'intentional_miss_count':len(misses),'cover_blocked_shot_count':len(blocked)}
    return dict(scope=kind,passed=not failed,failure=failed or None,facts=facts,final_game_accepted=False)


def require_aim_contracts(gate):
    records=gate.get('aim_contracts',[]) or [v['gate']['aim_contract']
        for v in gate.get('regressions',{}).get('regressions',[]) if 'aim_contract' in v['gate']]
    scopes={v.get('scope') for v in records if v.get('passed') and v.get('candidate')==gate.get('candidate_commit')}
    return scopes>={'aligned','miss','wall','near-cover'}

