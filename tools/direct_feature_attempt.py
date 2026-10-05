#!/usr/bin/env python3
"""Fresh bounded run: known local repair -> limited milestone -> vehicle microtasks."""
import argparse
import json
import os
from pathlib import Path
import signal
import time
from datetime import datetime

from inspect_and_repair_grounding import grounding_scenario, summarize
from loop_controller.core import Files,Halt,atomic,exclusive,now,read_json,seal,sha,verify_seal
from loop_controller.features import accept_subfeature,pavement_coverage,vehicle_heading,references_capture
from loop_controller.model import tool,typed_arguments
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
                'Input API: LoopInput.Pressed(KeyCode) is edge-triggered; Held(KeyCode), MoveX and MoveY also exist. '
                'There are no per-key E/W/S properties.\n'
                f'Maximum {max_lines} replacement/new-file lines.\nTASK:\n'+goal+
                '\nEXACT SELECTED SPAN:\n'+selected+'\nCURRENT BOOTSTRAP CONTEXT:\n'+context)
        if ident=='vehicle-install':
            prompt+='\nEXACT NEW MODULE:\n'+files.read('Assets/Game/VehicleInteraction.cs',line_count=100)['content']
        schema=tool('edit_selected_span','Save the exact selected span or designated new module; hash/scope are enforced.',{'content':S})
        if ident=='corridor' and self.store.get('recover_local_proposal'):
            # The first save was rejected solely for 15 lines versus 14. Reuse
            # only its submitted tool argument, never its private reasoning.
            response=read_json(self.store.root/'private/sessions/corridor-direct/response-000.json')
            calls=response['choices'][0]['message'].get('tool_calls',[])
            if len(calls)!=1 or calls[0]['function']['name']!='edit_selected_span':raise Halt('Expected one local selected-edit proposal')
            fields=typed_arguments(calls[0]['function'],[schema])
            if len(fields['content'].splitlines())!=15:raise Halt('Recovery applies only to the diagnosed fifteen-line proposal')
            edit=SelectedEdit(files,path,matches[0]+1,matches[0]+1,16)
            if git(self.repo,'rev-parse','HEAD')!=self.store.get('source_checkpoint'):raise Halt('Source checkpoint changed before recovery')
            if git(self.repo,'show','HEAD:game/'+path)!=files.path(path).read_text().strip():raise Halt('Uncommitted source changed before proposal recovery')
            outcome=edit.apply('corridor-recover-local-proposal',fields['content'])
            self.store.event('local-proposal-recovered',original_session='corridor-direct',lines=15,
                exact_tool_payload=True,new_inference=False,hash_check_preserved=True)
            self.store.set(recover_local_proposal=False)
        elif ident=='vehicle-module' and self.store.get('recover_vehicle_proposal'):
            response=read_json(self.store.root/'private/sessions/vehicle-module-direct/response-000.json')
            calls=response['choices'][0]['message'].get('tool_calls',[])
            if len(calls)!=1 or calls[0]['function']['name']!='edit_selected_span':raise Halt('Expected one local module proposal')
            fields=typed_arguments(calls[0]['function'],[schema])
            if len(fields['content'].splitlines())!=92 or len(fields['content'].encode())!=3659:
                raise Halt('Recovery applies only to the diagnosed submitted vehicle module')
            outcome=files.create('vehicle-recover-local-proposal',path,fields['content'])
            self.store.event('local-proposal-recovered',original_session='vehicle-module-direct',lines=92,
                exact_tool_payload=True,new_inference=False,existing_file_protection=True)
            self.store.set(recover_vehicle_proposal=False)
        else:
            outcome=self.model.session('builder',ident+'-direct',
                'You are local Qwen, the substantive C# author. Save the one concrete mechanical edit first.',prompt,
                [schema],{'edit_selected_span':dispatch},turns=1,reasoning_effort='low')
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
        if scenario['coverage']=='driving' and (bundle/'captures/scene-transforms.json').exists():
            gate['vehicle_heading']=vehicle_heading(bundle)
            gate['return_walk_pavement']=pavement_coverage(bundle,only_grounded=True)
            if not gate['vehicle_heading']['passed'] or not gate['return_walk_pavement']['passed']:
                gate.update(passed=False,failure=['vehicle-forward-heading-or-return-pavement',gate.get('failure')])
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
            if not references_capture(f['summary'],names):raise ValueError('Summary must cite an actual supplied frame identifier')
            return {'ok':True,**f}
        scope=('Grounded control, readable third-person camera, visibly rendered blue coupe, and continuous visible paved '
               'surface beneath the entire approximately19m walking route. Buildings and props may remain rough. '
               'A surface-bounds pass alone cannot prove a good render: inspect start/middle/end. '
               'The player must not end on brown unrendered background.' if ident=='foundation-short-walk' else
               'A limited vehicle entry, forward driving over3m, exit and return to walking demonstration with the same blue coupe. '
               'Judge visible car/player coherence, not final driving feel or full collision/audio quality.')
        if ident in ('vehicle-safe-exit-view','vehicle-clear-exit'):
            scope+=' This follow-up specifically requires the on-foot character to be identifiable in BOTH exit frame-003.png and return frame-004.png. Pillar/fence/car occlusion hiding the player is a FIX, not outside scope.'
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='scoped-critic',current_task=scope);self.store.report()
        result=self.model.session('critic',ident+'-review',
            'You are a fresh local visual critic. Judge this explicitly limited subfeature from actual evidence only.',
            'SCOPE: '+scope+'\nFinal ten-minute game, Chicago-target art quality, HUD/audio/FPS and mission acceptance remain unmet. '
            'Do not require those broader deliverables for this milestone, and do not claim they passed. '
            'Return PASS only if the stated limited scope is supported. Keep summary concise and cite supplied filenames. '
            'Set camera_readable, car_visible, continuous_paving and exit_player_visible truthfully from the images. '
            '\nNATIVE OBSERVATIONS:\n'+json.dumps(gate)+'\nSURFACE OBSERVATIONS:\n'+json.dumps(coverage)+
            '\nSUPPLIED ACTUAL FILES: '+json.dumps(names),
            [tool('submit_review','Judge only the limited subfeature; final-quality acceptance is separate.',
                  {'verdict':S,'summary':S,'camera_readable':B,'car_visible':B,'continuous_paving':B,'exit_player_visible':B})],
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

    def corridor(self):
        self.edit('corridor',
            'Preserve this street-position assignment, then instance ONLY an existing sidewalk mesh with its material as a '
            'continuous visible pavement/road apron. Existing two Street modules coverZ0..28 but sidewalk width is onlyX-0.8..2.4. '
            'Actual player route isX0..3.2003,Z1.7..20.3354; player radius0.32. Fit the added flat surface bounds to approximately '
            'X-1..6 andZ-2..30, keeping topY0.14. Use the sidewalk Renderer from the existing street instance; do not clone an entire '
            'building. Preserve imported FBX basis when cloning, and account for its world/local scale axes when fitting bounds. '
            'Name the rendered clone Pavement. Do not alter existing colliders, player, camera, car or props. No new primitive/art. '
            'A small bounded search of child renderers is allowed. This must immediately instantiate a visible surface; no unused helper.',
            anchor='street.transform.position = new Vector3(-0.9f, 0f, 7f);',max_lines=20)
        return self.native('corridor',grounding_scenario())

    def work(self):
        self.model.ready();self.guard()
        if self.store.get('repair_exit_facing'):
            self.edit('vehicle-exit-facing',
                'Change only this player exit-facing assignment. The player now exits on the correct clear side atX2.1, '
                'but facing negative vehicle.right rotates Follow toward the facade: actual exit frame is blocked by a '
                'building/bench. Face the player along the upright vehicle.forward, horizontally along the paved corridor '
                '(+Z in this replay), so the unchanged Follow offset remains over the street. Preserve clear-side position, '
                'vertical clearance, camera code, car heading and all mechanics.',
                anchor='_player.transform.rotation =',path='Assets/Game/VehicleInteraction.cs',max_lines=1)
            self.store.set(repair_exit_facing=False)
            return self.vehicle_test('vehicle-clear-exit',bounded_route=True,feature='vehicle-safe-exit-view')
        if self.store.get('repair_vehicle_exit'):
            self.edit('vehicle-safe-exit',
                'Correct only this exit placement and add its facing assignment. Existing exit uses positive vehicle.right, '
                'putting playerX5.1 in the rail-pier/fence lane (piers nearX5.5); actual final camera is blocked by a pillar. '
                'Place the player on the opposite clear side, 1.5m along negative vehicle.right (aboutX2.1), keeping the same '
                '0.3m vertical clearance. Face the player outward away from the car along negative vehicle.right so Follow '
                'does not look through the coupe at the exit. Preserve all other exit/control/physics behavior and the camera code.',
                anchor='_player.transform.position = transform.position + transform.right * 1.5f',
                path='Assets/Game/VehicleInteraction.cs',max_lines=2)
            self.store.set(repair_vehicle_exit=False)
            return self.vehicle_test('vehicle-safe-exit-view',bounded_route=True,feature='vehicle-safe-exit-view')
        if self.store.get('repair_vehicle_heading'):
            self.edit('vehicle-heading',
                'Preserve the SetParent line, then correct only the imported coupe VISUAL heading relative to its upright '
                'runtime vehicle root. Actual bumper_f centre isZ5.68 and bumper_rZ10.24 while root forward and W motion '
                'are+Z. The visible nose currently points-Z, so W drives the car backward visually. Apply a180-degree '
                'world-up yaw to the imported coupe visual around its existing origin after parenting, preserving imported '
                'tilt/scale and parked position. Do not reverse the runtime movement direction, change root physics, or add assets.',
                anchor='coupe.transform.SetParent(root.transform, true);',path='Assets/Game/VehicleInteraction.cs',max_lines=2)
            self.store.set(repair_vehicle_heading=False)
            return self.vehicle_test('vehicle-heading-corrected',bounded_route=True)
        if 'foundation-short-walk' in self.store.get('accepted_subfeatures',{}):
            return self.vehicle()
        if self.store.get('repair_pavement_axis'):
            self.edit('corridor-axis',
                'Change only this local-scale assignment. Actual native Pavement bounds are worldX0.140002,Y7,Z32 metres; '
                'it is vertical instead of flat. The imported mesh localX maps to worldZ, localY maps to negative worldX, '
                'and localZ maps to worldY (measured up=-X,forward=+Y). Required bounds are worldX7,Y0.14,Z32. '
                'Use these measured axis mappings and existing sharedMesh bounds to correct the one scale assignment. '
                'Preserve position, imported rotation, mesh/material, camera, colliders and all other code.',
                anchor='var ls = new Vector3(',max_lines=1)
            self.store.set(repair_pavement_axis=False)
            bundle,gate=self.native('corridor-axis',grounding_scenario())
        else:bundle,gate=self.corridor()
        coverage=pavement_coverage(bundle);atomic(bundle/'pavement-coverage.json',coverage)
        self.store.set(pavement_coverage=coverage);self.store.report()
        if not coverage['passed']:raise Halt('Rendered pavement bounds do not cover the unchanged full route with clearance')
        review=self.scoped_review('foundation-short-walk',bundle,gate,coverage)
        self.milestone('foundation-short-walk',bundle,gate,review,coverage)
        return self.vehicle()

    def vehicle(self):
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
            path='Assets/Game/VehicleInteraction.cs',max_lines=120)
        module=self.project/'Assets/Game/VehicleInteraction.cs'
        if 'bool e = LoopInput.E;' in module.read_text():
            self.edit('vehicle-input-api',
                'Correct this one input read to use the actual edge-triggered LoopInput.Pressed(KeyCode) API for E. '
                'LoopInput.E does not exist. Preserve all other module code; save one replacement line.',
                anchor='bool e = LoopInput.E;',path='Assets/Game/VehicleInteraction.cs',max_lines=1)
        self.native('vehicle-module-walk-regression',grounding_scenario())
        self.edit('vehicle-install',
            'Preserve the existing Follow target assignment, then invoke the new VehicleInteraction.Install exactly once with '
            'existing body, coupe and Follow component. Guard a missing coupe. No other change. The new module is supplied below.',
            anchor='rig.AddComponent<Follow>().target = body.transform;',max_lines=3)
        return self.vehicle_test('vehicle-entry-drive-exit')

    def vehicle_test(self,ident,bounded_route=False,feature='vehicle-entry-drive-exit'):
        scenario={'id':'limited-vehicle-entry-drive-exit','coverage':'driving','duration':18,
            'steps':[{'start':4,'end':5.5,'keys':['W']},{'start':5.5,'end':6.5,'keys':['D']},
                     {'start':7,'end':7.25,'keys':['E']},{'start':8,'end':10,'keys':['W']},
                     {'start':10,'end':11,'keys':['S']},{'start':12,'end':12.25,'keys':['E']},
                     {'start':13,'end':15,'keys':['W']}], 'captures':[3.2,6.8,9.5,12.8,16]}
        if bounded_route:
            scenario['steps'][3]['end']=9.3
            scenario['steps'][4].update(start=9.3,end=10.3)
        bundle,gate=self.native(ident,scenario)
        review=self.scoped_review(ident,bundle,gate)
        self.milestone(feature,bundle,gate,review)
        if feature=='vehicle-safe-exit-view':
            regression,walk=self.native('final-walk-regression',grounding_scenario())
            coverage=pavement_coverage(regression);atomic(regression/'pavement-coverage.json',coverage)
            if not coverage['passed']:raise Halt('Original short-walk pavement regression failed')
            self.store.set(final_walk_regression={'gate':walk,'pavement':coverage,'evidence':str(regression.relative_to(self.store.root))})
        self.store.set(status='paused-scope-complete',stage='idle',blocker=None,
            next_task='Inspect driving feel/collision regression, then continue the original game plan; final quality remains unmet')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-run',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--authorize-bounded-continuation',action='store_true')
    parser.add_argument('--recover-local-proposal',action='store_true')
    parser.add_argument('--repair-pavement-axis',action='store_true')
    parser.add_argument('--recover-vehicle-proposal',action='store_true')
    parser.add_argument('--repair-vehicle-heading',action='store_true')
    parser.add_argument('--repair-vehicle-exit',action='store_true')
    parser.add_argument('--repair-exit-facing',action='store_true')
    a=parser.parse_args()
    if not a.authorize_bounded_continuation:parser.error('Current parent authorization required')
    os.umask(0o077)
    recovering=a.recover_local_proposal or a.repair_pavement_axis or a.recover_vehicle_proposal or a.repair_vehicle_heading or a.repair_vehicle_exit or a.repair_exit_facing
    if a.run_dir.exists() and not recovering:raise Halt('Fresh attempt requires a new ledger; preserve every previous run')
    old=read_json(a.previous_run/'status.json')
    if old.get('controller_pid') or old['status']!='paused':raise Halt('Previous sole owner must be stopped')
    c=read_json(a.previous_run/'private-config.json')
    known=read_json(a.previous_run/old['latest_evidence']/'grounding-gate.json')
    if not known.get('stationary_grounded') or (not recovering and known['candidate_commit']!=git(Path(c['game_repository']),'rev-parse','HEAD')):
        raise Halt('Current source must match the previous grounded candidate')
    hashes={name:sha((a.previous_run/name).read_bytes()) for name in ('state.sqlite3','status.json')}
    started=time.time();deadline=min(started+3600,old['overall_deadline_epoch'])
    if deadline<=started:raise Halt('Overall authorization ceiling expired')
    c.update(wall_hours=1,verified_progress_minutes=20,output_tokens=8192,planner_output_tokens=16384,
             planner_timeout_seconds=600,model_timeout_seconds=300,csharp_only=True)
    if not recovering:
        a.run_dir.mkdir(mode=0o700);atomic(a.run_dir/'private-config.json',c)
    else:c=read_json(a.run_dir/'private-config.json')
    r=DirectRunner(a.run_dir,c);s=r.store
    if recovering:
        if s.get('controller_pid') or s.get('status') not in ('paused','paused-scope-complete') or s.get('source_checkpoint')!=git(r.repo,'rev-parse','HEAD'):
            raise Halt('Expected the stopped current candidate')
        if a.recover_local_proposal and s.get('source_checkpoint')!=known['candidate_commit']:
            raise Halt('Exact proposal recovery requires the original unchanged source')
        if a.repair_pavement_axis:
            latest=read_json(a.run_dir/s.get('latest_evidence')/'grounding-gate.json')
            if not latest.get('stationary_grounded') or latest['candidate_commit']!=s.get('source_checkpoint'):
                raise Halt('Axis correction requires current native grounding evidence')
        started=s.get('started_epoch');deadline=s.get('attempt_deadline_epoch')
        if time.time()>=min(deadline,s.get('last_verified_progress_epoch',started)+1200):raise Halt('Original fresh-attempt bounds expired')
        if a.recover_vehicle_proposal and 'foundation-short-walk' not in s.get('accepted_subfeatures',{}):
            raise Halt('Vehicle work requires the verified limited foundation')
        if a.repair_vehicle_heading:
            accepted=s.get('accepted_subfeatures',{})
            if 'foundation-short-walk' not in accepted:raise Halt('Preserve the verified foundation before heading correction')
            prior=accepted.pop('vehicle-entry-drive-exit',None)
            if prior:
                evidence=vehicle_heading(a.run_dir/prior['evidence'])
                if evidence['passed']:raise Halt('Expected the measured backward-driving discrepancy')
                superseded=s.get('superseded_subfeatures',[])
                superseded.append({**prior,'status':'requires-correction','reason':'Visual nose opposes W motion; longer return walk leaves pavement','heading_evidence':evidence})
                s.set(superseded_subfeatures=superseded,accepted_subfeatures=accepted,
                    last_verified_progress_epoch=datetime.fromisoformat(accepted['foundation-short-walk']['accepted_utc']).timestamp(),
                    last_verified_progress_utc=accepted['foundation-short-walk']['accepted_utc'])
                note=r.project/'Notes/vehicle-entry-drive-exit-milestone.json'
                atomic(note,superseded[-1]);git(r.repo,'add','--','game/Notes/vehicle-entry-drive-exit-milestone.json')
                git(r.repo,'-c','user.name=Evidence controller','-c','user.email=254017794+oh-ashen-one@users.noreply.github.com',
                    'commit','-m','Supersede vehicle milestone after measured heading discrepancy; preserve prior evidence')
                s.set(source_checkpoint=git(r.repo,'rev-parse','HEAD'))
                s.event('subfeature-superseded',feature='vehicle-entry-drive-exit',heading=evidence,verified_clock_restored_to_foundation=True)
        s.set(recover_local_proposal=a.recover_local_proposal,repair_pavement_axis=a.repair_pavement_axis,
              recover_vehicle_proposal=a.recover_vehicle_proposal,
              repair_vehicle_heading=a.repair_vehicle_heading,
              repair_vehicle_exit=a.repair_vehicle_exit,
              repair_exit_facing=a.repair_exit_facing,
              controller_pid=os.getpid(),status='running',blocker=None)
        s.event('bounded-diagnosed-recovery',reason=('Exit framing still intersects facade; local corridor-aligned facing with unchanged camera' if a.repair_exit_facing else 'Observed exit camera is occluded; local clear-side placement and outward facing' if a.repair_vehicle_exit else 'Native front/rear measurements contradict forward driving; local visual-heading correction and bounded drive replay' if a.repair_vehicle_heading else 'Exact92-line local vehicle proposal plus one measured input API correction' if a.recover_vehicle_proposal else 'Measured native pavement axes require one scale assignment' if a.repair_pavement_axis
                else 'Exact local tool proposal has15lines; allow16 preserving hash and source scope'),
                original_deadline_unchanged=True,original_inference_record_unchanged=True)
        if a.repair_pavement_axis:
            bounds=s.get('bounds');bounds['diagnosed_axis_correction_edits']=1;s.set(bounds=bounds)
        if a.recover_vehicle_proposal:
            bounds=s.get('bounds');bounds['diagnosed_input_api_edits']=1;s.set(bounds=bounds)
        if a.repair_vehicle_heading or a.repair_vehicle_exit:
            bounds=s.get('bounds');bounds['diagnosed_heading_edits']=1
            if a.repair_vehicle_exit:bounds['diagnosed_exit_placement_edits']=1
            s.set(bounds=bounds)
        if a.repair_exit_facing:
            bounds=s.get('bounds');bounds['diagnosed_exit_facing_edits']=1;s.set(bounds=bounds)
    else:s.set(started_epoch=started,started_utc=now(),attempt_deadline_epoch=deadline,
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
