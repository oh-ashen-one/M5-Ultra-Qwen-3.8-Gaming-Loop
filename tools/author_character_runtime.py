#!/usr/bin/env python3
"""Local incremental importer, foot presentation and one-line installation."""
import json
from author_clothed_character import ACCEPTED,ART,TASK
from qualify_qwen_capacity import CapacityAuthor
from resume_three_day_queue import main
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.source_artifact import complete_csharp

SOURCE='c21818b5deec5e3d792e19893427586a76c940f0'
PRIOR='q0198-1d013de2'
IMPORTER='Assets/Game/PlayerClipImport.cs'
RUNTIME='Assets/Game/PlayerPresentation.cs'
BOOT='Assets/Game/Bootstrap.cs'
SAVED='Halt: Local character clip importer and foot playback saved; unload inference for native motion proof'


def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,source_checkpoint=SOURCE,
        last_playable_checkpoint=ACCEPTED,current_round=PRIOR,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        blocker='Halt: Clothed character exported and early native preview saved; inspect actual pixels then author runtime animation')
    preview=old.get('clothed_character_preview_outcome',{});review=old.get('clothed_character_cloud_pixel_review',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('character_foot_runtime_attempted')
            or preview.get('candidate')!=SOURCE or not preview.get('native_gate',{}).get('passed')
            or review.get('candidate')!=SOURCE or review.get('verdict')!='FIX'):
        raise Halt('Require the source-matched fresh native/import and actual pixel boundary')


def validate_component(source,importer=False):
    forbidden=('System.IO','System.Reflection','System.Diagnostics','LoopRuntime','LoopInput.Replay',
        'LoopInput.Elapsed','GetCommandLineArgs','Application.Quit','Time.timeScale','LoopCharacterObservation',
        'LoopPlayerDeathFixture','AssetDatabase','EditorApplication','UnityWebRequest','GetEnvironmentVariable')
    if any(x in source for x in forbidden):raise Halt('Presentation cannot inspect acceptance or external state')
    if importer:
        if (not source.lstrip().startswith('#if UNITY_EDITOR') or not source.rstrip().endswith('#endif')
                or 'Assets/Resources/Generated/player/scene.fbx' not in source):
            raise Halt('Only a conditional player-asset importer is allowed')
    elif any(x in source for x in ('UnityEditor','CharacterController.Move','Physics.','Rigidbody','PlayerPrefs')):
        raise Halt('Runtime presentation cannot author physics, editor or persistent state')
    return source


class CharacterRuntime(CapacityAuthor):
    def validate_recovery(self,old):
        validate_boundary(old)
        self.bundle=self.store.root/'evidence'/(PRIOR+'-character-preview')
        self.imported=read_json(self.bundle/'build/character-import.json')
        self.review=read_json(self.bundle/'cloud-pixel-review.json')
        if (not self.review.get('inspected_actual_pixels') or self.review.get('candidate')!=SOURCE
                or not self.imported.get('clips') or self.imported.get('defaultTakes')!=[
                    dict(name='Scene',takeName='Scene',firstFrame=1.0,lastFrame=279.0)]):
            raise Halt('Require the observed combined Blender timeline before local integration')
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(character_foot_runtime_attempted=True,recovery_route='local-importer-and-native-foot-animation-increments',
            recovery_change='Preserve original Blender clips and diagnosed aim/art defects. Local Qwen saves a player-only conditional importer, foot presentation and one exact installation line independently. All accepted mechanics and the external acceptance harness stay protected; native motion and gameplay tests remain mandatory.')
    def work(self):
        ident=self.begin(TASK,'local-character-clip-importer')
        files=Files(self.project,self.store)
        baseline={p:sha(p.read_bytes()) for p in self.project.rglob('*') if p.is_file() and p.suffix in ('.cs','.py','.fbx','.blend','.shader')}
        before_boot=files.path(BOOT).read_text()
        for name in (IMPORTER,RUNTIME):
            if files.path(name).exists():raise Halt('Never overwrite an existing presentation component')
        self.c.update(working_context_tokens=98304,output_tokens=getattr(self,'response_tokens',16384),model_timeout_seconds=600)
        phases=[('importer',IMPORTER,
            'Create one compact original C# asset-import component, at most120lines. Entire file starts '
            '#if UNITY_EDITOR and ends #endif, so no UnityEditor code enters the native player. It lives at '
            'Assets/Game/PlayerClipImport.cs; no external Editor/harness file is writable. Define an '
            'AssetPostprocessor which returns immediately for EVERY asset except the exact '
            'Assets/Resources/Generated/player/scene.fbx path. OnPreprocessModel must set this one model '
            'to Legacy animation with importAnimation enabled. OnPreprocessAnimation must split its '
            'observed Scene take into Idle1..61, Walk71..101, Jog111..135, Aim145..175, Board185..209, '
            'Drive219..279 at30fps. The actual default take firstFrame IS1 and lastFrame279, so preserve '
            'the observed offset: do not blindly subtract one. Use the real takeName from '
            'defaultClipAnimations. Loop Idle/Walk/Jog/Aim/Drive; Board is Once. Preserve mesh/material '
            'import, scale, static visual root/facing and all other assets. Do not generate curves, poses, '
            'root motion, events, files or acceptance data. No global AssetDatabase operations, reimport '
            'loops, reflection or scene/build modifications. This file only configures imported local '
            'original clip data through ModelImporter properties. Return only complete C# final content.\n'
            'ACTUAL IMPORT OBSERVATION:\n'+json.dumps(self.imported)),
            ('foot-playback',RUNTIME,
            'Create one compact original ChicagoGame.PlayerPresentation MonoBehaviour at most260lines '
            'with public static Install(GameObject body). This is FOOT PRESENTATION ONLY as a usable '
            'increment; vehicle boarding/driving presentation follows separately. Never change current '
            'VehicleInteraction, body/controller, camera, reticle, physics, ray aiming or mission behavior. '
            'Only animate the existing body child PlayerVisual using the six imported original Legacy '
            'clips at Resources Generated/player/scene. Add/reuse Animation on PlayerVisual, disable '
            'autoplay, and bind real imported AnimationClip assets by exact names. Avoid restarting clips '
            'every frame; support reliable looping and short crossfades. No procedural replacement '
            'poses, root movement, new meshes, fake animation state or dependence on acceptance/replay. '
            'Use actual horizontal body displacement to distinguish idle from locomotion; stop walking '
            'against a wall. Ordinary held LeftShift may select the Jog PRESENTATION cycle while moving, '
            'but real Walker speed remains3.2m/s and there is no new sprint mechanic. Without it use Walk. '
            'Idle plays on a living stationary foot actor. Aim responds to ordinary Mouse1 hold and a '
            'brief recent Mouse0 shot interval, without changing the actual Combat firing ray or trigger. '
            'Aim should use an upper-body mixing layer rooted at pivot_spine so hip/knee locomotion '
            'continues while aiming. Do not repair the diagnosed Blender weapon pose in C#; preserve it '
            'for a focused local art pass after real native playback. No runtime Euler/position posing. '
            'DeathAuthority.IsDead freezes/stops presentation, and the real LoopSignals.Restarts edge '
            'clears transient aim/gait state. Vehicle mode yields to the existing hidden PlayerVisual; '
            'never reactivate it or delay E. A later explicit vehicle increment will add DriverVisual. '
            'Handle return to foot/reset correctly. Keep all logic in this new component and use the '
            'concrete APIs below. Return only complete C# final content.\n'
            'API: LoopSignals.Player/Vehicle are Transform; Mode/Mission string; Health float; '
            'Restarts/Shots/Hits/PursuitLevel int. LoopInput.Held(KeyCode),Pressed(KeyCode),MoveX,MoveY '
            'are ordinary input. DeathAuthority.IsDead is public static bool. Bootstrap already creates '
            'and offsets PlayerVisual correctly and installs all gameplay. Your Install(body) will be '
            'called once immediately after HudStatus.Install(cam). Do not require camera changes or '
            'new input machinery. Visual FBX root has imported rotation/scale; leave it untouched. '
            'Native transform paths and clip data:\n'+json.dumps(self.imported))]
        outcomes=[]
        for label,path,instruction in phases:
            self.store.set(stage='local-character-'+label);self.store.report()
            session=ident+'-'+label
            self.model.session('builder',session,'You are local Qwen, sole author of original game presentation source. Save one small complete C# increment.',
                instruction+'\nUse supported xhigh, but finish this bounded component promptly. No tools, JSON, FILE markers or prose; one optional csharp code fence. '
                'This source is not accepted until real Unity compilation and motion checks pass.',
                [],{},turns=1,reasoning_effort='xhigh',tool_choice='none',
                retained_assistant=getattr(self,'retained_by_phase',{}).get(label),
                retained_instruction='Continue the exact retained local component without restarting analysis. Return the COMPLETE bounded C# source as final content NOW. No new features, tools, prose or JSON. Preserve the already specified API and player-only scope; save the usable component promptly with unchanged xhigh.')
            response=self.store.root/'private/sessions'/session/'response-000.json'
            source=validate_component(complete_csharp(read_json(response)),importer=label=='importer')
            if any(sha(p.read_bytes())!=h for p,h in baseline.items()):raise Halt('Existing source changed during local presentation authoring')
            files.create(ident+'-save-'+label,path,source)
            candidate=self.checkpoint_source('Local Qwen: original character '+label)
            outcomes.append(dict(phase=label,path=path,candidate=candidate,sha256=sha(source.encode()),response_sha256=sha(response.read_bytes())))
            self.store.set(source_checkpoint=candidate,character_runtime_saved_phases=outcomes);self.store.report()
        # The local author supplies the exact installation replacement as a
        # separate tiny artifact; the cloud controller never writes game logic.
        anchor='            HudStatus.Install(cam);\n'
        if before_boot.count(anchor)!=1:raise Halt('Require the exact existing install anchor')
        session=ident+'-install';self.store.set(stage='local-character-install');self.store.report()
        self.model.session('builder',session,'You are local Qwen. Return one tiny completed JSON installation patch.',
            'Your saved ChicagoGame.PlayerPresentation declares public static Install(GameObject body). '
            'Install it once immediately after the exact existing line below in Bootstrap.Create, using '
            'the already-created body variable. Preserve the old line exactly, indentation and a final '
            'newline. No other changes. Return ONLY {"old":<exact supplied line>,"new":<old line plus '
            'one installation call line>} as final JSON. No tools or prose.\n'+json.dumps(anchor),
            [],{},turns=1,reasoning_effort='xhigh',tool_choice='none')
        response=self.store.root/'private/sessions'/session/'response-000.json';d=read_json(response)
        choices=d.get('choices',[])
        if len(choices)!=1 or choices[0].get('finish_reason')!='stop' or choices[0]['message'].get('tool_calls'):
            raise Halt('Preserve partial components until a complete local installation patch arrives')
        content=choices[0]['message'].get('content','').strip()
        if content.startswith('```json\n') and content.endswith('\n```'):content=content[8:-4]
        patch=json.loads(content);new=patch.get('new','')
        if (patch.get('old')!=anchor or not new.startswith(anchor) or len(new.splitlines())!=2
                or new.splitlines()[1].strip()!='PlayerPresentation.Install(body);'):
            raise Halt('Only the local exact presentation install call may be added')
        files.edit(ident+'-save-install',BOOT,sha(before_boot.encode()),old=anchor,new=new)
        candidate=self.checkpoint_source('Local Qwen: install original foot presentation')
        if any(sha(p.read_bytes())!=h for p,h in baseline.items() if p!=files.path(BOOT)):
            raise Halt('Protected gameplay, art or assets changed')
        outcome=dict(candidate=candidate,prior_playable=ACCEPTED,prior_character_source=SOURCE,local_authored=True,
            phases=outcomes,install_response_sha256=sha(response.read_bytes()),native_verified=False,
            vehicle_presentation='pending separate local increment',known_pose_defects='preserved for native-backed local Blender repair')
        atomic(self.store.root/'evidence'/(ident+'-character-runtime-source.json'),outcome)
        self.store.set(source_checkpoint=candidate,character_foot_runtime_source_outcome=outcome,
            stage='local-character-runtime-source-saved');self.store.report();raise Halt(SAVED.removeprefix('Halt: '))

if __name__=='__main__':raise SystemExit(main(CharacterRuntime))
