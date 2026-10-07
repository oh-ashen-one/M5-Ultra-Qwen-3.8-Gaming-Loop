"""Read-only trace hooks for one exact camera source, in a disposable build only."""
import math
from .core import Halt, sha

SOURCE_SHA='3a66d33bbd978406b79b31909316c4033d489760cd457ae48fabae34e7204eb2'
FIXTURE='camera-branch-diagnostic'


def instrument_source(raw):
    if sha(raw.encode())!=SOURCE_SHA:raise Halt('Camera branch diagnostic requires the exact inspected source')
    result=raw
    def insert(needle,extra):
        nonlocal result
        if result.count(needle)!=1:raise Halt('Camera diagnostic anchor is not unique')
        result=result.replace(needle,needle+extra,1)
    def record(name,pos):
        return '\n            LoopCameraBranchObservation.Record("'+name+'",'+pos+',cramped,top,camY,hHit,hDist);'
    insert('            Vector3 want = origin + hdir * hDist + Vector3.up * camY;',record('desired','want'))
    insert('                                       Mathf.Clamp01(damping * Time.deltaTime));',record('smoothed','pos'))
    needle='                        pos = pivot + sd * Mathf.Max(0.05f, v.distance - clearance);'
    if result.count(needle)!=1:raise Halt('Expected one exact final-segment branch')
    result=result.replace(needle,'                    {\n'+needle+'\n                        LoopCameraBranchObservation.Segment(v.collider.name,v.distance);\n                    }',1)
    needle='            // Final geometry-aware near-plane guard:'
    if result.count(needle)!=1:raise Halt('Expected unique segment boundary')
    result=result.replace(needle,record('after-segment','pos')+'\n'+needle,1)
    insert('            pos.y = Mathf.Max(pos.y, floorY + 0.08f);',record('after-world-clearance','pos'))
    needle='if (b.Contains(pos)) { pos.y = top + clearance; cramped = true; break; }'
    if result.count(needle)!=1:raise Halt('Expected exact saved target guard')
    result=result.replace(needle,'if (b.Contains(pos)) { pos.y = top + clearance; cramped = true; LoopCameraBranchObservation.Lift(r.name); break; }',1)
    needle='            transform.position = pos;'
    if result.count(needle)!=1:raise Halt('Expected one final camera assignment')
    result=result.replace(needle,record('final','pos')+'\n'+needle,1)
    return result


def apply_disposable_hooks(build_project):
    path=build_project/'Assets/Game/Bootstrap.cs'
    if path.is_symlink():raise Halt('Camera diagnostic source must be a regular build-copy file')
    before=path.read_text();after=instrument_source(before);path.write_text(after)
    return dict(scope='disposable-build-passive-camera-branch-hooks',source_sha256=sha(before.encode()),
        instrumented_sha256=sha(after.encode()),game_authoring_checkout_changed=False,
        fixture_only=True,controller_instrumentation_author='cloud',game_authorship='local Qwen')


def equivalent_trace(before,after):
    if len(before)!=len(after) or not before:return False
    for a,b in zip(before,after):
        if a.get('mode')!=b.get('mode') or a.get('keys')!=b.get('keys') or abs(a['time']-b['time'])>1e-5:return False
        for key in ['player','vehicle']:
            if a.get(key)!=b.get(key) and (not a.get(key) or not b.get(key) or math.dist(a[key],b[key])>1e-4):return False
        for key in ['cameraPosition','cameraForward']:
            x=a.get('cameraGeometry',{}).get(key);y=b.get('cameraGeometry',{}).get(key)
            if not x or not y or math.dist(x,y)>1e-5:return False
    return True


def changed_pixels(before,after):
    from PIL import Image,ImageChops
    with Image.open(before) as a,Image.open(after) as b:
        if a.size!=b.size:raise Halt('Return comparison must preserve capture dimensions')
        return ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox() is not None
