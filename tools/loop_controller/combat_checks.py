"""Independent native combat tests: real actor distances, occlusion and imported bounds."""
import math
from .continuous_checks import MOTOR_PROBE,scenario

FOOT_PROBE=scenario(16,[(4,5.6,['W']),(5.6,5.9,['D']),(6.3,6.6,['S']),
    (7.5,7.8,['Mouse0']),(9.2,9.5,['Mouse0'])],[3.2,6.9,8,10,14],'mission-core')
WALL_PROBE={**FOOT_PROBE,'id':'combat-wall-observation','fixture':'combat-wall'}
DRIVE_PROBE={**MOTOR_PROBE,'id':'combat-driving-actor','coverage':'mission-core','duration':22,
    'steps':[s for s in MOTOR_PROBE['steps'] if s['start']<19], 'captures':[3.2,7.8,11,14,18,21]}


def inspect_combat_contract(rows,kind):
    failed=[];facts={};samples=[(r,v) for r in rows for v in r.get('rivals',[]) if v.get('alive')]
    if not samples:return {'passed':False,'failure':['actual-rival-observations-missing']}
    sizes=[v['renderSize'] for r,v in samples if v.get('renderers',0)>0]
    facts['visible_height_range']=[min(v[1] for v in sizes),max(v[1] for v in sizes)] if sizes else None
    if not sizes or any(not 1.2<=v[1]<=2.4 or max(v[0],v[2])>1.8 for v in sizes):
        failed.append('rival-import-basis-or-visible-scale-invalid')
    changes=[]
    for (before,_),(r,v) in zip(samples,samples[1:]):
        if r.get('restarts',0)==before.get('restarts',0) and r.get('health',100)<before.get('health',100):
            changes.append(dict(time=r['time'],distance=v['actorDistance'],mode=r.get('mode'),
                                blocked=not v.get('attackUnobstructed'),collider=v.get('firstAttackCollider')))
    facts['damage_events']=changes
    if any(v['distance']>16.25 for v in changes):failed.append('damage-outside-actual-controlled-actor-range')
    if kind=='driving':
        driving=[(r,v) for r,v in samples if r.get('mode')=='vehicle']
        far=[(r,v) for r,v in driving if v['actorDistance']>18.25]
        facts['maximum_vehicle_distance']=max([v['actorDistance'] for r,v in driving] or [0])
        facts['far_pursuit_levels']=sorted({r['pursuit'] for r,v in far})
        if not driving:failed.append('actual-driving-not-exercised')
        if not far:failed.append('driving-escape-distance-not-exercised')
        elif any(r.get('pursuit')!=0 for r,v in far):failed.append('pursuit-does-not-follow-actual-vehicle-distance')
        if len(driving)>1:
            movement=math.dist(driving[0][1]['position'],driving[-1][1]['position'])
            facts['rival_motion_during_driving']=movement
            if movement<2:failed.append('rival-does-not-chase-controlled-vehicle')
    elif kind=='foot':
        facts['shots']=max(r.get('shots',0) for r in rows);facts['hits']=max(r.get('hits',0) for r in rows)
        if facts['hits']<1:failed.append('unoccluded-real-hit-not-exercised')
        if not any(r.get('pursuit',0)>0 for r,v in samples):failed.append('foot-pursuit-not-exercised')
        if not changes:failed.append('unoccluded-enemy-attack-not-exercised')
    elif kind=='wall':
        blocked=[(r,v) for r,v in samples if r['time']>=7.1 and v.get('firstAttackCollider')=='CombatValidationWall']
        fired=[(r,v) for r,v in blocked if 'Mouse0' in r.get('keys',[]) and v.get('firstAimCollider')=='CombatValidationWall']
        facts['blocked_attack_samples']=len(blocked);facts['blocked_shot_samples']=len(fired)
        if len(blocked)<10 or not fired:failed.append('real-wall-occlusion-not-exercised')
        if any(v['time']>=7.1 and v['blocked'] and v['collider']=='CombatValidationWall' for v in changes):
            failed.append('enemy-damages-through-nearer-wall')
        if blocked:
            baseline=next((r for r in rows if r['time']>=7.1),blocked[0][0])
            if any(r.get('hits',0)>baseline.get('hits',0) or v['hp']<blocked[0][1]['hp'] for r,v in blocked):
                failed.append('player-damages-rival-through-nearer-wall')
    else:raise ValueError('Unknown combat diagnostic kind')
    return {'passed':not failed,'failure':failed or None,'facts':facts,'scope':kind,'final_game_accepted':False}
