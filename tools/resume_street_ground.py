#!/usr/bin/env python3
"""Local street-ground detailing with physical curb proof and corrected mission planning."""
import json
import re
from continue_game_queue import ReadBoundEdits
from resume_chapter_presentation import ChapterPresentation,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.continuous_tasks import TASKS
from loop_controller.chapter_presentation import inspect_presentation
from loop_controller.street_ground_checks import probe,inspect_geometry,inspect_walkovers

SOURCE='c53cb5d79437823562d57f74b3b1fd7f0761b43d'
ROUND='q0105-4643cf8b'
PATH='Assets/Game/EastStreetGround.cs'
INSTALL='Assets/Game/ConnectedStreet.cs'
HASHES={'chapter-gate.json':'71578d61891a8e70cbdbccea18a98b201b6c263be69ef2136e0ad4ff575806bc',
    'critic.json':'b063700bd911cf0c850eb796b6a39581a91bc346ed7c1be4b16c86bca8928785',
    'presentation-outcome.json':'10b59a17e806d20b5e864fbed8c881d7101d7fad7afdf9a45b282976405d81e5',
    'next-pacing-plan.json':'09b5a998514e870aba3f60c8390dad1c417d92118412dfd6c2eb0a16f9801421',
    'captures/manifest.json':'ed049167c31a07fe721debfe2efcb5a2b8fd49b47d161d4f120eaa8b37d8330a'}
GROUND_TASK=dict(id='east-street-ground',phase='polish',checks=['mission_complete'],maximum=180,coverage='mission-core',
    review_frame_times=[27.3234,38.8,45.5,50.6],
    outcome='The east street reads as a road with raised sidewalks, curb edges and restrained lane markings, with real walkovers.',
    instructions='Judge original-mesh street-ground detail only: dark road, lighter north/south sidewalks, coherent6cm curb edges '
    'and non-emissive road dashes. Require correct scale, visible physical support and no floating surfaces or route blockage. '
    'The existing east cache remains at(50,.14,18); its chapter completes32.53s. After completion the external tester walks '
    'north curb near38.8s and south curb near45.5s, then R resets50.03s. This53second replay includes acceptance walkovers, '
    'not added story content or ten-minute pacing. Existing root road remainsY.14; raised sidewalks topY.20 with matching '
    'colliders. Do not confuse old courier pad(1,.15,26) with east cache. Preserve HUD/cache scoped PASS; broader art, '
    'actor occlusion, camera, repetitive facades, legacy green marker and varied-mission work remain open.')

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,stage='local-next-mission-pacing-design',
        blocker='Halt: Presentation qualified scope recorded and next varied mission design saved; seal its additive acceptance before implementation')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('street_ground_attempted'):
        raise Halt('Require completed presentation scope, saved proposal and unchanged baseline/history')
    if not old.get('chapter_presentation_outcome',{}).get('accepted') or not old.get('next_pacing_plan',{}).get('ok'):
        raise Halt('Preserve a different presentation/planner outcome')

def validate_module(content):
    if not isinstance(content,str) or len(content.splitlines())>150 or len(content.encode())>12000:
        raise ValueError('Save one bounded surface component within150lines/12KB')
    for term in ('LoopSignals','LoopInput','RouteMission','CourierMission','CreatePrimitive','Instantiate(',
                 'Destroy(','SetActive','MeshCollider','Rigidbody','Camera','UnityEditor','System.IO','Resources.Load'):
        if term in content:raise ValueError('Original ground-only scope prohibits '+term)
    if not all(t in content for t in ('class EastStreetGround','Install(GameObject parent)','sharedMesh',
                                     'StreetPavement','SidewalkSouth','SidewalkNorth','CurbSouth','CurbNorth','LaneDash')):
        raise ValueError('Require the agreed original surface API and independently observed names')
    return content

class StreetGround(ChapterPresentation):
    def validate_recovery(self,old):
        validate_pause(old);self.verify_presentation()
        if (self.project/PATH).exists():raise Halt('Never overwrite an existing ground module')

    def verify_presentation(self):
        e=self.store.root/'evidence'/ROUND
        for name,digest in HASHES.items():
            if sha((e/name).read_bytes())!=digest:raise Halt('Preserve completed presentation/plan evidence: '+name)
        verify_seal(e/'captures',HASHES['captures/manifest.json'])
        g=read_json(e/'chapter-gate.json');regs=g.get('regressions',{}).get('regressions',[])
        if not g.get('passed') or not g.get('presentation_geometry',{}).get('passed') or len(regs)!=10 or not all(x['gate'].get('passed') for x in regs):
            raise Halt('Require all native presentation and legacy passes')

    def recovery_settings(self):
        return dict(street_ground_attempted=True,
            recovery_route='local-original-street-ground-and-real-curb-walkovers',
            recovery_change='Preserve completed presentation scope and unimplemented planner proposal; original floor/anchors stayY.14, raised sidewalks match colliders; then correct nonexistent mission APIs before implementation')

    def source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files);raw=(self.project/INSTALL).read_text()
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-original-street-ground');self.store.report()
        def create(action,f):return edits.create(action,dict(path=PATH,content=validate_module(f['content'])))
        self.model.session('builder',ident+'-ground-module',
            'You are local Qwen, sole substantive game/art author. Call the offered create tool with complete source now.',
            'Create one static ChicagoGame.EastStreetGround class, public static void Install(GameObject parent), '
            '<=150lines/12KB. Improve ONLY the existing east street X22..60,Z8..28. Preserve all current ground/wall '
            'geometry, colliders, chapter anchors, actors, HUD and camera. No primitives/new assets/downloads. '
            'Use the existing original Pavement MeshFilter sharedMesh and transform.rotation as in ConnectedStreet. '
            'Its baked local bounds map localX->worldZ, localY->worldX, localZ->worldY. Reuse the proven mapping: '
            'scale=(worldSize.z/b.size.x,worldSize.x/b.size.y,worldSize.y/b.size.z), worldposition=center-rotation*'
            'Vector3.Scale(b.center,scale). New MeshFilter/Renderer objects share that ORIGINAL mesh. '
            'Create unit/identity root EastStreetGround under parent. Surface names must be immediate children. '
            'Keep StreetPavement geometry and collider exactly unchanged at topY.14; assign ONLY its MeshRenderer '
            'a new copied material color(0.085,0.085,0.095) for dark road. Do not recolor shared original materials '
            'or core/alley pavement. No second road slab or moved cache: the cache anchor/base remainsY.14. '
            'Create these four original-mesh boxes with matching BoxCollider center=b.center,size=b.size on each '
            'new transform: SidewalkSouth center(41,.17,9), size(38,.06,2); SidewalkNorth center(41,.17,27), '
            'size(38,.06,2); CurbSouth center(41,.17,10), size(38,.06,.12); CurbNorth center(41,.17,26), '
            'size(38,.06,.12). All topsY.20,6cm above road; no unsupported ledges. Copy original sidewalk/curb '
            'materials, muted light concrete colors (~.36,.35,.32 for sidewalks and .43,.41,.36 for curb edges). '
            'No glow. Add exactly9 decorative LaneDash00..08 renderer-only boxes from the same original mesh: '
            'centerX26+4*i,Y.142,Z18; size(2.4,.002,.10). Reuse/copy original road_dash00 material if found, '
            'otherwise a copied existing sidewalk material, muted cream(.55,.53,.45), emission disabled. '
            'These are thin painted strips, not physical obstacles. Add no other renderers or colliders. '
            'Do not mutate source transforms or materials. Null-check required original mesh/renderer before work. '
            'A separate exact line installs your module after EastStreetDetail.Install(parent). '
            'Call create_ground_module NOW; do not return prose or a fenced code block.\nEXACT ORIGINAL GROUND FACTORY:\n'+raw,
            [tool('create_ground_module','Create the bounded original-mesh street ground module.',{'content':{'type':'string'}})],
            {'create_ground_module':create},turns=1,reasoning_effort='low')
        if not (self.project/PATH).exists():raise Halt('Local street-ground module was not saved')
        candidate=self.checkpoint_source('Local Qwen: add original street sidewalks curbs and road markings')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        lines=[(i,t) for i,t in enumerate(raw.splitlines(),1) if 'EastStreetDetail.Install(parent);' in t]
        if len(lines)!=1:raise Halt('Expected one existing facade install anchor')
        line,old=lines[0];edit=SelectedEdit(files,INSTALL,line,line,max_lines=3)
        def install(_,f):
            if re.sub(r'\s+','',f['content'])!=re.sub(r'\s+','',old)+'EastStreetGround.Install(parent);':
                raise ValueError('Keep the facade install and add only the ground install')
            return edit.apply(ident+'-install',f['content'])
        self.c.update(output_tokens=1024,model_timeout_seconds=90)
        self.model.session('builder',ident+'-install',
            'You are local Qwen installing your saved component with the offered edit tool.',
            'Call edit_selected_span now. Keep this exact line and add EastStreetGround.Install(parent); immediately '
            'after it. No prose or fenced code; no other change.\n'+edit.old,
            [tool('edit_selected_span','Install the new original ground module once.',{'content':{'type':'string'}})],
            {'edit_selected_span':install},turns=1,reasoning_effort='low')
        if (self.project/INSTALL).read_text()==raw:raise Halt('Saved street-ground module has no install')
        candidate=self.checkpoint_source('Local Qwen: install physical east street ground detail')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

    def revised_plan(self,ident):
        fields=('next_objective','real_api_and_install','new_owned_state','positive_and_red_native_proof',
                'smallest_source_scope','varied_pacing_and_expansion','open_dependencies')
        def submit(_,f):
            if set(f)!=set(fields) or any(not isinstance(v,str) or not 20<=len(v)<=1800 for v in f.values()):
                raise ValueError('Return each concise design field,20..1800characters')
            return dict(ok=True,**f)
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-corrected-varied-mission-design');self.store.report()
        old=read_json(self.store.root/'evidence'/ROUND/'next-pacing-plan.json')
        source='\n\n'.join(p+'\n'+(self.project/p).read_text() for p in
            ['Assets/Game/RouteMission.cs','Assets/Game/Mission.cs','Assets/Game/Combat.cs','Assets/Game/VehicleInteraction.cs'])
        plan=self.model.session('planner',ident+'-revised-pacing',
            'You are local Qwen, the game designer. Return a concise implementable decision using actual APIs.',
            'Correct your saved proposal before any mission code. Verified conflicts: AlleyRetrievalArmed and '
            'AlleyRetrieval signals do NOT exist; RouteStage only0/1/2 and stays2 after its completion. Do not '
            'require new writes by RouteMission or write legacy Mission="failed"/Health to simulate outcomes. '
            'An additive component may read actual RouteMission fields; its own public instance state and '
            'separate passive observation can be added. A new component still needs one explicit Bootstrap '
            'installation line; do not claim no existing file edits. Reuse original visible crate/prop/actor '
            'meshes, not CreatePrimitive. Current doors are closed facades, and there are no unverified narrow '
            'corridors/LOS shortcuts. New opponents require actual damage/stagger/collision/aim proof before '
            'claiming them. Prefer a small materially different objective after the east cache, not another '
            'renamed box delivery or giant multi-agent system. New ground walkovers are external acceptance '
            'and must NOT count as playable mission duration. The current short mission still takes36seconds. '
            'Keep your honest conclusion that540..660seconds requires more meaningful actions and possibly '
            'connected physical expansion; fix inconsistent phase arithmetic and do not claim unmeasured times '
            'as facts. Specify a minimal next gameplay increment, actual anchors, ordinary controls, game-owned '
            'progress, true failure/reset, original-mesh reuse and separate immutable positive/red proof. '
            'Keep courier and east-cache gates unchanged. Return an implementable next source scope plus '
            'credible varied pacing/expansion dependencies. Call submit_plan now; no source edits or prose reply. '
            '\nPRESERVED ORIGINAL PROPOSAL (not implemented):\n'+json.dumps(old)+'\nACTUAL GAME SOURCE:\n'+source,
            [tool('submit_plan','Save corrected next gameplay and pacing decisions.',{k:{'type':'string'} for k in fields})],
            {'submit_plan':submit},turns=1,reasoning_effort='low')
        bundle=self.store.root/'evidence'/ident;atomic(bundle/'revised-pacing-plan.json',plan)
        self.store.set(revised_pacing_plan=plan,next_pacing_plan=plan,next_pacing_plan_evidence=str(bundle.relative_to(self.store.root)))
        if not plan.get('ok'):raise Halt('Corrected mission design was not submitted')

    def work(self):
        ident=self.begin(GROUND_TASK,'local-original-street-ground');candidate=self.source(ident)
        original=self.store.root/'evidence'/ROUND
        scenario=probe(read_json(original/'captures/scenario.json'))
        self.store.set(stage='native-ground-curb-walkovers');self.store.report()
        bundle,gate=self.chapter_native(ident,candidate,scenario)
        if not gate.get('passed'):raise Halt('Ground detail changed the native chapter; preserve actual failure')
        rows=[json.loads(x) for x in (bundle/'captures/trace.jsonl').read_text().splitlines()]
        checks=dict(ground_geometry=inspect_geometry(read_json(original/'captures/scene-transforms.json')['objects'],
            read_json(bundle/'captures/scene-transforms.json')['objects']),curb_walkovers=inspect_walkovers(rows),
            presentation_geometry=inspect_presentation(rows))
        gate.update(checks);atomic(bundle/'chapter-gate.json',gate)
        combined=dict(passed=all(c['passed'] for c in checks.values()),checks=checks,candidate=candidate)
        atomic(bundle/'ground-gate.json',combined)
        if not combined['passed']:raise Halt('Ground geometry/physical walkover/presentation gate failed: '+json.dumps({k:v['failure'] for k,v in checks.items() if not v['passed']}))
        self.store.set(stage='ground-legacy-regressions');self.store.report()
        gate['regressions']=self.regress(TASKS[7],ident,candidate);atomic(bundle/'chapter-gate.json',gate)
        if not gate['regressions']['passed']:raise Halt('Ground detail changed an accepted legacy mechanic')
        self.store.set(stage='fresh-ground-critique');self.store.report();gate['scope']=GROUND_TASK['id']
        atomic(bundle/'scoped-gate.json',gate);review=self.review(GROUND_TASK,ident,bundle,gate)
        record=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(bundle/'ground-outcome.json',record);self.store.set(street_ground_outcome=record)
        self.store.event('street-ground-qualified-scope',**record);self.store.report()
        if not review.get('ok'):raise Halt('Ground critic supplied no complete verdict')
        self.revised_plan(ident);self.store.report()
        raise Halt('Ground scope and corrected next gameplay design saved; seal additive mission acceptance before implementation')

if __name__=='__main__':raise SystemExit(main(StreetGround))
