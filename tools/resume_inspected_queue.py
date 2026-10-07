#!/usr/bin/env python3
"""Resume the same continuous queue after an explicitly completed user inspection."""
import argparse
import os
from pathlib import Path
import signal
import sqlite3
import time
import uuid

from continue_game_queue import ContinuousRunner
from loop_controller.core import Halt, atomic, exclusive, now, read_json
from loop_controller.runner import git


def validate_resume(state, source, dirty, stop_text, pending, epoch):
    if state.get('status') != 'paused' or state.get('controller_pid') or state.get('owned_process'):
        raise Halt('Expected a stopped sole controller with no owned engine')
    if 'User requested live Unity GUI inspection' not in stop_text:
        raise Halt('Resume is scoped to the recorded user inspection pause')
    if source != state.get('source_checkpoint') or dirty:
        raise Halt('Preserve unexpected source changes before resuming')
    if epoch >= state['overall_deadline_epoch']:
        raise Halt('Original overall ceiling expired')
    if any(a['kind'] != 'model-request' for a in pending):
        raise Halt('Pending mutation or engine action needs evidence reconciliation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--authorize-resume', action='store_true')
    args = parser.parse_args()
    if not args.authorize_resume:
        parser.error('Explicit owner authorization is required')
    os.umask(0o077)
    config = read_json(args.run_dir / 'private-config.json')
    coordination = Path(config['coordination_dir'])
    with exclusive(coordination / 'game-owner.lock'), exclusive(args.run_dir / 'controller.lock'):
        if (coordination / 'engine-request.json').exists() or (coordination / 'engine-ack.json').exists():
            raise Halt('Inspection handoff has not fully ended')
        runner = ContinuousRunner(args.run_dir, config)
        store = runner.store
        state = store.status()
        stop = args.run_dir / 'STOP'
        validate_resume(state, git(runner.repo, 'rev-parse', 'HEAD'),
                        git(runner.repo, 'status', '--porcelain'),
                        stop.read_text() if stop.exists() else '', store.incomplete(), time.time())
        runner.model.ready()
        archive = args.run_dir / 'inspection-pauses' / uuid.uuid4().hex
        archive.mkdir(parents=True)
        with sqlite3.connect(archive / 'state.sqlite3') as saved:
            store.db.backup(saved)
        atomic(archive / 'status.json', state)
        stop.rename(archive / 'STOP')
        deadline = state['overall_deadline_epoch']
        original_guard = runner.machine.guard

        def guard():
            original_guard()
            if time.time() >= deadline:
                raise Halt('Original overall ceiling reached')

        def halt(*_):
            raise Halt('Original overall deadline or explicit stop')

        runner.machine.guard = guard
        runner.model.guard = guard
        for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, halt)
        signal.alarm(max(1, int(deadline - time.time())))
        store.set(status='running', controller_pid=os.getpid(), blocker=None,
                  controller_started_utc=now(), inspection_resume_utc=now())
        store.event('authorized-inspection-resume', archive=str(archive.relative_to(args.run_dir)),
                    original_ceiling_unchanged=True, game_author='local Qwen',
                    source=state['source_checkpoint'], queue_index=state['task_index'])
        store.report()
        try:
            # Preserve interrupted role evidence; fresh IDs prevent replaying its unfinished request.
            runner.recover()
            runner.work()
        except Exception as error:
            store.set(status='paused', blocker=type(error).__name__ + ': ' + str(error))
            store.event('stopped', error_type=type(error).__name__, message=str(error))
        finally:
            signal.alarm(0)
            source = runner.checkpoint_source('Preserve local queue candidate after inspection resume')
            store.set(controller_pid=None, source_checkpoint=source)
            store.report()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
