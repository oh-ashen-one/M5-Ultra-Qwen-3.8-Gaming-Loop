"""Bounded yielding within the existing locked game owner; no extra driver."""
from pathlib import Path
import time
import uuid
from .core import Halt,atomic,now,read_json
from .model import MODEL

def wait_until_admitted(store,guard,probe,label,sleeper=time.sleep):
    """Every recheck preserves STOP, resource faults and the owner's deadline."""
    waiting=False
    while True:
        guard()
        observation=probe()
        if observation['available']:
            if waiting:store.event('capacity-admission-restored',resume_stage=label)
            store.set(status='running',stage=label,blocker=None,capacity_resume_stage=None,
                capacity_check_utc=now(),capacity_wait_observation=observation)
            store.report();return
        if not waiting:store.event('capacity-yield',resume_stage=label)
        waiting=True
        store.set(status='capacity-wait',stage='capacity-wait',capacity_resume_stage=label,
            blocker='Capacity wait: preserve other workloads; same owner rechecks in30seconds',
            capacity_check_utc=now(),capacity_recheck_seconds=30,capacity_wait_observation=observation)
        store.report();sleeper(30)

class CapacityContinuation:
    """Attach only to the current queue; preserve resident and foreign processes."""
    def __init__(self,runner):self.r=runner

    def probe(self):
        r=self.r
        if r.machine.child is not None or r.store.get('owned_process'):
            raise Halt('Capacity wait requires the owned engine to finish cleanup')
        observed=r.machine.snapshot();reasons=[]
        coordination=Path(r.c['coordination_dir'])
        if (coordination/'capacity-wait.json').exists():reasons.append('resident-admission-yielded')
        if len(observed['decision']['active_renderer_pids'])>1 and not r.c.get('authorized_shared_coexistence',False):
            reasons.append('renderer-capacity')
        if (coordination/'engine-request.json').exists() or (coordination/'engine-ack.json').exists():
            reasons.append('engine-handoff-active')
        health=r.model.api('/health');status=r.model.api('/api/status')
        if health.get('status')!='healthy' or health.get('engine_pool',{}).get('loaded_count')!=1:
            raise Halt('Resident unavailable while yielded; preserve source and diagnose, no runtime restart')
        if status.get('default_model')!=MODEL:raise Halt('Resident model identity changed while yielded')
        if status.get('active_requests',0) or status.get('waiting_requests',0):
            raise Halt('Another request owns the resident; no inference takeover')
        return dict(available=not reasons,reasons=reasons,snapshot=observed)

    def wait(self,label):
        wait_until_admitted(self.r.store,self.r.machine.guard,self.probe,label)

    def unity(self,original,project,bundle,scenario,candidate):
        r=self.r;bundle=Path(bundle);attempts=0
        resume_stage=r.store.get('capacity_resume_stage') or r.store.get('stage','native-qualification')
        while True:
            self.wait(resume_stage)
            try:return original(project,bundle,scenario,candidate)
            except Halt as error:
                capacity=str(error).startswith('Capacity wait:') or str(error)=='No room for one owned engine beside the existing renderer'
                if not capacity:raise
                if r.machine.child is not None or r.store.get('owned_process'):
                    raise Halt('Preserve interrupted engine until owned cleanup is confirmed') from error
                if (bundle/'gate.json').exists() or (bundle/'captures/manifest.json').exists():
                    raise Halt('Completed or sealed evidence requires explicit reconciliation; never replace it') from error
                attempts+=1
                if attempts>3:raise Halt('Repeated capacity interruption of one native case; preserve artifacts for diagnosis') from error
                if bundle.exists():
                    archive=r.store.root/'capacity-interruptions'/(bundle.name+'-'+uuid.uuid4().hex)
                    archive.parent.mkdir(parents=True,exist_ok=True);bundle.rename(archive)
                    atomic(archive/'capacity-interruption.json',dict(reason=str(error),candidate=candidate,
                        original_bundle=bundle.name,retry=attempts,original_files_preserved=True))
                    r.store.event('native-capacity-interruption-preserved',archive=str(archive.relative_to(r.store.root)),candidate=candidate)

    def session(self,original,*args,**kwargs):
        self.wait(self.r.store.get('stage','fresh-local-review'))
        # Never retry an interrupted inference response or restart its service.
        return original(*args,**kwargs)
