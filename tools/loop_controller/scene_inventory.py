"""Fail closed on incomplete native inventories before diagnosing gameplay."""
import math
from .core import Halt, read_json


def inspect_inventory(observation):
    failures=[]
    objects=observation.get('objects')
    if not isinstance(objects,list) or not all(isinstance(o,dict) for o in objects):
        return dict(passed=False,failure=['invalid-scene-object-list'])
    counts={'renderer':sum(o.get('kind')=='renderer' for o in objects),
            'collider':sum(o.get('kind')!='renderer' for o in objects)}
    if observation.get('schemaVersion')!=2:failures.append('missing-inventory-completeness-contract')
    if observation.get('complete') is not True or observation.get('truncated') is not False:
        failures.append('scene-inventory-not-complete')
    for kind in counts:
        total=observation.get(kind+'Total');recorded=observation.get(kind+'Recorded')
        if (type(total) is not int or type(recorded) is not int or total<0 or recorded<0
                or total!=recorded or recorded!=counts[kind]):
            failures.append(kind+'-inventory-count-mismatch')
    when=observation.get('observedAtSeconds')
    if not isinstance(when,(float,int)) or not math.isfinite(when) or not .5<=when<4:
        failures.append('scene-snapshot-outside-initialization-window')
    ids=[o.get('entityId') for o in objects]
    if any(not isinstance(i,str) or not i.strip() or i=='0' for i in ids) or len(set(ids))!=len(ids):
        failures.append('missing-or-duplicate-scene-component-identity')
    return dict(passed=not failures,failure=failures,observed_counts=counts,
        declared_counts={k:observation.get(k) for k in ('rendererTotal','rendererRecorded','colliderTotal','colliderRecorded')},
        observed_at_seconds=when,scope='Complete point-in-time scene component inventory; gameplay and rendered support criteria are unchanged')


def inspect_capture_inventory(captures):
    try:return inspect_inventory(read_json(captures/'scene-transforms.json'))
    except (FileNotFoundError,ValueError,TypeError):
        return dict(passed=False,failure=['missing-or-invalid-scene-inventory'])


def require_complete_inventory(receipt):
    if not receipt.get('scene_inventory',{}).get('passed'):
        raise Halt('Native scene inventory is incomplete; preserve source and diagnose the recorder before gameplay edits')


def require_gameplay_compile_failure(errors):
    if any('Assets/LoopHarness/' in line.replace('\\','/') for line in errors):
        raise Halt('Protected controller harness compilation failed; stop gameplay edits and repair infrastructure')
