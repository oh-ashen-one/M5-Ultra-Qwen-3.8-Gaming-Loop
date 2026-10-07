#!/usr/bin/env python3
"""Recover the measured entry blocker with one local selected-span edit, then continue."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import time

from continue_game_queue import ContinuousRunner
from loop_controller.core import Files,Halt,atomic,exclusive,now,read_json,sha
from loop_controller.continuous_checks import MOTOR_PROBE
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

PHYSICAL_SOURCE='8c3250ee2238aa324c4348c093fd01343ff4957a'
ENTRY_ANCHOR='if (e && Vector3.Distance(_player.transform.position, transform.position) < 2.5f)'


class EntryRecovery(ContinuousRunner):
    def edit(self,task,ident):
        if self.store.get('entry_selected_edit_saved') or task['id']!='vehicle-collision-reset':
            return super().edit(task,ident)
        files=Files(self.project,self.store);path='Assets/Game/VehicleInteraction.cs'
        lines=files.path(path).read_text().splitlines(keepends=True)
        matches=[i for i,line in enumerate(lines) if ENTRY_ANCHOR in line]
        if len(matches)!=1:raise Halt('Expected one unchanged measured entry predicate')
        selected=SelectedEdit(files,path,matches[0]+1,matches[0]+1,max_lines=3)
        self.c.update(output_tokens=8192,model_timeout_seconds=300)
        self.store.set(stage='selected-entry-repair');self.store.report()
        prompt=('Save ONE replacement for the exact entry-condition line below. Preserve all other code. '
            'Measured blocker: the player is stopped at the physical rear of a4.5m-long car,2.608m from its root. '
            'The current2.5m ROOT-distance gate rejects E, so later W occurs on foot. Correct ordinary near-car '
            'interaction to use distance to the actual vehicle BoxCollider surface via its closest point, with '
            'a reasonable short interaction reach. A BoxCollider already exists on this component GameObject. '
            'Keep the E-press condition and existing Enter() call. Do not add fields, helpers, new methods or '
            'rewrite physics/reset/camera. No replay/timing logic or fake signals. Your next response must be '
            'one complete edit_selected_span tool call containing at most3lines, replacing only the condition. '
            '\nEXACT SELECTED LINE:\n'+selected.old+
            '\nNEARBY UNCHANGED CONTEXT:\n'+''.join(lines[max(0,matches[0]-5):matches[0]+5]))
        self.model.session('builder',ident+'-entry-selected',
            'You are the local Qwen gameplay author. Implement the selected single-line interaction correction now.',
            prompt,[tool('edit_selected_span','Replace only the supplied condition; exact file hash and three-line scope are enforced.',
                         {'content':{'type':'string'}})],
            {'edit_selected_span':lambda a,f:selected.apply(a,f['content'])},turns=1,reasoning_effort='low')
        if sha(files.path(path).read_bytes())==selected.before:
            raise Halt('Selected entry correction saved no change; no blind generic retry')
        self.store.set(entry_selected_edit_saved=True)
        self.store.event('selected-entry-recovery',path=path,game_author='local Qwen',unchanged_native_probe=True)
        return {'ok':True,'scenario':MOTOR_PROBE,'summary':'One local selected entry-condition edit saved; native verification pending'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous-run',type=Path,required=True);p.add_argument('--run-dir',type=Path,required=True)
    a=p.parse_args();os.umask(0o077)
    if a.run_dir.exists():raise Halt('Use a new recovery ledger; preserve the stopped run')
    old=read_json(a.previous_run/'status.json');c=read_json(a.previous_run/'private-config.json')
    if old.get('controller_pid') or old.get('owned_process') or old['status']!='paused' or old.get('task_index')!=1:
        raise Halt('Expected the stopped sole owner at the measured vehicle blocker')
    if 'Repeated diagnosed blocker' not in old.get('blocker',''):raise Halt('Recovery is scoped to the evidenced repeated blocker')
    known=read_json(a.previous_run/'evidence/q0005-b8b63e5d/scoped-gate.json')
    if (known.get('candidate_commit')!=PHYSICAL_SOURCE or not known.get('passed')
            or not known.get('regressions',{}).get('passed')):raise Halt('Expected preserved passing physical vehicle/reset and regression evidence')
    repo=Path(c['game_repository'])
    if git(repo,'rev-parse','HEAD')!=old['source_checkpoint'] or git(repo,'status','--porcelain'):
        raise Halt('Unexpected source or another session change; preserve it')
    deadline=old['overall_deadline_epoch'];started=time.time()
    if deadline<=started:raise Halt('Original overall ceiling expired')
    hashes={n:sha((a.previous_run/n).read_bytes()) for n in ('state.sqlite3','status.json')}
    c.update(wall_hours=(deadline-started)/3600,output_tokens=8192,model_timeout_seconds=300)
    a.run_dir.mkdir(mode=0o700);atomic(a.run_dir/'private-config.json',c)
    r=EntryRecovery(a.run_dir,c);s=r.store;original=r.machine.guard
    def guard():
        original()
        if time.time()>=deadline:raise Halt('Original overall ceiling reached')
    r.machine.guard=guard;r.model.guard=guard
    def stop(*_):raise Halt('Original overall deadline or explicit stop')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    signal.alarm(max(1,int(deadline-time.time())))
    with exclusive(Path(c['coordination_dir'])/'game-owner.lock'),exclusive(a.run_dir/'controller.lock'):
        r.model.ready()
        # Existing local source is restored by commit identity; cloud authors no gameplay bytes.
        subprocess.run(['git','-C',str(repo),'restore','--source',PHYSICAL_SOURCE,'--worktree','--staged','--','game'],check=True)
        git(repo,'-c','user.name=Controller recovery','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Recover preserved physical vehicle candidate for focused entry diagnosis\n\nExisting game source: local Qwen at '+PHYSICAL_SOURCE+'. No cloud-authored gameplay edit.')
        source=git(repo,'rev-parse','HEAD')
        s.set(status='running',controller_pid=os.getpid(),owner='sole execution controller',manager='parent dot',
            started_epoch=started,started_utc=now(),overall_deadline_epoch=deadline,source_checkpoint=source,
            preserved_baseline=old['preserved_baseline'],last_playable_checkpoint=old['last_playable_checkpoint'],
            accepted_checkpoint=None,accepted_subfeatures=old['accepted_subfeatures'],
            accepted_queue_features=old['accepted_queue_features'],tasks=old['tasks'],task_index=1,
            previous_run=a.previous_run.name,previous_record_sha256=hashes,blocker=None,
            restored_physical_source=PHYSICAL_SOURCE,supplemental_gate_version=2,
            policy='One selected local entry fix, unchanged replay, stricter entry/exit checks, then continuous queue; original ceiling unchanged')
        s.event('evidenced-blocker-recovery',previous_stopped_run=a.previous_run.name,previous_records_preserved=True,
            measured_cause='Center distance2.608m exceeds2.5m interaction limit at firstE; laterE enters after throttle',
            selected_edit='One entry-condition span; local Qwen only',
            critic_repair='Actual capture times labeled; include end-stop, exit and post-reset images',
            restored_existing_source=PHYSICAL_SOURCE,original_ceiling_unchanged=True)
        s.report()
        try:r.work()
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:
            signal.alarm(0);candidate=r.checkpoint_source('Preserve local entry-recovery queue candidate at exit')
            s.set(controller_pid=None,source_checkpoint=candidate,
                previous_failure_record_unchanged=all(sha((a.previous_run/n).read_bytes())==h for n,h in hashes.items()))
            s.report()
    return 0

if __name__=='__main__':raise SystemExit(main())
