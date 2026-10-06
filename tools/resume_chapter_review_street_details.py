#!/usr/bin/env python3
"""Correct chapter evidence routing, then locally dress the existing east street."""
import json
import re
import shutil
from continue_game_queue import ContinuousRunner,ReadBoundEdits
from resume_east_dead_drop import EastDeadDrop,TASK,ACCEPTED
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,read_json,sha,verify_seal
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.small_edits import SelectedEdit
from loop_controller.continuous_tasks import TASKS
from loop_controller.street_detail_checks import inspect_details

SOURCE='3f5a0ef117c20fabf75d72495831ed75997af25b'
ROUND='q0098-2198d5a1'
PATH='Assets/Game/EastStreetDetail.cs'
INSTALL='Assets/Game/ConnectedStreet.cs'
HASHES={
    'chapter-gate.json':'809231e7b29d57f2bc0ab52b031bb32b8816a000cc88e4bb0a622c035461ac65',
    'critic.json':'f08e62f8dd0b91aed6dc76ac9b27f480236f0612ce3ac979e1917a286784696d',
    'chapter-outcome.json':'cff0336668ebc091ad9617711d2714fc64e6e50fce75a28f718a095065b421ea',
    'captures/manifest.json':'ae165522a2059a3c3f6446392d47e275906be07b63364ca68b874862f956a416',
    'captures/scenario.json':'d310895282f0f435ff78fe14f8c43a64534820180688c37f76e3824a9dc788d9',
}
CORRECTED={**TASK,'instructions':TASK['instructions']+
    ' There are TWO DIFFERENT objectives. Legacy courier DropPad/BeaconRing anchor=(1,.15,26), completed14.35s. '
    'The NEW RouteMission.Cache anchor=(50,.14,18), activation14.35s, vehicle arrival30.20s, E exit30.63s, '
    'close-foot F completion32.53s, R reset34.03s. Legacy Mission==complete does NOT mean the new chapter is complete. '
    'At15.2s the car is50m from the NEW cache, so that distance and the drive objective are correct. '
    'At30.27s distance5m; at30.97s actual on-foot approach3m; at33.10s chapter complete. '
    'The supplied frames now show the actual chapter, including on-foot approach. Judge their actual text overlap, '
    'actor visibility and marker readability honestly; do not conflate the legacy pad with the new cache. '
    'Any missing exact interaction image remains a visual-proof limitation, even with trace-proven F input.'}
ART_TASK={**CORRECTED,'phase':'polish','outcome':
    'Architectural relief makes the existing east-street enclosure read as building fronts while the entire chapter remains playable.',
    'instructions':CORRECTED['instructions']+
    ' Current visual scope is the NEW east-street facade dressing: actual visible windows, doors, projecting cornice '
    'and piers on existing south/north/east walls. Require coherent orientation/scale, readable surfaces and no '
    'floating geometry or route obstruction. Keep prior HUD clutter, neon cache and broader camera quality gaps '
    'explicitly open; this is not a whole-street/final-art waiver or ten-minute acceptance.'}

def validate_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=24,failure_streak=1,diagnosis_used=True,second_street_attempts=4,
        overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: East Dead-Drop scoped qualification recorded; preserve broader visual FIX and continue connected pacing')
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('chapter_review_street_details_attempted'):
        raise Halt('Require exact completed chapter qualification and unchanged failure history')
    outcome=old.get('east_dead_drop_outcome',{})
    if not outcome.get('native_pass') or outcome.get('accepted') or outcome.get('review',{}).get('verdict')!='FIX':
        raise Halt('Preserve the original chapter visual FIX')

def validate_module(content):
    if not isinstance(content,str) or len(content.splitlines())>120 or len(content.encode())>11000:
        raise ValueError('Save one compact decorative component within120lines/11KB')
    for term in ('LoopSignals','LoopInput','LoopRuntime','RouteMission','CourierMission','Collider','Rigidbody',
                 'Camera','Destroy','Instantiate','Resources.Load','UnityEditor','System.IO','CreatePrimitive',
                 'SetActive','Update(','.material =','.material='):
        if term in content:raise ValueError('Decorative mesh-only scope prohibits '+term)
    if not all(t in content for t in ('class EastStreetDetail','Install(GameObject parent)',
                                      'sharedMesh','sharedMaterials','EastStreetDetail','South','North','East')):
        raise ValueError('Require original mesh/material reuse and named three-sided detail root')
    if re.search(r'\b(?:src|source|street|mr|mf)\.transform\.\w+\s*=',content):
        raise ValueError('Never mutate the source assembly')
    return content

class ChapterReviewStreetDetails(EastDeadDrop):
    def validate_recovery(self,old):
        validate_pause(old)
        bundle=self.store.root/'evidence'/ROUND
        for name,digest in HASHES.items():
            if sha((bundle/name).read_bytes())!=digest:raise Halt('Original chapter evidence changed: '+name)
        verify_seal(bundle/'captures',HASHES['captures/manifest.json'])
        gate=read_json(bundle/'chapter-gate.json')
        regs=gate.get('regressions',{}).get('regressions',[])
        if (not gate.get('passed') or len(regs)!=10 or
            not all(x['gate'].get('passed') and x['gate'].get('candidate_commit')==SOURCE for x in regs)):
            raise Halt('Require all unchanged current-source native regressions')
        if (self.project/PATH).exists():raise Halt('Never overwrite an unrelated component')

    def recovery_settings(self):
        return dict(chapter_review_street_details_attempted=True,
            recovery_route='correct-chapter-evidence-then-local-facade-dressing',
            recovery_change='Preserve wrong-frame critic; correct dispatch and separate anchors; reuse sealed native proof; then bounded original facade relief')

    def source(self,ident):
        files=Files(self.project,self.store);edits=ReadBoundEdits(files)
        raw=(self.project/INSTALL).read_text()
        art=(self.project/'Art/street.py').read_text()[:5700]
        self.c.update(output_tokens=6144,model_timeout_seconds=320)
        self.store.set(stage='local-east-street-facade-module');self.store.report()
        def create(action,f):return edits.create(action,dict(path=PATH,content=validate_module(f['content'])))
        self.model.session('builder',ident+'-facade',
            'You are local Qwen, sole substantive game/art author. Save a compact static mesh-reuse component.',
            'Create Assets/Game/EastStreetDetail.cs, namespace ChicagoGame, static class EastStreetDetail, '
            'public static void Install(GameObject parent). Dress the existing bare east street with coherent original '
            'windows/doors/stone trim/cornices/piers. No new primitive geometry, assets, exports, scripts on objects, '
            'physics, lights, HUD or mission changes. Create only new GameObjects with Transform, MeshFilter and '
            'MeshRenderer; assign original sharedMesh/sharedMaterials. Never clone the whole Street or add colliders. '
            'Select ONE actual GameObject.Find("Street") as the source; two existing roots share that name but either '
            'works if offsets are relative to ITS actual transform.position. Its facade front faces +worldX, and its '
            '12m width runs along worldZ, centered on the root Z. Source root has Y0. Source front-plane X equals '
            'rootX. A window center is rootX+0.07, doors/trim are +0.06..0.59 into the street. Preserve source '
            'world mesh orientation and lossyScale; do not assume Blender axes are Unity axes. Read ONLY this root\'s '
            'GetComponentsInChildren<MeshRenderer>(); filter exact facade_base/facade_belt/cornice_bed/cornice and '
            'prefixes win,door,pier,dentil. EXCLUDE facade_wall, ef_, roof, chimney, stoop, planter, fireesc, all ground '
            'and props. Never change the source transforms/materials. New root named EastStreetDetail under parent. '
            'Use seven assemblies named South-0..2, North-0..2, East-0. Three south centers atX28.5,41,53.5/Y0/Z8, '
            'rotation about worldY -90deg; three north centers sameX/Y0/Z28, Y+90deg; east centerX60/Y0/Z18,Y180deg. '
            'These rotations face the original front inward. To place each selected mesh: new world position = '
            'assemblyCenter + yawRotation*(originalRenderer.transform.position - originalStreet.transform.position); '
            'new world rotation = yawRotation*originalRenderer.transform.rotation; new unit-root localScale = '
            'originalRenderer.transform.lossyScale. Assembly/root parents must remain unit scale/identity rotation '
            'if using these world transforms. Name each mesh by its original name beneath its assembly for independent '
            'inventory checks. This keeps relief within0.65m of walls and clear of driving corridor/cache. '
            'Existing walls/colliders/pavement and material colors remain unchanged. Null-check missing mesh/material '
            'components. Save <=120lines now via create_facade_module, then a separate tool call will install it. '
            '\nEXACT CONNECTED STREET:\n'+raw+'\nORIGINAL ART GEOMETRY:\n'+art,
            [tool('create_facade_module','Save the one original-mesh facade component.',{'content':{'type':'string'}})],
            {'create_facade_module':create},turns=1,reasoning_effort='low')
        if not (self.project/PATH).exists():raise Halt('Local facade module was not saved')
        candidate=self.checkpoint_source('Local Qwen: reuse original architectural facade details on east street')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate)
        needle='            AddFill(parent, new Vector3(50f, 4f, 18f), 20f, 2.5f);'
        if raw.count(needle)!=1:raise Halt('Unique street installation anchor changed')
        line=raw[:raw.index(needle)].count('\n')+1;edit=SelectedEdit(files,INSTALL,line,line,max_lines=3)
        def install(action,f):
            if re.sub(r'\s+','',f['content'])!=re.sub(r'\s+','',needle)+'EastStreetDetail.Install(parent);':
                raise ValueError('Preserve existing fill and add only the new facade install')
            return edit.apply(action,f['content'])
        self.c.update(output_tokens=1024,model_timeout_seconds=90)
        self.model.session('builder',ident+'-facade-install',
            'You are local Qwen installing your saved original-mesh facade component.',
            'Keep this exact line and add EastStreetDetail.Install(parent); immediately after it. No other changes.\n'+edit.old,
            [tool('edit_selected_span','Install the saved facade once.',{'content':{'type':'string'}})],
            {'edit_selected_span':install},turns=1,reasoning_effort='low')
        if (self.project/INSTALL).read_text()==raw:raise Halt('Saved facade component has no installation')
        candidate=self.checkpoint_source('Local Qwen: install east street architectural relief')
        self.store.set(source_checkpoint=candidate,candidate_commit=candidate);return candidate

    def work(self):
        original=self.store.root/'evidence'/ROUND
        ident=self.begin(CORRECTED,'corrected-chapter-frame-review')
        bundle=self.store.root/'evidence'/ident;bundle.mkdir()
        shutil.copytree(original/'captures',bundle/'captures')
        gate=read_json(original/'chapter-gate.json');atomic(bundle/'scoped-gate.json',gate)
        atomic(bundle/'evidence-reuse.json',dict(original_round=ROUND,hashes=HASHES,
            native_rerun=False,source_unchanged=SOURCE,reason='Legacy mission selector overwrote chapter frame selection'))
        self.store.set(next_task='Local original facade relief; same chapter replay and all ten regressions')
        self.store.report();review=self.review(CORRECTED,ident,bundle,gate)
        record=dict(candidate=SOURCE,evidence=str(bundle.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),
            original_fix_preserved=True,final_game_accepted=False)
        atomic(bundle/'chapter-corrected-review.json',record)
        self.store.set(east_dead_drop_corrected_review=record)
        self.store.event('chapter-review-routing-corrected',**record)
        if not review.get('ok'):raise Halt('Corrected chapter review supplied no complete verdict')
        findings=self.store.get('deferred_visual_findings',[])
        findings.append(dict(scope='Chapter presentation',candidate=SOURCE,review=review,
            disposition='Preserved during independent facade scope; no final visual waiver'))
        self.store.set(deferred_visual_findings=findings)
        ident=self.begin(ART_TASK,'local-east-street-facade-module');candidate=self.source(ident)
        probe=read_json(original/'captures/scenario.json')
        self.store.set(stage='native-east-street-facade-route');self.store.report()
        bundle,gate=self.chapter_native(ident,candidate,probe)
        if not gate.get('passed'):raise Halt('Facade dressing changed the proven native chapter route')
        before=read_json(original/'captures/scene-transforms.json')['objects']
        after=read_json(bundle/'captures/scene-transforms.json')['objects']
        detail=inspect_details(before,after);gate['facade_details']=detail
        atomic(bundle/'chapter-gate.json',gate)
        if not detail['passed']:raise Halt('Native facade inventory failed: '+json.dumps(detail['failure']))
        self.store.set(stage='facade-legacy-regressions');self.store.report()
        gate['regressions']=self.regress(TASKS[7],ident,candidate)
        atomic(bundle/'chapter-gate.json',gate)
        if not gate['regressions']['passed']:raise Halt('Facade dressing changed an accepted legacy mechanic')
        self.store.set(stage='fresh-facade-critique');self.store.report()
        atomic(bundle/'scoped-gate.json',gate);review=self.review(ART_TASK,ident,bundle,gate)
        record=dict(candidate=candidate,evidence=str(bundle.relative_to(self.store.root)),native_pass=True,
            review=review,accepted=bool(review.get('ok') and review.get('verdict')=='PASS'),final_game_accepted=False)
        atomic(bundle/'facade-outcome.json',record);self.store.set(east_street_facade_outcome=record)
        self.store.event('east-street-facade-scope-recorded',**record);self.store.report()
        raise Halt('East street facade scope recorded; connected mission pacing and outstanding presentation remain')

if __name__=='__main__':raise SystemExit(main(ChapterReviewStreetDetails))
