#!/usr/bin/env python3
"""Local compact HUD/cache styling; preserve mechanics, then plan meaningful pacing."""
import json
import re
from resume_east_dead_drop import EastDeadDrop,TASK,PATH,ACCEPTED
from resume_three_day_queue import main
from resume_chapter_review_street_details import CORRECTED
from loop_controller.core import Files,Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.chapter_presentation import inspect_presentation
from loop_controller.continuous_tasks import TASKS

SOURCE='d7b2153b5a560fa5edb842bce0262ea264663f27'
ROUND='q0101-b3301b17'
HASHES={'chapter-gate.json':'1a004c538684bd9814ec617d2a1337c8dded440973ffef7a3694be686ee8a8fc',
    'critic.json':'eb6cdb164d3e1467a15e2327201ee2e0bb33dcc843bf1525c4cf4f414d9ed036',
    'facade-outcome.json':'beabe4feaac3ed52c7eeb76a3a0291d202769440c09079c7d1a174ddfeca20ea',
    'captures/manifest.json':'70aa27db07b97c6d4861d5afb01f5ec6ca4724afb021fa756d096f038aa19058'}
PRESENTATION={**CORRECTED,'outcome':'Compact non-overlapping chapter HUD and a grounded original cache prop with a restrained status accent.',
    'instructions':CORRECTED['instructions']+
    ' CURRENT SCOPE: require all three HUD panels readable, inside the screen and mutually separate, with the '
    'main objective no longer blocking the middle of the street. The unchanged legacy receipt remains visible '
    'but secondary. Require the new cache to read as its original dumpster mesh with muted body/lid/wheels and '
    'at most one small emissive accent, visibly grounded at its unchanged world anchor. Completion still has clear '
    'feedback. A new capture near32.55s brackets the actual F edge; reset is also supplied. Keep the old green '
    'courier beacon, repetitive facades, uniform ground/lack of curbs and broader camera/final-art findings open. '
    'Original mesh reuse is verified: do not label the cache an engine primitive without evidence.'}

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: East street facade scope recorded; connected mission pacing and outstanding presentation remain')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('chapter_presentation_attempted'):
        raise Halt('Require exact completed facade scope and unchanged baseline/counters')
    outcome=old.get('east_street_facade_outcome',{})
    if not outcome.get('accepted') or outcome.get('review',{}).get('verdict')!='PASS':
        raise Halt('Preserve a different facade verdict')

def validate_visual_span(content,marker=False):
    if not isinstance(content,str) or len(content.encode())>6000 or len(content.splitlines())>(55 if marker else 140):
        raise ValueError('Keep this exact visual span within its bounded edit size')
    for term in ('LoopRuntime','LoopRouteObservation','LoopInput','void Update(', 'void ActivateCache(',
                 'class LoopSignals','Destroy(', 'CreatePrimitive','System.IO','GetCommandLineArgs'):
        if term in content:raise ValueError('Visual-only scope prohibits '+term)
    for field in ('RouteStage','RouteComplete','Cache','Objective','reachedInVehicle','lastRestarts'):
        if re.search(r'\b'+field+r'\s*(?:=(?!=)|\+\+|--|[+*/-]=)',content):
            raise ValueError('Keep real progress and fixed anchor immutable')
    if re.search(r'LoopSignals\.\w+\s*=',content):raise ValueError('Never write legacy signals')
    checked=content.replace('card.gameObject.SetActive(false);','')
    if 'SetActive(false)' in checked:raise ValueError('Never hide legacy receipt/status or world markers')
    if marker and any(x in content for x in ('SetActive','Collider','player.','cam.')):
        raise ValueError('Marker styling changes only cloned renderer materials and child alignment')
    return content

def visual_probe(original):
    probe=json.loads(json.dumps(original));probe['captures']=sorted(set(probe['captures']+[32.55]))
    return probe

class ChapterPresentation(EastDeadDrop):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_prior()

    def verify_prior(self):
        bundle=self.store.root/'evidence'/ROUND
        for name,digest in HASHES.items():
            if sha((bundle/name).read_bytes())!=digest:raise Halt('Preserve original facade evidence: '+name)
        verify_seal(bundle/'captures',HASHES['captures/manifest.json'])
        g=read_json(bundle/'chapter-gate.json');regs=g.get('regressions',{}).get('regressions',[])
        if not g.get('passed') or len(regs)!=10 or not all(r['gate'].get('passed') for r in regs):
            raise Halt('Require the saved chapter and all ten current-source passes')

    def recovery_settings(self):
        return dict(chapter_presentation_attempted=True,
            recovery_route='local-compact-hud-and-cache-materials-then-pacing-design',
            recovery_change='Preserve Update and legacy state; passive projected UI/cache bounds checks; unchanged inputs plus one F-edge capture')

    def hud_request(self,ident,hud,raw,save):
        self.model.session('builder',ident+'-hud',
            'You are local Qwen, sole substantive game author, making one bounded presentation-only replacement.',
            'Replace the selected HUD fields/BuildHud/LateUpdate region, <=110lines/6000bytes. Keep game Update '
            'and all progress/anchor state untouched. The actual frame shows an oversized central objective and '
            'tiny stale courier receipt overlapping Health/Wanted. Make a compact upper-right chapter objective '
            'with two concise lines, live distance and contextual E/F controls. Keep EAST DEAD-DROP in every '
            'active/complete title; stage2 says chapter COMPLETE, not whole game. Original MissionHud text must '
            'stay visible, unchanged, readable and secondary in a separate lower-left panel; do not hide it or '
            'change Mission.cs. Existing HudStatus remains visible with real health/wanted. You may only reposition '
            'and scale those two camera-child UI transforms while chapter active, caching/restoring their original '
            'position AND scale at stage0/R. HudStatus is installed AFTER RouteMission, so discover/cache its '
            'transform lazily in LateUpdate, once it exists; do not assume BuildHud can find it. '
            'Useful camera-space layout (camera FOV64,960x540,z1.6): RouteHud upper-center anchor at '
            '(0.52,0.85,1.6), font40, characterSize0.017..0.018, two lines; backing width1.75,height0.23, '
            'center(0,-0.06,0.025),thickness0.01. Position MissionHud at(-1.05,-0.70,1.6), scale0.9*original, '
            'preserving its three-line text/card. HudStatus at(-1.55,0.85,1.6), original scale. Preserve and restore '
            'all original transforms on stage0. Keep each card within viewport, no overlap. Clone only existing '
            'HudCard for the new objective, disable only that clone collider; no new primitive, world or camera edit. '
            'Retain `card` variable for the owned backing. Cache original values exactly, never derive defaults. '
            'Use the existing ReadStr/ReadTransform/XZDist/player/cam/hud helpers and fields. Do not redefine them. '
            'LateUpdate may also set tintedMat color/emission ONLY as a visual status accent: while RouteStage1 '
            'muted teal color(0.10,0.50,0.48), emission(0.015,0.10,0.09); stage2 muted green color(0.12,0.48,0.18), '
            'emission(0.015,0.08,0.02). A following source edit makes tintedMat only the small rail material, '
            'not the whole cache body. No writes to RouteStage,RouteComplete,Cache,Objective,reachedInVehicle, '
            'lastRestarts or LoopSignals. Save the replacement now.\nSELECTED REGION:\n'+hud.old+
            '\nFULL COMPONENT:\n'+raw,
            [tool('edit_selected_span','Save the compact HUD-only replacement.',{'content':{'type':'string'}})],
            {'edit_selected_span':save},images=[('actual oversized HUD and neon cache',
                self.store.root/'evidence'/ROUND/'captures/frame-010.png')],turns=1,reasoning_effort='low')

    def source(self,ident):
        files=Files(self.project,self.store);raw=files.path(PATH).read_text()
        before_logic=raw[raw.index('        void Update()'):raw.index('        void ActivateCache()')]
        first=raw.index('        Transform missionHud;');last=raw.index('        void Update()')
        hud=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last),max_lines=140)
        def save(_,f):return hud.apply(ident+'-hud',validate_visual_span(f['content']))
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-compact-chapter-hud');self.store.report()
        self.hud_request(ident,hud,raw,save)
        if files.path(PATH).read_text()==raw:raise Halt('Local compact HUD edit was not saved')
        candidate=self.checkpoint_source('Local Qwen: compact and separate chapter HUD panels')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        raw=files.path(PATH).read_text();first=raw.index('                foreach (var rd in c.GetComponentsInChildren<Renderer>())')
        last=raw.index('\n            }\n            Cache.gameObject.SetActive(true);',first)
        edit=SelectedEdit(files,PATH,raw.count('\n',0,first)+1,raw.count('\n',0,last)+1,max_lines=55)
        def marker(_,f):return edit.apply(ident+'-cache',validate_visual_span(f['content'],True))
        self.c.update(output_tokens=4096,model_timeout_seconds=240)
        self.store.set(stage='local-cache-material-grounding');self.store.report()
        self.model.session('builder',ident+'-cache',
            'You are local Qwen styling only the existing cloned original cache prop.',
            'Replace this selected renderer-material/bounds block, <=55lines/6000bytes. Keep existing cloned meshes '
            'and their scale/orientation. No primitives, colliders, source-asset changes or progress writes. '
            'Give body/lid muted dark steel/teal, wheels dark rubber; copy every material before adjusting it. '
            'Only the renderer whose name contains `rail` receives a restrained teal emissive accent; assign '
            'tintedMat to that new rail material so the unchanged completion code and new LateUpdate affect '
            'only the rail. All other new materials disable _EMISSION and set _EmissionColor black. Use original '
            'sharedMesh assets unchanged. Compute aggregate bounds of ALL cloned renderers, then move ONLY c '
            'by a WORLD offset so combined bounds center X/Z equals anchor.position X/Z and combined bounds '
            'minimum Y equals anchor.position.y(0.14). Do not move anchor/Cache itself. Cache root, mission input '
            'logic and all source objects stay unchanged. `c` is the cloned Transform, `anchor` the stationary '
            'GameObject already created immediately above. Save now.\nSELECTED:\n'+edit.old,
            [tool('edit_selected_span','Save restrained copied materials and aggregate child alignment.',{'content':{'type':'string'}})],
            {'edit_selected_span':marker},turns=1,reasoning_effort='low')
        after=files.path(PATH).read_text()
        if after==raw:raise Halt('Local cache styling edit was not saved')
        if after[after.index('        void Update()'):after.index('        void ActivateCache()')]!=before_logic:
            raise Halt('Gameplay Update changed outside the visual scope')
        candidate=self.checkpoint_source('Local Qwen: shade original cache with a small status accent')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

    def pacing_plan(self,ident):
        fields=('first_next_objective','player_choices','varied_ten_minute_path','existing_state_compatibility',
                'smallest_source_scope','independent_native_proof','street_ground_detail_scope')
        def submit(_,f):
            if set(f)!=set(fields) or any(not isinstance(v,str) or not 20<=len(v)<=1800 for v in f.values()):
                raise ValueError('Return every concise design field,20..1800characters each')
            return dict(ok=True,**f)
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-next-mission-pacing-design');self.store.report()
        source='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in
            [PATH,'Assets/Game/Mission.cs','Assets/Game/Combat.cs','Assets/Game/VehicleInteraction.cs'])
        plan=self.model.session('planner',ident+'-next-mission',
            'You are local Qwen, the game designer. Return concise operational design, not private reasoning.',
            'The real connected route currently lasts36seconds: legacy courier, drive through alley/east street, '
            'exit, close F at cache, reset. It is NOT a ten-minute game. Define the next small meaningful playable '
            'objective following the east cache, preserving both completed chapter contracts and ordinary controls. '
            'Prefer a materially different action/decision (investigation, retrieving specific cargo, pursuit escape '
            'or combat with real health/cover) over another copy of deliver-a-box. Explain a credible varied '
            '540..660second route using meaningful actions and traversal, never timer locks, idle waiting, '
            'repeated identical deliveries, cutscene padding or relabeling this short component as final. '
            'Current topology: coreX-1..6/Z-2..30, alleyX6..22/Z8..20, east streetX22..60/Z8..28. '
            'Facades are decorative, closed doors do not imply enterable buildings. If a larger connected area '
            'or missing mechanics are needed for pacing, say so and sequence a bounded physical acceptance first. '
            'Include next actual world anchors, actor/mode/input/state transitions, R reset, positive and red '
            'proof, and smallest source surface. Keep legacy mission/progress truthful and new state additive. '
            'Also specify a small following street-ground task using original assets for road/sidewalk contrast '
            'and markings/curbs with matching support/collision; no unsupported cosmetic ledges or downloads. '
            'No edits in this role. Call submit_plan now.\nCURRENT GAME SOURCE:\n'+source,
            [tool('submit_plan','Save the next concrete varied-mission and street-ground design.',
                  {k:{'type':'string'} for k in fields})],{'submit_plan':submit},turns=1,reasoning_effort='low')
        bundle=self.store.root/'evidence'/ident;atomic(bundle/'next-pacing-plan.json',plan)
        self.store.set(next_pacing_plan=plan,next_pacing_plan_evidence=str(bundle.relative_to(self.store.root)))
        if not plan.get('ok'):raise Halt('Next mission designer supplied no complete design')

    def work(self):
        ident=self.begin(PRESENTATION,'local-compact-chapter-hud');candidate=self.source(ident)
        original=read_json(self.store.root/'evidence'/ROUND/'captures/scenario.json')
        probe=visual_probe(original)
        self.store.set(stage='native-chapter-presentation');self.store.report()
        bundle,gate=self.chapter_native(ident,candidate,probe)
        if not gate.get('passed'):raise Halt('Presentation source changed the proven native chapter')
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        check=inspect_presentation(rows);gate['presentation_geometry']=check
        atomic(bundle/'chapter-gate.json',gate)
        if not check['passed']:raise Halt('Measured HUD/cache presentation requires correction: '+json.dumps(check['failure']))
        self.store.set(stage='presentation-legacy-regressions');self.store.report()
        gate['regressions']=self.regress(TASKS[7],ident,candidate);atomic(bundle/'chapter-gate.json',gate)
        if not gate['regressions']['passed']:raise Halt('Presentation source changed an accepted legacy mechanic')
        self.store.set(stage='fresh-presentation-critique');self.store.report()
        atomic(bundle/'scoped-gate.json',gate);review=self.review(PRESENTATION,ident,bundle,gate)
        record=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(bundle/'presentation-outcome.json',record);self.store.set(chapter_presentation_outcome=record)
        self.store.event('chapter-presentation-scope-recorded',**record);self.store.report()
        if not review.get('ok'):raise Halt('Presentation critic supplied no complete verdict')
        self.pacing_plan(ident)
        self.store.report()
        raise Halt('Presentation qualified scope recorded and next varied mission design saved; seal its additive acceptance before implementation')

if __name__=='__main__':raise SystemExit(main(ChapterPresentation))
