"""Observe the four courier HUD states; pixel readability still needs visual review."""
import math
from .mission_anchors import actor_child


def inspect_courier_hud(rows):
    def text(row):return ' '.join(row.get('visibleText') or []).lower()
    def parcel(row):return next((o for o in row.get('missionObjects',[]) if o['name']=='Parcel'),None)
    carried=next((r for r in rows if parcel(r) and actor_child(parcel(r))),None)
    complete=next((r for r in rows if r.get('mission')=='complete'),None)
    before=[r for r in rows if r['time']>=1 and (not carried or r['time']<carried['time'])]
    carrying=[r for r in rows if carried and r['time']>=carried['time'] and
              (not complete or r['time']<complete['time'])]
    failure=[]
    if not before or any('grab' not in text(r) or 'parcel in hand' in text(r) for r in before):
        failure.append('hud-before-pickup-state-wrong')
    if not carrying or not all('parcel in hand' in text(r) for r in carrying):
        failure.append('hud-carrying-state-unverified')
    if not complete or 'delivery complete' not in text(complete):
        failure.append('hud-completion-state-unverified')
    reset=None
    if complete:
        candidates=[r for r in rows if r['time']>complete['time'] and
                    r.get('restarts',0)>complete.get('restarts',0)]
        for r in candidates:
            obj=parcel(r)
            recent_input=any('R' in x.get('keys',[]) and 0<=r['time']-x['time']<=2 for x in rows)
            if (recent_input and r.get('mission')=='active' and r.get('mode')=='foot'
                    and r.get('grounded') and r.get('playerCollisionEnabled') and obj and not actor_child(obj)
                    and 'grab' in text(r) and 'parcel in hand' not in text(r)
                    and math.dist(r.get('player') or [999]*3,[0,.135,1.7])<.4
                    and math.dist(r.get('vehicle') or [999]*3,[3.6,0,8])<.4):
                reset=r;break
    if not reset:failure.append('hud-and-physical-reset-after-completion-unverified')
    return {'passed':not failure,'failure':failure,'before_pickup':bool(before) and
            'hud-before-pickup-state-wrong' not in failure,
            'carrying_seconds':carried['time'] if carried else None,
            'completion_seconds':complete['time'] if complete else None,
            'reset_seconds':reset['time'] if reset else None,
            'pixel_readability':'requires actual native capture review'}
