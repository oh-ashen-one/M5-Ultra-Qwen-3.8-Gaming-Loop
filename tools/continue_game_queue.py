#!/usr/bin/env python3
"""One durable serial owner advances scoped native passes through the full authorized queue."""
import argparse
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import time
import uuid

from inspect_and_repair_grounding import grounding_scenario, summarize
from loop_controller.core import Files, Halt, atomic, exclusive, failure_key, now, read_json, seal, sha, verify_seal
from loop_controller.continuous_checks import evaluate_step, validate_proposed, WORLD_PROBE, MOTOR_PROBE
from loop_controller.continuous_tasks import BASELINE, TASKS
from loop_controller.features import pavement_coverage, references_capture
from loop_controller.model import tool
from loop_controller.runner import API_GUIDE, Runner, git, target_for
from loop_controller.replay_contract import finish_tool, replay_guide, validate_submission
from loop_controller.review_summary import critic_evidence,require_combat_contracts

S={'type':'string'}; I={'type':'integer'}
STEPS={'type':'array','items':{'type':'object','properties':{
    'start':{'type':'number'},'end':{'type':'number'},'keys':{'type':'array','items':S}},
    'required':['start','end','keys'],'additionalProperties':False}}


def verified_time_citations(summary,capture_times):
    found={}
    groups=[m.group(1) for m in re.finditer(r'\bt\s*=\s*(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*)',summary,re.I)]
    groups += [m.group(1) for m in re.finditer(r'(?<![\w.])(\d+(?:\.\d+)?)\s*(?:s\b|seconds?\b)',summary,re.I)]
    for group in groups:
        for token in group.split('/'):
            precision=len(token.split('.')[1]) if '.' in token else 0
            tolerance=.5*10**(-precision)+1e-8
            matches=[name for name,when in capture_times.items() if abs(float(token)-when)<=tolerance]
            if len(matches)==1:found[matches[0]]=capture_times[matches[0]]
    return found


def validate_scoped_review(fields,names,capture_times=None):
    verdict=fields['verdict'].strip().upper()
    if verdict not in ('PASS','FIX','UNVERIFIED') or len(fields['fixes'])>5:
        raise ValueError('Use PASS/FIX/UNVERIFIED with at most five prioritized fixes')
    cited=verified_time_citations(fields['summary'],capture_times or {})
    if not references_capture(fields['summary'],names) and not cited:
        raise ValueError('Cite an actual supplied frame filename or unambiguous capture time in summary')
    if verdict!='PASS' and not fields['fixes']:raise ValueError('State an actionable evidence-based fix or missing proof')
    result={'ok':True,**fields,'verdict':verdict}
    if cited:result['verified_capture_time_citations']=cited
    return result


def review_evidence_seal(captures,candidate,scope):
    """Reuse verified evidence without regenerating its manifest timestamp."""
    path=Path(captures)/'manifest.json'
    if not path.exists():return seal(captures,{'candidate':candidate,'scope':scope})
    expected=sha(path.read_bytes())
    manifest=verify_seal(captures,expected)
    if manifest.get('candidate')!=candidate or manifest.get('scope')!=scope:
        raise Halt('Existing review evidence has a different candidate or scope')
    return expected


def review_captures(task,bundle):
    frames=sorted((bundle/'captures').glob('frame-*.png'))
    scenario=read_json(bundle/'captures/scenario.json')
    indices=[0,3,4,5,6] if task['id']=='vehicle-collision-reset' and len(frames)==7 else [0,len(frames)//2,len(frames)-1]
    chosen=[frames[i] for i in indices]
    trace=bundle/'captures/trace.jsonl'
    if task['id']=='east-dead-drop' and trace.exists():
        from loop_controller.chapter_route_probe import chapter_capture_selection
        rows=[json.loads(line) for line in trace.read_text().splitlines()]
        selected=chapter_capture_selection(frames,scenario,rows,task.get('chapter_review_reset',True))
        if selected:chosen=selected
    if task['id']=='connected-map-extension' and trace.exists():
        from qualify_map_extension import outside_distance
        rows=[json.loads(line) for line in trace.read_text().splitlines()]
        selected=[]
        for mode,key in [('foot','player'),('vehicle','vehicle')]:
            for frame in frames:
                when=scenario['captures'][int(frame.stem.split('-')[-1])]
                near=min(rows,key=lambda row:abs(row['time']-when))
                if (abs(near['time']-when)<=.25 and near.get('mode')==mode
                        and near.get(key) and outside_distance(near[key],task.get('prior_bounds'))>=6):
                    selected.append(frame);break
        junction=[]
        for frame in frames:
            when=scenario['captures'][int(frame.stem.split('-')[-1])]
            near=min(rows,key=lambda row:abs(row['time']-when))
            if (abs(near['time']-when)<=.25 and near.get('mode')=='foot' and near.get('player')
                    and 0<outside_distance(near['player'],task.get('prior_bounds'))<=2):
                junction=[frame];break
        # A measured junction view replaces the redundant opening image. Keep
        # four actual images plus the reference within the established budget.
        chosen=sorted(set([*(junction or [frames[0]]),*selected,frames[-1]]))
    if 'mission_complete' in task.get('checks',[]) and task['id']!='east-dead-drop' and trace.exists():
        rows=[json.loads(line) for line in trace.read_text().splitlines()]
        observed=[]
        for frame in frames:
            when=scenario['captures'][int(frame.stem.split('-')[-1])]
            near=min(rows,key=lambda row:abs(row['time']-when)) if rows else None
            if near and abs(near['time']-when)<=.25:observed.append((frame,near))
        initial_restarts=rows[0].get('restarts',0) if rows else 0
        def carrying(row):
            return row.get('mission')=='active' and any(o['name']=='Parcel' and
                (o.get('playerChild') or o.get('vehicleChild')) for o in row.get('missionObjects',[]))
        predicates=[lambda row:row.get('mission')=='active' and not carrying(row),carrying,
                    lambda row:row.get('mission')=='complete',
                    lambda row:row.get('restarts',0)>initial_restarts and row.get('mission')=='active' and not carrying(row),
                    lambda row:row.get('mission')=='failed' or row.get('health',100)<=0]
        if 'failure_retry' in task.get('checks',[]):
            # Failed, reset, carrying and completed retain all required transitions.
            # Omit the redundant initial frame so a tool correction fits the context budget.
            predicates=[predicates[4],predicates[3],predicates[1],predicates[2]]
        elif 'combat' in task.get('checks',[]):
            # Include the actual fight instead of a redundant initial state;
            # retain carrying/ending/reset with room for the reference image.
            predicates=[lambda row:row.get('hits',0)>0 and row.get('pursuit',0)>0,
                        predicates[1],predicates[2],predicates[3]]
        selected=[]
        for predicate in predicates:
            match=next((frame for frame,row in observed if predicate(row)),None)
            if match is not None and match not in selected:selected.append(match)
        # At most five genuine state captures fit the bounded image context.
        # Missing state captures remain missing evidence; never invent or relabel them.
        if selected:chosen=sorted(selected)
    if task.get('review_frame_times') is not None:
        requested=task['review_frame_times']
        if not 1<=len(requested)<=5:raise Halt('Bound the explicit scoped image selection to five frames')
        chosen=[]
        for when in requested:
            match=min(frames,key=lambda p:abs(scenario['captures'][int(p.stem.split('-')[-1])]-when))
            actual=scenario['captures'][int(match.stem.split('-')[-1])]
            if abs(actual-when)>.06 or match in chosen:raise Halt('Requested scoped capture is missing or duplicated')
            chosen.append(match)
    mapping={p.name:scenario['captures'][int(p.stem.split('-')[-1])] for p in chosen}
    return chosen,mapping


class ReadBoundEdits:
    """Remember a read's hash so the model need not transcribe hashes; never waive staleness."""
    def __init__(self, files, polish=False):
        self.files=files; self.reads={}; self.polish=polish

    def read(self, _, fields):
        value=self.files.read(**fields)
        previous=self.reads.get(fields['path'])
        ranges=previous['ranges'] if previous and previous['sha256']==value['sha256'] else []
        self.reads[fields['path']]={**value,'ranges':[*ranges,value['content']]}
        return value

    def allowed(self, path, content):
        self.files.path(path,write=True)
        if self.polish and path in {'Assets/Game/Mission.cs','Assets/Game/VehicleInteraction.cs'}:
            raise ValueError('Presentation polish preserves accepted mission anchors and boarding. A measured mechanics defect needs a separate scoped repair.')
        code=path.startswith('Assets/Game/') and path.endswith('.cs')
        art=self.polish and path in {'Art/'+name+'.py' for name in ('street','coupe','props','player')}
        if not (code or art):raise ValueError('This job edits game C# only; polish may revise the four existing Art scripts')
        if len(content.encode())>20000 or len(content.splitlines())>400:
            raise ValueError('Save a smaller module or unique replacement span, at most20KB/400lines')

    def create(self, action, fields):
        self.allowed(fields['path'],fields['content'])
        if fields['path'].startswith('Art/'):raise ValueError('No new art scripts')
        return self.files.create(action,**fields)

    def replace(self, action, fields):
        self.allowed(fields['path'],fields['new'])
        previous=self.reads.get(fields['path'])
        if not previous or not any(fields['old'] in content for content in previous['ranges']):
            raise ValueError('Read the exact current target span before replacing it; all reads must match the current file hash')
        result=self.files.edit(action,expected_sha256=previous['sha256'],**fields)
        self.reads.pop(fields['path'],None)
        return result


class ContinuousRunner(Runner):
    def propose_replay(self,task,ident):
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        files=Files(self.project,self.store)
        paths=[x['path'] for x in files.tree() if x['path'].startswith('Assets/Game/') and x['path'].endswith('.cs')]
        source='\n'.join(p+'\n'+files.path(p).read_text() for p in paths)
        self.store.set(stage='local-replay-submission');self.store.report()
        result=self.model.session('replay-author',ident+'-replay',
            'You are local Qwen submitting a normal-input test of the current game. No source editing. Call finish_task now.',
            replay_guide(task)+'\nTASK:'+json.dumps(task)+'\nACTUAL FEEDBACK:'+json.dumps(self.store.get('feedback',{}))[:16000]+
            '\nCURRENT SOURCE:\n'+source,
            [finish_tool()],{'finish_task':lambda _,f:validate_submission(f,task)},turns=2,reasoning_effort='low')
        if not result.get('scenario'):
            raise Halt('Replay-only role supplied no valid finish_task; required: summary, duration, input_steps, captures')
        self.store.set(last_valid_replay=result['scenario'])
        self.store.event('replay-preflight-passed',task=task['id'],duration=result['scenario']['duration'],
                         steps=len(result['scenario']['steps']),captures=len(result['scenario']['captures']))
        return result

    def design(self,task,ident,diagnosis=False):
        self.c.update(output_tokens=16384,model_timeout_seconds=600)
        def submit(_,f):return {'ok':True,'decision':f['decision'][:6500]}
        prompt=('Give one bounded implementable design/diagnosis for this task, not a project-wide plan. '
                'Use current source APIs and observed feedback. Return concise decisions, next smallest edit and how normal '
                'inputs will prove it. Never supply acceptance shortcuts.\nTASK:'+json.dumps(task)+
                '\nFEEDBACK:'+json.dumps(self.store.get('feedback',{}))[:12000])
        files=Files(self.project,self.store)
        prompt+='\nCURRENT C# INVENTORY:'+json.dumps([x for x in files.tree() if x['path'].startswith('Assets/Game/')])
        result=self.model.session('diagnosis' if diagnosis else 'planner',ident+'-design',
            'You are the local Qwen game designer. Make one bounded decision from real evidence.',prompt,
            [tool('read_file','Read a relevant current source range.',{'path':S,'start_line':I,'line_count':I},['path']),
             tool('submit_plan','Return one concise task-specific design decision.',{'decision':S})],
            {'read_file':lambda _,f:files.read(**f),'submit_plan':submit},turns=4,reasoning_effort='xhigh')
        if result.get('ok'):self.store.set(task_design=result['decision'])
        self.store.event('bounded-design-result',task=task['id'],completed=bool(result.get('ok')),
                         bounded_stop=result.get('bounded_stop'))
        return result

    def edit(self,task,ident):
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        files=Files(self.project,self.store);edits=ReadBoundEdits(files,task.get('polish',False))
        def finish(_,f):
            replay=task.get('probe') or validate_proposed(
                {'duration':f['duration'],'steps':f['input_steps'],'captures':f['captures']},task['maximum'],task['coverage'])
            return {'ok':True,'summary':f['summary'][:2000],'scenario':replay}
        tools=[tool('read_file','Read exact current source; controller remembers its full hash.',
                    {'path':S,'start_line':I,'line_count':I},['path']),
               tool('create_file','Create one NEW compact game C# module, without overwriting.',{'path':S,'content':S}),
               tool('replace_text','Replace an exact unique span from your latest read. Controller enforces its saved hash.',
                    {'path':S,'old':S,'new':S}),
               tool('finish_task','Finish this microtask with a normal-input replay. Fixed early probes ignore proposed steps.',
                    {'summary':S,'duration':{'type':'number'},'input_steps':STEPS,
                     'captures':{'type':'array','items':{'type':'number'}}})]
        dispatch={'read_file':edits.read,'create_file':edits.create,'replace_text':edits.replace,'finish_task':finish}
        if task.get('polish'):
            def blender(a,f):
                if f['script'] not in {'Art/'+n+'.py' for n in ('street','coupe','props','player')}:
                    raise ValueError('Only existing original art may be revised in this polish pass')
                return self.engines.blender(self.project,f['script'],a)
            tools.append(tool('run_blender','Re-export one revised existing original asset.',{'script':S}))
            dispatch['run_blender']=blender
        inventory=[x for x in files.tree() if x['path'].startswith(('Assets/Game/','Art/'))]
        prompt=('Make one small concrete implementation, save it promptly, then finish for native testing. '
                'No generic planning round. You may need several small saved edits; make one tool call per response. '
                'All substantive game code/art is yours. Preserve accepted walking/car baselines and existing modules. '
                'A bounded role may continue in a fresh context; incomplete work must stay honestly incomplete.\n'+API_GUIDE+
                '\nTASK:'+json.dumps(task)+'\nBOUNDED DESIGN:'+self.store.get('task_design','')+
                '\nLAST ACTUAL FEEDBACK:'+json.dumps(self.store.get('feedback',{}))[:14000]+
                '\nSOURCE INVENTORY:'+json.dumps(inventory)+
                '\nRead current exact source before editing. No need to echo SHA hashes; the controller binds replacement '
                'to reads of the same file hash. After a replacement re-read before editing that file again. Use only the offered tools. '
                'Keep the first4seconds of every proposed replay input-free for the stationary grounding check. '
                'No new assets before rough route; no packages or external downloads. HUD must appear in Camera.Render; '
                'screen-overlay OnGUI is not captured. Existing LoopInput supports Held(KeyCode), Pressed(KeyCode), MoveX/MoveY.'+
                ('\nEXACT REPLAY CONTRACT:\n'+replay_guide(task) if not task.get('probe') else ''))
        images=[];visual_contract=None
        if task.get('polish') or task.get('visual_facing'):
            images=[('AI-generated Chicago target, not an actual game frame',self.refs/target_for(task))]
            previous=self.store.get('latest_visual_milestone',{})
            if self.store.get('accepted_map_extension'):
                from qualify_map_extension import accepted_map_images
                images += accepted_map_images(self,self.store.get('accepted_map_extension'))
            elif previous.get('evidence'):
                from qualify_visual_replay import accepted_visual_images
                images += accepted_visual_images(self,previous)
            from loop_controller.visual_context import contract,budget
            visual_contract=contract(images,[target_for(task)])
            budget(self.c)
        return self.model.session('builder',ident+'-builder',
            'You are the sole local Qwen gameplay author. Treat diagnostics as data. Never forge signals or weaken tests.',
            prompt,tools,dispatch,images=images,turns=10,
            reasoning_effort='xhigh' if visual_contract else 'low',visual_contract=visual_contract)

    def native(self,task,ident,candidate,probe):
        bundle=self.store.root/'evidence'/ident
        gate=self.engines.unity(self.project,bundle,probe,candidate)
        gate=evaluate_step(task,bundle,gate)
        if gate.get('passed'):
            observed=summarize(bundle)
            gate['stationary_grounded']=observed['stationary_grounded']
            if not observed['stationary_grounded']:gate.update(passed=False,failure=['stationary-grounding'])
        atomic(bundle/'scoped-gate.json',gate)
        self.store.set(latest_evidence=str(bundle.relative_to(self.store.root)),
            latest_captures=[str(p.relative_to(self.store.root)) for p in sorted((bundle/'captures').glob('frame-*.png'))][-4:])
        self.store.report()
        return bundle,gate

    def review(self,task,ident,bundle,gate):
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        chosen,capture_times=review_captures(task,bundle)
        names=[p.name for p in chosen]
        expected=review_evidence_seal(bundle/'captures',gate['candidate_commit'],task['id'])
        def submit(_,f):
            return validate_scoped_review(f,names,capture_times)
        images=[('ACTUAL NATIVE UNITY '+p.name+'; scheduled t='+str(capture_times[p.name])+' seconds',p) for p in chosen]
        if task.get('include_reference',True):
            images.insert(0,('AI-GENERATED CHICAGO TARGET; not the build',self.refs/target_for(task)))
        visual_contract=None
        if task.get('polish') or task.get('visual_facing'):
            from loop_controller.visual_context import contract,budget
            visual_contract=contract(images,[target_for(task)])
            budget(self.c)
        result=self.model.session('critic',ident+'-critic',
            'You are a fresh local visual critic. Judge actual evidence and only the stated current scope.',
            'TASK:'+json.dumps(task)+'\nCOMPACT ACTUAL NATIVE OBSERVATIONS:'+json.dumps(critic_evidence(gate))+
            '\nFILES:'+json.dumps(names)+'\nAUTHORITATIVE CAPTURE SCHEDULE, seconds:'+json.dumps(capture_times)+
            '\nFrame numbers refer to the complete replay sequence, not their order in this selected image set. '
            'Use these supplied times; do not invent a different timing or call post-reset captures pre-reset. '
            'Use the separate target as visual direction for the existing plan. Prioritize concrete improvements '
            'within the current scope; a mechanical PASS never establishes target visual quality. '
            '\nRequire readable actors, coherent controls/route evidence, and no visible '
            'blocking regression. Early mechanics may retain rough development art; reserve reference-quality judgment '
            'for polish. A scoped PASS is not final game acceptance. Audio RMS establishes a mixer signal, not good sound. '
            'Use FIX when only part of the scope passes; partial is not a supported verdict. '
            'Enemy damage_events describe player/vehicle health loss; player_shot_rival_damage_events separately '
            'show actual rival HP changes from Mouse0. Use pursuit_transitions to assess arming before the clear interval. '
            'For presentation fixes, preserve verified mission anchor positions and interaction reach unless a new '
            'physical defect is measured. '
            'Report missing proof honestly and prioritize three to five fixes when needed. Do not infer completion from source.',
            [tool('submit_review','Return a scoped evidence-based verdict.',
                {'verdict':{'type':'string','enum':['PASS','FIX','UNVERIFIED','pass','fix','unverified']},
                 'summary':S,'fixes':{'type':'array','items':S}})],
            {'submit_review':submit},images=images,turns=3,reasoning_effort='xhigh',visual_contract=visual_contract)
        verify_seal(bundle/'captures',expected);atomic(bundle/'critic.json',result)
        return result

    def regress(self,task,ident,candidate):
        checks=[('walk',grounding_scenario(),{'id':'walking-regression','checks':[]})]
        if self.store.get('task_index',0)>=1:checks.append(('world',WORLD_PROBE,TASKS[0]))
        if self.store.get('task_index',0)>=2:checks.append(('motor',MOTOR_PROBE,TASKS[1]))
        if self.store.get('task_index',0)>=3:
            accepted=self.store.get('accepted_queue_features',{}).get('connected-mission')
            if not accepted:raise Halt('Failure/retry requires the accepted courier regression receipt')
            evidence=self.store.root/accepted['evidence']
            prior=read_json(evidence/'scoped-gate.json')
            if not prior.get('passed') or prior.get('candidate_commit')!=accepted['candidate']:
                raise Halt('Accepted courier regression provenance mismatch')
            probe=validate_proposed(read_json(evidence/'captures/scenario.json'),TASKS[2]['maximum'],TASKS[2]['coverage'])
            checks.append(('courier',probe,TASKS[2]))
        if self.store.get('task_index',0)>=4:
            accepted=self.store.get('accepted_queue_features',{}).get('mission-failure-retry')
            if not accepted:raise Halt('Combat requires the accepted failure/retry regression receipt')
            evidence=self.store.root/accepted['evidence'];prior=read_json(evidence/'scoped-gate.json')
            if not prior.get('passed') or prior.get('candidate_commit')!=accepted['candidate']:
                raise Halt('Accepted failure/retry regression provenance mismatch')
            probe=validate_proposed(read_json(evidence/'captures/scenario.json'),TASKS[3]['maximum'],TASKS[3]['coverage'])
            checks.append(('failure-retry',probe,TASKS[3]))
        results=[]
        for name,probe,contract in checks:
            bundle,gate=self.native(contract,ident+'-regression-'+name,candidate,probe)
            if name=='walk' and gate.get('passed'):
                gate['pavement']=pavement_coverage(bundle)
                if gate['player_displacement']<17 or not gate['pavement']['passed']:
                    gate.update(passed=False,failure=['accepted-walk-regression'])
                atomic(bundle/'scoped-gate.json',gate)
            results.append({'test':name,'gate':gate})
            if not gate.get('passed'):return {'passed':False,'failure':['accepted-baseline-regression'], 'regressions':results}
        if 'combat' in task.get('checks',[]):
            from loop_controller.combat_checks import FOOT_PROBE,WALL_PROBE,DRIVE_PROBE,inspect_combat_contract
            from loop_controller.aim_checks import AIM_PROBES,inspect_aim_contract
            aim_required=task['id'] in ('rough-whole-route','chicago-polish-whole-route')
            for kind,probe in [('foot',FOOT_PROBE),('wall',WALL_PROBE),('driving',DRIVE_PROBE)]:
                bundle=self.store.root/'evidence'/(ident+'-regression-combat-'+kind)
                gate=self.engines.unity(self.project,bundle,probe,candidate)
                if gate.get('passed'):
                    rows=[json.loads(line) for line in (bundle/'captures/trace.jsonl').read_text().splitlines()]
                    contract=inspect_combat_contract(rows,kind)
                    contract.update(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),build_id=gate['build_id'])
                    gate.update(combat_contract=contract,passed=contract['passed'],failure=contract.get('failure'))
                    if gate.get('passed') and aim_required and kind in ('foot','wall'):
                        events=[json.loads(line) for line in (bundle/'captures/aim-shots.jsonl').read_text().splitlines()]
                        aim=inspect_aim_contract(events,'aligned' if kind=='foot' else 'wall')
                        aim.update(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),build_id=gate['build_id'])
                        gate.update(aim_contract=aim,passed=aim['passed'],failure=aim.get('failure'))
                atomic(bundle/'combat-regression-gate.json',gate)
                results.append({'test':'combat-'+kind,'gate':gate})
                if not gate.get('passed'):return {'passed':False,'failure':['accepted-combat-regression'],'regressions':results}
            if aim_required:
                for kind in ('miss','near-cover'):
                    bundle=self.store.root/'evidence'/(ident+'-regression-aim-'+kind)
                    gate=self.engines.unity(self.project,bundle,AIM_PROBES[kind],candidate)
                    if gate.get('passed'):
                        events=[json.loads(line) for line in (bundle/'captures/aim-shots.jsonl').read_text().splitlines()]
                        aim=inspect_aim_contract(events,kind)
                        aim.update(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),build_id=gate['build_id'])
                        gate.update(aim_contract=aim,passed=aim['passed'],failure=aim.get('failure'))
                    atomic(bundle/'aim-regression-gate.json',gate)
                    results.append({'test':'aim-'+kind,'gate':gate})
                    if not gate.get('passed'):return {'passed':False,'failure':['aim-alignment-or-cover-regression'],'regressions':results}
        return {'passed':True,'regressions':results}

    def promote(self,task,candidate,bundle,gate,review):
        if gate.get('acceptance_fixture'):raise Halt('A diagnostic fixture cannot promote a playable game')
        if not gate.get('passed') or not review.get('ok') or review.get('verdict')!='PASS':raise Halt('Cannot promote unverified candidate')
        if 'mission_complete' in task.get('checks',[]) and not gate.get('scoped_facts',{}).get('mission_anchors',{}).get('passed'):
            raise Halt('Mission promotion requires the automatic world-anchor and input-transition gate')
        if 'combat' in task.get('checks',[]) and not require_combat_contracts(gate):
            raise Halt('Combat promotion requires current-source foot/wall/driving contracts and sustained escape')
        if task.get('id') in ('rough-whole-route','chicago-polish-whole-route'):
            from loop_controller.aim_checks import require_aim_contracts
            if not require_aim_contracts(gate):
                raise Halt('Whole-route promotion requires current-source aligned hit, intentional miss and wall/near-cover proof')
        records=self.store.get('accepted_queue_features',{})
        record={'candidate':candidate,'scope':task['id'],'accepted_utc':now(),
                'evidence':str(bundle.relative_to(self.store.root)),'review':review,'final_game_accepted':False}
        records[task['id']]=record
        atomic(self.project/'Notes'/('continuous-'+task['id']+'.json'),record)
        git(self.repo,'add','--','game/Notes/continuous-'+task['id']+'.json')
        git(self.repo,'-c','user.name=Evidence controller','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Record scoped queue PASS: '+task['id']+'\n\nGame source: local Qwen. Evidence metadata: cloud controller. Final quality remains separate.')
        saved=git(self.repo,'rev-parse','HEAD')
        self.store.set(accepted_queue_features=records,last_playable_checkpoint=saved,source_checkpoint=saved,
                       task_index=self.store.get('task_index',0)+1,stage='accepted',feedback={},task_design='',
                       failure_streak=0,failure_key=None,task_failures=0,diagnosis_used=False,
                       last_verified_progress_epoch=time.time(),last_verified_progress_utc=now())
        self.store.event('queue-auto-advance',feature=task['id'],playable_checkpoint=saved,next_index=self.store.get('task_index'))
        self.store.report()

    def reject_scoped(self,task,ident,feedback,candidate):
        key=failure_key({k:feedback[k] for k in ('failure','compile_errors','verdict','fixes') if k in feedback})
        streak=self.store.get('failure_streak',0)+1 if key==self.store.get('failure_key') else 1
        attempts=self.store.get('task_failures',0)+1
        self.store.set(feedback=feedback,failure_key=key,failure_streak=streak,task_failures=attempts,stage='rejected')
        self.store.event('queue-candidate-rejected',candidate=candidate,task=task['id'],streak=streak,attempts=attempts)
        if streak>=3 or attempts>=6:
            if not self.store.get('diagnosis_used'):
                diagnosis=self.design(task,ident+'-repeated',diagnosis=True)
                self.store.set(diagnosis_used=True)
                if not diagnosis.get('ok'):
                    raise Halt('Repeated blocker diagnosis supplied no plan; preserve failure counters and source')
                self.store.set(failure_streak=0,task_failures=0)
            else:
                known=self.store.get('last_playable_checkpoint')
                archive=self.store.root/'failed-source'/ident;archive.parent.mkdir(parents=True,exist_ok=True)
                shutil.move(str(self.project),archive)
                subprocess.run(['git','-C',str(self.repo),'restore','--source',known,'--worktree','--staged','--','game'],check=True)
                git(self.repo,'-c','user.name=Controller recovery','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
                    'commit','--allow-empty','-m','Restore verified playable state after diagnosed repeated blocker')
                self.store.event('queue-recovery',preserved_candidate=candidate,restored=known,archive=ident)
                raise Halt('Repeated diagnosed blocker on '+task['id']+'; failed source preserved and last playable state restored')

    def work(self):
        self.model.ready()
        while self.store.get('task_index',0)<len(TASKS):
            self.machine.guard()
            index=self.store.get('task_index',0);task=TASKS[index]
            ident='q%04d-%s'%(self.store.get('rounds',0)+1,uuid.uuid4().hex[:8])
            self.store.set(current_round=ident,rounds=self.store.get('rounds',0)+1,phase=task['phase'],
                current_task=task['outcome'],next_task=TASKS[index+1]['outcome'] if index+1<len(TASKS) else 'Whole-game evidence review',
                stage='local-microtask');self.store.report()
            if task.get('design') and not self.store.get('task_design'):self.design(task,ident)
            result=self.edit(task,ident)
            candidate=self.checkpoint_source('Local Qwen: '+task['id']+' / '+ident)
            self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
            # Presentation-only exports keep the proven input/camera fixture.
            # They receive scoped visual review and never satisfy whole-route pacing.
            if task.get('polish'):
                from qualify_visual_replay import qualify_saved_visual_candidate
                if qualify_saved_visual_candidate(self,task,ident,candidate):continue
            probe=task.get('probe') or result.get('scenario')
            if not probe:
                self.store.event('separate-replay-role',task=task['id'],saved_candidate=candidate,
                                 builder_stop=result.get('bounded_stop'),native_pass_claimed=False)
                probe=self.propose_replay(task,ident)['scenario']
            # A valid model tool call is not enough: check replay semantics before engine admission.
            if not task.get('probe'):
                probe=validate_proposed(probe,task['maximum'],task['coverage'])
            self.store.set(stage='native-scoped-gate');self.store.report()
            bundle,gate=self.native(task,ident,candidate,probe)
            if gate.get('passed'):
                regression=self.regress(task,ident,candidate)
                gate['regressions']=regression
                if not regression['passed']:gate.update(passed=False,failure=regression['failure'])
                atomic(bundle/'scoped-gate.json',gate)
            if not gate.get('passed'):
                self.reject_scoped(task,ident,gate,candidate);continue
            self.store.set(stage='fresh-scoped-critique');self.store.report()
            review=self.review(task,ident,bundle,gate)
            if review.get('verdict')!='PASS' or not review.get('ok'):
                self.reject_scoped(task,ident,review,candidate);continue
            self.promote(task,candidate,bundle,gate,review)
        self.store.set(status='reviewable-delivery',stage='idle',
            blocker='Whole-route evidence ready for parent review; no automatic final art/audio/performance claim')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous-run',required=True,type=Path);p.add_argument('--run-dir',required=True,type=Path)
    a=p.parse_args();os.umask(0o077)
    if a.run_dir.exists():raise Halt('Use a fresh ledger; never overwrite or silently resume another owner')
    old=read_json(a.previous_run/'status.json');c=read_json(a.previous_run/'private-config.json')
    if old.get('controller_pid') or old['status']!='paused-scope-complete':raise Halt('Expected the completed baseline owner')
    if git(Path(c['game_repository']),'rev-parse','HEAD')!=BASELINE:raise Halt('Expected accepted baseline754dd595')
    if git(Path(c['game_repository']),'status','--porcelain'):raise Halt('Preserve unexpected working-tree changes')
    deadline=old['overall_deadline_epoch'];started=time.time()
    if deadline<=started:raise Halt('Original overall ceiling expired')
    c.update(wall_hours=(deadline-started)/3600,output_tokens=8192,model_timeout_seconds=400,csharp_only=True)
    a.run_dir.mkdir(mode=0o700);atomic(a.run_dir/'private-config.json',c)
    r=ContinuousRunner(a.run_dir,c);s=r.store
    hashes={n:sha((a.previous_run/n).read_bytes()) for n in ('state.sqlite3','status.json')}
    original=r.machine.guard
    def guard():
        original()
        if time.time()>=deadline:raise Halt('Original overall ceiling reached')
    r.machine.guard=guard;r.model.guard=guard
    def stop(*_):raise Halt('Original overall deadline or explicit stop')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    signal.alarm(max(1,int(deadline-time.time())))
    with exclusive(Path(c['coordination_dir'])/'game-owner.lock'),exclusive(a.run_dir/'controller.lock'):
        s.set(status='running',controller_pid=os.getpid(),owner='sole execution controller',manager='parent dot',
              started_epoch=started,started_utc=now(),overall_deadline_epoch=deadline,source_checkpoint=BASELINE,
              preserved_baseline=BASELINE,last_playable_checkpoint=BASELINE,accepted_checkpoint=None,
              accepted_subfeatures=old['accepted_subfeatures'],accepted_queue_features={},tasks=TASKS,task_index=0,
              previous_run=a.previous_run.name,previous_record_sha256=hashes,blocker=None,
              policy='Auto-advance every scoped PASS; stop only repeated diagnosed blocker, access/resource fault or original ceiling')
        s.event('authorized-continuous-queue',baseline=BASELINE,prior_records_preserved=True,
                game_author='local Qwen',cloud_role='controller, acceptance, measured supervision',overall_ceiling_unchanged=True)
        s.report()
        try:r.work()
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:
            signal.alarm(0)
            candidate=r.checkpoint_source('Preserve local queue candidate at exit')
            s.set(controller_pid=None,source_checkpoint=candidate,
                  previous_failure_record_unchanged=all(sha((a.previous_run/n).read_bytes())==h for n,h in hashes.items()))
            s.report()
    return 0

if __name__=='__main__':raise SystemExit(main())
