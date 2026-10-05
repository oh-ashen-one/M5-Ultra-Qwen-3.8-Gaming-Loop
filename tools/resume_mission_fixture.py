#!/usr/bin/env python3
"""Resume saved mission edits by submitting the supplied native test fixture once."""
import argparse
import json
import os
from pathlib import Path
import signal
import sqlite3
import time
import uuid

from continue_game_queue import ContinuousRunner
from loop_controller.core import Halt, atomic, exclusive, now, read_json
from loop_controller.replay_contract import MISSION_EXAMPLE, finish_tool, validate_submission
from loop_controller.runner import git


class FixtureResume(ContinuousRunner):
    def edit(self, task, ident):
        if not self.store.get('provided_fixture_pending'):
            return super().edit(task, ident)
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='submit-provided-replay');self.store.report()
        result=self.model.session('replay-author',ident+'-provided-fixture',
            'This is a JSON serialization task. Immediately call finish_task by copying the provided object exactly. '
            'Do not analyze gameplay, calculate timings, plan, read files or change any value. The controller runs the real test.',
            'The provided fixture is structurally validated but gameplay success is UNKNOWN. Submit it unchanged. '
            'Do not try to prove or optimize it. Exact finish_task arguments:\n'+json.dumps(MISSION_EXAMPLE),
            [finish_tool()],{'finish_task':lambda _,f:validate_submission(f,task)},turns=2,reasoning_effort='low')
        if not result.get('scenario'):raise Halt('Provided fixture was not submitted; preserve the saved gameplay edits')
        self.store.set(provided_fixture_pending=False,last_valid_replay=result['scenario'])
        self.store.event('replay-preflight-passed',source='supplied infrastructure fixture submitted by local Qwen',
                         required_fields=['summary','duration','input_steps','captures'],gameplay_success='unverified')
        return result


def main(runner_class=FixtureResume):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--authorize-recovery',action='store_true')
    args=parser.parse_args();os.umask(0o077)
    if not args.authorize_recovery:parser.error('Explicit ongoing mission recovery authorization required')
    config=read_json(args.run_dir/'private-config.json')
    with exclusive(Path(config['coordination_dir'])/'game-owner.lock'),exclusive(args.run_dir/'controller.lock'):
        runner=runner_class(args.run_dir,config);store=runner.store;state=store.status()
        if (state.get('controller_pid') or state.get('owned_process') or state['status']!='paused'
                or not state.get('mission_selected_repairs_done') or state['task_index']!=2
                or not state.get('blocker','').startswith(getattr(runner,'recovery_prefixes',
                    ('Halt: Replay-only role supplied no valid finish_task',)))):
            raise Halt('Expected only the evidenced post-edit replay output-limit stop')
        if git(runner.repo,'rev-parse','HEAD')!=state['source_checkpoint'] or git(runner.repo,'status','--porcelain'):
            raise Halt('Source changed; preserve it')
        deadline=state['overall_deadline_epoch']
        if time.time()>=deadline:raise Halt('Original overall ceiling expired')
        runner.model.ready()
        archive=args.run_dir/'replay-stops'/uuid.uuid4().hex;archive.mkdir(parents=True)
        with sqlite3.connect(archive/'state.sqlite3') as saved:store.db.backup(saved)
        atomic(archive/'status.json',state)
        original=runner.machine.guard
        def guard():
            original()
            if time.time()>=deadline:raise Halt('Original overall ceiling reached')
        def stop(*_):raise Halt('Original overall deadline or explicit stop')
        runner.machine.guard=guard;runner.model.guard=guard
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop)
        signal.alarm(max(1,int(deadline-time.time())))
        store.set(status='running',controller_pid=os.getpid(),blocker=None,provided_fixture_pending=True,
                  fixture_resume_utc=now())
        store.event('replay-output-limit-recovery',previous_stop=str(archive.relative_to(args.run_dir)),
                    cause=state.get('blocker'),change=getattr(runner,'recovery_description','Serialization-only provided fixture'),
                    game_edits_preserved=state['source_checkpoint'],deadline_unchanged=True)
        store.report()
        try:runner.work()
        except Exception as error:
            store.set(status='paused',blocker=type(error).__name__+': '+str(error))
            store.event('stopped',error_type=type(error).__name__,message=str(error))
        finally:
            signal.alarm(0);source=runner.checkpoint_source('Preserve local mission fixture continuation candidate')
            store.set(controller_pid=None,source_checkpoint=source);store.report()
    return 0


if __name__=='__main__':raise SystemExit(main())
