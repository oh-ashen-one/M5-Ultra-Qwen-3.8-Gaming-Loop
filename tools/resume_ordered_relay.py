#!/usr/bin/env python3
"""Local relay implementation followed by sealed ordinary-input acceptance."""
import json
import re
from resume_ground_cited_review import GroundCitedReview,HASHES as GROUND_HASHES,ROUND as GROUND_ROUND,SOURCE,ACCEPTED
from resume_three_day_queue import main
from continue_game_queue import ContinuousRunner,ReadBoundEdits
from loop_controller.core import Files,Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.continuous_tasks import TASKS
from loop_controller.relay_contract import scenarios,inspect_relay,ANCHORS
from loop_controller.route_chapter import inspect_chapter

ROUND='q0108-0480baca'
PLAN_SHA='aa95d708b62e995dc16fb39a732e80039fb35ab54c06dae82cb8cd810d63939d'
PATH='Assets/Game/RelaySequence.cs'
BOOT='Assets/Game/Bootstrap.cs'
TASK=dict(id='ordered-relay',phase='mission',checks=['mission_complete'],maximum=100,coverage='mission-core',
    include_reference=False,review_frame_times=[38.7,49.15,59.75,80.6],
    outcome='After the real east cache, complete three ordered on-foot relay interactions before45seconds, with wrong-order feedback and reset.',
    instructions='Judge the new ordered relay only. The old courier and east-cache chapter remain complete while the relay '
    'runs. Three fixed original-mesh props stand on existing sidewalks: north(53,.2,27), south(41,.2,9), northwest(29,.2,27). '
    'Require clearly numbered readable sites/HUD, actual fresh nearby foot F interactions in order, visible progress/ending '
    'and reset, no overlapping HUD or floating/colliding art. Separate native red evidence proves held/remote F cannot '
    'progress, wrong-order resets relay progress only,45second expiry fails and R fully resets. Red waiting is not story '
    'duration. Prior broad character/camera/architecture quality remains open, including striped lower-window/transom '
    'overlap artifacts. Do not claim route choice from a fixed order or ten-minute/final game completion. Cite supplied filenames.')

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,ground_cited_review_recovered=True,
        blocker='Halt: Ground scope and corrected next gameplay design saved; seal additive mission acceptance before implementation')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('ordered_relay_attempted'):
        raise Halt('Require exact saved local relay design and qualified ground scope')
    if not old.get('street_ground_outcome',{}).get('accepted') or not old.get('revised_pacing_plan',{}).get('ok'):
        raise Halt('Preserve another ground/design outcome')

def validate_module(content):
    if not isinstance(content,str) or len(content.splitlines())>240 or len(content.encode())>19000:
        raise ValueError('Create one bounded complete relay component within240lines/19KB')
    for term in ('LoopRuntime','LoopRelayObservation','LoopRouteObservation','LoopInput.Replay','GetCommandLineArgs',
        'System.IO','UnityEditor','CreatePrimitive','class LoopSignals','BootstrapInstall','GameObject.Find("Player")'):
        if term in content:raise ValueError('Use actual additive gameplay APIs; prohibited '+term)
    if re.search(r'LoopSignals\.\w+\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):
        raise ValueError('Do not write legacy/protected game state')
    for name in ('class RelaySequence','Install(GameObject player, Camera cam)','Active','AllComplete','Failed',
        'ActivationCount','ExpectedIndex','WrongOrderCount','Remaining','Objective','Relays','RelayHud'):
        if name not in content:raise ValueError('Require agreed actual component API: '+name)
    return content

class OrderedRelay(GroundCitedReview):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_presentation()
        e=self.store.root/'evidence'/GROUND_ROUND
        for name,digest in GROUND_HASHES.items():
            if sha((e/name).read_bytes())!=digest:raise Halt('Preserve qualified ground evidence: '+name)
        verify_seal(e/'captures',GROUND_HASHES['captures/manifest.json'])
        if sha((self.store.root/'evidence'/ROUND/'revised-pacing-plan.json').read_bytes())!=PLAN_SHA:
            raise Halt('Saved local relay proposal changed')
        if (self.project/PATH).exists():raise Halt('Never overwrite an existing relay component')

    def recovery_settings(self):
        return dict(ordered_relay_attempted=True,recovery_route='local-three-site-relay-and-native-red-proof',
            recovery_change='Seal exact anchors/real APIs and external ordinary-input positive/wrong-order/timeout/reset checks before local source creation; no legacy-state or timer padding changes')

    def source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files);raw=(self.project/BOOT).read_text()
        route=(self.project/'Assets/Game/RouteMission.cs').read_text()
        self.c.update(output_tokens=10000,model_timeout_seconds=480)
        self.store.set(stage='local-ordered-relay-module');self.store.report()
        def create(action,f):return edits.create(action,dict(path=PATH,content=validate_module(f['content'])))
        prompt=('Implement your saved three ordered relay interaction design now as ONE complete ChicagoGame.RelaySequence '
            'MonoBehaviour, <=240lines/19KB. Call create_relay_module with source, not prose. This is substantive local game '
            'code; no external harness/legacy edits. Static signature EXACTLY Install(GameObject player, Camera cam). '
            'Create stationary RelaySequence host; public fields: bool Active,AllComplete,Failed; int ActivationCount,'
            'ExpectedIndex,WrongOrderCount; float Remaining; string Objective; Transform[] Relays (length3). '
            'Read actual RouteMission from GameObject.Find("RouteMission").GetComponent<RouteMission>(); only arm after '
            'RouteStage==2 AND RouteComplete. RouteMission and LoopSignals are read-only here. Existing LoopSignals has '
            'Restarts(int),Mode(string). Use real passed player object; use LoopInput.Pressed(KeyCode.F) ONLY for new F '
            'edges. No key-held progress. Do not inspect command line, replay, harness, test names or special input. '
            'Public Active remains true after relay completion or failure until reset, so the outcome stays visible. '
            'On arming set local startTime=Time.time, Remaining45, count/expected0, WrongOrderCount0. Every update set '
            'Remaining=max(0,45-(Time.time-startTime)) until outcome. Deadline45seconds: if not complete and elapsed>=45 '
            'set Failed=true, freeze progress and display RELAY FAILED / R to retry. Never change old Mission/Health. '
            'Relays exact stationary identity/unit root anchors: index0 (53,.2,27), index1 (41,.2,9), index2 (29,.2,27). '
            'Name visible objectives NORTH FRONTAGE, SOUTH FRONTAGE, NORTHWEST FRONTAGE and number1,2,3. All on existing '
            'raised sidewalks. Root anchors do not move. Build three identical original-mesh props by cloning ONLY '
            'AlleyDumpster (fallback dumpster_a). Preserve actual original orientation. Use aggregate MeshRenderer bounds '
            'to uniformly fit each cloned prop within max dimension1.0m, then center worldX/Z and ground minY exactly '
            'at its anchor.y (already.2, do not add again). Start aggregate from FIRST real renderer, never a zero origin '
            'bound. Disable all colliders ONLY on each new clone. Add exactly one root BoxCollider center/size matching '
            'aggregate rendered bounds in the identity root, solid not trigger. Do not alter original props/geometry. '
            'Reuse shared original meshes; per-renderer copied materials, muted dark utility-box appearance, restrained '
            'cyan accent while next, muted green when activated, red flash0.3s for wrong press. No giant neon block. '
            'Small world TextMesh labels1/2/3 may face camera; do not include those labels in prop fitting/collider bounds. '
            'Before arm hide the three roots; after R hide them again. Null checks may fail visibly but never fake success. '
            'On a fresh F, only Mode=="foot", Active && !Failed && !AllComplete can interact. Find a relay within1.5m '
            'horizontal XZ distance to player. A far F does nothing. Correct index==ExpectedIndex increments count and '
            'expected together; each prop visibly changes. Third correct press sets AllComplete=true and RELAY COMPLETE. '
            'Wrong index resets count/expected0, increments WrongOrderCount ONCE per fresh F, flashes the pressed box '
            'red0.3s; deadline does NOT restart. Already-activated wrong site is also wrong order. Do not reset the courier '
            'or east-cache chapter. Wrong-order message must explain restart at1. Holding F through arrival must not '
            'activate; require a release/new edge. R is global retry: detect LoopSignals.Restarts change FIRST, clear all '
            'relay state/outcomes/wrong counter, hide props/HUD, then RETURN from update; wait for a new real chapter '
            'completion. No same-frame rearm after R. Own remaining/UI only; do not rewrite other component fields. '
            'HUD: create RelayHud camera child, compact two lines in LOWER RIGHT, leaving RouteHud upper right and '
            'legacy receipt lower left untouched. Copy the existing RouteHud TextMesh style or create equivalent text '
            'using LegacyRuntime.ttf. At camera-local z1.6 place centerx .52, topy -.55; characterSize .0125, fontSize40, '
            'UpperCenter/Center, short lines <=34characters. Copy the existing original HudCard child into RelayHud: '
            'localposition(0,-.065,.025),scale(1.3,.23,.01),identityrotation; disable its clone collider. This fits live4:3 '
            'and render16:9. Hide HUD before arm/after R, show progress 0/3 plus remaining seconds and next named site/'
            'distance/F. Keep Objective nonempty while active. Do NOT alter RouteHud, MissionHud, HudStatus or camera. '
            'Do not claim measured duration. Actual Walker speed3.2m/s. The cloud acceptance replay uses ordinary keys; '
            'your component must work interactively too. Separate exact install follows RouteMission.Install(body,cam); '
            'in existing Bootstrap source, no invented BootstrapInstall method. No additional assets/exports. '
            '\nACTUAL CHAPTER/PROP/HUD SOURCE:\n'+route+
            '\nEXACT BOOTSTRAP INSTALL CONTEXT:\n'+raw.split('    public class Follow')[0])
        self.model.session('builder',ident+'-relay-module',
            'You are local Qwen, sole substantive game author. Save the complete requested additive module through its tool.',
            prompt,[tool('create_relay_module','Save the one complete original-mesh ordered relay component.',{'content':{'type':'string'}})],
            {'create_relay_module':create},turns=1,reasoning_effort='low')
        if not (self.project/PATH).exists():raise Halt('Local relay component was not saved')
        candidate=self.checkpoint_source('Local Qwen: add ordered three-site relay chapter')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        return self.install(ident,raw)

    def install(self,ident,raw):
        files=Files(self.project,self.store)
        matches=[(i,t) for i,t in enumerate(raw.splitlines(),1) if 'RouteMission.Install(body,cam);' in t]
        if len(matches)!=1:raise Halt('Require exact unchanged RouteMission installation')
        line,old=matches[0];edit=SelectedEdit(files,BOOT,line,line,max_lines=3)
        def exact(content):
            if re.sub(r'\s+','',content)!=re.sub(r'\s+','',old)+'RelaySequence.Install(body,cam);':
                raise ValueError('Preserve chapter install and add only RelaySequence.Install(body,cam);')
            return content
        self.c.update(output_tokens=1024,model_timeout_seconds=90)
        self.store.set(stage='local-ordered-relay-install');self.store.report()
        self.model.session('builder',ident+'-relay-install',
            'You are local Qwen installing your saved gameplay component.',
            'Call edit_selected_span now: preserve this exact line then add RelaySequence.Install(body,cam); '
            'as the next line. No other edit, no prose.\n'+edit.old,
            [tool('edit_selected_span','Install the saved relay once.',{'content':{'type':'string'}})],
            {'edit_selected_span':lambda a,f:edit.apply(a,exact(f['content']))},turns=1,reasoning_effort='low')
        if (self.project/BOOT).read_text()==raw:
            path=self.store.root/'private/sessions'/(ident+'-relay-install')/'response-000.json'
            response=path.read_bytes();c=json.loads(response)['choices'][0];m=c['message']
            if c.get('finish_reason')!='stop' or m.get('tool_calls'):raise Halt('Relay installation incomplete')
            content=exact(m.get('content') or '')
            edit.apply(ident+'-complete-relay-install',content)
            self.store.event('complete-local-install-recovered',response_sha256=sha(response),
                content_sha256=sha(content.encode()),private_reasoning_used=False,original_response_preserved=True)
        candidate=self.checkpoint_source('Local Qwen: install ordered relay chapter')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

    def relay_native(self,ident,candidate,probe,case):
        task={**TASK,'checks':[]} if case=='inactive' else TASK
        bundle,gate=ContinuousRunner.native(self,task,ident,candidate,probe)
        if gate.get('passed'):
            rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
            check=inspect_relay(rows,case);gate['relay_contract']=check
            chapter=inspect_chapter(rows,case!='inactive',case!='inactive',case=='inactive')
            gate['chapter_contract']=chapter
            if not check['passed'] or not chapter['passed']:
                gate.update(passed=False,failure=(check['failure'] or [])+(chapter['failure'] or []))
        atomic(bundle/'relay-gate.json',gate);return bundle,gate

    def work(self):
        ident=self.begin(TASK,'local-ordered-relay-module')
        self.store.set(next_task='Native relay success, wrong-order/timeout/reset and no-handoff proof, then all ten regressions and scoped critique')
        candidate=self.source(ident)
        probes=scenarios(read_json(self.store.root/'evidence'/GROUND_ROUND/'captures/scenario.json'))
        results={}
        for case in ('positive','wrong-timeout','inactive'):
            self.store.set(stage='native-relay-'+case);self.store.report()
            bundle,gate=self.relay_native(ident+'-'+case,candidate,probes[case],case)
            results[case]=dict(evidence=str(bundle.relative_to(self.store.root)),gate=gate)
            self.store.set(relay_native_results=results);self.store.report()
            if not gate.get('passed'):raise Halt('Relay '+case+' requires measured diagnosis: '+json.dumps(gate.get('failure')))
        self.store.set(stage='relay-legacy-regressions');self.store.report()
        regression=self.regress(TASKS[7],ident,candidate)
        bundle=self.store.root/results['positive']['evidence'];gate=results['positive']['gate']
        gate['regressions']=regression
        gate['relay_red_proofs']={k:v['gate'].get('relay_contract') for k,v in results.items() if k!='positive'}
        atomic(bundle/'relay-gate.json',gate)
        if not regression['passed']:raise Halt('Relay changed an accepted legacy mechanic')
        self.store.set(stage='fresh-relay-critique');self.store.report()
        gate['scope']=TASK['id'];atomic(bundle/'scoped-gate.json',gate)
        review=self.review(TASK,ident,bundle,gate)
        outcome=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(bundle/'relay-outcome.json',outcome);self.store.set(relay_outcome=outcome);self.store.report()
        raise Halt('Relay qualification recorded; continue measured gameplay and broad visual work under existing authority')

if __name__=='__main__':raise SystemExit(main(OrderedRelay))
