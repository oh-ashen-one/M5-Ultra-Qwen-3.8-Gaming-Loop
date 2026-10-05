#!/usr/bin/env python3
"""Fresh bounded measured repair, then a continuing game loop using small edits."""
import argparse
import json
import os
from pathlib import Path
import signal
import time
import uuid

from inspect_and_repair_grounding import grounding_scenario,summarize
from loop_controller.core import Files,Halt,atomic,encode,exclusive,now,read_json,sha,seal
from loop_controller.model import tool
from loop_controller.runner import Runner,API_GUIDE,scenario_for,git
from loop_controller.small_edits import SelectedEdit

STRING={'type':'string'}
INT={'type':'integer'}

class SmallRunner(Runner):
    def builder(self,task,round_id,brief):
        files=Files(self.project,self.store);reads={}
        def read(_,f):
            count=f.get('line_count',80)
            if count>100:raise ValueError('Read at most 100 lines for one small task')
            result=files.read(f['path'],f.get('start_line',1),count)
            reads[f['path']]=result
            return result
        def patch(action,f):
            saved=reads.get(f['path'])
            if not saved:raise ValueError('Read this exact section first')
            start,end=f['start_line'],f['end_line']
            if not saved['start_line']<=start<=end<saved['start_line']+len(saved['content'].splitlines()):
                raise ValueError('Edit only lines provided by the exact read')
            edit=SelectedEdit(files,f['path'],start,end)
            if edit.before!=saved['sha256']:raise ValueError('Source changed; read again')
            if not f['path'].startswith('Assets/Game/'):raise ValueError('C# only; no art edits')
            result=edit.apply(action,f['content']);reads.pop(f['path'],None);return result
        def create(action,f):
            if not f['path'].startswith('Assets/Game/') or len(f['content'].splitlines())>80:
                raise ValueError('Create only a small C# module of at most 80 lines')
            return files.create(action,**f)
        tools=[tool('list_files','List C# source paths.',{}),
               tool('read_file','Read an exact source section, at most 100 lines.',{'path':STRING,'start_line':INT,'line_count':INT},['path']),
               tool('edit_span','Replace only selected lines from the last exact read. Full-file hash enforced. At most 40 replacement lines.',{'path':STRING,'start_line':INT,'end_line':INT,'content':STRING}),
               tool('create_file','Create a new C# module, at most 80 lines.',{'path':STRING,'content':STRING}),
               tool('finish_task','Submit this small changed candidate for real native tests.',{'summary':STRING})]
        prompt=('Work on ONE small concrete fix or feature, then finish_task. No whole-file rewrite or broad redesign. '
                'No new art. The broader task remains:\n'+json.dumps(task)+'\nObserved feedback:\n'
                +json.dumps(self.store.get('feedback',{}))[:6000]+'\nNative API:\n'+API_GUIDE+
                '\nThis job exposes only small C# edits. Read the exact section needed, change at most 40 lines, then test. '
                'Prefer grounded control and readable existing-street framing before extra features. Never invent success.')
        return self.model.session('builder',round_id+'-small-builder',
            'You are the local game coder. Make one small file tool call at a time; do not emit long plans.',prompt,tools,
            {'list_files':lambda *_:{'files':[x for x in files.tree() if x['path'].startswith('Assets/Game/')]},
             'read_file':read,'edit_span':patch,'create_file':create,
             'finish_task':lambda _,f:{'ok':True,'summary':f['summary'],'scenario':scenario_for(task['phase'])}},turns=8)

def select_block(files,needle):
    lines=files.path('Assets/Game/Bootstrap.cs').read_text().splitlines(keepends=True)
    start=next(i for i,line in enumerate(lines) if needle in line)
    if 'var body =' in needle:return start+1,start+2
    depth=0;opened=False
    for i in range(start,len(lines)):
        depth+=lines[i].count('{')-lines[i].count('}')
        opened=opened or '{' in lines[i]
        if opened and depth==0:return start+1,i+1
    raise ValueError('Selected block has no closing brace')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run-dir','previous-run','config','brief'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--authorize-repair',action='store_true');a=p.parse_args()
    if not a.authorize_repair or a.run_dir.exists():p.error('Explicit authorization and fresh run directory required')
    old=read_json(a.previous_run/'status.json')
    if old.get('controller_pid') or old.get('status') not in ('paused','paused-deadline'):raise Halt('Previous owner must be stopped')
    preserved={n:sha((a.previous_run/n).read_bytes()) for n in ('status.json','state.sqlite3')}
    c=read_json(a.config);c.update(csharp_only=True,wall_hours=12,max_rounds=96,no_accepted_progress_minutes=120)
    os.umask(0o077);r=SmallRunner(a.run_dir,c);s=r.store
    started=time.time();repair_deadline=started+30*60;overall_deadline=started+12*3600
    tasks=read_json(a.previous_run/'plan.json');atomic(a.run_dir/'plan.json',tasks);atomic(a.run_dir/'private-config.json',c)
    s.set(controller_pid=os.getpid(),status='running',started_epoch=started,started_utc=now(),tasks=tasks,task_index=0,
          previous_run=a.previous_run.name,previous_record_sha256=preserved,repair_deadline_epoch=repair_deadline,
          overall_deadline_epoch=overall_deadline,stop_conditions={'repair_minutes':30,'attempts_per_selected_edit':2,
          'native_repair_rounds':3,'continuation_hours':12,'continuation_requires':'stationary grounded control plus actual readable-frame review'})
    def stop(*_):raise Halt('Current bounded deadline or explicit stop reached')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);signal.alarm(30*60)
    with exclusive(a.run_dir/'controller.lock'):
        try:
            r.model.ready();r.machine.guard();files=Files(r.project,s)
            stages=[('separate-physics-root','var body = UnityEngine.Object.Instantiate',
                'Replace only this player-instantiation span. Keep body a GameObject, but make it a new identity-rotation, '
                'unit-scale physics root. Instantiate the existing imported player as its visual child, preserving the imported '
                'visual scale/rotation: actual visual height is 1.57m; the imported root has scale 100 and up -Z. '
                'Do not normalize the imported mesh or add another CharacterController: later code already adds it and Walker '
                'to body and registers body.transform. Only separate physics from visual. At most 20 replacement lines.'),
              ('world-ground-spawn','if (street.GetComponentInChildren<Collider>() == null)',
                'Replace only this ground block. Its inherited Street transform makes an enormous tilted wall. '
                'Create invisible world-aligned collision ground on an independent unit-scale identity-rotation object, '
                'aligned to the existing visible sidewalk top Y=0.14m. The sidewalk world bounds are 14m x .14m x 3.2m '
                'centered at (0,.07,1.7); facade bounds 12m x 8.8m x 8m centered at (0,4.4,-4). '
                'Set body spawn just above a safe visible surface. Do not change imported visible geometry. '
                'Following code adds a 1.75m CharacterController centered at local y=.9 and radius .32. '
                'Keep it compact, at most 25 replacement lines. Do not add camera or other fixes here.')]
            for label,needle,instruction in stages:
                for attempt in range(2):
                    start,end=select_block(files,needle);edit=SelectedEdit(files,'Assets/Game/Bootstrap.cs',start,end,30)
                    all_lines=files.path(edit.path).read_text().splitlines()
                    context='\n'.join(all_lines[max(0,start-5):min(len(all_lines),end+12)])
                    c.update(output_tokens=2048 if attempt==0 else 4096,model_timeout_seconds=180)
                    s.set(stage='selected-edit',current_task=label,selected_lines=[start,end]);s.report()
                    result=r.model.session('builder',label+'-'+str(attempt+1),
                        'You are the local C# author. Make exactly one small edit_selected_span call now; no essay or full-file output.',
                        instruction+'\nSELECTED SPAN TO REPLACE:\n'+edit.old+'\nNearby context (read-only):\n'+context,
                        [tool('edit_selected_span','Replace only the supplied span; exact full-file hash enforced.',{'content':STRING})],
                        {'edit_selected_span':lambda action,f:edit.apply(action,f['content'])},turns=1)
                    if sha(files.path(edit.path).read_bytes())!=edit.before:
                        candidate=r.checkpoint_source('Local Qwen: '+label)
                        s.set(source_checkpoint=candidate,candidate_commit=candidate)
                        s.event('selected-edit-saved',stage=label,candidate=candidate,path=edit.path,sha256=sha(files.path(edit.path).read_bytes()))
                        s.report();break
                    s.event('selected-edit-unsaved',stage=label,attempt=attempt+1,outcome=result)
                else:raise Halt('Two attempts saved no selected edit: '+label)
            native_unity=r.engines.unity
            def grounded_unity(project,bundle,scenario,candidate):
                if scenario['coverage']=='foundation':scenario=grounding_scenario()
                gate=native_unity(project,bundle,scenario,candidate)
                if scenario['coverage']=='foundation':
                    observed=summarize(bundle) if (Path(bundle)/'captures/scene-transforms.json').exists() else {'stationary_grounded':False}
                    atomic(Path(bundle)/'world-observations.json',observed)
                    gate['stationary_grounded']=observed['stationary_grounded']
                    if not observed['stationary_grounded']:
                        gate['passed']=False;gate['failure']=(gate.get('failure') if isinstance(gate.get('failure'),list) else [])+['stationary-grounding-preflight']
                    atomic(Path(bundle)/'grounding-gate.json',gate)
                return gate
            r.engines.unity=grounded_unity
            for attempt in range(3):
                candidate=r.checkpoint_source('Local Qwen: preserve bounded grounding candidate')
                bundle=a.run_dir/'evidence'/('grounding-'+str(attempt+1));s.set(stage='native-grounding');s.report()
                gate=grounded_unity(r.project,bundle,grounding_scenario(),candidate)
                s.set(latest_evidence=str(bundle.relative_to(a.run_dir)),feedback=gate,
                      latest_captures=[str(x.relative_to(a.run_dir)) for x in sorted((bundle/'captures').glob('frame-*.png'))])
                s.report()
                if gate['passed']:
                    def review(_,f):
                        if f['verdict'] not in ('PASS','FIX','UNVERIFIED'):raise ValueError('Use PASS, FIX or UNVERIFIED')
                        return {'ok':True,**f}
                    c.update(output_tokens=2048,model_timeout_seconds=180)
                    review_result=r.model.session('critic','grounded-framing-'+str(attempt+1),
                        'You are an independent visual reviewer. Return one short tool verdict now.',
                        'This is an early development scene. Mechanics have a native stationary-grounding and walking pass. '
                        'Inspect the actual frame: is an upright, visible player framed together with a readable existing street/building? '
                        'PASS only that narrow framing goal, not polish or whole-game completion. FIX for void, clipping or unreadable framing. '
                        'Give only the single biggest concrete next fix, at most 35 words.',
                        [tool('submit_review','Return the narrow evidence-based framing verdict.',{'verdict':STRING,'next_fix':STRING})],
                        {'submit_review':review},images=[('Actual native frame, not a target',bundle/'captures/frame-000.png'),
                        ('Actual native frame after movement',bundle/'captures/frame-003.png')],turns=1)
                    atomic(bundle/'basic-framing-review.json',review_result)
                    if review_result.get('verdict')=='PASS':
                        s.set(basic_grounded_checkpoint=candidate,basic_grounded_evidence=str(bundle.relative_to(a.run_dir)),
                              basic_grounded_utc=now(),basic_grounded_evidence_sha256=seal(bundle,{'scope':'grounded-control and readable framing only'}))
                        s.event('basic-grounded-control-qualified',candidate=candidate,whole_game_accepted=False)
                        signal.alarm(max(1,int(overall_deadline-time.time())))
                        c.update(output_tokens=8192,model_timeout_seconds=400)
                        s.set(feedback={'next':'Grounded control and basic framing qualified; continue original local plan using small edits.'},stage='idle')
                        r.run(a.brief.read_text());break
                    s.set(feedback={**gate,'framing_review':review_result})
                if attempt==2:raise Halt('Three native repair rounds did not qualify grounded control and framing')
                c.update(output_tokens=4096,model_timeout_seconds=180)
                task={'phase':'foundation','outcome':'Fix only the latest measured grounding or rendered framing failure','acceptance':'Stationary grounded unit-scale upright root, real walking and readable existing street in the camera'}
                r.builder(task,'repair-'+str(attempt+1),'')
            else:raise Halt('Bounded grounding repair exhausted')
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:
            signal.alarm(0)
            candidate=r.checkpoint_source('Preserve local edits at bounded repair exit')
            s.set(controller_pid=None,source_checkpoint=candidate,previous_failure_record_unchanged=all(
                sha((a.previous_run/n).read_bytes())==h for n,h in preserved.items()));s.report()
    return 0
if __name__=='__main__':raise SystemExit(main())
