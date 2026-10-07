"""Measure observed local joint motion; actor travel and stills are insufficient."""
import math


def quaternion_angle(a, b):
    if len(a) != 4 or len(b) != 4 or not all(math.isfinite(v) for v in a+b):
        raise ValueError('Require finite four-component rotations')
    length = math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
    if length < 1e-8:
        raise ValueError('A zero quaternion cannot prove motion')
    return math.degrees(2*math.acos(min(1, abs(sum(x*y for x,y in zip(a,b))/length))))


def measure(rows, start, end, visual_suffix='PlayerVisual'):
    samples = [r for r in rows if start <= r['time'] <= end]
    tracks = {}
    for sample in samples:
        for visual in sample.get('characterPresentation', {}).get('visuals', []):
            if not visual['path'].endswith('/'+visual_suffix) or not visual.get('active'):
                continue
            for joint in visual.get('joints', []):
                if joint.get('active') and joint['path'] != visual['path']:
                    tracks.setdefault(joint['path'], []).append((sample['time'], joint))
    joints = []
    for name, frames in tracks.items():
        first = frames[0][1]
        rotation = max(quaternion_angle(first['localRotation'], f['localRotation']) for _,f in frames)
        displacement = max(math.dist(first['localPosition'], f['localPosition']) for _,f in frames)
        joints.append(dict(path=name, samples=len(frames), first_seconds=frames[0][0],
            last_seconds=frames[-1][0], max_rotation_from_first_degrees=rotation,
            max_local_translation_from_first_m=displacement))
    return dict(start=start, end=end, sample_count=len(samples),
        observed_span=0 if len(samples)<2 else samples[-1]['time']-samples[0]['time'],
        joints=joints, actual_joint_observations=bool(joints),
        interpretation='Local joint transforms only; root travel and rendered stills do not establish articulation')


def moving_joints(report, names, minimum_degrees, minimum_span=.4):
    selected = [j for j in report['joints'] if any(n in j['path'].split('/')[-1] for n in names)]
    return bool(report['observed_span'] >= minimum_span and selected and any(
        j['samples'] >= 4 and j['last_seconds']-j['first_seconds'] >= minimum_span
        and j['max_rotation_from_first_degrees'] >= minimum_degrees for j in selected))
