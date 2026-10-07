"""Required reference/native pixels, request receipts and distinct visual verdicts."""
import base64
from pathlib import Path
from .core import Halt,sha

TARGETS=('chicago_01_neighborhood_on_foot.png','chicago_02_downtown_l_driving.png',
         'chicago_03_alley_combat.png','chicago_04_riverwalk_bridge.png','chicago_05_rainy_night_driving.png')


def contract(images,required_targets,minimum_actual=1,broad=False):
    required=set(TARGETS if broad else required_targets)
    if not required or not required<=set(TARGETS): raise Halt('Visual task needs known target images')
    records=[]
    for label,path in images:
        p=Path(path);raw=p.read_bytes()
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise Halt('Visual input is not actual PNG bytes')
        records.append(dict(label=label,name=p.name,sha256=sha(raw),kind='target' if p.name in TARGETS else 'native'))
    supplied={v['name'] for v in records if v['kind']=='target'}
    if not required<=supplied:raise Halt('Missing required visual reference pixels')
    if sum(v['kind']=='native' for v in records)<minimum_actual:raise Halt('Missing current native visual pixels')
    if len({v['label'] for v in records})!=len(records):raise Halt('Visual input labels must distinguish every frame')
    return dict(records=records,required_targets=sorted(required),minimum_actual=minimum_actual,broad=broad)


def verify_payload(messages,expected):
    """Verify the actual API image bytes, not a filename listed in a prompt."""
    observed=[]
    for msg in messages:
        content=msg.get('content');label=None
        if not isinstance(content,list):continue
        for part in content:
            if part.get('type')=='text':label=part.get('text')
            elif part.get('type')=='image_url':
                url=part.get('image_url',{}).get('url','');prefix='data:image/png;base64,'
                if not url.startswith(prefix):raise Halt('Visual request must carry immutable native PNG bytes')
                try:raw=base64.b64decode(url[len(prefix):],validate=True)
                except ValueError as error:raise Halt('Invalid request image encoding') from error
                observed.append(dict(label=label,sha256=sha(raw)))
    desired=[{k:r[k] for k in ('label','sha256')} for r in expected['records']]
    if observed!=desired:raise Halt('Actual request images differ from required visual packet')
    return dict(verified=True,image_count=len(observed),records=expected['records'],
                required_targets=expected['required_targets'],broad=expected['broad'])


def budget(config,broad=False):
    # Seven images use57344 conservative tokens; leave room for source and a
    # complete thinking-enabled response, below the native262144 context.
    config.update(working_context_tokens=98304,output_tokens=16384,model_timeout_seconds=1200)


def visual_verdict(fields,broad=False):
    if fields.get('verdict') not in ('PASS','FIX','UNVERIFIED'):raise ValueError('Use PASS/FIX/UNVERIFIED')
    if not isinstance(fields.get('summary'),str) or not fields['summary'].strip():raise ValueError('Explain actual pixel evidence')
    fixes=fields.get('fixes')
    if not isinstance(fixes,list) or len(fixes)>5 or any(not isinstance(x,str) for x in fixes):raise ValueError('At most five concrete fixes')
    return dict(ok=True,**fields,scope='broad-visual' if broad else 'matched-visual-improvement',
                final_game_accepted=False,gameplay_pass_is_visual_pass=False)
