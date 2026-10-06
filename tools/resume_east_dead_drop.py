#!/usr/bin/env python3
"""Implement the saved local chapter design through scoped game-only tools."""
import copy
import json
import re
from resume_mission_pacing_design import MissionPacingDesign, SOURCE, ACCEPTED, evidence
from resume_three_day_queue import main
from continue_game_queue import ContinuousRunner, ReadBoundEdits
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.continuous_tasks import TASKS
from loop_controller.continuous_checks import validate_proposed,scenario
from loop_controller.route_chapter import inspect_chapter
from loop_controller.replay_contract import finish_tool,validate_submission
from loop_controller.runner import git

ROUND='q0093-a7aec9b3'
PLAN_SHA='a66148068032209bec56b8a541918643cd5126da76793bbd1b0ad3db96a53a70'
PATH='Assets/Game/RouteMission.cs'
BOOT='Assets/Game/Bootstrap.cs'
TASK=dict(id='east-dead-drop',phase='mission',checks=['mission_complete'],maximum=180,coverage='mission-core',
    outcome='Real courier handoff, driving arrival at the east cache, E exit, close F interaction and R reset.',
    instructions='Judge this short connected chapter, not ten-minute or final art acceptance. Require the actual east '
    'cache, readable non-overlapping objective text, visible driving approach and on-foot interaction, and reset. '
    'Keep broader street and camera visual FIX findings open. No timer padding or primitive marker replacements.')
NO_HANDOFF=scenario(18,[(4,5,['W']),(6,6.35,['F']),(8,8.35,['F'])],[3,5.5,9,16],'chapter-inactive-red')

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,mission_pacing_design_attempted=True,
        stage='connected-mission-design-saved',
        blocker='Halt: Connected mission design saved; dedicated external acceptance and local source implementation are next')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('east_dead_drop_implementation_attempted'):
        raise Halt('Expected exact saved local mission design and unchanged history')

def validate_module(content):
    if not isinstance(content,str) or len(content.encode())>14000 or len(content.splitlines())>190:
        raise ValueError('Create one compact game component, at most190lines/14KB')
    for term in ['LoopInput.Replay','LoopRuntime','LoopRouteObservation','GetCommandLineArgs','System.IO',
                 'class LoopSignals','MissionComplete','UnityEditor','CreatePrimitive']:
        if term in content:raise ValueError('Use actual game APIs and original meshes; prohibited: '+term)
    if re.search(r'LoopSignals\.\w+\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):
        raise ValueError('This additive chapter reads existing LoopSignals; never write legacy or protected state')
    required=['class RouteMission','RouteStage','RouteComplete','Cache','Objective']
    if any(x not in content for x in required):raise ValueError('Preserve the agreed externally observed game-component API')
    return content

class EastDeadDrop(MissionPacingDesign):
    def validate_recovery(self,old):
        validate_pause(old)
        from resume_mission_pacing_design import ROUND as street_round
        evidence(self.store.root/'evidence'/street_round)
        if sha((self.store.root/'evidence'/ROUND/'connected-mission-plan.json').read_bytes())!=PLAN_SHA:
            raise Halt('Saved local design changed')
        if (self.project/PATH).exists():raise Halt('Never overwrite an existing chapter component')
        self.accepted_probe()

    def recovery_settings(self):
        return dict(east_dead_drop_implementation_attempted=True,
            recovery_route='local-east-dead-drop-additive-chapter',
            recovery_change='Correct nonexistent mission API; local game-component state; immutable observer and additive chapter gates; preserve street FIX and old mechanics')

    def source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files)
        raw=(self.project/BOOT).read_text()
        source='\n'.join([p+'\n'+(self.project/p).read_text() for p in
            ['Assets/Game/Mission.cs','Assets/Game/HudStatus.cs']])
        source+='\nBOOTSTRAP INSTALL CONTEXT:\n'+raw.split('    public class Follow')[0]
        plan=read_json(self.store.root/'evidence'/ROUND/'connected-mission-plan.json')
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-east-dead-drop-module');self.store.report()
        def create(action,fields):
            content=validate_module(fields['content'])
            return edits.create(action,dict(path=PATH,content=content))
        self.model.session('builder',ident+'-module',
            'You are local Qwen, sole substantive gameplay author. Save one compact RouteMission.cs module now.',
            'Implement your saved East Dead-Drop design as a SHORT chapter, not final ten-minute completion. '
            'Important verified API corrections: external LoopSignals has Player,Vehicle (Transform), Mode and Mission '
            '(string), Health(float), Shots,Hits,PursuitLevel,Restarts(int). There is NO MissionComplete field. '
            'CourierMission writes to that absent member by tolerant reflection; it does not exist. Read actual '
            'LoopSignals.Mission == "complete" for the legacy handoff. DO NOT edit or redefine LoopSignals, harness, '
            'Mission.cs, VehicleInteraction.cs, camera or combat. Add game-owned public instance fields on RouteMission: '
            'int RouteStage (0 inactive,1 active,2 chapter complete); bool RouteComplete; Transform Cache; string Objective. '
            'Expose static Install(GameObject player,Camera cam). A separate small edit installs it once. '
            'Create one stationary host. Before legacy completion keep chapter inactive, cache hidden and no duplicate HUD. '
            'After real courier ending activate the fixed cache at (50,0.14,18). Cache must be a stationary unparented/world '
            'Transform at that exact anchor, with rendered mesh children grounded at pavementY0.14. Reuse existing original '
            'GameObject.Find("AlleyDumpster") or GameObject.Find("dumpster_a") mesh hierarchy, retaining shared Mesh assets, '
            'correct orientation and scale. Clone to a child under the cache anchor; align child world bounds to the anchor '
            'without moving Cache itself. No primitives/new art. Remove/disable colliders ONLY on the new decorative clone, '
            'never the source, player or world. Use copied materials for cyan/green status without repainting original props. '
            'Require actual Mode vehicle and Vehicle XZ distance<=6m AFTER activation, then a real vehicle->foot mode '
            'transition, then fresh LoopInput.Pressed(F) while Mode foot and player XZ distance<=1.5m. Only then set stage2 '
            'and your RouteComplete=true. Holding F early or remote F must not finish. Stage2 HUD must say EAST DEAD-DROP '
            'COMPLETE, not imply the entire game is done. No timer lock or timeout for this follow-on chapter. '
            'Restarts change must clear all chapter progress, hide marker/HUD and wait for a fresh legacy delivery; return '
            'early from that reset update to avoid same-frame handoff races. Do not change legacy Mission or other signals. '
            'Use a compact camera-child TextMesh with LegacyRuntime.ttf, a visible readout of objective/distance/controls, '
            'at a different screen location from existing top courier/health text. Avoid a solid world-primitive backing. '
            'While chapter active keep Objective non-empty and rendered text containing EAST DEAD-DROP. '
            'Preserve every legacy courier/retry/combat/camera behavior. No replay/fixture introspection or generated telemetry. '
            'Call create_route_module with complete source <=190lines now; do not request other files or write a replay. '
            '\nYOUR ORIGINAL PLAN (API corrections above supersede its mistaken references):\n'+json.dumps(plan)+
            '\nEXACT CURRENT SOURCE:\n'+source,
            [tool('create_route_module','Create the one new game component.',{'content':{'type':'string'}})],
            {'create_route_module':create},turns=1,reasoning_effort='low')
        if not (self.project/PATH).exists():raise Halt('Local chapter module was not saved; preserve complete/partial response evidence')
        saved=self.checkpoint_source('Local Qwen: add East Dead-Drop chapter module')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        needle='Combat.Install(body,cam);'
        candidates=[(i,line) for i,line in enumerate(raw.splitlines(),1) if 'Combat.Install(' in line]
        if len(candidates)!=1:raise Halt('Expected one exact existing combat install anchor')
        line,text=candidates[0];edit=SelectedEdit(files,BOOT,line,line,max_lines=3)
        def install(action,f):
            content=f['content']
            compact=re.sub(r'\s+','',content)
            if compact!=re.sub(r'\s+','',text)+'RouteMission.Install(body,cam);':
                raise ValueError('Preserve the exact old install statement and add only RouteMission.Install(body,cam);')
            return edit.apply(action,content)
        self.c.update(output_tokens=1536,model_timeout_seconds=120)
        self.store.set(stage='local-east-dead-drop-install');self.store.report()
        self.model.session('builder',ident+'-install',
            'You are local Qwen making one installation edit for your saved module.',
            'Replace the exact selected line with itself plus one following RouteMission.Install(body,cam); statement. '
            'Do not change any other code.\nSELECTED:\n'+edit.old,
            [tool('edit_selected_span','Install the authored chapter once.',{'content':{'type':'string'}})],
            {'edit_selected_span':install},turns=1,reasoning_effort='low')
        if (self.project/BOOT).read_text()==raw:raise Halt('Saved chapter has no installation edit')
        saved=self.checkpoint_source('Local Qwen: install East Dead-Drop chapter')
        self.store.set(source_checkpoint=saved,candidate_commit=saved);return saved

    def chapter_native(self,ident,candidate,probe,require_complete=True,require_reset=True,expect_inactive=False):
        task=dict(TASK,checks=[]) if expect_inactive else (TASK if require_complete else TASKS[2])
        bundle,gate=ContinuousRunner.native(self,task,ident,candidate,probe)
        if gate.get('passed'):
            rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            check=inspect_chapter(rows,require_complete,require_reset,expect_inactive)
            gate['chapter_contract']=check
            if not check['passed']:gate.update(passed=False,failure=check['failure'])
        atomic(bundle/'chapter-gate.json',gate);return bundle,gate

    def propose_chapter_replay(self,ident,activation):
        sources='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in
            [PATH,'Assets/Game/VehicleInteraction.cs','Assets/Game/ConnectedStreet.cs'])
        walk=(self.project/BOOT).read_text().split('    public class Follow')[0]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-east-dead-drop-replay');self.store.report()
        prompt='Submit one <=180second normal-input route for the saved short chapter. Preserve0..4seconds input-free. '            'Start with the exact accepted courier inputs below but REMOVE its R17 reset so chapter1 completion persists. '            'After delivery around14.3seconds the car faces mostly north nearX1/Z26. Reverse toward the alley atZ14, '            'turn east using actual steering, drive through alleyX6..22/Z8..20 and east street to cache(50,0.14,18). '            'Require actual vehicle approach<=6m, E exit, on-foot approach<=1.5m and fresh F. Then R and a remote F to '            'prove reset. Avoid wall penetration and support gaps. WASD foot motion is world axes; vehicle W/S is throttle '            'and A/D steer. Vehicle turn uses90degrees/s scaled by speed/4 with reverse sign. Do not assume W means east '
        prompt+='without turning. Supply captures of new objective, open X22 junction, cache arrival, exit, F completion, '            'and reset. This is not ten-minute or final-art proof. Submit finish_task only, no edits. '            '\nACCEPTED COURIER INPUTS:\n'+json.dumps(activation)+            '\nACTUAL MODULES:\n'+sources+'\nWALKER:\n'+walk
        result=self.model.session('replay-author',ident+'-chapter-replay',
            'You are local Qwen authoring a bounded physical replay for the saved mission chapter.',
            prompt,[finish_tool()],{'finish_task':lambda _,f:validate_submission(f,TASK)},turns=1,reasoning_effort='low')
        if not result.get('scenario'):raise Halt('Chapter route author supplied no complete normal-input replay')
        return result['scenario']

    def work(self):
        ident=self.begin(TASK,'local-east-dead-drop-module')
        self.store.set(next_task='Native chapter activation/reset, no-handoff red case, full arrival/exit/F route and unchanged regressions')
        candidate=self.source(ident)
        receipt=self.store.get('accepted_queue_features',{})['connected-mission']
        activation=read_json(self.store.root/receipt['evidence']/'captures/scenario.json')
        activation=validate_proposed(activation,150,'mission-core')
        bundle,gate=self.chapter_native(ident+'-activation',candidate,activation,False,True)
        if not gate.get('passed'):raise Halt('Saved chapter failed additive native activation/reset gate')
        self.store.set(east_dead_drop_activation=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),
            gate_sha256=sha((bundle/'chapter-gate.json').read_bytes()),final_game_accepted=False))
        return self.continue_chapter(ident,candidate,activation)

    def continue_chapter(self,ident,candidate,activation):
        _,red=self.chapter_native(ident+'-inactive-red',candidate,NO_HANDOFF,False,False,True)
        if not red.get('passed'):raise Halt('Chapter no-handoff probe failed: '+json.dumps(red.get('failure')))
        probe=self.propose_chapter_replay(ident,activation)
        self.store.set(stage='native-east-dead-drop-route',last_valid_replay=probe);self.store.report()
        bundle,gate=self.chapter_native(ident,candidate,probe)
        if not gate.get('passed'):raise Halt('East Dead-Drop route requires measured diagnosis; preserve source and native chapter failure')
        self.store.set(stage='chapter-legacy-regressions');self.store.report()
        regression=self.regress(TASKS[7],ident,candidate);gate['regressions']=regression
        atomic(bundle/'chapter-gate.json',gate)
        if not regression['passed']:raise Halt('East Dead-Drop changed an accepted legacy mechanic')
        self.store.set(stage='fresh-chapter-critique');self.store.report()
        gate['scope']=TASK['id'];atomic(bundle/'scoped-gate.json',gate)
        review=self.review(TASK,ident,bundle,gate)
        record=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(bundle/'chapter-outcome.json',record);self.store.set(east_dead_drop_outcome=record)
        # Keep broader unaccepted street and final route separate even on chapter PASS.
        self.store.event('east-dead-drop-qualified-scope',**record)
        self.store.report()
        raise Halt('East Dead-Drop scoped qualification recorded; preserve broader visual FIX and continue connected pacing')

if __name__=='__main__':raise SystemExit(main(EastDeadDrop))
