#!/usr/bin/env python3
"""Three small local C# writes after the recorded two-request recovery failure.

Keeps that recovery's original wall deadline and immutable failure history.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import time

from loop_controller.core import Files, Halt, exclusive, now, read_json, sha
from loop_controller.model import tool
from loop_controller.runner import Runner, scenario_for


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--previous-run',type=Path,required=True)
    p.add_argument('--brief',type=Path,required=True)
    p.add_argument('--authorize-micro-recovery',action='store_true')
    a=p.parse_args()
    if not a.authorize_micro_recovery or not (a.run_dir/'state.sqlite3').is_file():
        p.error('Explicit recovery authorization and the existing bounded ledger are required')
    os.umask(0o077)
    c=read_json(a.run_dir/'private-recovery-config.json')
    r=Runner(a.run_dir,c);s=r.store
    if s.get('controller_pid') or s.get('status')!='paused' or s.get('micro_recovery_started_utc'):
        raise Halt('Expected this stopped recovery; do not duplicate or replay microsteps')
    if not str(s.get('blocker','')).startswith('Halt: Two bounded real create requests saved no Bootstrap'):
        raise Halt('This correction applies only to the evidenced two-create failure')
    deadline=s.get('started_epoch')+45*60
    remaining=int(deadline-time.time())
    if remaining<=0: raise Halt('Original recovery deadline has expired')
    preserved=s.get('prior_failure_record_sha256')
    if not all(sha((a.previous_run/n).read_bytes())==h for n,h in preserved.items()):
        raise Halt('Original failure record changed; diagnose before continuing')
    files=Files(r.project,s);target='Assets/Game/Bootstrap.cs'
    if (r.project/target).exists(): raise Halt('A Bootstrap already exists; do not overwrite with a seed')
    def stop(*_): raise Halt('Original recovery deadline or explicit stop reached')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    signal.alarm(remaining)
    with exclusive(a.run_dir/'controller.lock'):
        s.set(controller_pid=os.getpid(),status='recovering',blocker=None,micro_recovery_started_utc=now(),
              micro_request_limit=3,original_recovery_deadline_epoch=deadline)
        s.event('cloud-infrastructure-intervention',action='Decompose capped Bootstrap request into three small local writes',
                previous_requests_preserved=True,deadline_unchanged=True,game_code_authorship='local Qwen')
        try:
            r.model.ready()
            instructions=[
                'Create a valid C# file with namespace ChicagoGame, public static class Bootstrap, and '
                'an empty public static void Create() method. At most ten lines. No gameplay yet. '
                'Call create_file now with path Assets/Game/Bootstrap.cs and the complete small file content.',
                'Extend this C# file into a tiny Unity startup scene. In Bootstrap.Create instantiate the existing '
                'Resources prefabs Generated/street/scene and Generated/player/scene. Register the actual player '
                'transform in global LoopSignals.Player and set LoopSignals.Mode to foot. Add a tagged MainCamera '
                'with AudioListener and a directional light. Use existing meshes as visible art; invisible primitive '
                'colliders are allowed. No movement yet, no new art or features. Keep the complete file under 65 lines. '
                'Call edit_bootstrap with the complete replacement file now.',
                'Add minimal real WASD walking with CharacterController, gravity and collision, and a following '
                'camera to this existing scene. Global LoopInput.MoveX and MoveY are float properties for human '
                'and replay input; use them without defining the API or detecting replay. Keep LoopSignals.Player '
                'registered to the actual moving transform. Add ground collision if necessary without new visible '
                'art. Keep the complete file under 120 lines; small MonoBehaviour classes in this file are allowed. '
                'No driving, combat, mission, cursor lock, new assets or extra polish yet. This is Unity 6000.6.4f1 '
                'Built-in. Call edit_bootstrap with the complete replacement file now.'
            ]
            for i,instruction in enumerate(instructions):
                r.machine.guard()
                before=(r.project/target).read_bytes() if i else None
                c.update(output_tokens=2048 if i==0 else 4096,model_timeout_seconds=180)
                s.set(stage='micro-write',current_task='Local Qwen microstep '+str(i+1),micro_step=i+1)
                s.report()
                if i==0:
                    def dispatch(action,fields):
                        if fields.get('path')!=target: raise ValueError('Only the Bootstrap path is admitted')
                        return files.create(action,**fields)
                    tools=[tool('create_file','Create the new C# file using only path and content.',
                                {'path':{'type':'string'},'content':{'type':'string'}})]
                    handlers={'create_file':dispatch}
                    prompt=instruction
                else:
                    expected=sha(before)
                    def dispatch(action,fields):
                        # The exact read hash is enforced by the controller; the
                        # model need not transcribe it. Concurrent edits still fail.
                        return files.edit(action,target,expected,content=fields['content'])
                    tools=[tool('edit_bootstrap','Replace only the supplied Bootstrap file; controller enforces its exact read hash.',
                                {'content':{'type':'string'}})]
                    handlers={'edit_bootstrap':dispatch}
                    prompt=instruction+'\nCurrent complete file:\n'+before.decode()
                result=r.model.session('builder','micro-'+str(i+1),
                    'Perform exactly the one tiny C# edit requested. Your next response is one tool call. '
                    'Do not explain, plan, expand scope or write markdown. The external controller tests afterward.',
                    prompt,tools,handlers,turns=1)
                path=r.project/target
                if not path.is_file() or (before is not None and path.read_bytes()==before):
                    raise Halt('Microstep '+str(i+1)+' saved no changed file; stop and inspect finish/tool metadata')
                commit=r.checkpoint_source('Local Qwen: focused Bootstrap microstep '+str(i+1))
                s.set(source_checkpoint=commit,candidate_commit=commit)
                s.event('recovery-file-saved',path=target,sha256=sha(path.read_bytes()),bytes=path.stat().st_size,
                        candidate=commit,micro_step=i+1)
                s.report()
            c.update(output_tokens=16384,model_timeout_seconds=600)
            ordinary=r.builder
            def first_candidate(task,round_id,brief):
                r.builder=ordinary
                return {'ok':True,'scenario':scenario_for('foundation'),'summary':'Exercise local microstep candidate'}
            r.builder=first_candidate
            r.run(a.brief.read_text())
        except Exception as error:
            s.set(status='paused',blocker=type(error).__name__+': '+str(error)[:2500])
            s.event('stopped',error_type=type(error).__name__,message=str(error)[:2500])
        finally:
            signal.alarm(0)
            s.set(controller_pid=None,previous_failure_record_unchanged=all(
                sha((a.previous_run/n).read_bytes())==h for n,h in preserved.items()))
            s.report()
    return 0 if s.get('status')=='reviewable-delivery' else 2


if __name__=='__main__': raise SystemExit(main())
