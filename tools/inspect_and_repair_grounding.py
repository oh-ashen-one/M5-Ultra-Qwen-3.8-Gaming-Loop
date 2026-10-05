#!/usr/bin/env python3
"""Observe world transforms, ask local Qwen for one correction, verify stationary grounding."""
import argparse
import json
import os
from pathlib import Path
import signal
import time
from loop_controller.core import Files,Halt,atomic,exclusive,now,read_json,sha
from loop_controller.model import tool
from loop_controller.runner import Runner,scenario_for

def summarize(bundle):
    rows=[json.loads(l) for l in (bundle/'captures/trace.jsonl').read_text().splitlines()]
    idle=[r for r in rows if .5<=r['time']<1.8 and not r.get('keys')]
    objects=read_json(bundle/'captures/scene-transforms.json')['objects']
    streets=[o for o in objects if o['kind']=='renderer' and o['name'].startswith('Street/')]
    colliders=[o for o in objects if o['kind']!='renderer']
    selected=sorted(streets,key=lambda o:o['boundsSize'][0]*o['boundsSize'][2],reverse=True)[:4]
    result={'stationary_samples':len(idle),'stationary_first':idle[0] if idle else None,
            'stationary_last':idle[-1] if idle else None,'colliders':colliders,'largest_street_renderers':selected}
    result['stationary_grounded']=bool(len(idle)>=6 and all(r.get('hasController') for r in idle)
        and sum(bool(r.get('grounded')) for r in idle)/len(idle)>=.8
        and max(r['player'][1] for r in idle)-min(r['player'][1] for r in idle)<.15
        and all(abs(v-1)<.02 for r in idle for v in r.get('playerScale',[]))
        and all(r.get('playerUp',[0,0,0])[1]>.99 for r in idle))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--brief',type=Path,required=True);p.add_argument('--authorize-recovery',action='store_true');a=p.parse_args()
    if not a.authorize_recovery:p.error('Explicit existing-run recovery authorization required')
    os.umask(0o077);c=read_json(a.run_dir/'private-recovery-config.json');r=Runner(a.run_dir,c);s=r.store
    if s.get('controller_pid') or s.get('status')!='paused' or s.get('transform_probe_started_utc'):
        raise Halt('Expected this paused sole-owner recovery; never duplicate inspection')
    remaining=int(s.get('original_recovery_deadline_epoch')-time.time())
    if remaining<=0:raise Halt('Original deadline expired')
    def stop(*_):raise Halt('Original recovery deadline or explicit stop reached')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);signal.alarm(remaining)
    with exclusive(a.run_dir/'controller.lock'):
        s.set(controller_pid=os.getpid(),status='running',stage='transform-probe',transform_probe_started_utc=now())
        s.event('cloud-infrastructure-intervention',action='Parent-requested read-only world transform probe and local correction',deadline_unchanged=True)
        try:
            r.recover();s.set(stage='transform-probe');s.report()
            candidate=r.checkpoint_source('Preserve local source before world-transform inspection')
            before=a.run_dir/'evidence/transform-probe-before'
            gate=r.engines.unity(r.project,before,scenario_for('foundation'),candidate)
            if gate.get('compile_errors') or not (before/'captures/scene-transforms.json').exists():raise Halt('Native transform inspection did not complete')
            observed=summarize(before);atomic(before/'world-observations.json',observed)
            files=Files(r.project,s);path='Assets/Game/Bootstrap.cs';source=files.read(path,line_count=300);expected=source['sha256']
            c.update(output_tokens=8192,model_timeout_seconds=min(300,int(s.get('original_recovery_deadline_epoch')-time.time())))
            s.set(stage='local-grounding-repair',current_task='Inspect measured world transforms, correct grounding, frame existing street');s.report()
            prompt=('Review these actual runtime world-space observations. Imported transforms are a hypothesis, not a presumed cause. '
                'Fix this one existing C# file: unit-scale upright physics root, imported player mesh as visual child, independently '
                'positioned world-meter ground collision at the visible street surface, and verified spawn height. No new art. '
                'First establish stationary grounding before WASD; then frame the existing street clearly with the camera. '
                'Do not fabricate telemetry or weaken tests. Make one compact complete-file edit now.\nOBSERVATIONS:\n'
                +json.dumps(observed)+'\nEXACT CURRENT SOURCE:\n'+source['content'])
            def edit(action,f):return files.edit(action,path,expected,content=f['content'])
            r.model.session('builder','measured-grounding-1','You are the local game coder. Inspect actual measurements; next response is one focused C# tool edit.',
                prompt,[tool('edit_bootstrap','Replace the supplied file; exact original hash is enforced by the controller.',{'content':{'type':'string'}})],{'edit_bootstrap':edit},turns=1)
            if sha((r.project/path).read_bytes())==expected:raise Halt('Measured grounding request saved no change; inspect finish/tool metadata')
            candidate=r.checkpoint_source('Local Qwen: repair measured grounding and street framing')
            after=a.run_dir/'evidence/transform-probe-after';gate=r.engines.unity(r.project,after,scenario_for('foundation'),candidate)
            observed=summarize(after) if (after/'captures/scene-transforms.json').exists() else {'stationary_grounded':False}
            atomic(after/'world-observations.json',observed)
            gate['stationary_grounded']=observed['stationary_grounded']
            if not observed['stationary_grounded']:
                gate['passed']=False;gate['failure']=(gate.get('failure') if isinstance(gate.get('failure'),list) else [])+['stationary-grounding-preflight']
            atomic(after/'grounding-gate.json',gate)
            s.set(source_checkpoint=candidate,candidate_commit=candidate,latest_evidence=str(after.relative_to(a.run_dir)),
                latest_captures=[str(x.relative_to(a.run_dir)) for x in sorted((after/'captures').glob('frame-*.png'))],feedback=gate,stage='rejected')
            s.report()
            c.update(output_tokens=16384,model_timeout_seconds=600)
            r.run(a.brief.read_text()+'\nPrioritize grounded walking and camera framing of the existing street. No new art; inspect latest measured grounding observations.')
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:signal.alarm(0);s.set(controller_pid=None);s.report()
    return 0
if __name__=='__main__':raise SystemExit(main())
