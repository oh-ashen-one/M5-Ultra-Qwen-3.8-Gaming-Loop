#!/usr/bin/env python3
"""Continue the existing authorized recovery without resetting its hard deadline."""
import argparse
import os
from pathlib import Path
import signal
import time

from loop_controller.core import Halt, exclusive, now, read_json
from loop_controller.runner import Runner


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--brief',type=Path,required=True)
    p.add_argument('--authorize-recovery',action='store_true')
    a=p.parse_args()
    if not a.authorize_recovery or not (a.run_dir/'state.sqlite3').exists():
        p.error('Explicit recovery authorization and the existing ledger are required')
    os.umask(0o077)
    c=read_json(a.run_dir/'private-recovery-config.json')
    r=Runner(a.run_dir,c);s=r.store
    if s.get('controller_pid') or s.get('status')!='paused':
        raise Halt('Expected this stopped recovery, never another active owner')
    deadline=s.get('original_recovery_deadline_epoch',s.get('started_epoch')+45*60)
    remaining=int(deadline-time.time())
    if remaining<=0: raise Halt('Existing recovery deadline expired; no extension')
    def stop(*_): raise Halt('Original recovery deadline or explicit stop reached')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    signal.alarm(remaining)
    with exclusive(a.run_dir/'controller.lock'):
        s.set(controller_pid=os.getpid(),controller_started_utc=now())
        s.event('cloud-infrastructure-intervention',action='Resume normal local editing after saved native candidate',
                output_tokens=c['output_tokens'],deadline_unchanged=True,art_tools=False,
                game_code_authorship='local Qwen')
        try:
            r.run(a.brief.read_text()+'\n\nIMMEDIATE RECOVERY PRIORITY: fix the evidenced player fall and '
                  'imported visual/controller scale/orientation using existing assets. Establish a grounded, upright '
                  'walking candidate before new features or polish. Inspect exact source, make a small edit, then '
                  'finish_task for native verification. No new art. Full prior game goals remain unaccepted.')
        except Exception as error:
            s.set(status='paused',blocker=type(error).__name__+': '+str(error)[:2500])
            s.event('stopped',error_type=type(error).__name__,message=str(error)[:2500])
        finally:
            signal.alarm(0)
            s.set(controller_pid=None);s.report()
    return 0 if s.get('status')=='reviewable-delivery' else 2


if __name__=='__main__': raise SystemExit(main())
