#!/usr/bin/env python3
"""Continue authorized game work after measured grounding, one local micro-plan/edit at a time."""
import argparse
import json
import os
from pathlib import Path
import signal
import time

from inspect_and_repair_grounding import grounding_scenario,summarize
from loop_controller.core import Files,Halt,atomic,exclusive,now,read_json,seal,sha
from loop_controller.model import tool
from loop_controller.runner import Runner,scenario_for,git
from loop_controller.small_edits import SelectedEdit

S={'type':'string'};I={'type':'integer'}

class ElementaryRunner(Runner):
    def builder(self,task,round_id,brief):
        files=Files(self.project,self.store);reads={}
        def read(_,f):
            if not f['path'].startswith('Assets/Game/'):raise ValueError('Read game C# only for this small job')
            count=min(f.get('line_count',60),80)
            result=files.read(f['path'],f.get('start_line',1),count)
            reads.setdefault(f['path'],[]).append(result);return result
        def submit(_,f):
            if f['kind'] not in ('replace','create') or len(f['goal'].split())>40:raise ValueError('One replace/create goal, at most 40 words')
            files.path(f['path'],write=True)
            if not f['path'].startswith('Assets/Game/') or not f['path'].endswith('.cs'):raise ValueError('Runtime C# only')
            if f['kind']=='replace':
                if not 1<=f['start_line']<=f['end_line'] or f['end_line']-f['start_line']>=8:raise ValueError('Select at most eight existing lines')
                matches=[v for v in reads.get(f['path'],[]) if v['start_line']<=f['start_line']<=f['end_line']<v['start_line']+len(v['content'].splitlines())]
                if not matches:raise ValueError('Read the exact selected lines first')
                edit=SelectedEdit(files,f['path'],f['start_line'],f['end_line'],12)
                if edit.before!=matches[-1]['sha256']:raise ValueError('Stale selection; read again')
            elif files.path(f['path']).exists():raise ValueError('New module already exists')
            return {'ok':True,**f}
        inventory=[v for v in files.tree() if v['path'].startswith('Assets/Game/')]
        excerpts=[]
        bootstrap='Assets/Game/Bootstrap.cs'
        if files.path(bootstrap).exists():
            total=len(files.path(bootstrap).read_text().splitlines())
            excerpts.append(read(None,{'path':bootstrap,'start_line':10,'line_count':min(55,max(1,total-9))}))
            if total>80:excerpts.append(read(None,{'path':bootstrap,'start_line':max(1,total-24),'line_count':25}))
        self.store.set(stage='local-micro-plan',current_task='Choose one elementary edit for: '+task['outcome']);self.store.report()
        self.c.update(output_tokens=2048,model_timeout_seconds=180)
        plan=self.model.session('planner',round_id+'-micro-plan',
            'You are the local game planner. Select ONE elementary C# change, then call submit_plan. Do not write code or a long design.',
            'Choose one assignment, one short object creation, or a simple block of at most 12 new lines. '
            'Keep the goal at most 40 words. Prioritize the actual failure below. Preserve verified grounding. '
            'For framing, reuse/instance existing street prefabs or adjust the camera; no new art. '
            'Existing Resources paths: Generated/street/scene, Generated/player/scene, Generated/coupe/scene, Generated/props/scene. '
            'Original task remains: '+json.dumps(task)+'\nEvidence/critic feedback:\n'+json.dumps(self.store.get('feedback',{}))[:5000]+
            '\nSource inventory:\n'+json.dumps(inventory)+'\nExact available excerpts:\n'+json.dumps(excerpts),
            [tool('read_file','Read one exact C# section, at most 80 lines; result includes total_lines.',{'path':S,'start_line':I,'line_count':I},['path']),
             tool('submit_plan','Select one tiny edit; do not return code.',{'kind':S,'path':S,'start_line':I,'end_line':I,'goal':S})],
            {'read_file':read,'submit_plan':submit},turns=4)
        if not plan.get('ok'):return {'bounded_stop':'micro-plan','summary':'No qualified elementary plan; preserve source'}
        self.store.event('local-micro-plan',plan_kind=plan['kind'],
                         **{k:plan[k] for k in ('path','start_line','end_line','goal')})
        self.store.set(current_micro_plan=plan,stage='local-micro-edit');self.store.report()
        if plan['kind']=='replace':
            edit=SelectedEdit(files,plan['path'],plan['start_line'],plan['end_line'],12)
            lines=files.path(plan['path']).read_text().splitlines()
            context='\n'.join(lines[max(0,plan['start_line']-4):min(len(lines),plan['end_line']+4)])
            selected=edit.old;before=edit.before
            dispatch=lambda action,f:edit.apply(action,f['content'])
        else:
            selected='(new C# module)';context='';before=None
            def dispatch(action,f):
                if len(f['content'].splitlines())>12:raise ValueError('Create a tiny module, at most 12 lines')
                return files.create(action,plan['path'],f['content'])
        for attempt in range(2):
            self.c.update(output_tokens=2048 if attempt==0 else 4096,model_timeout_seconds=180)
            self.model.session('builder',round_id+'-micro-edit-'+str(attempt+1),
                'You are the local C# author. Perform only the selected tiny change through the tool now.',
                'Implement this local plan: '+plan['goal']+'\nReturn only the replacement span, at most 12 lines; never the whole file. '
                'UnityEngine.Object.Instantiate must be qualified inside a static helper. Preserve all unselected code.\nSELECTED:\n'
                +selected+'\nNearby read-only context:\n'+context,
                [tool('edit_selected_span','Apply only this selected span/new tiny module; original hash and limits enforced.',{'content':S})],
                {'edit_selected_span':dispatch},turns=1)
            path=files.path(plan['path'])
            if path.exists() and sha(path.read_bytes())!=before:
                self.c.update(output_tokens=8192,model_timeout_seconds=400)
                return {'ok':True,'summary':plan['goal'],'scenario':scenario_for(task['phase'])}
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        return {'bounded_stop':'micro-edit','summary':'Two attempts saved no selected edit; preserve candidate'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--brief',type=Path,required=True);p.add_argument('--authorize-existing-game',action='store_true');a=p.parse_args()
    if not a.authorize_existing_game:p.error('Existing full-game authorization is required')
    os.umask(0o077);c=read_json(a.run_dir/'private-config.json');r=ElementaryRunner(a.run_dir,c);s=r.store
    if s.get('controller_pid') or s.get('status')!='paused':raise Halt('Expected the stopped sole-owner repair')
    gate_path=a.run_dir/'evidence/grounding-3/grounding-gate.json';gate=read_json(gate_path)
    if not gate.get('passed') or not gate.get('stationary_grounded') or gate['candidate_commit']!=git(r.repo,'rev-parse','HEAD'):
        raise Halt('Current source must match the actual grounded native candidate')
    remaining=int(s.get('overall_deadline_epoch')-time.time())
    if remaining<=0:raise Halt('Authorized overall deadline expired')
    def stop(*_):raise Halt('Authorized overall deadline or explicit stop reached')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);signal.alarm(remaining)
    native=r.engines.unity
    def grounded(project,bundle,scenario,candidate):
        if scenario['coverage']=='foundation':scenario=grounding_scenario()
        result=native(project,bundle,scenario,candidate)
        if scenario['coverage']=='foundation':
            observations=summarize(bundle) if (Path(bundle)/'captures/scene-transforms.json').exists() else {'stationary_grounded':None}
            atomic(Path(bundle)/'world-observations.json',observations);result['stationary_grounded']=observations['stationary_grounded']
            if not result['stationary_grounded']:
                prior=result.get('failure');prior=prior if isinstance(prior,list) else ([prior] if prior else [])
                result.update(passed=False,failure=prior+['stationary-grounding-preflight'])
            atomic(Path(bundle)/'grounding-gate.json',result)
        return result
    r.engines.unity=grounded
    with exclusive(a.run_dir/'controller.lock'):
        conditions=dict(s.get('stop_conditions',{}))
        previous_requirement=conditions.get('continuation_requires')
        conditions['continuation_requires']='measured stationary grounded control; framing FIX remains required game work'
        if previous_requirement!=conditions['continuation_requires']:
            s.event('continuation-condition-clarified',previous=previous_requirement,
                    current=conditions['continuation_requires'],
                    authorization='Once basic grounded control passes, continue the authorized game loop')
        s.set(controller_pid=os.getpid(),status='running',blocker=None,mechanical_grounded_checkpoint=gate['candidate_commit'],
              mechanical_grounded_evidence='evidence/grounding-3',continuation_started_utc=now(),stop_conditions=conditions)
        s.event('cloud-infrastructure-intervention',action='Continue authorized game after proven grounded control; framing FIX remains first task',
                authorization='Once basic grounded control passes, continue the authorized game loop',accepted_game_checkpoint_unchanged=True,
                overall_deadline_unchanged=True,local_planner_and_coder=True)
        try:r.run(a.brief.read_text())
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:
            signal.alarm(0);candidate=r.checkpoint_source('Preserve local micro-edit progress at game-loop exit')
            s.set(controller_pid=None,source_checkpoint=candidate);s.report()
    return 0
if __name__=='__main__':raise SystemExit(main())
