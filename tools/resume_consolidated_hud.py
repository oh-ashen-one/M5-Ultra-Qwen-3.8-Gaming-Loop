#!/usr/bin/env python3
"""Locally author one mission panel, then requalify actual state and inputs."""
import json
import re
from resume_ordered_relay import OrderedRelay,BOOT
from resume_post_relay_design import SOURCE,ACCEPTED
from resume_ground_cited_review import ROUND as GROUND_ROUND
from resume_three_day_queue import main
from continue_game_queue import ContinuousRunner,ReadBoundEdits
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.relay_contract import scenarios
from loop_controller.consolidated_hud import inspect_hud
from loop_controller.continuous_tasks import TASKS

ROUND='q0113-42d476f4'
PLAN_SHA='812789e06b05ef95e925fbe9f8878a444f1e55c807fc45526e95b5d547fec734'
PATH='Assets/Game/MissionDirectorHud.cs'
TASK=dict(id='consolidated-mission-hud',phase='mission',checks=['mission_complete'],maximum=100,
    coverage='mission-core',include_reference=False,review_frame_times=[3.2,27.3234,38.7,59.75],
    outcome='One readable truthful current objective panel plus health/wanted, with compact completed-stage receipts',
    instructions='Judge consolidated HUD only: ONE MissionBoard objective panel plus existing health/wanted. '
    'Old delivery/cache/relay renderer cards must be suppressed, not their state/scripts. Actual stage, next action, '
    'distance/control, timer and completed receipts must stay truthful. Readable compact text/backing in live4:3 '
    'and captured16:9 without overlap. Separate native red/reset and ten regression proofs cover mechanics. '
    'This explicitly replaces the old simultaneous three/four-card layout, not its mechanic or cache geometry '
    'contracts. Current measured progression59.633seconds includes27.100relay; no new duration is claimed. '
    'Character/window/art/ten-minute quality remains open. Cite actual filenames.')

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Corrected next gameplay plan saved; continue authorized consolidated HUD implementation')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('consolidated_hud_attempted'):
        raise Halt('Require corrected-plan boundary with original relay/source/history intact')

def validate_module(content):
    if not isinstance(content,str) or len(content.splitlines())>160 or len(content.encode())>12000:
        raise ValueError('One complete HUD component, maximum160lines/12KB')
    for forbidden in ['LoopRuntime','LoopRelayObservation','LoopRouteObservation','LoopInput.Replay',
        'GetCommandLineArgs','System.IO','UnityEditor','CreatePrimitive','Destroy(','SetValue(','class LoopSignals']:
        if forbidden in content:raise ValueError('Presentation-only component forbids '+forbidden)
    if re.search(r'LoopSignals\.\w+\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):raise ValueError('Legacy state is read-only')
    for required in ['using UnityEngine;','class MissionDirectorHud','DefaultExecutionOrder(31000)',
        'Install(GameObject player, Camera cam)','MissionBoard','MissionHud','RouteHud','RelayHud','HudStatus']:
        if required not in content:raise ValueError('Missing agreed actual HUD API: '+required)
    return content

class ConsolidatedHud(OrderedRelay):
    def validate_recovery(self,old):
        validate_pause(old)
        p=self.store.root/'evidence'/ROUND/'corrected-pacing-plan.json'
        if sha(p.read_bytes())!=PLAN_SHA or not read_json(p).get('ok'):raise Halt('Saved local plan changed')
        if (self.project/PATH).exists():raise Halt('Do not overwrite an existing HUD component')

    def recovery_settings(self):
        return dict(consolidated_hud_attempted=True,recovery_route='local-single-primary-hud',
            recovery_change='Local HUD source only; actual MissionHud/RouteHud/RelayHud provide objectives (HudStatus provides health only). New explicit two-panel layout contract; all native mechanics preserved.')

    def source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files)
        before={p:sha(p.read_bytes()) for p in (self.project/'Assets/Game').glob('*.cs')}
        mission=(self.project/'Assets/Game/Mission.cs').read_text()
        actual=mission[mission.index('        void RefreshHud()'):mission.index('        // ---- mission stage state')]
        actual+='\n'+(self.project/'Assets/Game/RelaySequence.Hud.cs').read_text()
        prompt=('Create ONLY one small complete ChicagoGame.MissionDirectorHud : MonoBehaviour, with using UnityEngine; '
            'and [DefaultExecutionOrder(31000)]. Static Install(GameObject player, Camera cam) creates one stationary '
            'host and stores references. Bootstrap will call it AFTER RelaySequence.Install(body,cam). No other file. '
            'This is HUD consolidation only, zero gameplay/state/camera/actor changes. Actual objective sources are '
            'MissionHud,RouteHud,RelayHud TextMeshes; HudStatus has ONLY health/wanted, not objective state. '
            'Get existing RouteMission and RelaySequence components from their named hosts. CourierMission host has '
            'public Transform parcel, public Renderer padRend. Actual LoopSignals.Mission/Mode/Restarts are read-only. '
            'Create MissionBoard camera child at local(.50,.85,1.6),identity. TextMesh UpperCenter/Center, font '
            'LegacyRuntime.ttf,fontSize40,characterSize.0145,near-white. Clone original MissionHud/HudCard backing '
            'ONLY (no primitive), rename BoardCard, local(0,-.125,.025),scale(1.5,.36,.01),identity, ensure active '
            'and renderers enabled, disable only clone colliders. No new asset or geometry. '
            'LateUpdate runs after existing HUD writers: select one truthful current state and update YOUR TextMesh; '
            'then disable ONLY Renderer.enabled on existing MissionHud,RouteHud,RelayHud hierarchies (including '
            'inactive children). Keep their GameObjects/scripts/text/state alive; never clear their text or disable '
            'scripts. Keep HudStatus rendered and set ONLY its localPosition(-1.20,.85,1.6) each LateUpdate so it '
            'does not overlap. Do not modify its text/scale/material, camera or gameplay. '
            'Primary maximum4lines, each<=40chars. Priority: relay.Active -> route.RouteStage>=1 -> courier. '
            'Relay: copy actual RelayHud TextMesh two lines (child Text, use GetComponentInChildren<TextMesh>(true)), '
            'then ONE compact footer: Delivery complete / Dead-drop complete. This includes actual progress/time, '
            'site/distance/F, ending/failed/R from relay writer. Add R reset to completed relay second line if useful. '
            'Route: copy actual RouteHud two lines, then footer DELIVERY COMPLETE; chapter2 briefly shows its real '
            'ending until relay arms. Courier: if LoopSignals.Mission==failed show MISSION FAILED / R to retry. '
            'If complete show DELIVERY COMPLETE / R to reset. Otherwise determine actual carried parcel from '
            'CourierMission.parcel.IsChildOf(player.transform) or actual MissionHud containing parcel in hand. '
            'Uncollected: COURIER: grab parcel / actual horizontal parcel distance m, F grab and countdown / '
            'WASD move | E car | R reset. Carrying: PARCEL IN HAND / actual pad distance m plus countdown / '
            'E car | F deliver | Mouse0 fire / R reset. Measure distance from actual controlled vehicle when '
            'Mode==vehicle, otherwise player; target actual parcel or padRend transform. Read legacy countdown '
            'from ACTUAL MissionHud text: initial [Ns], carrying remaining: N s. You may use Regex to parse only '
            'that live displayed number; never introduce another timer or fake state. Keep lowercase words grab '
            'and parcel in hand recognizable case-insensitively. Before completion no completion footer. '
            'On whole R reset, existing components reset; each LateUpdate selects actual state afresh so MissionBoard '
            'returns to grab without stale receipts. Do not cache phase/outcome. No game input handling. '
            'Null safety should visibly show OBJECTIVE UNAVAILABLE if required source is missing, not fake success. '
            'Use modest short code, target<120lines. Call create_hud with complete source NOW.\n'
            'ACTUAL COURIER AND RELAY HUD SOURCE:\n'+actual)
        self.c.update(output_tokens=6144,model_timeout_seconds=330)
        self.model.session('builder',ident+'-hud-source','You are local Qwen, sole substantive game HUD author.',prompt,
            [tool('create_hud','Save the complete one-panel HUD component.',{'content':{'type':'string'}})],
            {'create_hud':lambda a,f:edits.create(a,dict(path=PATH,content=validate_module(f['content'])))},
            turns=1,reasoning_effort='low')
        if not (self.project/PATH).exists():raise Halt('Local consolidated HUD source not saved')
        if any(sha(p.read_bytes())!=digest for p,digest in before.items()):raise Halt('HUD creation changed an existing source')
        candidate=self.checkpoint_source('Local Qwen: one consolidated mission HUD')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);self.store.report()
        raw=(self.project/BOOT).read_text();lines=raw.splitlines();matches=[(i+1,l) for i,l in enumerate(lines) if 'RelaySequence.Install(body,cam);' in l]
        if len(matches)!=1:raise Halt('Require exact existing relay install')
        line,old=matches[0];edit=SelectedEdit(files,BOOT,line,line,max_lines=3)
        def exact(content):
            if re.sub(r'\s+','',content)!=re.sub(r'\s+','',old)+'MissionDirectorHud.Install(body,cam);':
                raise ValueError('Keep relay install and append only MissionDirectorHud.Install(body,cam);')
            return content
        self.c.update(output_tokens=1024,model_timeout_seconds=90)
        self.store.set(stage='local-consolidated-hud-install');self.store.report()
        self.model.session('builder',ident+'-hud-install','You are local Qwen installing your own saved HUD component.',
            'Preserve this line then add MissionDirectorHud.Install(body,cam); on the next line. Call edit_selected_span now.\n'+edit.old,
            [tool('edit_selected_span','Install the saved HUD exactly once.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda a,f:edit.apply(a,exact(f['content']))},turns=1,reasoning_effort='low')
        if (self.project/BOOT).read_text()==raw:
            p=self.store.root/'private/sessions'/(ident+'-hud-install')/'response-000.json';data=p.read_bytes();c=json.loads(data)['choices'][0]
            if c.get('finish_reason')!='stop' or c['message'].get('tool_calls'):raise Halt('HUD installation not saved')
            edit.apply(ident+'-complete-install',exact(c['message'].get('content') or ''))
            self.store.event('complete-local-hud-install-recovered',response_sha256=sha(data),private_reasoning_used=False)
        candidate=self.checkpoint_source('Local Qwen: install consolidated mission HUD')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

    def work(self):
        ident=self.begin(TASK,'local-consolidated-hud-source');candidate=self.source(ident)
        probes=scenarios(read_json(self.store.root/'evidence'/GROUND_ROUND/'captures/scenario.json'))
        results={}
        for case in ('positive','wrong-timeout','inactive'):
            self.store.set(stage='native-consolidated-hud-'+case);self.store.report()
            bundle,gate=self.relay_native(ident+'-'+case,candidate,probes[case],case)
            if gate.get('passed'):
                rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
                required=['grab','carrying','dead-drop','relay','relay-complete'] if case=='positive' else (['relay-failed'] if case=='wrong-timeout' else ['grab'])
                gate['consolidated_hud']=inspect_hud(rows,required)
                if not gate['consolidated_hud']['passed']:gate.update(passed=False,failure=gate['consolidated_hud']['failure'])
            atomic(bundle/'consolidated-hud-gate.json',gate);results[case]=dict(evidence=str(bundle.relative_to(self.store.root)),passed=gate.get('passed'))
            self.store.set(consolidated_hud_native_results=results);self.store.report()
            if not gate.get('passed'):raise Halt('Consolidated HUD '+case+' needs measured diagnosis: '+json.dumps(gate.get('failure')))
        self.store.set(stage='consolidated-hud-legacy-regressions');self.store.report()
        regression=self.regress(TASKS[7],ident,candidate)
        if not regression['passed']:raise Halt('Consolidated HUD changed a legacy contract')
        hud_checks=[]
        for path in sorted((self.store.root/'evidence').glob(ident+'-regression-*/captures/trace.jsonl')):
            rows=[json.loads(x) for x in path.read_text().splitlines()]
            check=inspect_hud(rows);atomic(path.parent.parent/'consolidated-hud-gate.json',check)
            hud_checks.append(dict(evidence=path.parent.parent.name,check=check))
        if len(hud_checks)!=10 or not all(c['check']['passed'] for c in hud_checks):raise Halt('Legacy-session HUD truth/readability requires diagnosis')
        bundle=self.store.root/results['positive']['evidence'];gate=read_json(bundle/'consolidated-hud-gate.json')
        gate.update(regressions=regression,hud_regressions=hud_checks,scope=TASK['id']);atomic(bundle/'scoped-gate.json',gate)
        self.store.set(stage='fresh-consolidated-hud-critique');self.store.report();review=self.review(TASK,ident,bundle,gate)
        outcome=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),review=review,
            accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(bundle/'consolidated-hud-outcome.json',outcome);self.store.set(consolidated_hud_outcome=outcome);self.store.report()
        raise Halt('Consolidated HUD qualification recorded; continue corrected encounter acceptance and broad visual work')

if __name__=='__main__':raise SystemExit(main(ConsolidatedHud))
