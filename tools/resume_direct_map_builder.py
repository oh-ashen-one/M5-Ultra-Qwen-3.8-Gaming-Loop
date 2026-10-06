#!/usr/bin/env python3
"""Replace repeated non-submitting planning with bounded local source actions."""
from continue_game_queue import ContinuousRunner
from resume_three_day_queue import ThreeDayRunner, main
from resume_courier_qualification import NEXT_MAP
from qualify_map_extension import MAP_TASK, qualify_one_extension
from loop_controller.core import Files, Halt
from loop_controller.delivery_policy import HARD_CAP_EPOCH
from loop_controller.model import tool
from loop_controller.replay_contract import finish_tool, validate_submission
from loop_controller.runner import git
from loop_controller.small_edits import SelectedEdit

SOURCE='9062fb834071aa88fc374bce4181e48703a0f2ef'
ACCEPTED='d269dc43ac66c39afca4cb98ea53f9e7ed36806f'
ROUND='q0052-0380f1ce'
BLOCKER='Halt: Focused map plan completion did not submit; no automatic reattempt'
MODULE='Assets/Game/MapExtension.cs'
INSTALL_LINE='            WorldColliders.Install(new UnityEngine.Object[] { street, streetExt, props }, fencePrefab);'


def validate_direct_pause(old):
    expected=dict(source_checkpoint=SOURCE,last_playable_checkpoint=ACCEPTED,current_round=ROUND,
        task_index=7,task_failures=8,failure_streak=1,diagnosis_used=True,
        overall_deadline_epoch=HARD_CAP_EPOCH,blocker=BLOCKER,map_plan_completion_attempted=True)
    if any(old.get(k)!=v for k,v in expected.items()) or old.get('map_direct_builder_attempted'):
        raise Halt('Expected exact preserved map plan output-limit stop')
    if old.get('map_extension_plan') or old.get('accepted_map_extension'):
        raise Halt('Do not overwrite an existing map plan or acceptance')


def validate_module(content):
    if not isinstance(content,str) or len(content.encode())>10000 or len(content.splitlines())>170:
        raise ValueError('One compact module, maximum10000bytes/170lines')
    if 'class MapExtension' not in content or 'void Install(GameObject street)' not in content:
        raise ValueError('Required interface: ChicagoGame.MapExtension.Install(GameObject street)')
    return content


class DirectMapBuilder(ThreeDayRunner):
    def validate_recovery(self,old):
        validate_direct_pause(old)
        if git(self.repo,'diff','--name-only',ACCEPTED,SOURCE,'--','game'):
            raise Halt('Direct map work requires exact accepted fallback')
        if (self.project/MODULE).exists():raise Halt('Preserve an existing map module')

    def recovery_settings(self):return {'map_direct_builder_attempted':True}

    def edit(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().edit(task,ident)
        files=Files(self.project,self.store)
        bootstrap=files.path('Assets/Game/Bootstrap.cs').read_text().split('    public class Follow')[0]
        world=files.path('Assets/Game/WorldColliders.cs').read_text()
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='direct-local-map-module');self.store.report()
        def save(action,fields):
            return files.create(action,MODULE,validate_module(fields['content']))
        self.model.session('builder',ident+'-map-module',
            'You are the sole local Qwen game author. Make the bounded design in your implementation and save it now.',
            'The separate planner has failed twice without submitting; do not produce another planning essay. '
            'Call create_map_module with one compact complete original C# module, at most170lines/10000bytes. '
            'Namespace ChicagoGame; public static class MapExtension; public static void Install(GameObject street). '
            'A separate local-authored hookup will call Install(street) immediately after WorldColliders.Install. '
            'Choose and implement only one connected side extension suitable for walking and a car round trip. '
            'Keep the original forward end at Z30 and western boundary at X-1 intact so old collision probes work. '
            'A new side connection must replace only its relevant barrier segment with physically bounded opening; '
            'do not disable all collision or alter original actors/camera/missions. Use the already authored street '
            'and pavement meshes/materials by cloning or extracting existing instances, retaining their world/local '
            'basis correctly. No asset generation, primitive final art, extra package, scene file or new control. '
            'Create visibly connected support at the existing Y0.14 surface, wide enough for actual vehicle turning '
            'or reversing, reaching at least6m outside the old rectangle; make new outer obstacles visible and '
            'collidable. Choose a simple bounded geometry to make native input testing feasible. The existing '
            'GroundCollider is invisible support and cannot stand in for rendered paving. New flat ground names '
            'should describe their actual role as pavement/road/sidewalk for observation. No test inspection, '
            'LoopSignals mutation, teleport or special replay handling. Do not touch original Blender models. '
            'Save this one module now; no read tools or replay submission in this call.\nCURRENT BOOTSTRAP/WALKER:\n'+
            bootstrap+'\nCURRENT WORLD COLLISION:\n'+world,
            [tool('create_map_module','Save only the new bounded original map module.',{'content':{'type':'string'}})],
            {'create_map_module':save},turns=1,reasoning_effort='low')
        if not files.path(MODULE).exists():raise Halt('Direct map author saved no module; no automatic reattempt')
        saved=self.checkpoint_source('Local Qwen: implement one connected map extension module')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        raw=files.path('Assets/Game/Bootstrap.cs').read_text()
        line=next(i+1 for i,v in enumerate(raw.splitlines()) if v==INSTALL_LINE)
        edit=SelectedEdit(files,'Assets/Game/Bootstrap.cs',line,line,max_lines=3)
        self.store.set(stage='direct-local-map-hookup');self.store.report()
        def hook(action,fields):
            new=fields['content']
            if INSTALL_LINE.strip() not in new or 'MapExtension.Install(street);' not in new:
                raise ValueError('Preserve existing world installation and add the required map call')
            return edit.apply(action,new)
        self.model.session('builder',ident+'-map-hookup',
            'You are local Qwen making one exact small game-code hookup.',
            'Replace the single supplied line with itself followed by MapExtension.Install(street);. '
            'Do not change any other behavior. Call edit_selected_span now.\nEXACT CURRENT LINE:\n'+edit.old,
            [tool('edit_selected_span','Save the existing install line plus the new local-authored module invocation.',
                {'content':{'type':'string'}})],{'edit_selected_span':hook},
            turns=1,reasoning_effort='low')
        if files.path('Assets/Game/Bootstrap.cs').read_text()==raw:
            raise Halt('Saved map module was not hooked up; preserve source for diagnosis')
        saved=self.checkpoint_source('Local Qwen: install the connected map extension')
        self.store.set(source_checkpoint=saved,candidate_commit=saved)
        return self.propose_replay(task,ident)

    def propose_replay(self,task,ident):
        if task['id']!=MAP_TASK['id']:return super().propose_replay(task,ident)
        files=Files(self.project,self.store)
        paths=[MODULE,'Assets/Game/WorldColliders.cs','Assets/Game/VehicleInteraction.cs']
        source='\n\n'.join(p+'\n'+files.path(p).read_text() for p in paths)
        source+='\nBOOTSTRAP/WALKER:\n'+files.path('Assets/Game/Bootstrap.cs').read_text().split('    public class Follow')[0]
        self.c.update(output_tokens=8192,model_timeout_seconds=400)
        self.store.set(stage='local-map-replay');self.store.report()
        result=self.model.session('replay-author',ident+'-map-replay',
            'You are local Qwen submitting normal-input traversal of the actual saved map. No source editing.',
            'Call finish_task with exactly summary, duration, input_steps, captures. Each input step is '
            '{start,end,keys}; times are seconds from launch. Keep0..4 input-free; duration16..150seconds, '
            'at least4 increasing capture times before end. E presses at least0.25seconds. '
            'This is a MAP proof, not the old parcel-delivery mission: no pickup/delivery required. '
            'First walk at least6m beyond X-1..6 or Z-2..30, stay there at least1second, capture, physically '
            'walk back inside. Then approach the actual car, E enter, drive at least6m outside, stay at least1second, '
            'capture and physically drive back inside (reversing is allowed). Avoid R; reset teleport cannot '
            'establish either return. Use actual world-space walking and actual yaw/throttle controls shown below; '
            'capture the junction and each excursion/return. Fit the route to this implementation, not an assumed '
            'map. No source changes. Native evaluation, not this proposal, determines success.\nEXACT SOURCE:\n'+source,
            [finish_tool()],{'finish_task':lambda _,f:validate_submission(f,task)},
            turns=2,reasoning_effort='low')
        if not result.get('scenario'):raise Halt('Direct map replay was not submitted; saved source preserved')
        self.store.set(last_valid_replay=result['scenario'])
        self.store.event('map-replay-preflight',duration=result['scenario']['duration'],native_pass_claimed=False)
        return result

    def work(self):
        self.machine.guard()
        self.store.set(task_design=NEXT_MAP)
        qualify_one_extension(self,integrated_builder=True)
        self.store.set(task_design=NEXT_MAP,
            feedback={'accepted_connector':self.store.get('accepted_map_extension'),
                      'next_required_milestone':NEXT_MAP})
        return ContinuousRunner.work(self)


if __name__=='__main__':raise SystemExit(main(DirectMapBuilder))
