#!/usr/bin/env python3
"""Fresh bounded local-C# recovery; preserves the expired run and existing art."""
import argparse
import json
import os
from pathlib import Path
import signal
import time

from loop_controller.core import Files, Halt, atomic, exclusive, now, read_json, sha
from loop_controller.model import tool
from loop_controller.runner import Runner, scenario_for


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--run-dir', type=Path, required=True)
    p.add_argument('--previous-run', type=Path, required=True)
    p.add_argument('--brief', type=Path, required=True)
    p.add_argument('--authorize-recovery', action='store_true')
    a = p.parse_args()
    if not a.authorize_recovery or a.run_dir.exists():
        p.error('Explicit recovery authorization and a fresh run directory are required')
    old = read_json(a.previous_run/'status.json')
    if old.get('controller_pid') or old.get('status') != 'paused-deadline':
        p.error('Expected the explicitly handed-off stopped deadline run')
    preserved = {n: sha((a.previous_run/n).read_bytes()) for n in ('status.json','state.sqlite3','STOP')}
    c = read_json(a.config)
    c.update(wall_hours=0.75, no_accepted_progress_minutes=45, max_rounds=6,
             model_timeout_seconds=600, csharp_only=True)
    os.umask(0o077)
    r = Runner(a.run_dir, c)
    s = r.store
    if (r.project/'Assets/Game/Bootstrap.cs').exists():
        raise Halt('Bootstrap already exists; diagnose exact current source instead of creating over it')
    tasks = read_json(a.previous_run/'plan.json')
    atomic(a.run_dir/'plan.json', tasks)
    atomic(a.run_dir/'private-recovery-config.json', c)
    s.set(status='recovering', controller_pid=os.getpid(), started_epoch=time.time(), started_utc=now(),
          tasks=tasks, task_index=0, previous_run=a.previous_run.name,
          recovery_goal='One local-authored Bootstrap C# file, then native compile/input/captures; no new art',
          stop_conditions={'wall_minutes':45,'initial_write_requests':2,'max_rounds':6,
                           'identical_failure_limit':c['identical_failure_limit'],'resource_guards':'unchanged'},
          prior_failure_record_sha256=preserved)
    s.event('cloud-infrastructure-intervention', action='Fresh explicitly authorized C# recovery',
            previous_run=a.previous_run.name, previous_deadline_unchanged=True,
            game_code_authorship='local Qwen', art_tools=False)
    def stop(*_):
        raise Halt('Bounded recovery stopped by deadline or explicit signal')
    signal.signal(signal.SIGALRM, stop)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    signal.alarm(45*60)
    with exclusive(a.run_dir/'controller.lock'):
        try:
            r.machine.guard()
            r.model.ready()
            files = Files(r.project,s)
            def create(action, fields):
                if fields.get('path') != 'Assets/Game/Bootstrap.cs':
                    raise ValueError('Create only Assets/Game/Bootstrap.cs for this first recovery action')
                if len(fields.get('content','').encode()) > 24000:
                    raise ValueError('Keep this first standalone Bootstrap below 24 KB')
                return files.create(action, **fields)
            prompt = (
                'Create one self-contained Assets/Game/Bootstrap.cs now, preferably under 140 lines. '
                'This is a minimal developmental Unity 6000.6.4f1 Built-in native walking scene, not the finished game. '
                'Implement public static void ChicagoGame.Bootstrap.Create(). You may include small MonoBehaviour classes in this file. '
                'Existing original prefabs load via Resources.Load<GameObject>("Generated/street/scene"), '
                '"Generated/player/scene", "Generated/coupe/scene", "Generated/props/scene". Reuse them; no new assets or art tools. '
                'Place the street, player and optional existing props sensibly, with usable collision, grounded WASD movement, '
                'a following tagged MainCamera with AudioListener, and basic readable lighting. The player must actually move '
                'through the regular control path. LoopInput.MoveX and LoopInput.MoveY are float properties; '
                'LoopInput.Held(KeyCode) and LoopInput.Pressed(KeyCode) are bool methods. These global public static APIs '
                'support both human and replay controls; their implementation is supplied externally. '
                'Set global LoopSignals.Player to the actual controlled Transform and LoopSignals.Mode="foot". '
                'LoopSignals.Health is a float. Never detect a replay, fabricate telemetry, lock the cursor on startup, '
                'write harness code, define duplicate LoopInput/LoopSignals, or download anything. '
                'Use UnityEngine and ordinary Unity APIs. Invisible primitive colliders are allowed; visible game art uses existing exports. '
                'Make exactly one create_file tool call with path and complete C# content. No architecture essay, '
                'no markdown code fences, no multi-file plan. A small saved compilable walking candidate is the goal. '
                'The controller will compile and exercise it next. Do not claim a pass in advance.'
            )
            for attempt in range(2):
                s.set(current_task='Local Qwen: save minimal Bootstrap.cs', stage='recovery-write',
                      phase='foundation', initial_write_attempt=attempt+1)
                s.report()
                result = r.model.session('builder', 'recovery-create-'+str(attempt+1),
                    'You are the local game coder. Make the one small requested tool call promptly; original game code is yours.',
                    prompt + (' Previous attempt saved no file. Reduce scope and keep the complete C# under 80 lines.' if attempt else ''),
                    [tool('create_file','Create the new Bootstrap file atomically; path/content only.',
                          {'path':{'type':'string'},'content':{'type':'string'}})],
                    {'create_file':create}, turns=1)
                target = r.project/'Assets/Game/Bootstrap.cs'
                if target.is_file():
                    commit = r.checkpoint_source('Local Qwen: bounded recovery Bootstrap')
                    s.set(source_checkpoint=commit, candidate_commit=commit)
                    s.event('recovery-file-saved', path='Assets/Game/Bootstrap.cs',
                            sha256=sha(target.read_bytes()), bytes=target.stat().st_size, candidate=commit)
                    break
                s.event('recovery-write-unsaved', attempt=attempt+1, outcome=result)
            else:
                raise Halt('Two bounded real create requests saved no Bootstrap; inspect safe finish/tool metadata')
            # Reuse the ordinary immutable native gate and critic, without another
            # builder call before exercising the just-saved candidate.
            ordinary_builder = r.builder
            def first_candidate(task, round_id, brief):
                r.builder = ordinary_builder
                return {'ok':True, 'summary':'Exercise the local-authored recovery file; acceptance remains unverified',
                        'scenario':scenario_for('foundation')}
            r.builder = first_candidate
            r.run(a.brief.read_text())
        except Exception as error:
            s.set(status='paused', blocker=type(error).__name__+': '+str(error)[:2500])
            s.event('stopped',error_type=type(error).__name__,message=str(error)[:2500])
        finally:
            signal.alarm(0)
            unchanged = all(sha((a.previous_run/n).read_bytes())==h for n,h in preserved.items())
            s.set(controller_pid=None, previous_failure_record_unchanged=unchanged)
            s.report()
    return 0 if s.get('status')=='reviewable-delivery' else 2


if __name__ == '__main__':
    raise SystemExit(main())
