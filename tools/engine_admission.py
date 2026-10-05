"""Private M5 process/lease observations and conservative engine ownership decisions."""
import datetime
import fcntl
import json
import os
from pathlib import Path


def same_identity(a,b):
    return a.get('pid')==b.get('pid') and abs(a.get('start',-1)-b.get('start',-2))<.01


def ownership(rows,baseline,lease=None):
    """Use one live process snapshot; registered groups survive parent exit."""
    by_pid={p['pid']:p for p in rows};active=[p for p in rows if p.get('renderer')]
    owner=by_pid.get(lease['controller_pid']) if lease else None
    valid_owner=bool(owner and same_identity(owner,{'pid':lease['controller_pid'],'start':lease['controller_start']}))
    owned=[];foreign=[]
    for p in active:
        if any(same_identity(p,old) for old in baseline):continue
        chain=p;seen=set();descendant=False
        while valid_owner and chain and chain['pid'] not in seen:
            seen.add(chain['pid'])
            if chain['pid']==owner['pid']:descendant=True;break
            chain=by_pid.get(chain.get('ppid'))
        group=bool(valid_owner and lease.get('engine_pid') and
            p.get('pgid')==lease['engine_pid'] and p['start']>=lease.get('engine_start',float('inf'))-.01)
        (owned if descendant or group else foreign).append(p['pid'])
    reasons=[]
    if lease and not valid_owner:reasons.append('lease-owner-missing-or-reused')
    if len(active)>(2 if lease else 1):reasons.append('renderer-capacity')
    if foreign:reasons.append('unowned-renderer')
    return {'status':'capacity-wait' if reasons else 'available','reasons':reasons,
        'active_renderer_pids':[p['pid'] for p in active],'owned_renderer_pids':owned,
        'foreign_renderer_pids':foreign,'renderer_cap':2,'owner_identity_valid':valid_owner if lease else None}


def snapshot(coordination=None,baseline=None,lease=None,process_module=None):
    if process_module is None:import psutil as process_module
    from unity_smoke import renderer_process
    rows=[]
    for p in process_module.process_iter(['pid','ppid','name','exe','cmdline','create_time']):
        try:
            v=p.info;argv=v['cmdline'] or [];exe=v['exe'] or '';name=v['name'] or ''
            renderer=renderer_process(exe,name.lower(),argv)
            unity=exe.endswith('/Unity.app/Contents/MacOS/Unity')
            item=dict(pid=p.pid,ppid=v['ppid'],start=v['create_time'],pgid=os.getpgid(p.pid),
                name=name,renderer=renderer)
            if renderer or unity:
                item.update(exe=exe,null_import_worker=unity and not renderer,
                    flags=[a for a in argv if a in ('-nographics','-batchmode','-force-metal')])
                for flag in ('-name','-parentPid'):
                    if flag in argv and argv.index(flag)+1<len(argv):item[flag.lstrip('-')]=argv[argv.index(flag)+1]
            # Do not retain a renderer that exited during this scan.
            if p.is_running() and abs(p.create_time()-item['start'])<.01:rows.append(item)
        except (process_module.NoSuchProcess,process_module.AccessDenied,ProcessLookupError):continue
    coord=Path(coordination) if coordination else None
    records={}
    for name in ('engine-request.json','engine-ack.json','capacity-wait.json'):
        if coord and (coord/name).exists():
            try:
                value=json.loads((coord/name).read_text())
                records[name]={k:v for k,v in value.items() if k!='snapshot'}
            except (OSError,ValueError):records[name]={'unreadable':True}
    lease=lease or records.get('engine-request.json')
    base=Path.home()/'.cache/gpu-slot';slots={}
    for p in sorted(base.glob('locks/*.lock')):
        try:
            with p.open('r') as f:
                try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=False
                except BlockingIOError:held=True
            slots[str(p.relative_to(base))]={'held':held}
        except OSError:slots[str(p.relative_to(base))]={'unreadable':True}
    for folder in ('holders','queue'):
        for p in sorted((base/folder).glob('*.json')):
            try:
                value=json.loads(p.read_text())
                slots[str(p.relative_to(base))]={k:value[k] for k in ('pid','start','class','label','slot','reserved_slots','state') if k in value}
            except (OSError,ValueError):slots[str(p.relative_to(base))]={'unreadable':True}
    relevant=[p for p in rows if p.get('renderer') or p.get('null_import_worker') or
        (lease and (p['pid']==lease.get('controller_pid') or p.get('pgid')==lease.get('engine_pid')))]
    return {'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host_scope':'local-machine-only',
        'processes':relevant,'slots':slots,'leases':records,'lease':lease,
        'decision':ownership(rows,list(baseline),lease) if baseline is not None else
            {'status':'observation-only','active_renderer_pids':[p['pid'] for p in rows if p.get('renderer')]},
        'shared_paused':(base/'PAUSED').exists()}
