"""Native articulation proof for an unaccepted original presentation increment."""
import math
import statistics
from .character_motion_checks import measure,moving_joints,quaternion_angle

CLIPS={'Idle':2.,'Walk':1.,'Jog':.8,'Aim':1.,'Board':.8,'Drive':2.}
WINDOWS={'Idle':(.5,1.65),'Walk':(4.1,5.0),'Jog':(5.6,7.0),'Aim':(1.95,2.95)}


def visuals(row):
    return [v for v in row.get('characterPresentation',{}).get('visuals',[])
            if v.get('active') and v['path'].endswith('/PlayerVisual')]


def clip_progress(rows,name,start,end):
    observations=[]
    for row in rows:
        if start<=row['time']<=end:
            for visual in visuals(row):
                for clip in visual.get('clips',[]):
                    if clip['name']==name and clip.get('playing') and clip.get('enabled') and clip.get('weight',0)>.05:
                        observations.append((row['time'],clip['time']))
    return dict(samples=len(observations),observed_span=observations[-1][0]-observations[0][0] if observations else 0,
        clip_time_range=max(v for _,v in observations)-min(v for _,v in observations) if observations else 0)


def horizontal_speed(rows,start,end):
    selected=[r for r in rows if start<=r['time']<=end and r.get('player')]
    values=[]
    for a,b in zip(selected,selected[1:]):
        dt=b['time']-a['time']
        if dt>0:values.append(math.hypot(b['player'][0]-a['player'][0],b['player'][2]-a['player'][2])/dt)
    return statistics.median(values) if values else None


def assess(rows,imported):
    clips={c['name']:c for c in imported.get('clips',[]) if not c.get('preview')}
    failures=[]
    if imported.get('animationType')!='Legacy':failures.append('character-import-is-not-Legacy')
    for name,length in CLIPS.items():
        c=clips.get(name,{})
        if not c.get('legacy') or abs(c.get('length',-10)-length)>.04 or c.get('curveCount',0)<20:
            failures.append('missing-or-invalid-imported-'+name)
    motion={name:measure(rows,*window) for name,window in WINDOWS.items()}
    progress={name:clip_progress(rows,name,*window) for name,window in WINDOWS.items()}
    requirements={'Idle':(['head','spine','shoulder'],.2),'Walk':(['hip','knee'],4.),
                  'Jog':(['hip','knee'],8.),'Aim':(['shoulder','elbow','spine'],.3)}
    for name,(joints,threshold) in requirements.items():
        if not moving_joints(motion[name],joints,threshold):failures.append('no-measured-joint-motion-'+name)
        p=progress[name]
        if p['samples']<4 or p['observed_span']<.4 or p['clip_time_range']<.1:
            failures.append('no-observed-clip-progress-'+name)
    idle={j['path']:j['localRotation'] for r in rows if .5<=r['time']<=1.5 for v in visuals(r)
          for j in v.get('joints',[]) if 'shoulder' in j['path'].split('/')[-1]}
    raised=[quaternion_angle(idle[j['path']],j['localRotation'])
            for r in rows if 2.1<=r['time']<=2.8 for v in visuals(r) for j in v.get('joints',[])
            if j['path'] in idle]
    max_raise=max(raised) if raised else 0
    if max_raise<30:failures.append('aim-did-not-raise-shoulders')
    capsule=[r.get('characterPresentation',{}) for r in rows]
    if not capsule or any(abs(v.get('controllerHeight',0)-1.75)>1e-4 or
                          abs(v.get('controllerRadius',0)-.32)>1e-4 for v in capsule):
        failures.append('accepted-capsule-dimensions-changed-or-unobserved')
    speeds={name:horizontal_speed(rows,*WINDOWS[name]) for name in ('Walk','Jog')}
    for name,value in speeds.items():
        if value is None or abs(value-3.2)>.25:failures.append('unexpected-real-foot-speed-'+name)
    return dict(passed=not failures,failures=failures,motion=motion,clip_progress=progress,
        aim_max_shoulder_change_degrees=max_raise,median_real_foot_speed_mps=speeds,
        scope='Imported original clips plus actual native joint/time observations; art quality, vehicle presentation and full gameplay acceptance remain separate',
        new_sprint_mechanic=False,final_character_accepted=False)
