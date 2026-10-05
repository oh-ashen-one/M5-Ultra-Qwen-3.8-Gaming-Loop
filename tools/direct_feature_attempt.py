#!/usr/bin/env python3
"""Fresh bounded run: known local repair -> limited milestone -> vehicle microtasks."""
import argparse
import json
import os
from pathlib import Path
import signal
import time

from inspect_and_repair_grounding import grounding_scenario, summarize
from loop_controller.core import Files,Halt,atomic,exclusive,now,read_json,seal,sha,verify_seal
from loop_controller.features import accept_subfeature,pavement_coverage
from loop_controller.model import tool
from loop_controller.runner import Runner,git
from loop_controller.small_edits import SelectedEdit

S={'type':'string'};B={'type':'boolean'}


class DirectRunner(Runner):
    def guard(self):
        self.machine.guard()
        if time.time()>=self.store.get('attempt_deadline_epoch'):raise Halt('Fresh attempt deadline reached')
        last=self.store.get('last_verified_progress_epoch',self.store.get('started_epoch'))
        if time.time()-last>self.c['verified_progress_minutes']*60:
            raise Halt('No new verified subfeature within this attempt window')

    def edit(self,ident,goal,anchor=None,path='Assets/Game/Bootstrap.cs',max_lines=12):
        self.guard();files=Files(self.project,self.store)
        context=files.read('Assets/Game/Bootstrap.cs',line_count=200)['content']
        if anchor:
            lines=files.path(path).read_text().splitlines(keepends=True)
            matches=[i for i,line in enumerate(lines) if anchor in line]
            if len(matches)!=1:raise Halt('Direct selection must match one exact current line')
            edit=SelectedEdit(files,path,matches[0]+1,matches[0]+1,max_lines)
            before=edit.before;selected=edit.old
            dispatch=lambda action,f:edit.apply(action,f['content'])
        else:
            if files.path(path).exists():raise Halt('New local module already exists; do not overwrite')
            before=None;selected='NEW FILE: '+path
            def dispatch(action,f):
                if len(f['content'].splitlines())>max_lines:raise ValueError('New module exceeds line budget')
                return files.create(action,path,f['content'])
        self.c.update(output_tokens=8192,model_timeout_seconds=300)
        self.store.set(stage='direct-local-edit',current_round=ident,current_task=goal,phase='foundation' if ident=='corridor' else 'driving')
        self.store.event('direct-task',task_id=ident,path=path,goal=goal,planner_bypassed=True,game_author='local Qwen')
        self.store.report()
        prompt=('Implement this measured, already-selected task and SAVE through the tool now. Thinking is enabled at low effort. '
                'Do not re-plan the game. No new art, assets, cameras, acceptance changes or physics changes outside the stated task. '
                'Preserve all unselected code. The next response should be a complete tool call. '
                f'Maximum {max_lines} replacement/new-file lines.\nTASK:\n'+goal+
                '\nEXACT SELECTED SPAN:\n'+selected+'\nCURRENT BOOTSTRAP CONTEXT:\n'+context)
        if ident=='vehicle-install':
            prompt+='\nEXACT NEW MODULE:\n'+files.read('Assets/Game/VehicleInteraction.cs',line_count=100)['content']
        outcome=self.model.session('builder',ident+'-direct',
            'You are local Qwen, the substantive C# author. Save the one concrete mechanical edit first.',prompt,
            [tool('edit_selected_span','Save the exact selected span or designated new module; hash/scope are enforced.',{'content':S})],
            {'edit_selected_span':dispatch},turns=1,reasoning_effort='low')
        if not files.path(path).exists() or sha(files.path(path).read_bytes())==before:
            self.store.event('direct-edit-stopped',task_id=ident,bounded_stop=outcome.get('bounded_stop'),saved=False)
            raise Halt('Direct local edit saved no change; diagnose before any retry')
        candidate=self.checkpoint_source('Local Qwen: '+ident+' bounded direct edit')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate,last_source_progress_utc=now())
        self.store.event('source-progress',candidate=candidate,task_id=ident,final_acceptance_unchanged=True)
        return candidate

    def native(self,ident,scenario):
        self.guard();candidate=git(self.repo,'rev-parse','HEAD')
        bundle=self.store.root/'evidence'/ident
        self.store.set(stage='native-'+ident);self.store.report()
        gate=self.engines.unity(self.project,bundle,scenario,candidate)
        if scenario['coverage']=='foundation' and (bundle/'captures/scene-transforms.json').exists():
            observed=summarize(bundle);atomic(bundle/'world-observations.json',observed)
            gate['stationary_grounded']=observed['stationary_grounded']
            if not gate['stationary_grounded']:
                gate.update(passed=False,failure=['stationary-grounding-preflight',gate.get('failure')])
        atomic(bundle/'grounding-gate.json',gate)
        self.store.set(latest_evidence=str(bundle.relative_to(self.store.root)),feedback=gate,
            latest_captures=[str(p.relative_to(self.store.root)) for p in sorted((bundle/'captures').glob('frame-*.png'))])
        self.store.report()
        if not gate.get('passed'):raise Halt('Native candidate failed; preserve evidence for diagnosis')
        return bundle,gate

    def scoped_review(self,ident,bundle,gate,coverage=None):
        self.guard();capture_hash=seal(bundle/'captures',{'candidate':gate['candidate_commit'],'scope':ident})
        frames=sorted((bundle/'captures').glob('frame-*.png'))
        chosen=[frames[0],frames[1],frames[-1]] if ident=='foundation-short-walk' else frames
        names=[p.name for p in chosen]
        def submit(_,f):
            if f['verdict'] not in ('PASS','FIX','UNVERIFIED'):raise ValueError('Use PASS, FIX, UNVERIFIED')
            if not any(n in f['summary'] for n in names):raise ValueError('Summary must cite an exact actual frame filename')
            return {'ok':True,**f}
        scope=('Grounded control, readable third-person camera, visibly rendered blue coupe, and continuous visible paved '
               'surface beneath the entire approximately19m walking route. Buildings and props may remain rough. '
               'A surface-bounds pass alone cannot prove a good render: inspect start/middle/end. '
               'The player must not end on brown unrendered background.' if ident=='foundation-short-walk' else
               'A limited vehicle entry, forward driving over3m, exit and return to walking demonstration with the same blue coupe. '
               'Judge visible car/player coherence, not final driving feel or full collision/audio quality.')
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='scoped-critic',current_task=scope);self.store.report()
        result=self.model.session('critic',ident+'-review',
            'You are a fresh local visual critic. Judge this explicitly limited subfeature from actual evidence only.',
            'SCOPE: '+scope+'\nFinal ten-minute game, Chicago-target art quality, HUD/audio/FPS and mission acceptance remain unmet. '
            'Do not require those broader deliverables for this milestone, and do not claim they passed. '
            'Return PASS only if the stated limited scope is supported. Keep summary concise and cite supplied filenames. '
            'Set camera_readable, car_visible and continuous_paving truthfully from the images. '
            '\nNATIVE OBSERVATIONS:\n'+json.dumps(gate)+'\nSURFACE OBSERVATIONS:\n'+json.dumps(coverage)+
            '\nSUPPLIED ACTUAL FILES: '+json.dumps(names),
            [tool('submit_review','Judge only the limited subfeature; final-quality acceptance is separate.',
                  {'verdict':S,'summary':S,'camera_readable':B,'car_visible':B,'continuous_paving':B})],
            {'submit_review':submit},images=[('ACTUAL NATIVE UNITY '+p.name,p) for p in chosen],turns=2,reasoning_effort='xhigh')
        verify_seal(bundle/'captures',capture_hash);atomic(bundle/'scoped-critic.json',result)
        return result

    def milestone(self,ident,bundle,gate,review,coverage=None):
        record=accept_subfeature(self.store,ident,gate['candidate_commit'],str(bundle.relative_to(self.store.root)),gate,review,coverage)
        notes=self.project/'Notes';notes.mkdir(exist_ok=True)
        atomic(notes/(ident+'-milestone.json'),record)
        git(self.repo,'add','--','game/Notes/'+ident+'-milestone.json')
        git(self.repo,'-c','user.name=Evidence controller','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
            'commit','-m','Record limited verified subfeature: '+ident+'\n\nEvidence metadata: cloud controller; game source: local Qwen. Final game acceptance remains open.')
        self.store.set(source_checkpoint=git(self.repo,'rev-parse','HEAD'),stage='subfeature-accepted');self.store.report()

    def work(self):
        self.model.ready();self.guard()
        self.edit('corridor',
            'Preserve this street-position assignment, then instance ONLY an existing sidewalk mesh with its material as a '
            'continuous visible pavement/road apron. Existing two Street modules coverZ0..28 but sidewalk width is onlyX-0.8..2.4. '
            'Actual player route isX0..3.2003,Z1.7..20.3354; player radius0.32. Fit the added flat surface bounds to approximately '
            'X-1..6 andZ-2..30, keeping topY0.14. Use the sidewalk Renderer from the existing street instance; do not clone an entire '
            'building. Preserve imported FBX basis when cloning, and account for its world/local scale axes when fitting bounds. '
            'Name the rendered clone Pavement. Do not alter existing colliders, player, camera, car or props. No new primitive/art. '
            'A small bounded search of child renderers is allowed. This must immediately instantiate a visible surface; no unused helper.',
            anchor='street.transform.position = new Vector3(-0.9f, 0f, 7f);',max_lines=14)
        bundle,gate=self.native('corridor',grounding_scenario())
        coverage=pavement_coverage(bundle);atomic(bundle/'pavement-coverage.json',coverage)
        self.store.set(pavement_coverage=coverage);self.store.report()
        if not coverage['passed']:raise Halt('Rendered pavement bounds do not cover the unchanged full route with clearance')
        review=self.scoped_review('foundation-short-walk',bundle,gate,coverage)
        self.milestone('foundation-short-walk',bundle,gate,review,coverage)
        self.edit('vehicle-module',
            'Create a small ChicagoGame.VehicleInteraction MonoBehaviour with public static Install(GameObject player, '
            'GameObject importedCoupe, Follow follow). It is called once after existing Follow setup. Implement ordinary LoopInput '
            'E press near the coupe (within2.5m) to enter; a later E exits safely beside it. Use a unit upright runtime vehicle root '
            'with the existing imported coupe as visual child preserving world geometry/orientation. Keep the parked car position. '
            'On entry disable Walker/CharacterController and hide only PlayerVisual; set LoopSignals.Vehicle to the actual moving '
            'vehicle root and Mode from real state. Follow the vehicle while driving and restore player follow, visible character, '
            'Walker/CC and Mode foot on exit. Drive with LoopInput W/S throttle/brake and A/D steering using deltaTime, bounded speed '
            'and ground-respecting collision. Preserve original mesh/materials, no new art. This is an early entry/driving microtask, '
            'not finished vehicle physics, audio or final quality. No harness/replay detection or artificial telemetry. '
            'No public/private APIs outside Unity/LoopInput/LoopSignals and current game classes. Save a complete compact module.',
            path='Assets/Game/VehicleInteraction.cs',max_lines=90)
        self.native('vehicle-module-walk-regression',grounding_scenario())
        self.edit('vehicle-install',
            'Preserve the existing Follow target assignment, then invoke the new VehicleInteraction.Install exactly once with '
            'existing body, coupe and Follow component. Guard a missing coupe. No other change. The new module is supplied below.',
            anchor='rig.AddComponent<Follow>().target = body.transform;',max_lines=3)
        scenario={'id':'limited-vehicle-entry-drive-exit','coverage':'driving','duration':18,
            'steps':[{'start':4,'end':5.5,'keys':['W']},{'start':5.5,'end':6.5,'keys':['D']},
                     {'start':7,'end':7.25,'keys':['E']},{'start':8,'end':10,'keys':['W']},
                     {'start':10,'end':11,'keys':['S']},{'start':12,'end':12.25,'keys':['E']},
                     {'start':13,'end':15,'keys':['W']}], 'captures':[3.2,6.8,9.5,12.8,16]}
        bundle,gate=self.native('vehicle-entry-drive-exit',scenario)
        review=self.scoped_review('vehicle-entry-drive-exit',bundle,gate)
        self.milestone('vehicle-entry-drive-exit',bundle,gate,review)
        self.store.set(status='paused-scope-complete',stage='idle',blocker=None,
            next_task='Inspect driving feel/collision regression, then continue the original game plan; final quality remains unmet')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-run',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--authorize-bounded-continuation',action='store_true')
    a=parser.parse_args()
    if not a.authorize_bounded_continuation:parser.error('Current parent authorization required')
    os.umask(0o077)
    if a.run_dir.exists():raise Halt('Fresh attempt requires a new ledger; preserve every previous run')
    old=read_json(a.previous_run/'status.json')
    if old.get('controller_pid') or old['status']!='paused':raise Halt('Previous sole owner must be stopped')
    c=read_json(a.previous_run/'private-config.json')
    known=read_json(a.previous_run/old['latest_evidence']/'grounding-gate.json')
    if not known.get('stationary_grounded') or known['candidate_commit']!=git(Path(c['game_repository']),'rev-parse','HEAD'):
        raise Halt('Current source must match the previous grounded candidate')
    hashes={name:sha((a.previous_run/name).read_bytes()) for name in ('state.sqlite3','status.json')}
    started=time.time();deadline=min(started+3600,old['overall_deadline_epoch'])
    if deadline<=started:raise Halt('Overall authorization ceiling expired')
    c.update(wall_hours=1,verified_progress_minutes=20,output_tokens=8192,planner_output_tokens=16384,
             planner_timeout_seconds=600,model_timeout_seconds=300,csharp_only=True)
    a.run_dir.mkdir(mode=0o700);atomic(a.run_dir/'private-config.json',c)
    r=DirectRunner(a.run_dir,c);s=r.store
    s.set(started_epoch=started,started_utc=now(),attempt_deadline_epoch=deadline,
          overall_deadline_epoch=old['overall_deadline_epoch'],previous_run=a.previous_run.name,
          previous_record_sha256=hashes,source_checkpoint=known['candidate_commit'],
          final_acceptance_tasks=old['tasks'],accepted_checkpoint=None,accepted_subfeatures={},
          owner='sole execution controller',manager='parent dot',status='running',controller_pid=os.getpid(),
          current_task='Direct local pavement repair',next_task='Limited foundation milestone then vehicle entry/driving',
          bounds={'fresh_attempt_minutes':60,'without_verified_subfeature_minutes':20,'direct_edits':3,'identical_retries':0})
    original_guard=r.machine.guard
    def bounded_guard():
        original_guard()
        if time.time()>=deadline:raise Halt('Fresh attempt deadline reached')
        if time.time()-s.get('last_verified_progress_epoch',started)>1200:raise Halt('Verified subfeature progress window exhausted')
    r.machine.guard=bounded_guard;r.model.guard=bounded_guard
    def stop(*_):raise Halt('Fresh attempt deadline or explicit stop')
    signal.signal(signal.SIGALRM,stop);signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    signal.alarm(max(1,int(deadline-time.time())))
    with exclusive(Path(c['coordination_dir'])/'game-owner.lock'),exclusive(a.run_dir/'controller.lock'):
        s.event('cloud-infrastructure-intervention',action='Fresh explicitly authorized bounded direct repair and separate subfeature milestones',
                prior_records_preserved=True,game_code_author='local Qwen',planner_bypassed_for_known_repairs=True)
        s.report()
        try:r.work()
        except Exception as e:
            s.set(status='paused',blocker=type(e).__name__+': '+str(e));s.event('stopped',error_type=type(e).__name__,message=str(e))
        finally:
            signal.alarm(0)
            candidate=r.checkpoint_source('Preserve local direct-edit candidate at bounded exit')
            unchanged=all(sha((a.previous_run/name).read_bytes())==digest for name,digest in hashes.items())
            s.set(controller_pid=None,source_checkpoint=candidate,previous_failure_record_unchanged=unchanged);s.report()
    return 0

if __name__=='__main__':raise SystemExit(main())
