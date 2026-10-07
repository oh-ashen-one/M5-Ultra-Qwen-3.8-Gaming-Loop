#!/usr/bin/env python3
"""Local Qwen saves the first complete Counter-Exfil incident after native survey."""
import json
from qualify_qwen_capacity import CapacityAuthor
from resolve_death_pixel_review import SOURCE
from resume_three_day_queue import main
from continue_game_queue import ReadBoundEdits
from loop_controller.core import Files,Halt,atomic,read_json,sha
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool

TASK=dict(id='counter-exfil-first-incident',phase='mission',visual_facing=True,
    outcome='One local-authored physical three-runner chapter with explicit post-ending activation')
NEW={'Assets/Game/CounterExfilMission.cs','Assets/Game/CounterExfilRunner.cs'}
HUD='Assets/Game/MissionDirectorHud.cs'
READ={'Assets/Game/'+name for name in ('Combat.cs','InterceptionMission.cs','VehicleInteraction.cs',
    'DeathAuthority.cs','MissionDirectorHud.cs','Bootstrap.cs')}

def validate_boundary(old):
    expected=dict(status='paused',controller_pid=None,owned_process=None,
        source_checkpoint=SOURCE,last_playable_checkpoint=SOURCE,task_index=7,task_failures=24,
        failure_streak=1,diagnosis_used=True,overall_deadline_epoch=HARD_CAP_EPOCH,
        counter_exfil_preflight_attempted=True,
        blocker='Halt: Native westbound geometry recorded; local Qwen must implement the one-incident parent contract')
    survey=old.get('counter_exfil_preflight',{})
    if (any(old.get(k)!=v for k,v in expected.items()) or old.get('counter_exfil_source_attempted')
            or survey.get('candidate')!=SOURCE or not survey.get('build_id') or not survey.get('routes')):
        raise Halt('Require actual accepted-source native geometry before first incident implementation')

def survey_context(survey):
    value={k:survey[k] for k in ('scope','time','health','player','vehicle','actualBoxCenter','actualBoxSize','actualBoxScale')}
    value['routes']=[]
    for route in survey['routes']:
        value['routes'].append(dict(name=route['name'],capsuleClear=route['capsuleClear'],coupeClear=route['coupeClear'],
            groundedAndRendered=route['groundedAndRendered'],
            groundedAndRenderedUnion=route.get('groundedAndRenderedUnion'),
            support_interpretation='Original single-mesh footprint test can fail at a join; renderer union checks the whole footprint across both existing surfaces.',
            endpoints=[route['points'][0]['position'],route['points'][-1]['position']],
            obstacles=sorted({name for p in route['points'] for name in p['capsuleOverlaps']+p['coupeOverlaps']}),
            swept_obstacles=sorted({name for p in route['segments'] for name in p['capsuleHits']+p['coupeHits']}),
            overlap_positions=len(route['points']),swept_segments=len(route['segments'])))
    return value

def validate_source(path,content):
    if path not in NEW|{HUD}:raise ValueError('Only two new chapter modules and existing MissionDirectorHud integration are writable')
    for word in ('LoopRuntime','LoopInput.Replay','LoopCounterExfil','GetCommandLineArgs','Time.timeScale',
                 'Application.Quit','System.IO','System.Reflection','SetValue','DestroyImmediate'):
        if word in content:raise ValueError('Preserve external acceptance and ordinary game state; forbidden API '+word)
    # Existing HUD already contains reflection for legacy read-only signal access.
    # Its pre-existing using/read accessor is validated separately by the caller.

class ImplementCounterExfil(CapacityAuthor):
    author_context_tokens=98304
    author_output_tokens=32768
    focused_instruction=''
    context_files=READ
    writable_paths=NEW|{HUD}
    must_change={HUD}
    def validate_recovery(self,old):
        validate_boundary(old)
        self.survey=old['counter_exfil_preflight']
        self.resume_capacity=self.priority_resume=self.transport_recovery=self.admission_recovery=False
    def recovery_settings(self):
        return dict(counter_exfil_source_attempted=True,recovery_route='local-counter-exfil-source-after-native-survey',
            recovery_change='Implement the fixed one-incident parent contract now. Local Qwen creates source through bounded read-backed tools; preserve old chapters, camera, reticle, health and environment. No further broad planning role.')
    def work(self):
        ident=self.begin(TASK,'local-counter-exfil-source')
        files=Files(self.project,self.store);edits=ReadBoundEdits(files)
        baseline={str(p.relative_to(self.project)):sha(p.read_bytes()) for p in self.project.rglob('*')
            if p.is_file() and p.suffix in ('.cs','.shader','.py','.fbx','.blend')}
        original_hud=files.path(HUD).read_text()
        phase_before={p:files.path(p).read_text() if files.path(p).is_file() else None for p in self.writable_paths}
        def read(action,fields):
            if fields['path'] not in READ|NEW:raise ValueError('Read exact supplied APIs or new chapter modules only')
            return edits.read(action,fields)
        def protected():
            if any(sha(files.path(p).read_bytes())!=h for p,h in baseline.items() if p not in self.writable_paths):
                raise Halt('First incident changed a protected accepted source or asset')
        def check(path,content):
            if path not in self.writable_paths:raise ValueError('This focused phase may edit only: '+', '.join(sorted(self.writable_paths)))
            # Keep the existing legacy read-only accessor, but permit no new reflection.
            if path==HUD:
                old_accessor=original_hud[original_hud.index('        static string ReadStr('):]
                if old_accessor not in content:raise ValueError('Preserve existing HUD signal accessor')
                validate_source(path,content.replace('using System.Reflection;','').replace(old_accessor,''))
            else:validate_source(path,content)
        def checkpoint():
            protected();self.store.set(source_checkpoint=self.checkpoint_source('Local Qwen: first Counter-Exfil incident source'));self.store.report()
        def create(action,fields):
            if fields['path'] not in NEW:raise ValueError('Create only CounterExfilMission.cs or CounterExfilRunner.cs')
            check(fields['path'],fields['content']);result=edits.create(action,fields);checkpoint();return result
        def replace(action,fields):
            path=fields['path'];current=files.path(path).read_text()
            if not fields['old'] or current.count(fields['old'])!=1:raise ValueError('Use one exact current source span')
            check(path,current.replace(fields['old'],fields['new'],1))
            result=edits.replace(action,fields);checkpoint();return result
        def finish(_,fields):
            protected()
            if not all(files.path(p).is_file() for p in NEW) or any(files.path(p).read_text()==phase_before[p] for p in self.must_change):
                raise ValueError('Save the required actual current-phase edits before finishing')
            return dict(ok=True,local_authored=True,summary=fields['summary'],candidate=self.store.get('source_checkpoint'),
                changed_files=sorted(p for p in phase_before if files.path(p).read_text()!=phase_before[p]),native_verified=False,final_game_accepted=False)
        context=[]
        for path in sorted(self.context_files|({p for p in NEW if files.path(p).is_file()} if self.context_files==READ else set())):
            source=files.path(path).read_text()
            # Supply Bootstrap installation/Walker exactly; the protected Follow
            # class remains available through read_file if a concrete API is needed.
            last=source[:source.index('    public class Follow : MonoBehaviour')].count('\n') if path.endswith('/Bootstrap.cs') else len(source.splitlines())
            for start in range(1,last+1,200):
                value=read('context',dict(path=path,start_line=start,line_count=min(200,last-start+1)))
                context.append(path+' line'+str(start)+'\n'+value['content'])
        contract=(self.engines.source_root/'docs/COUNTER-EXFIL-ACCEPTANCE.md').read_text()
        self.c.update(working_context_tokens=self.author_context_tokens,output_tokens=self.author_output_tokens,model_timeout_seconds=600)
        result=self.model.session('builder',ident+'-counter-exfil-source',
            'You are local Qwen, sole substantive game-code author. The design is fixed. Save usable C# now through tools.',
            contract+'\n'+self.focused_instruction+'\nIMPLEMENTATION BOUNDARY: Save two compact modules CounterExfilMission.cs and CounterExfilRunner.cs '
            'and integrate installation/HUD in existing MissionDirectorHud.cs. No other existing source is writable. '
            'Combat already damages any genuinely hit live RivalAgent; reuse that exact API rather than editing combat. '
            'Install once via MissionDirectorHud.Install with its real player/camera; keep existing old death/failure '
            'priority and old ending visible. No changes to Bootstrap/Follow, DeathAuthority, old chapters, vehicle, '
            'existing rivals, assets or geometry. No hidden heal, state coercion, collider disabling, fake hits or '
            'test recognition. New runners reuse the original player prefab and real solid capsule/body. '
            'Use actual physical contact/obstruction to qualify live pins; a ray/proximity alone does not establish '
            'contact. Reset the uninterrupted timer on separation; moving the car releases a live pin immediately. '
            'Avoid permanently freezing a pinned live actor or caching pin resolution. Maintain exact three actor '
            'identities with their actual RivalAgent hp/alive, counts, active time and physical pin durations as '
            'ordinary public read-only observation state. Collision-aware runner movement must honor existing '
            'obstacles and gravity; no transform teleport traversal. Preserve exact normal R behavior even after '
            'Complete/Failed or death. Use native survey facts below to select a physically supported central '
            'path and exit; preflight is evidence, not game success. The survey uses thin renderer bounds as a '
            'support proxy and has not tested turning or driven travel. Supply runtime fail-closed checks where '
            'needed without detecting the harness. Solve the gameplay within this one incident, not a twelve-wave '
            'framework. Keep useful files <=400 lines and20KB each; split into the two modules. Save code promptly '
            'before polishing prose; use finish_task only after integration is complete. Every successful edit '
            'is checkpointed. Refresh read_file after editing before another replacement. '
            '\nREAD-ONLY INPUT/SIGNAL API: LoopSignals.Health float; Restarts/Shots/Hits/PursuitLevel int; '
            'Mode/Mission string (driving mode is vehicle); Player/Vehicle Transform. LoopInput.Pressed(KeyCode), '
            'Held(KeyCode),MoveX,MoveY are ordinary input. DeathAuthority.CurrentHealth() is a method. '
            '\nACTUAL NATIVE SURVEY:\n'+json.dumps(survey_context(self.survey))+
            '\nEXACT CURRENT SOURCE:\n'+'\n\n'.join(context),
            [tool('read_file','Read exact current source and hash;1..300lines.',{'path':{'type':'string'},
                'start_line':{'type':'integer','minimum':1},'line_count':{'type':'integer','minimum':1,'maximum':300}},['path']),
             tool('create_file','Save one complete NEW chapter module; never overwrite.',{'path':{'type':'string'},'content':{'type':'string'}}),
             tool('replace_text','Replace one exact current read-backed span.',{'path':{'type':'string'},'old':{'type':'string'},'new':{'type':'string'}}),
             tool('finish_task','Finish saved source; native acceptance remains independent.',{'summary':{'type':'string'}})],
            {'read_file':read,'create_file':create,'replace_text':replace,'finish_task':finish},turns=16,reasoning_effort='xhigh',
            retained_assistant=getattr(self,'retained_author',None),
            retained_instruction=getattr(self,'retained_instruction',None))
        self.finish_author(ident,result)

    def finish_author(self,ident,result):
        atomic(self.store.root/'evidence'/(ident+'-counter-exfil-author.json'),result)
        self.store.set(counter_exfil_source_outcome=result);self.store.report()
        if not result.get('ok'):raise Halt('Preserve usable local Counter-Exfil saves; complete source submission needs focused continuation')
        raise Halt('Local Counter-Exfil source saved; unload idle inference and qualify actual inputs and negatives')

if __name__=='__main__':raise SystemExit(main(ImplementCounterExfil))
