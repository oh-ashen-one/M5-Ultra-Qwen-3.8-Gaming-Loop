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
            if f['kind'] not in ('replace','create'):raise ValueError('kind must be exactly replace or create')
            if len(f['goal'].split())>40:raise ValueError('goal must contain at most 40 words')
            if f['operation'] not in ('assignment','call','module'):raise ValueError('operation must be exactly assignment, call, or module')
            files.path(f['path'],write=True)
            if not f['path'].startswith('Assets/Game/') or not f['path'].endswith('.cs'):raise ValueError('Runtime C# only')
            if f['kind']=='replace':
                if f['operation']=='module':raise ValueError('Existing edits must be one assignment or one call')
                if not 1<=f['start_line']<=f['end_line'] or f['end_line']-f['start_line']>=2:raise ValueError('Select at most two existing lines')
                matches=[v for v in reads.get(f['path'],[]) if v['start_line']<=f['start_line']<=f['end_line']<v['start_line']+len(v['content'].splitlines())]
                if not matches:raise ValueError('Read the exact selected lines first')
                edit=SelectedEdit(files,f['path'],f['start_line'],f['end_line'],4)
                if edit.before!=matches[-1]['sha256']:raise ValueError('Stale selection; read again')
            elif f['operation']!='module' or files.path(f['path']).exists():raise ValueError('Create one new tiny module only')
            return {'ok':True,**f}
        inventory=[v for v in files.tree() if v['path'].startswith('Assets/Game/')]
        excerpts=[]
        bootstrap='Assets/Game/Bootstrap.cs'
        if files.path(bootstrap).exists():
            total=len(files.path(bootstrap).read_text().splitlines())
            excerpts.append(read(None,{'path':bootstrap,'start_line':10,'line_count':min(55,max(1,total-9))}))
            if total>80:excerpts.append(read(None,{'path':bootstrap,'start_line':max(1,total-24),'line_count':25}))
        observed={}
        evidence=self.store.get('latest_evidence')
        if evidence:
            candidate=(self.store.root/evidence/'world-observations.json').resolve()
            if candidate.is_relative_to(self.store.root.resolve()) and candidate.is_file():
                value=read_json(candidate)
                observed={k:value.get(k) for k in ('largest_street_renderers','player_visual_bounds','stationary_first','colliders')}
        self.store.set(stage='local-micro-plan',current_micro_plan=None,current_task='Choose one elementary edit for: '+task['outcome']);self.store.report()
        # Reserve genuine planning for a sufficient thinking/tool-call budget.
        # Known mechanical repairs bypass this planner via direct_feature_attempt.
        planning_tokens=self.c.get('planner_output_tokens',16384)
        if not 8192<=planning_tokens<=16384:raise Halt('Planner budget must be 8192..16384')
        self.c.update(output_tokens=planning_tokens,model_timeout_seconds=self.c.get('planner_timeout_seconds',600))
        plan=self.model.session('planner',round_id+'-micro-plan',
            'You are the local game planner. Select ONE elementary C# change, then call submit_plan. Do not write code or a long design.',
            'Choose exactly one field/property assignment or one method call in at most two selected old lines; '
            'the replacement permits at most four lines. A genuinely new module may have at most 12 lines. '
            'No grids, rings, loops, repeated instantiation, or compound multi-object tasks. '
            'submit_plan requires literal kind="replace" with operation="assignment" or "call" for existing lines; '
            'a new file uses kind="create" and operation="module". Use exactly these enum values. '
            'Keep the goal at most 40 words. Prioritize one actual failure below. Preserve verified grounding. '
            'For framing, change one camera parameter or place ONE existing object; no new art. '
            'Existing Resources paths: Generated/street/scene, Generated/player/scene, Generated/coupe/scene, Generated/props/scene. '
            'Original task remains: '+json.dumps(task)+'\nEvidence/critic feedback:\n'+json.dumps(self.store.get('feedback',{}))[:5000]+
            '\nMeasured world bounds:\n'+json.dumps(observed)+
            '\nSource inventory:\n'+json.dumps(inventory)+'\nExact available excerpts:\n'+json.dumps(excerpts),
            [tool('read_file','Read one exact C# section, at most 80 lines; result includes total_lines.',{'path':S,'start_line':I,'line_count':I},['path']),
             tool('submit_plan','Select one assignment/call, or a new tiny module; do not return code.',
                  {'kind':{'type':'string','enum':['replace','create']},
                   'operation':{'type':'string','enum':['assignment','call','module']},
                   'path':S,'start_line':I,'end_line':I,'goal':S})],
            {'read_file':read,'submit_plan':submit},turns=4)
        if not plan.get('ok'):
            self.store.event('micro-plan-format-stopped',outcome=plan,action='Inspect tool schema and errors; no identical automatic retry')
            if plan.get('bounded_stop')=='output':
                raise Halt('Planner exhausted its output budget without submitting a plan; no identical retry')
            raise Halt('Planner submitted no valid tiny plan; inspect tool-format errors before another request')
        self.store.event('local-micro-plan',plan_kind=plan['kind'],operation=plan['operation'],
                         **{k:plan[k] for k in ('path','start_line','end_line','goal')})
        self.store.set(current_micro_plan=plan,stage='local-micro-edit');self.store.report()
        if plan['kind']=='replace':
            edit=SelectedEdit(files,plan['path'],plan['start_line'],plan['end_line'],4)
            lines=files.path(plan['path']).read_text().splitlines()
            context='\n'.join(lines[max(0,plan['start_line']-4):min(len(lines),plan['end_line']+4)])
            selected=edit.old;before=edit.before
            dispatch=lambda action,f:edit.apply(action,f['content'])
        else:
            selected='(new C# module)';context='';before=None
            def dispatch(action,f):
                if len(f['content'].splitlines())>12:raise ValueError('Create a tiny module, at most 12 lines')
                return files.create(action,plan['path'],f['content'])
        self.c.update(output_tokens=8192,model_timeout_seconds=300)
        result=self.model.session('builder',round_id+'-micro-edit-1',
            'You are the local C# author. Briefly solve the one selected change and save it through the tool first.',
            'Implement this local plan: '+plan['goal']+'\nSave with edit_selected_span now: at most four replacement lines '
            '(12 only for a new module); never the whole existing file. No grid, loop, repeated instantiation or broad redesign. '
            'UnityEngine.Object.Instantiate must be qualified inside a static helper. Preserve all unselected code.\nSELECTED:\n'
            +selected+'\nNearby read-only context:\n'+context+'\nMeasured world bounds:\n'+json.dumps(observed),
            [tool('edit_selected_span','Save only this selected span/new tiny module; original hash and limits enforced.',{'content':S})],
            {'edit_selected_span':dispatch},turns=1,reasoning_effort='low')
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        path=files.path(plan['path'])
        if path.exists() and sha(path.read_bytes())!=before:
            return {'ok':True,'summary':plan['goal'],'scenario':scenario_for(task['phase'])}
        self.store.event('micro-edit-hypothesis-stopped',outcome=result,plan=plan,
                         action='Inspect safe accounting and tool formatting; no identical automatic retry')
        raise Halt('Low-effort micro-edit saved no change; inspect formatting/accounting before another request')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--brief',type=Path,required=True);p.add_argument('--authorize-existing-game',action='store_true');a=p.parse_args()
    if not a.authorize_existing_game:p.error('Existing full-game authorization is required')
    os.umask(0o077);c=read_json(a.run_dir/'private-config.json');r=ElementaryRunner(a.run_dir,c);s=r.store
    if s.get('controller_pid') or s.get('status')!='paused':raise Halt('Expected the stopped sole-owner repair')
    evidence=s.get('mechanical_grounded_evidence','evidence/grounding-3')
    gate_path=(a.run_dir/evidence/'grounding-gate.json').resolve()
    if not gate_path.is_relative_to(a.run_dir.resolve()):raise Halt('Grounded evidence must be inside this run')
    gate=read_json(gate_path)
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
    c['reasoning_policy']='xhigh planning/critique; low elementary editing; thinking enabled'
    with exclusive(a.run_dir/'controller.lock'):
        conditions=dict(s.get('stop_conditions',{}))
        previous_requirement=conditions.get('continuation_requires')
        conditions['continuation_requires']='measured stationary grounded control; framing FIX remains required game work'
        if previous_requirement!=conditions['continuation_requires']:
            s.event('continuation-condition-clarified',previous=previous_requirement,
                    current=conditions['continuation_requires'],
                    authorization='Once basic grounded control passes, continue the authorized game loop')
        s.set(controller_pid=os.getpid(),status='running',blocker=None,mechanical_grounded_checkpoint=gate['candidate_commit'],
              mechanical_grounded_evidence=evidence,continuation_started_utc=now(),stop_conditions=conditions)
        s.event('cloud-infrastructure-intervention',action='Continue authorized game after proven grounded control; framing FIX remains first task',
                authorization='Once basic grounded control passes, continue the authorized game loop',accepted_game_checkpoint_unchanged=True,
                overall_deadline_unchanged=True,local_planner_and_coder=True,
                reasoning_policy=c['reasoning_policy'],identical_unsaved_edit_retries=0)
        try:r.run(a.brief.read_text())
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:
            signal.alarm(0);candidate=r.checkpoint_source('Preserve local micro-edit progress at game-loop exit')
            s.set(controller_pid=None,source_checkpoint=candidate);s.report()
    return 0
if __name__=='__main__':raise SystemExit(main())
