"""Measure the actual camera, obstacle and actor visibility; never accept a game from a fixture."""
import math

CAMERA_PROBE = dict(id='camera-clearance', coverage='foundation', fixture='camera-clearance', duration=22,
    steps=[dict(start=18,end=20,keys=['W'])], captures=[3.2,6.5,10.5,14.5,17.5,20.5])


def inspect_camera(rows):
    phases=[];failed=[]
    flags=['cameraInsideFixture','fixtureBetweenTargetAndCamera','nearPlaneTouchesFixture','legacyEndpointCrowding']
    def measured(o):
        distance=o.get('probeDistance')
        return (o.get('available') is True and o.get('probeHit') is True
            and o.get('probeCollider')=='CameraClearanceWall'
            and type(distance) in (int,float) and math.isfinite(distance) and distance>0
            and all(type(o.get(k)) is bool for k in flags)
            and o.get('targetSamples')==9
            and all(type(o.get(k)) is int and 0<=o[k]<=9 for k in ['inFrameSamples','unobstructedSamples']))
    for phase,start,end in [('near',6,7.5),('middle',10,11.5),('endpoint',14,15.5)]:
        observations=[r['cameraGeometry'] for r in rows if start<=r.get('time',-1)<=end and r.get('cameraGeometry')]
        valid=[o for o in observations if o.get('phase')==phase and measured(o)]
        facts=dict(phase=phase,samples=len(valid))
        if len(valid)<5:
            failed.append(phase+'-missing-measured-wall-case');phases.append(facts);continue
        facts.update(probe_distance_min=min(o['probeDistance'] for o in valid),
            probe_distance_max=max(o['probeDistance'] for o in valid),
            camera_inside_samples=sum(bool(o.get('cameraInsideFixture')) for o in valid),
            camera_beyond_wall_samples=sum(bool(o.get('fixtureBetweenTargetAndCamera')) for o in valid),
            near_plane_intersection_samples=sum(bool(o.get('nearPlaneTouchesFixture')) for o in valid),
            legacy_endpoint_predicate_samples=sum(bool(o.get('legacyEndpointCrowding')) for o in valid),
            minimum_actor_samples_in_frame=min(o.get('inFrameSamples',0) for o in valid),
            minimum_actor_samples_unobstructed=min(o.get('unobstructedSamples',0) for o in valid))
        low,high={'near':(.4,1.0),'middle':(2.8,3.2),'endpoint':(5.1,5.7)}[phase]
        if not low<=facts['probe_distance_min']<=facts['probe_distance_max']<=high:
            failed.append(phase+'-case-distance-unverified')
        if any(facts[k] for k in ['camera_inside_samples','camera_beyond_wall_samples','near_plane_intersection_samples']):
            failed.append(phase+'-camera-crosses-obstacle')
        phases.append(facts)
    return dict(passed=not failed,failure=failed,phases=phases,
        scope='disposable-camera-clearance-diagnostic',final_game_accepted=False,
        visibility_note='Viewport and occlusion samples describe actor visibility; full art/framing quality needs actual images')
