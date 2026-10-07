#!/usr/bin/env python3
"""One real local-model create call in a fresh isolated fixture, never game code."""
import argparse
import json
import os
from pathlib import Path
import time

from loop_controller.adapters import Machine
from loop_controller.core import Files, Store, atomic, now, read_json, sha
from loop_controller.model import LocalModel, tool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--authorize-live-check', action='store_true')
    args = parser.parse_args()
    if not args.authorize_live_check or args.run_dir.exists():
        parser.error('Explicit live-check authorization and a fresh fixture directory are required')
    os.umask(0o077)
    store = Store(args.run_dir)
    store.set(started_epoch=time.time(), started_utc=now(), status='qualifying-create')
    config = read_json(args.config)
    config.update(output_tokens=2048, model_timeout_seconds=150, wall_hours=0.1)
    machine = Machine(config, store)
    model = LocalModel(config, store, machine.guard)
    files = Files(args.run_dir/'fixture', store)
    receipt = {'started_utc': now(), 'scope': 'isolated tool fixture; not game implementation',
               'authorship': 'local Qwen', 'output_tokens': 2048, 'requests_max': 1}
    def create(action, fields):
        if fields.get('path') != 'Notes/create-tool-check.md':
            raise ValueError('Only the fixed diagnostic note path is admitted')
        return files.create(action, **fields)
    try:
        result = model.session('tool-qualification', 'create-only-check',
            'You are testing a file tool. Make exactly one tiny create_file call now. Do not plan a game or explain.',
            'Create Notes/create-tool-check.md containing a single short sentence in your own words confirming '
            'that this is an isolated file-tool check. Use create_file with path and content only.',
            [tool('create_file', 'Atomically create a new file; path and content only, no hash.',
                  {'path': {'type': 'string'}, 'content': {'type': 'string'}})],
            {'create_file': create}, turns=1)
        receipt['session_outcome'] = result
    except Exception as error:
        receipt['error'] = type(error).__name__+': '+str(error)[:1600]
    receipt['actions'] = [dict(id=a, kind=k, status=s, result=json.loads(r) if r else None)
        for a,k,s,r in store.db.execute('SELECT id,kind,status,result FROM actions ORDER BY rowid')]
    target = args.run_dir/'fixture/Notes/create-tool-check.md'
    receipt['saved_file'] = {'path': 'fixture/Notes/create-tool-check.md', 'bytes': target.stat().st_size,
                             'sha256': sha(target.read_bytes())} if target.is_file() else None
    receipt['passed'] = bool(receipt['saved_file']) and any(
        a['kind']=='source-create' and (a['result'] or {}).get('ok') for a in receipt['actions'])
    receipt['finished_utc'] = now()
    atomic(args.run_dir/'receipt.json', receipt)
    store.set(status='qualified' if receipt['passed'] else 'failed', controller_pid=None)
    store.report()
    print(json.dumps(receipt, indent=2), flush=True)
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
