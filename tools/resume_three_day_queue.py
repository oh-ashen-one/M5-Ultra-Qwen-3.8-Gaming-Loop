#!/usr/bin/env python3
"""Resume the existing sole queue under the owner's fixed three-day project cap."""
import argparse
import os
from pathlib import Path
import signal
import sqlite3
import time
import uuid
from continue_game_queue import review_captures
from resume_mission_focus import MissionFocus
from resume_mission_review import verified_probe
from loop_controller.core import Halt, atomic, exclusive, now, read_json
from loop_controller.delivery_policy import HARD_CAP_EPOCH, HARD_CAP_UTC, apply_authorized_cap, deadline_guard, preserve_closeout, queue_milestone
from loop_controller.runner import git


class ThreeDayRunner(MissionFocus):
    def validate_recovery(self,old):
        if not old.get('blocker','').startswith('Halt: Replay-only role supplied no valid finish_task'):
            raise Halt('Preserve other faults and unchanged-failure retry protections')
        if old['task_index']!=2:
            raise Halt('Expected the preserved mission replay stop')

    def recovery_settings(self):
        return {'three_day_recovery_probe_pending':True}

    def edit(self,task,ident):
        if self.store.get('three_day_recovery_probe_pending'):
            for label,needle,instruction in [
                ('hud-readable-size','tm.characterSize =','Increase only the TextMesh character size to0.012; preserve actual mission-stage text.'),
                ('hud-card-alignment','card.transform.localPosition =','Put the backing just behind and below the text origin at local X0,Y-0.06,Z0.025. Preserve the text and gameplay.'),
                ('hud-card-compact','card.transform.localScale =','Set the backing size to width1.5,height0.20,thickness0.01 so it closely backs the three short HUD lines.')]:
                self.line_edit(ident,label,needle,instruction)
            probe,evidence=verified_probe(self.store.root,task)
            self.store.set(three_day_recovery_probe_pending=False,last_valid_replay=probe)
            self.store.event('reuse-native-passing-mission-probe',prior_evidence=evidence,
                             current_source_requires_requalification=True)
            return {'ok':True,'scenario':probe}
        return super().edit(task,ident)

    def native(self,task,ident,candidate,probe):
        bundle,gate=super().native(task,ident,candidate,probe)
        if gate.get('passed') and 'regression' not in ident:
            frames,times=review_captures(task,bundle)
            queue_milestone(self.store,'native-milestone',task,bundle,gate,frames,times)
        return bundle,gate

    def review(self,task,ident,bundle,gate):
        result=super().review(task,ident,bundle,gate)
        frames,times=review_captures(task,bundle)
        queue_milestone(self.store,'native-milestone',task,bundle,gate,frames,times,result)
        return result

    def promote(self,task,candidate,bundle,gate,review):
        super().promote(task,candidate,bundle,gate,review)
        frames,times=review_captures(task,bundle)
        queue_milestone(self.store,'accepted-feature',task,bundle,gate,frames,times,review)
        self.store.report()

    def reject_scoped(self,task,ident,feedback,candidate):
        bundle=self.store.root/'evidence'/ident
        queued=self.store.root/'milestones/outbox'/(ident+'--native-milestone.json')
        if queued.exists() and 'build_id' in feedback:
            frames,times=review_captures(task,bundle)
            queue_milestone(self.store,'native-milestone',task,bundle,feedback,frames,times)
        return super().reject_scoped(task,ident,feedback,candidate)


def main(runner_type=ThreeDayRunner):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--authorize-three-day-cap',action='store_true')
    a=p.parse_args();os.umask(0o077)
    if not a.authorize_three_day_cap:p.error('Owner-authorized three-day cap required')
    c=read_json(a.run_dir/'private-config.json')
    with exclusive(Path(c['coordination_dir'])/'game-owner.lock'),exclusive(a.run_dir/'controller.lock'):
        r=runner_type(a.run_dir,c);s=r.store;old=s.status()
        if old.get('controller_pid') or old.get('owned_process') or old.get('status')!='paused':
            raise Halt('Preserve the current owner; this migration requires a stopped controller')
        r.validate_recovery(old)
        if git(r.repo,'rev-parse','HEAD')!=old['source_checkpoint'] or git(r.repo,'status','--porcelain'):
            raise Halt('Expected the preserved checkpoint and clean local source')
        if (a.run_dir/'STOP').exists():raise Halt('Preserve an independent stop request')
        r.model.ready()
        archive=a.run_dir/'policy-migrations'/uuid.uuid4().hex;archive.mkdir(parents=True)
        with sqlite3.connect(archive/'state.sqlite3') as saved:s.db.backup(saved)
        atomic(archive/'status.json',old);atomic(archive/'private-config.json',c)
        apply_authorized_cap(s,c)
        original=r.machine.guard
        def guard():deadline_guard(s);original()
        def stop(signum,_):
            raise Halt('Three-day project cap reached' if signum==signal.SIGALRM else 'Explicit controller stop')
        r.machine.guard=guard;r.model.guard=guard
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop)
        signal.setitimer(signal.ITIMER_REAL,max(.001,HARD_CAP_EPOCH-time.time()))
        s.set(status='running',controller_pid=os.getpid(),blocker=None,**r.recovery_settings(),
              cap_resume_utc=now(),alarm_deadline_utc=HARD_CAP_UTC)
        s.event('three-day-queue-resumed',archive=str(archive.relative_to(a.run_dir)),
                preserved_failure_streak=old.get('failure_streak'),preserved_task_failures=old.get('task_failures'))
        s.report();reason='Queue reached reviewable delivery'
        try:r.work()
        except Exception as error:
            reason=type(error).__name__+': '+str(error)
            reached=time.time()>=HARD_CAP_EPOCH or 'Three-day project cap reached' in str(error)
            s.set(status='deadline-complete' if reached else 'paused',blocker=reason)
            s.event('stopped',error_type=type(error).__name__,message=str(error))
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            try:
                source=r.checkpoint_source('Preserve local source at three-day queue closeout')
                s.set(source_checkpoint=source)
            except Exception as error:
                s.set(checkpoint_save_error=type(error).__name__+': '+str(error))
                reason+='; latest working files preserved but checkpoint save failed: '+str(error)
            s.set(controller_pid=None)
            preserve_closeout(r,reason,s.get('status')=='deadline-complete' or time.time()>=HARD_CAP_EPOCH)
            s.report()
    return 0


if __name__=='__main__':raise SystemExit(main())
