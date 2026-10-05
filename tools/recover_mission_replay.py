#!/usr/bin/env python3
"""Recover preserved local mission source through selected edits and a separate replay role."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import time

from continue_game_queue import ContinuousRunner
from loop_controller.core import Files, Halt, atomic, exclusive, now, read_json, sha
from loop_controller.continuous_tasks import TASKS
from loop_controller.model import tool
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

PRESERVED = 'bf1ab69bd2633a5f7eb14ed3b7e40e4ed59c88cc'
PLAYABLE = '479c138bd2d60e5bd6c0f7fcacca182a838dbabd'
MISSION = 'Assets/Game/Mission.cs'


def block_span(text, needle):
    lines=text.splitlines(keepends=True)
    matches=[i for i,line in enumerate(lines) if needle in line]
    if len(matches)!=1:raise Halt('Expected one selected mission block: '+needle)
    start=matches[0];depth=0;opened=False
    for i in range(start,len(lines)):
        depth+=lines[i].count('{')-lines[i].count('}')
        opened=opened or '{' in lines[i]
        if opened and depth==0:return start+1,i+1
    raise Halt('Selected mission block has no closing brace')


class MissionRecovery(ContinuousRunner):
    def selected(self,ident,label,needle,instruction,max_lines):
        files=Files(self.project,self.store)
        text=files.path(MISSION).read_text()
        start,end=block_span(text,needle)
        edit=SelectedEdit(files,MISSION,start,end,max_lines=max_lines)
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='selected-mission-repair',recovery_microtask=label);self.store.report()
        prompt=('Make exactly one complete edit_selected_span call replacing ONLY this supplied C# block. '
                'The controller enforces its exact source hash and scope; you need no read tool and must not echo the old span. '
                'Preserve unrelated behavior. No replay detection, forced telemetry, packages or art changes. '+instruction+
                '\nFIELD CONTEXT:\n'+'\n'.join(text.splitlines()[:40])+
                '\nTRUSTED SIGNAL TYPES: LoopSignals.Player and .Vehicle are Transform; .Mode and .Mission are string; '
                '.Restarts is int. Mission stage is0=ground parcel,1=carrying,2=delivered. padPos is the fixed destination. '
                '\nEXACT SELECTED BLOCK:\n'+edit.old)
        self.model.session('builder',ident+'-'+label,
            'You are the sole local Qwen game author. Save the one requested mechanical correction now.',
            prompt,[tool('edit_selected_span','Replace only the supplied complete block.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda a,f:edit.apply(a,f['content'])},turns=1,reasoning_effort='low')
        if sha(files.path(MISSION).read_bytes())==edit.before:
            raise Halt('Selected mission microtask saved no edit: '+label)
        candidate=self.checkpoint_source('Local Qwen: focused mission '+label)
        self.store.set(source_checkpoint=candidate)
        self.store.event('selected-mission-edit-saved',microtask=label,candidate=candidate,game_author='local Qwen')
        self.store.report()

    def edit(self,task,ident):
        if self.store.get('mission_selected_repairs_done') or task['id']!='connected-mission':
            return super().edit(task,ident)
        self.selected(ident,'transform-api','void Build()',
            'Fix only the six GameObject/Transform API errors: pad and beaconGo are GameObject values, '
            'so SetParent, position and localScale must be accessed through each object\'s Transform. '
            'Keep GetComponent calls on the GameObject. Preserve both existing stationary roots, all positions, '
            'materials, collider removals and mission setup exactly.',80)
        self.selected(ident,'vehicle-delivery-position','else if (stage == 1)',
            'When driving, delivery proximity must use the actual registered LoopSignals.Vehicle world position. '
            'The player transform remains at entry because VehicleInteraction disables Walker. Require a real vehicle '
            'transform, actual fixed-pad proximity and the existing F interaction; preserve vehicle-only delivery, '
            'the stage2 latch, parcel removal and ending signals. Do not modify VehicleInteraction or teleport actors.',65)
        self.selected(ident,'objective-status','void RefreshHud()',
            'Show the actual current stage: objective/pickup instruction while stage0, drive and F delivery instruction '
            'while carrying, and an unmistakable DELIVERY COMPLETE ending at stage2. Distance must refer to the '
            'uncollected parcel or fixed pad as appropriate, and use the actual vehicle position while driving. '
            'Keep controls readable and concise. This is presentation only; do not alter mission state.',45)
        self.store.set(mission_selected_repairs_done=True)
        return self.propose_replay(task,ident)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-run',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--authorize-recovery',action='store_true')
    args=parser.parse_args();os.umask(0o077)
    if not args.authorize_recovery:parser.error('Explicit full-project recovery authorization required')
    if args.run_dir.exists():raise Halt('Use a fresh recovery ledger; preserve the stopped run')
    old=read_json(args.previous_run/'status.json');config=read_json(args.previous_run/'private-config.json')
    if (old.get('controller_pid') or old.get('owned_process') or old['status']!='paused'
            or old['task_index']!=2 or old['last_playable_checkpoint']!=PLAYABLE
            or old.get('feedback',{}).get('failure')!=['microtask-no-complete-input-replay']):
        raise Halt('Expected the stopped evidenced mission replay blocker')
    repo=Path(config['game_repository'])
    if git(repo,'rev-parse','HEAD')!=old['source_checkpoint'] or git(repo,'status','--porcelain'):
        raise Halt('Unexpected source changes; preserve them')
    deadline=old['overall_deadline_epoch'];started=time.time()
    if started>=deadline:raise Halt('Original overall ceiling expired')
    hashes={n:sha((args.previous_run/n).read_bytes()) for n in ('state.sqlite3','status.json')}
    config.update(wall_hours=(deadline-started)/3600,output_tokens=8192,model_timeout_seconds=400)
    args.run_dir.mkdir(mode=0o700);atomic(args.run_dir/'private-config.json',config)
    with exclusive(Path(config['coordination_dir'])/'game-owner.lock'),exclusive(args.run_dir/'controller.lock'):
        runner=MissionRecovery(args.run_dir,config);s=runner.store
        runner.model.ready()
        if (Path(config['coordination_dir'])/'engine-request.json').exists():raise Halt('Engine handoff still active')
        subprocess.run(['git','-C',str(repo),'restore','--source',PRESERVED,'--worktree','--staged','--','game'],check=True)
        git(repo,'-c','user.name=Controller recovery','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Recover preserved local mission candidate for selected repairs and native replay\n\nExisting gameplay source: local Qwen at '+PRESERVED)
        source=git(repo,'rev-parse','HEAD')
        s.set(status='running',controller_pid=os.getpid(),owner='sole execution controller',manager='parent dot',
              started_epoch=started,started_utc=now(),overall_deadline_epoch=deadline,source_checkpoint=source,
              preserved_baseline=old['preserved_baseline'],last_playable_checkpoint=PLAYABLE,
              accepted_checkpoint=None,accepted_subfeatures=old['accepted_subfeatures'],
              accepted_queue_features=old['accepted_queue_features'],tasks=TASKS,task_index=2,
              previous_run=args.previous_run.name,previous_record_sha256=hashes,blocker=None,
              last_verified_progress_epoch=old['last_verified_progress_epoch'],
              last_verified_progress_utc=old['last_verified_progress_utc'],supplemental_gate_version=3,
              task_design='Preserved courier design; three selected local repairs then separate schema-validated replay. '+
                          'World-anchor observations are mandatory for every subsequent mission promotion. '+
                          'Temporary mission primitives remain inadmissible for final art acceptance.')
        s.event('authorized-mission-recovery',preserved_source=PRESERVED,playable_baseline=PLAYABLE,
                missing_submission='No finish_task call; summary,duration,input_steps,captures all absent',
                previous_records_preserved=True,original_ceiling_unchanged=True,automatic_mission_anchor_gate=True)
        original=runner.machine.guard
        def guard():
            original()
            if time.time()>=deadline:raise Halt('Original overall ceiling reached')
        def stop(*_):raise Halt('Original overall deadline or explicit stop')
        runner.machine.guard=guard;runner.model.guard=guard
        for sig in (signal.SIGALRM,signal.SIGTERM,signal.SIGINT):signal.signal(sig,stop)
        signal.alarm(max(1,int(deadline-time.time())));s.report()
        try:runner.work()
        except Exception as error:
            s.set(status='paused',blocker=type(error).__name__+': '+str(error))
            s.event('stopped',error_type=type(error).__name__,message=str(error))
        finally:
            signal.alarm(0)
            candidate=runner.checkpoint_source('Preserve local mission recovery candidate at exit')
            s.set(controller_pid=None,source_checkpoint=candidate,
                  previous_failure_record_unchanged=all(sha((args.previous_run/n).read_bytes())==h for n,h in hashes.items()))
            s.report()
    return 0


if __name__=='__main__':raise SystemExit(main())
